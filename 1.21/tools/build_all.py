#!/usr/bin/env python3
"""Build every 1.21.x band from this one folder.

    py -3 tools/build_all.py              every band in versions/
    py -3 tools/build_all.py 1.21.4       just the bands named

Each band is `gradlew build -Pmc=<band>`. Jars carry the band's Minecraft version in their name,
so all bands sit side by side in each loader's build/libs. Gradle runs on JDK 24 here (Gradle
8.14.3 cannot run on 25); set JAVA_HOME to override.
"""
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
JDK = os.environ.get('JAVA_HOME', r'C:\Program Files\Java\jdk-24')


def main():
    known = sorted(f[:-len('.properties')] for f in os.listdir(os.path.join(ROOT, 'versions'))
                   if f.endswith('.properties'))
    bands = sys.argv[1:] or known
    unknown = [b for b in bands if b not in known]
    if unknown:
        sys.exit('unknown band(s) %s; known: %s' % (', '.join(unknown), ', '.join(known)))
    env = dict(os.environ, JAVA_HOME=JDK)
    gradlew = os.path.join(ROOT, 'gradlew.bat' if os.name == 'nt' else 'gradlew')
    for band in bands:
        print('== band %s' % band, flush=True)
        done = subprocess.run([gradlew, 'build', '-Pmc=' + band, '--console=plain', '-q'],
                              cwd=ROOT, env=env)
        if done.returncode:
            sys.exit('band %s failed to build' % band)


if __name__ == '__main__':
    main()
