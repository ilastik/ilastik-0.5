# -*- coding: utf-8 -*-
import os, sys

installDir = os.environ["HOME"] + "/ilastik_deps_build"

# copy deps:

os.system("rm -Rf linux-bin/*")
cmd = "cd " + installDir + """ && pwd && find . \\
\( -name \*.so \\
-o -path ./lib/python2.7/config/Makefile \\
-o -path ./include/python2.7/pyconfig.h \\
-o -path ./bin/python2.7 \\
-o -name \*.so.\* \\
-o -name \*.py \\
-o -name \*.pth \\
-o -name \*.png \\
-o -name EGG_INFO \\
-o -name \*.egg-info \\
-o -name \*.egg \\
\) | cpio -admp """
cmd = cmd + os.getcwd() + "/linux-bin"
print cmd
os.system(cmd)

# copy ilastik proper:

os.system("cp -v ../run-ilastik-linux.sh linux-bin/")
os.system("""cd ../ilastik && find . -not -path ./scripts \\
                                   -not -name \*.h5 \\
                                   -not -name \*.ilp \\
                                   -not -name \*.pyc | \\
                                   cpio -admp """ + os.getcwd() + "/linux-bin/ilastik""")

os.system("cd linux-bin && chmod -R +w .")
os.system("find linux-bin -name \*.so\* -type f | xargs strip")

if os.path.isfile("/usr/local/lib/libstdc++.so"):
    os.system("(cd /usr/local/lib/; tar cvf - libstdc++*)|(cd linux-bin/lib; tar xvf -)")

pkg_name = "linux-bin"
if len(sys.argv) > 1:
    pkg_name = sys.argv[1]
    os.system("mv linux-bin " + pkg_name)

os.system("tar jcvf " + pkg_name + ".tar.bz2 " + pkg_name)
