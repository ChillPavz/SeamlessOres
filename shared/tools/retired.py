"""Retired block ids, every band: the generator side of RetiredBlocks.

An earlier release registered these ids and this one no longer builds them (the Cobblemon lore rule,
5.1.0; the geology rule in the game's own rock, the release after it). Each keeps a placeholder block that turns into its host stone; it is drawn as that stone until it
does. This writes its blockstate, block model and item model, and copies the band's list
(tools/<band>/retired_ids.json, a committed file that only ever grows) into the jar, where the mod reads it.
"""
import json
import os

from assetgen import write_json

MOD_ID = "seamlessores"


def write(list_path, hosts, assets_dir, resources_dir, item_definitions=False):
    """hosts: the band's placed.Hosts (look, side and end textures by host name). item_definitions: the
    band reads items/<id>.json (1.21.4 and up) rather than models/item. Returns the count."""
    rows = json.load(open(list_path, encoding="utf-8"))["retired"]
    for row in rows:
        cfg = hosts[row["host"]]
        name = row["id"]
        if cfg["look"] == "column":
            model = {"parent": "minecraft:block/cube_column", "textures": {"side": cfg["side"], "end": cfg["end"]}}
        elif cfg["look"] == "textures4":
            model = {"parent": "minecraft:block/cube_all", "textures": {"all": cfg["side"] + "0"}}
        elif cfg["look"] == "weighted":
            model = {"parent": "minecraft:block/cube_all", "textures": {"all": cfg["side"][0][0]}}
        else:
            model = {"parent": "minecraft:block/cube_all", "textures": {"all": cfg["side"]}}
        write_json(os.path.join(assets_dir, "models", "block", "retired", f"{name}.json"), model)
        write_json(os.path.join(assets_dir, "blockstates", f"{name}.json"),
                   {"variants": {"": {"model": f"{MOD_ID}:block/retired/{name}"}}})
        if item_definitions:
            write_json(os.path.join(assets_dir, "items", f"{name}.json"),
                       {"model": {"type": "minecraft:model", "model": f"{MOD_ID}:block/retired/{name}"}})
        else:
            write_json(os.path.join(assets_dir, "models", "item", f"{name}.json"),
                       {"parent": f"{MOD_ID}:block/retired/{name}"})
    write_json(os.path.join(resources_dir, MOD_ID, "retired_ids.json"),
               json.load(open(list_path, encoding="utf-8")))
    return len(rows)
