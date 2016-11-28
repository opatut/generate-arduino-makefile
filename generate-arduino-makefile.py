#!/usr/bin/env python3

# This tool generates a Makefile for building Arduino CPP projects.
# It reads the hardware specifiation according to the arduino IDE 3rd party guidelines from
#
#     https://github.com/arduino/Arduino/wiki/Arduino-IDE-1.5-3rd-party-Hardware-specification
#
# However, your project structure will be different.

from itertools import chain
from glob import glob
import re
import os
import argparse
from os.path import join, abspath, isabs, basename, dirname, expanduser, isdir

parser = argparse.ArgumentParser(description='Generate a Makefile that performs compilation/upload actions just like the Arduino IDE.')
parser.add_argument('-b', '--board', help='select a board', required=True)
parser.add_argument('-v', '--vendor', help='select a platform vendor', required=True)
parser.add_argument('-a', '--architecture', '--arch', dest='arch', help='select a platform architecture', required=True)
parser.add_argument('-o', '--output', help='output Makefile at this path (default: stdout)')
parser.add_argument('-r', '--root-dir', dest='root_dir', help='root directory of the sketch', default=os.getcwd())
parser.add_argument('-n', '--name', help='project name')
parser.add_argument('-s', '--source-dir', dest='source_dir', help='source directory, relative to root or absolute', default='src')
parser.add_argument('-B', '--build-dir', dest='build_dir', help='build directory, relative to root or absolute', default='build')
parser.add_argument('-l', '--lib', '--library', dest='libraries', help='library to include', action='append')
parser.add_argument('-L', '--library-directory', dest='library_directories', help='where to search for libraries', action='append', default=[])
parser.add_argument('-V', '--verbose', help='talk a lot', action='store_true')
parser.add_argument('-C', '--compile-flags', help='more args for gcc', action='store')
parser.add_argument('-P', '--serial-port', dest='serial_port', default='/dev/ttyACM0')
args = parser.parse_args()

template_file = join(dirname(abspath(__file__)), "template.mk")
with open(template_file, "r") as f:
    template = f.read()

def find_hardware_path():
    hardware_root = expanduser("~/.arduino15/packages/{}/hardware/{}".format(args.vendor, args.arch))

    if not isdir(hardware_root) and args.vendor == "arduino":
        hardware_root = expanduser("/usr/share/arduino/hardware/{}".format(args.arch))

    if not isdir(hardware_root):
        raise Exception("Hardware folder not found: " + hardware_root)

    versions = sorted(os.listdir(hardware_root))

    if not versions:
        raise Exception("No versions found in hardware root " + hardware_root)

    return join(hardware_root, versions[-1])

hardware_path = find_hardware_path()

arduino_dirs = [
    hardware_path,
    dirname(hardware_path),
    abspath(expanduser("~/.arduino15/packages/arduino")),
    "/usr/share/arduino/",
]

ide_version = "10611"
root_dir = abspath(args.root_dir)
project_name = args.name or basename(root_dir)
source_dir = abspath(args.source_dir if isabs(args.source_dir) else join(root_dir, args.source_dir))
build_dir = abspath(args.build_dir if isabs(args.build_dir) else join(root_dir, args.build_dir))

properties = {
    "runtime.platform.path": arduino_dirs[0],
    "runtime.hardware.path": arduino_dirs[0],
    "runtime.ide.path": arduino_dirs[-1],
    "runtime.ide.version": "10611",
    "runtime.os": "linux",
    "ide_version": "{runtime.ide.version}",
    "build.path": build_dir,
    "build.project_name": project_name,
    "build.arch": args.arch.upper(),
    "serial.port.file": basename(args.serial_port),
}

# read hardware configurations
for filename in ["platform.txt", "boards.txt", "programmers.txt"]:
    with open(os.path.join(properties["runtime.platform.path"], filename), "r") as f:
        for line in f.readlines():
            line = line.strip()
            if line.startswith("#"): continue
            if not "=" in line: continue
            k, v = line.split("=", 1)
            properties[k] = v

# find tools
for arduino_dir in arduino_dirs:
    tools_dir = os.path.join(arduino_dir, "tools")

    if not os.path.isdir(tools_dir):
        continue


    for name in os.listdir(tools_dir):
        tool_dir = os.path.join(tools_dir, name)

        if not os.path.isdir(tool_dir):
            continue

        for version in os.listdir(tool_dir):
            version_dir = os.path.join(tool_dir, version)

            if not os.path.isdir(version_dir):
                continue

            properties["runtime.tools.{}.path".format(name)] = version_dir
            properties["runtime.tools.{}-{}.path".format(name, version)] = version_dir

def load_config():
    global properties

def interpolate(string, extras):
    return re.sub(r'{([^}]+)}', lambda m: get_config(m.group(1), extras), string)

def get_config(key, extras):
    # special cylcic dependency keys
    if key == "build.core.path":
        return os.path.join(
            get_config("runtime.hardware.path", extras),
            "cores",
            get_config("build.core", extras),
        )
    if key == "build.variant.path":
        return os.path.join(
            get_config("runtime.hardware.path", extras),
            "variants",
            get_config("build.variant", extras),
        )
    if key == "build.system.path":
        return os.path.join(
            get_config("runtime.hardware.path", extras),
            "system",
        )

    if not key.startswith(args.board + "."):
        try:
            return get_config("{}.{}".format(args.board, key), extras)
        except:
            pass

    if key in extras:
        return interpolate(extras[key], extras)
    elif key in properties:
        return interpolate(properties[key], extras)
    else:
        raise Exception("Key {} not found in properties.".format(key))

