from distutils.core import setup
import py2exe

from glob import glob
    
msvs_redist = ("Microsoft.VC90.CRT", glob('./gui/msvs-redist/*.*'))

class Target:
    def __init__(self, **kw):
        self.__dict__.update(kw)

ilastikGUI = Target(
    name='IlastikGUI',
    version='0.3',
    company_name = "HCI",
    description='Interactive Learning and Segmentation Tool Kit- GUI',
    author='Christoph Sommer',
    author_email='christoph.sommer@iwr.uni-heidelberg.de',
    copyright = "",
    url='http://hci.iwr.uni-heidelberg.de/',
    script = "ilastikMain.py",
    icon_resources = [(1, "./gui/pyc.ico")]
)

setup(
    windows = [ilastikGUI],
    data_files = [('gui', ['./gui/pyc.ico', "./gui/dlgChannels.ui", "./gui/dlgFeature.ui", "./gui/dlgProject.ui"]), msvs_redist],
    zipfile = "shared.lib",
    options = {"py2exe": {"compressed": 0, "optimize": 0, "includes":["core", "sip", "tables", "tables._comp_bzip2", "h5py", "h5py._stub", "h5py._sync","h5py.utils", "PyQt4.QtSvg", "labelArrayDrawQImage"], "dll_excludes": ["MSVCP90.dll"]}},
)

print "*********************\n>>copy vigra numpy core"
import os
os.chdir('dist')
os.system('copy vigra.vigranumpycore.pyd vigranumpycore.pyd' )
