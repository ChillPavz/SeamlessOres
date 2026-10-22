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


def write(hosts, variants, retired_path, resources_dir):
    """hosts: the band's placed.Hosts; variants: its (host, cfg, ore, form, tier) list. Returns the
    number of renamed ids."""
    renamed = (json.load(open(hosts.renamed_path, encoding="utf-8"))["renamed"]
               if os.path.exists(hosts.renamed_path) else {})
    retired = {row["id"] for row in json.load(open(retired_path, encoding="utf-8"))["retired"]}
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