def get_source_code_pattern(language):
    return get_config("recipe.{}.o.pattern".format(language), dict(
        includes="$(INCLUDES)",
        source_file="$<",
        object_file="$@",
    ))

def get_core_archive_pattern():
    return get_config("recipe.ar.pattern", dict(
        object_file="$$obj",
        archive_file="core.a",
    ))

def get_extract_recipe(ext):
    return get_config("recipe.objcopy.{}.pattern".format(ext), {})

def get_combine_pattern():
    return get_config("recipe.c.combine.pattern", dict(
        object_files="$^",
        archive_file="core.a",
    ))


def get_upload_command():
    tool = get_config("upload.tool", {})
    ext = {
        "upload.verbose": "{tools." + tool + ".upload.params.verbose}" if args.verbose else "",
        "upload.quiet": "" if args.verbose else"{tools." + tool + ".upload.params.quiet}",
    }

    for subkey in list_keys("^tools." + tool + "\.(.*)$", 1):
        if subkey != "upload.pattern":
            ext[subkey] = get_config("tools." + tool + "." + subkey, ext)

    return get_config("tools.{}.upload.pattern".format(tool), ext)

def list_keys(regex, group=0):
    keys = properties.keys()
    keys = set([re.sub(r'\.(linux|windows|macos)$', '', key) for key in keys])
    keys = [re.match(regex, key) for key in keys]
    keys = [key for key in keys if key]
    keys = [key.group(group) for key in keys]
    return keys

extract_extensions = list_keys(r'^recipe\.objcopy\.([a-zA-Z0-9_-]+)\.pattern$', 1)

addLib = lambda x: os.path.join(x, "libraries")
library_directories = \
    [addLib(get_config("runtime.platform.path", {}))] \
    + list(map(addLib, arduino_dir)) \
    + args.library_directories

def find_library(lib):
    for library_directory in library_directories:
        path = os.path.join(library_directory, lib)
        if os.path.isdir(path):
            return path

    raise Exception("Library {} not found.".format(lib))

lib_dirs = [abspath(find_library(lib)) for lib in args.libraries or []]

include_paths = [
    get_config("build.core.path", {}),
    get_config("build.variant.path", {}),
    get_config("build.system.path", {}),
] + lib_dirs

include_paths = [abspath(p) for p in include_paths]

compiler_step_dirs = {
    '$(SRCDIR)': '$(OBJDIR)',
    '$(CORE_PATH)': '$(OBJDIR)/core',
    '$(VARIANT_PATH)': '$(OBJDIR)/core',
}
for lib_dir in lib_dirs:
    compiler_step_dirs[lib_dir] = '$(OBJDIR)/libs'

silent = '' if args.verbose else '@'
compiler_steps = ""
for source, target in compiler_step_dirs.items():
    compiler_steps +=  """
{target}/%.cpp.o: {source}/%.cpp
\t{silent}mkdir -p $(dir $@)
\t{silent}{recipe_cpp} {compile_flags}

{target}/%.S.o: {source}/%.S
\t{silent}mkdir -p $(dir $@)
\t{silent}{recipe_S} {compile_flags}

{target}/%.c.o: {source}/%.c
\t{silent}mkdir -p $(dir $@)
\t{silent}{recipe_c} {compile_flags}

    """.format(
        target=target,
        source=source,
        compile_flags=args.compile_flags or '',
        silent=silent,
        recipe_c=get_source_code_pattern("c"),
        recipe_S=get_source_code_pattern("S"),
        recipe_cpp=get_source_code_pattern("cpp"),
    )


reset = "{}/ard-reset-arduino --caterina {}".format(abspath(dirname(__file__)), args.serial_port)

# get the
result = template.format(
    build_dir=build_dir,
    core_path=get_config('build.core.path', {}),
    extract_targets=" ".join(["$(OBJDIR)/{}.{}".format(project_name, ext) for ext in extract_extensions]),
    extractions="\n".join("$(OBJDIR)/{}.{}: $(OBJS) $(OBJDIR)/{}.elf\n\t{}{}""".format(project_name, ext, project_name, '' if args.verbose else '@', get_extract_recipe(ext)) for ext in extract_extensions),
    includes=" ".join(["-I{}".format(include_path) for include_path in include_paths]),
    lib_dirs=" ".join(lib_dirs),
    project_name=project_name,
    recipe_combine=get_combine_pattern(),
    recipe_a=get_core_archive_pattern(),
    results=" ".join("$(OBJDIR)/{}.{}".format(project_name, ext) for ext in extract_extensions),
    silent=silent,
    source_dir=source_dir,
    upload=get_upload_command(),
    variant_path=get_config('build.variant.path', {}),
    compiler_steps=compiler_steps,
    reset=reset,
)

if args.output:
    with open(args.output, "w") as f:
        f.write(result)
else:
    print(result)
