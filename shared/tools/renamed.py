"""Variant ids and renamed ids, every band: the generator side of VariantIds.

6.0.0 named every variant by one rule (placed.id_of). A world or an inventory from an earlier release
still holds the old ids, so the band's tools/<band>/renamed_ids.json (committed; only ever grows) maps
each shipped old id to its new one, and the loaders register those as registry aliases. Its "kept"
entries are pairs that keep a shipped id because the rule would hand that id to another pair: an id
never changes meaning.

This writes seamlessores/ids.json into the jar: every variant's id by host and ore key (the Java side
reads it instead of naming anything itself) and the renamed list. It stops the build where an id would
be ambiguous: two variants with one id, or a variant taking an id that once meant something else.
"""
import json
import os

from assetgen import write_json

MOD_ID = "seamlessores"


def seed(hosts, variants, retired, retired_path, shipped_path):
    """Add to renamed_ids.json every id a release shipped (shipped_path: a JSON list of the block ids
    one band of that release registered) whose pair the id rule now names differently. Only adds. Prints
    the shipped ids that end up neither live, renamed nor retired: those would vanish from old worlds."""
    with open(hosts.renamed_path, encoding="utf-8") as fh:
        table = json.load(fh)
    shipped = set(json.load(open(shipped_path, encoding="utf-8")))
    renamed = table["renamed"]
    live = {hosts.name_of(host, ore) for host, _cfg, ore, _form, _tier in variants}
    added, clash = {}, []
    for host, _cfg, ore, _form, _tier in variants:
        old, new = hosts.legacy_name_of(host, ore), hosts.name_of(host, ore)
        if old == new or old not in shipped or old in renamed or old in retired:
            continue
        if old in live:
            clash.append(f"{host}|{ore['key']}: shipped {old}, which the rule now gives another pair")
            continue
        added[old] = new
    renamed.update(dict(sorted(added.items())))     # appended: the lines already there never move
    with open(hosts.renamed_path, "w", encoding="utf-8") as fh:
        json.dump(table, fh, indent=2)
        fh.write("\n")
    print(f"  seed {os.path.basename(shipped_path)}: {len(added)} renamed ids added")
    for line in clash:
        print(f"  seed CLASH {line}")
    # A shipped id this release neither builds nor renames is RETIRED: a placeholder that turns into its
    # host stone, so the block does not vanish from an old world. Its host is the longest host name it
    # starts with; an id with no known host is only reported.
    lost = sorted(shipped - live - set(renamed) - retired)
    with open(retired_path, encoding="utf-8") as fh:
        rtable = json.load(fh)
    names = sorted(hosts.keys(), key=len, reverse=True)
    orphans = []
    for old in lost:
        host = next((h for h in names if old.startswith(h + "_") and old.endswith("_ore")), None)
        if host is None:
            orphans.append(old)
            continue
        rtable["retired"].append({"id": old, "host": host, "ore": old[len(host) + 1:-len("_ore")]})
    with open(retired_path, "w", encoding="utf-8") as fh:
        json.dump(rtable, fh, indent=1)
        fh.write("\n")
    print(f"  seed: {len(lost) - len(orphans)} shipped ids retired")
    if orphans:
        print(f"  seed: {len(orphans)} shipped ids with no known host, NOT handled: {orphans}")


def write(hosts, variants, retired_path, resources_dir):
    """hosts: the band's placed.Hosts; variants: its (host, cfg, ore, form, tier) list. Returns the
    number of renamed ids. With SO_SEED_SHIPPED set to a shipped-id list, seeds renamed_ids.json first."""
    retired = {row["id"] for row in json.load(open(retired_path, encoding="utf-8"))["retired"]}
    if os.environ.get("SO_SEED_SHIPPED"):
        seed(hosts, variants, retired, retired_path, os.environ["SO_SEED_SHIPPED"])
        retired = {row["id"] for row in json.load(open(retired_path, encoding="utf-8"))["retired"]}
    renamed = (json.load(open(hosts.renamed_path, encoding="utf-8"))["renamed"]
               if os.path.exists(hosts.renamed_path) else {})
    ids = {}
    for host, cfg, ore, form, tier in variants:
        ids[f"{host}|{ore['key']}"] = hosts.name_of(host, ore)
    seen = {}
    for pair, name in ids.items():
        if name in seen:
            raise SystemExit(f"{seen[name]} and {pair} would both be {MOD_ID}:{name}")
        seen[name] = pair
        if name in renamed or name in retired:
            raise SystemExit(f"{pair} would take {MOD_ID}:{name}, which an earlier release used for another"
                             f" block: keep that pair's shipped id in {hosts.renamed_path} (\"kept\")")
    # A renamed id whose new block is gone is covered when its OLD id is retired: the old id is then a
    # placeholder that turns into its stone (a pair the geology or lore rule cut after the rename).
    missing = sorted(old for old, new in renamed.items() if new not in seen and new not in retired
                     and old not in retired)
    if missing:
        print(f"  renamed ids whose new block this band does not build (left unconverted): {missing}")
    write_json(os.path.join(resources_dir, MOD_ID, "ids.json"), {"ids": ids, "renamed": renamed})
    return len(renamed)
