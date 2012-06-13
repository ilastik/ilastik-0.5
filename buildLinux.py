# -*- coding: utf-8 -*-
import os, sys, string

import PackagesGlobals

def copy_files(build_dir, bin_dir, name_print):
    cmd = ("cd " + build_dir + " && pwd && " + name_print + "| cpio -dmp "
           + os.getcwd() + "/" + bin_dir)
    print cmd
    sys.stdout.flush()
    os.system(cmd)

build_dir = os.environ["HOME"] + "/ilastik-build"
bin_dir = "linux-bin"
pythonVersion = PackagesGlobals.python_version()
release_file  = PackagesGlobals.release_default_name()

os.system("rm -Rf " + bin_dir + "/*")


python_dirs = open(build_dir + "/directory.list").read().splitlines()

copy_files(build_dir, bin_dir, "find"
                               + " include lib plugins share"
                               + " " + string.join(python_dirs)
                               + " \( -name \*.so"
                               + " -o -name \*.so.\*"
                               + " -o -name \*.ui"
                               + " -o -name \*.py"
                               + " -o -name \*.pth"
                               + " -o -name \*.png"
                               + " -o -name EGG_INFO"
                               + " -o -name \*.egg-info"
                               + " -o -name \*.egg"
                               + " \)")

copy_files(build_dir, bin_dir, "echo"
                     + " ./lib/python" + pythonVersion + "/config/Makefile"
                     + " ./include/python" + pythonVersion + "/pyconfig.h"
                     + " ./bin/python" + pythonVersion
                     + " ./" + release_file
                     + " ./ilastik |xargs -n1 echo")

os.system("cd " + bin_dir + " && chmod -R +w .")
os.system("find " + bin_dir + " -name \*.so\* -type f | xargs strip")

# in case of a local compiler, e.g., for fc8 (do _not_ strip these files)
if os.path.isfile("/usr/local/lib/libstdc++.so"):
    copy_files("/usr/local/lib/", bin_dir + "/lib", "find . -name libstdc++\*")

pkg_name = bin_dir
if len(sys.argv) > 1:
    pkg_name = sys.argv[1]
    os.system("mv " + bin_dir + " " + pkg_name)

os.system("tar jcvf " + pkg_name + ".tar.bz2 " + pkg_name)
