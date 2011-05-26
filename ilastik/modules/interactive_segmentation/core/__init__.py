import interactiveSegmentationModuleMgr

import sys, getopt

startupOutputPath = None

toRemove = []
for i, arg in enumerate(sys.argv[1:]):
    if arg.startswith("--segmentations-dir="):
        startupOutputPath = arg[len('--segmentations-dir='):]
        print startupOutputPath
        toRemove.append(i)
sys.argv = [sys.argv[0]] + [arg for i, arg in enumerate(sys.argv[1:]) if i not in toRemove]
if not startupOutputPath:
    print "*"
    print "* Module interactive segmentation"
    print "*   You can specify the directory where to store finished segmentations"
    print "*   and where to load from on initialization with the flag"
    print "*   --segmentations-dir"
    print "*"
del toRemove

'''
if startupOutputPath is None:
    from PyQt4.QtGui import QFileDialog
    startupOutputPath = str(QFileDialog.getExistingDirectory(None, "Select empty directory to store segmentations in"))
'''