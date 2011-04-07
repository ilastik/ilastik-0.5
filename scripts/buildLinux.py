# -*- coding: utf-8 -*-
import os

os.system("rm -Rf linux-bin/*")
cmd = """cd /ilastik && pwd && find . \\
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
\) | cpio -admp /home/ilastik/ilastik-build/ilastik/scripts/linux-bin"""
print cmd
os.system(cmd)

os.system("cp -v ../run-ilastik-linux.sh linux-bin/")
os.system("""cd ../ilastik && find . -not -path ./scripts \\
                                   -not -name \*.h5 \\
                                   -not -name \*.ilp \\
                                   -not -name \*.pyc | \\
                                   cpio -admp /home/ilastik/ilastik-build/ilastik/scripts/linux-bin/ilastik""")

os.system("cd linux-bin && chmod -R +w .") 
os.system("find linux-bin -name \*.so\* -type f | xargs strip")

#tar -cjf ilastik-linux.tar.bz2 linux-bin/
