# #!/bin/sh -x

set -Eeu

# git clean -d -x -f

if git clean -d -x -n | grep -q .; then
    echo "Unclean repo."
    exit 1
fi

python2 -V
python3 -V
twine --version

ver="$(python3 -c '
import sys
import ast

new_version_s = sys.argv[1]

filename = "./setup.py"
prefix = "VERSION = "
new_version_s = None

def process_line(line):
    global new_version_s
    if not line.startswith(prefix):
        return line
    line = line[len(prefix):]
    if not new_version_s:
        version = ast.literal_eval(line.strip())
        version = list(int(item) for item in version.strip().split("."))
        version[1] += 1
        new_version_s = ".".join("{}".format(piece) for piece in version)
    return prefix + repr(new_version_s) + "\n"

data = "".join(
    process_line(line)
    for line in open(filename))
assert new_version_s, data
with open(filename, "w") as fobj:
    fobj.write(data)
print(new_version_s)
' \
  "${EXPLICIT_NEW_VERSION:-}"
)"

git commit -am "$ver"
git tag "$ver"
git push
git push --tags
python3 ./setup.py sdist bdist_wheel
python2 ./setup.py bdist_wheel
twine upload dist/*
git clean -d -x -f
