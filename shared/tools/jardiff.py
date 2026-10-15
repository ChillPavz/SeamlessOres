"""Compare two sets of built jars ENTRY FOR ENTRY: the proof that a reshuffle changed nothing.

    py -3 shared/tools/jardiff.py <before dir> <after dir> [--version OLD:NEW] [--allow PATTERN ...]

Every jar in <before> is paired with the jar of the same name in <after> (with --version, the after
jar's name and content may carry NEW where the before jar has OLD, at the same length, so the swap is
byte-exact). Each entry is reported as identical, changed only in line endings, changed, added or
removed. --allow takes fnmatch patterns of entry names whose change is expected (each still printed).
Exit 1 on any difference not allowed, or on a jar missing from either side.

Run it before and after any move between source folders, any build-script change and any toolchain
change, on every band's jars; the rule is in the maintainer notes' monolith convention.
"""
import argparse
import fnmatch
import os
import sys
import zipfile


def entries(path):
    with zipfile.ZipFile(path) as z:
        return {n: z.read(n) for n in z.namelist() if not n.endswith("/")}


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("before")
    ap.add_argument("after")
    ap.add_argument("--version", help="OLD:NEW, a version string that may differ, same length")
    ap.add_argument("--allow", nargs="*", default=[], help="entry patterns whose change is expected")
    ap.add_argument("--all", action="store_true", help="also compare -sources and -javadoc jars")
    args = ap.parse_args()

    old = new = None
    if args.version:
        old, new = args.version.split(":", 1)
        if len(old) != len(new):
            sys.exit("--version OLD and NEW must have the same length")
    skip = () if args.all else ("-sources.jar", "-javadoc.jar")
    jars = sorted(f for f in os.listdir(args.before) if f.endswith(".jar") and not f.endswith(skip))
    if not jars:
        sys.exit(f"no jars in {args.before}")
    bad = 0
    for name in jars:
        other = name.replace(old, new) if old else name
        b_path = os.path.join(args.after, other)
        if not os.path.isfile(b_path):
            print(f"MISSING {other} in {args.after}")
            bad += 1
            continue
        a, b = entries(os.path.join(args.before, name)), entries(b_path)
        same = eol = subst = 0
        problems, allowed = [], []
        for n in sorted(set(a) | set(b)):
            kind = None
            if n not in b:
                kind = "removed"
            elif n not in a:
                kind = "added"
            elif a[n] == b[n]:
                same += 1
            elif old and a[n].replace(old.encode(), new.encode()) == b[n]:
                subst += 1
            elif a[n].replace(b"\r\n", b"\n") == b[n].replace(b"\r\n", b"\n"):
                eol += 1
                kind = "eol-only"
            else:
                kind = "changed"
            if kind:
                (allowed if any(fnmatch.fnmatch(n, p) for p in args.allow) else problems).append(f"{kind:8} {n}")
        verdict = "IDENTICAL" if not problems and not allowed and not eol else ("ok" if not problems else "DIFFERS")
        extra = f", {subst} only {old}->{new}" if subst else ""
        print(f"{verdict:9} {name}: {len(b)} entries, {same} identical{extra}")
        for p in allowed:
            print(f"   allowed  {p}")
        for p in problems:
            print(f"   PROBLEM  {p}")
        bad += bool(problems)
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
