"""Joins the 26.1.x and 26.3 builds into one jar per loader that runs on every 26.x version.

    ./gradlew build -Pmc=26.3
    ./gradlew build -Pmc=26.1.x
    python tools/merge_bands.py

The 26.1.x jar is compiled against the oldest version, and every reference in it outside the era261
worldgen classes resolves on 26.2 and 26.3 as well. What changed shape at 26.3 is the worldgen package
worldgen/era263, compiled against 26.3 and loaded by name only there (see Worldgen). So the merged jar
is the 26.1.x jar plus the 26.3 jar's era263 classes, with:
  - the access widener and transformer carrying both eras' lines (a line naming a class a version does
    not have is never applied there),
  - the Minecraft and NeoForge ranges widened from the lower band's floor to the upper band's ceiling.
Everything else must already be identical in both jars, byte for byte, shared classes and data alike
(each version's loot is a pack overlay), and the merge stops if it is not: a shared class that compiles
differently against 26.1.2 and 26.3 names something whose shape changed, and belongs in an era folder.
The two band jars are removed from build/libs afterwards, so only the file to upload is left.
"""

import os
import re
import sys
import zipfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MOD_ID = "seamlessores"
LOW, HIGH = "26.1.x", "26.3"
ERA_PACKAGE = f"com/chillpavz/{MOD_ID}/worldgen/"
AW = f"{MOD_ID}.accesswidener"
AT = "META-INF/accesstransformer.cfg"
FABRIC_META = "fabric.mod.json"
NEOFORGE_META = "META-INF/neoforge.mods.toml"
# Differ between the two builds by design; each is handled below.
MERGED = {AW, AT, FABRIC_META, NEOFORGE_META, "META-INF/MANIFEST.MF"}


def props(path):
    out = {}
    for line in open(path, encoding="utf-8"):
        if "=" in line and not line.lstrip().startswith("#"):
            k, v = line.split("=", 1)
            out[k.strip()] = v.strip()
    return out


def era_class(name, era):
    return name.startswith(ERA_PACKAGE + f"era{era}/") and name.endswith(".class")


def directives(text):
    return [line for line in text.splitlines() if line.strip() and not line.lstrip().startswith("#")]


def joined_access(low, high, label):
    """The lower band's file, plus every line only the upper band has, under a comment saying why."""
    extra = [line for line in directives(high) if line not in directives(low)]
    if not extra:
        return low
    note = f"# 26.3 ({label} of the {HIGH} build; one jar serves every 26.x version, and a line naming a class" \
           " a version does not have is never applied there):"
    return low.rstrip("\n") + "\n" + note + "\n" + "\n".join(extra) + "\n"


def widened(text, low_range, merged_range, what):
    if text.count(low_range) < 1:
        sys.exit(f"{what}: {low_range!r} not found; the band files and the metadata disagree")
    return text.replace(low_range, merged_range)


def merge(loader, version, low_p, high_p):
    libs = os.path.join(ROOT, loader, "build", "libs")
    low_jar = os.path.join(libs, f"{MOD_ID}-{loader}-{low_p['minecraft_version']}-{version}.jar")
    high_jar = os.path.join(libs, f"{MOD_ID}-{loader}-{high_p['minecraft_version']}-{version}.jar")
    for jar in (low_jar, high_jar):
        if not os.path.isfile(jar):
            sys.exit(f"missing {jar}: build both bands first (see the top of this file)")
    low, high = zipfile.ZipFile(low_jar), zipfile.ZipFile(high_jar)
    low_names = [n for n in low.namelist()]
    high_names = [n for n in high.namelist()]

    # Classes: the same set apart from the era classes, which each build has only its own of.
    low_classes = {n for n in low_names if n.endswith(".class") and not era_class(n, "261")}
    high_classes = {n for n in high_names if n.endswith(".class") and not era_class(n, "263")}
    if low_classes != high_classes:
        sys.exit(f"{loader}: the shared classes differ: {sorted(low_classes ^ high_classes)}")
    if any(era_class(n, "263") for n in low_names) or any(era_class(n, "261") for n in high_names):
        sys.exit(f"{loader}: a build carries the other era's classes; was it built with the wrong -Pmc?")
    era263 = [n for n in high_names if era_class(n, "263")]
    if not era263 or not any(era_class(n, "261") for n in low_names):
        sys.exit(f"{loader}: an era class is missing from its build")

    # Everything else byte-identical, shared classes and data included.
    others = ({n for n in low_names + high_names if not n.endswith(".class") and not n.endswith("/")}
              | low_classes) - MERGED
    differ = sorted(n for n in others if n not in low_names or n not in high_names or low.read(n) != high.read(n))
    if differ:
        sys.exit(f"{loader}: {len(differ)} files differ between the bands, e.g. {differ[:5]}")

    lo, hi = low_p["minecraft_version_range"], high_p["minecraft_version_range"]
    maven = lo.split(",")[0] + "," + hi.split(",")[1]                      # [26.1, 26.4)
    flo, fhi = low_p["fabric_minecraft_version_range"], high_p["fabric_minecraft_version_range"]
    semver = flo.split(" ")[0] + " " + fhi.split(" ")[1]                  # >=26.1 <26.4
    nlo, nhi = low_p["neoforge_version_range"], high_p["neoforge_version_range"]
    neo = nlo.split(",")[0] + "," + nhi.split(",")[1]

    out = os.path.join(libs, f"{MOD_ID}-{loader}-26.x-{version}.jar")
    with zipfile.ZipFile(out + ".tmp", "w", zipfile.ZIP_DEFLATED) as z:
        for info in low.infolist():
            data = low.read(info.filename)
            if info.filename == AW:
                data = joined_access(data.decode("utf-8"), high.read(AW).decode("utf-8"), "access widener").encode("utf-8")
            elif info.filename == AT:
                data = joined_access(data.decode("utf-8"), high.read(AT).decode("utf-8"), "access transformer").encode("utf-8")
            elif info.filename == FABRIC_META:
                data = widened(data.decode("utf-8"), f'"{flo}"', f'"{semver}"', FABRIC_META).encode("utf-8")
            elif info.filename == NEOFORGE_META:
                # The minecraft and neoforge dependencies; one replace covers both when the ranges match.
                text = widened(data.decode("utf-8"), f'"{lo}"', f'"{maven}"', NEOFORGE_META)
                if nlo != lo:
                    text = widened(text, f'"{nlo}"', f'"{neo}"', NEOFORGE_META)
                data = text.encode("utf-8")
            z.writestr(info, data)
        for name in era263:
            z.writestr(high.getinfo(name), high.read(name))
    low.close()
    high.close()
    os.replace(out + ".tmp", out)
    for jar in os.listdir(libs):
        if re.fullmatch(rf"{MOD_ID}-{loader}-(?!26\.x-)[\d.]+-{re.escape(version)}\.jar", jar):
            os.remove(os.path.join(libs, jar))
    print(f"{loader}: {os.path.relpath(out, ROOT)} (Minecraft {maven}, {len(era263)} era263 classes added)")


def main():
    version = props(os.path.join(ROOT, "gradle.properties"))["version"]
    low_p = props(os.path.join(ROOT, "versions", f"{LOW}.properties"))
    high_p = props(os.path.join(ROOT, "versions", f"{HIGH}.properties"))
    for loader in ("fabric", "neoforge"):
        merge(loader, version, low_p, high_p)


if __name__ == "__main__":
    main()
