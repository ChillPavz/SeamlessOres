"""Parity with the ore a variant stands in for: the tags it is in and the cooking recipes it has.

Both are read from the source ore's own jars at generation time and written as plain files, so a
variant is mined by the same tools, angers the same piglins and smelts in the same furnace as the
ore it replaces, on every loader, with nothing patched at run time.

TAGS. Every block and item tag that lists the source ore (nested references resolved) is mirrored for
the variant, except the ones each band already writes itself (HANDLED) and the ones a person decided
against in source_tags.json. Copying blindly is wrong for a few tags: Ice and Fire PLACES blocks from
its dragon_cave_*_ores lists, Occultism drops items from drop_from/*. So a tag nobody has reviewed yet
stops the run, and the fix is one line in source_tags.json, "copy" or "skip".

COOKING. Every minecraft:smelting and minecraft:blasting recipe in the source ore's OWN jar (the game's
for a vanilla ore) whose ingredient names the ore item directly gets a copy taking the variant instead.
A recipe whose ingredient is a tag needs none: the tag copy above already puts the variant in it.
"""

import copy
import fnmatch
import json
import os
import re
import sys
import zipfile

from assetgen import jar_tags

POLICY = os.path.join(os.path.dirname(os.path.abspath(__file__)), "source_tags.json")

# What each band's generate_data already writes for a variant, by its own rules: the pickaxe and tier
# tags, the source mod's own needs_* tags, the convention ore and ground tags (c: from 1.20.5, c: and
# forge: on the older bands, with 1.20.1's c:<ore>_ores shape in its parity tags; a mod that still
# ships that shape on a later band names a convention nothing reads there). incorrect_for_* is derived by
# the game from the needs_* tags.
HANDLED = re.compile(r"^(minecraft:mineable/pickaxe|[a-z0-9_.-]+:needs_[^/]+|minecraft:incorrect_for_.+"
                     r"|(c|forge|neoforge):ores(/.+)?|(c|forge|neoforge):ores_in_ground/.+"
                     r"|(c|forge):[a-z0-9_]+_ores)$")

COOKING = ("minecraft:smelting", "minecraft:blasting")


def _load_policy():
    with open(POLICY, encoding="utf-8") as handle:
        policy = json.load(handle)
    return policy["copy"], policy["skip"]


def _matches(tag, entries):
    """Whether a tag is named in a policy table: exactly, or by a pattern with '*' in it."""
    return tag in entries or any("*" in key and fnmatch.fnmatchcase(tag, key) for key in entries)


class SourceTags:
    """Every block and item tag in a set of jars, resolved, and which of them a variant copies.

    jars: every jar whose tags count (the game's and every mod's of the run). Collect what each
    variant needs with tags_for(); call check() once afterwards: it stops the run on a tag nobody has
    reviewed, naming them all at once.
    """

    def __init__(self, jars):
        self.members = {"block": {}, "item": {}}
        for path in jars:
            if not path or not os.path.exists(path):
                continue
            with zipfile.ZipFile(path) as jar:
                for kind, table in self.members.items():
                    for tag, members in jar_tags(jar, kind).items():
                        table.setdefault(tag, set()).update(members)
        self.copy, self.skip = _load_policy()
        self.unreviewed = {}

    def tags_for(self, source_id):
        """(kind, "namespace:path") of every tag the variant of source_id joins."""
        found = []
        for kind, table in self.members.items():
            for tag, members in sorted(table.items()):
                if source_id not in members or HANDLED.match(tag) or _matches(tag, self.skip):
                    continue
                if _matches(tag, self.copy):
                    found.append((kind, tag))
                else:
                    self.unreviewed.setdefault(f"{kind} {tag}", source_id)
        return found

    def check(self):
        if self.unreviewed:
            lines = "\n".join(f"     {key}  (e.g. {source})" for key, source in sorted(self.unreviewed.items()))
            sys.exit(f"  !! {len(self.unreviewed)} tags list a source ore and are in neither list of "
                     f"{os.path.relpath(POLICY)}. Decide each one (copy: the variant joins it; skip: it "
                     f"does not) and run again:\n{lines}")


def add_tag_entries(target, tags, entry):
    """Adds one variant's entry to {(kind, tag): [entries]} for every tag tags_for returned."""
    for key in tags:
        target.setdefault(key, []).append(entry)


_RECIPES = {}


def _cooking_recipes(jar_path):
    """[(path in jar, recipe)] of every smelting and blasting recipe in a jar, read once per jar."""
    if jar_path not in _RECIPES:
        found = []
        with zipfile.ZipFile(jar_path) as jar:
            for name in jar.namelist():
                if re.match(r"^data/[^/]+/recipes?/.+\.json$", name):
                    try:
                        recipe = json.loads(jar.read(name))
                    except ValueError:
                        continue
                    if isinstance(recipe, dict) and recipe.get("type") in COOKING:
                        found.append((name, recipe))
        _RECIPES[jar_path] = found
    return _RECIPES[jar_path]


def _names(ingredient, item_id):
    """Whether an ingredient names the item directly, in any of the game's spellings: "id" (1.21.2 on),
    {"item": "id"} (up to 1.21.1), or a list of either."""
    if isinstance(ingredient, str):
        return ingredient == item_id
    if isinstance(ingredient, dict):
        return ingredient.get("item") == item_id
    if isinstance(ingredient, list):
        return any(_names(part, item_id) for part in ingredient)
    return False


def _swapped(ingredient, item_id, our_id):
    """The ingredient as the variant alone, in the spelling of the element that named the source."""
    if isinstance(ingredient, list):
        return [_swapped(next(p for p in ingredient if _names(p, item_id)), item_id, our_id)]
    if isinstance(ingredient, dict):
        return {**ingredient, "item": our_id}
    return our_id


def _as_string(ingredient, path, jar_path):
    """The ingredient in the plain spelling of 1.21.2 on: "id", "#tag", or a list of those."""
    if isinstance(ingredient, list):
        return [_as_string(part, path, jar_path) for part in ingredient]
    if isinstance(ingredient, dict):
        if set(ingredient) == {"item"}:
            return ingredient["item"]
        if set(ingredient) == {"tag"}:
            return "#" + ingredient["tag"]
        sys.exit(f"  !! {path} in {os.path.basename(jar_path)}: ingredient {ingredient} has no plain spelling")
    return ingredient


def cooking_copies(jar_path, source_id, our_id, name, item_strings=False):
    """{file stem: recipe} for the variant `name`: each cooking recipe of the source ore's own jar that
    names the ore item, with the variant in its place. Group, category, time, experience and result
    are the source's own, so the recipe book shows the variant beside the ore. A source recipe that
    carries load conditions of its own stops the run: merging them with ours is unchecked.

    item_strings: the band reads ingredients as a plain id or a list (1.21.2 on). A source jar read
    as a stand-in (a build made for an older game) may still spell {"item": id}, which those versions
    reject: the recipe then fails to load and the variant cannot be smelted. Our copy is written as
    the plain id whatever the source spelled."""
    copies = {}
    for path, recipe in _cooking_recipes(jar_path):
        if not _names(recipe.get("ingredient"), source_id):
            continue
        if any("condition" in key for key in recipe):
            sys.exit(f"  !! {path} in {os.path.basename(jar_path)} has load conditions of its own; "
                     f"its copy for {name} would need them merged with ours")
        recipe = copy.deepcopy(recipe)
        recipe["ingredient"] = _swapped(recipe["ingredient"], source_id, our_id)
        if item_strings:
            recipe["ingredient"] = _as_string(recipe["ingredient"], path, jar_path)
        stem = f"{name}_{recipe['type'].split(':')[1]}"
        n = 2
        while stem in copies:
            stem = f"{name}_{recipe['type'].split(':')[1]}_{n}"
            n += 1
        copies[stem] = recipe
    return copies
