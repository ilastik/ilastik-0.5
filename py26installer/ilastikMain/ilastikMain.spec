# -*- mode: python -*-
import os

def getOsPath():
	if os.name == 'posix':
		return 'build/pyi.linux2/ilastikMain/ilastikMain'
	elif os.name == 'nt':
		return 'build\\pyi.win32\\ilastikMain\\ilastikMain.exe'

a = Analysis([os.path.join(HOMEPATH,'support/_mountzlib.py'), os.path.join(HOMEPATH,'support/useUnicode.py'), '../ilastikMain.py'],
             pathex=[os.getcwd()])
pyz = PYZ(a.pure)
exe = EXE(pyz,
          a.scripts,
          exclude_binaries=1,
          name=getOsPath(),
          debug=False,
          strip=False,
          upx=True,
          console=True)
coll = COLLECT( exe,
               a.binaries,
               a.zipfiles,
               a.datas,
               strip=False,
               upx=True,
               name=os.path.join('dist', 'ilastikMain'))
import shutil
print "\n\n\n"
print "#"*30
print "Post build events"
print "-> Copy icons ",

shutil.copytree('../gui/icons','ilastikMain/dist/ilastikMain/gui/icons', ignore=shutil.ignore_patterns('.svn'))
print "Done"
print "-> Copy other files ",
shutil.copy('../installerScript.nsi','ilastikMain/dist/ilastikMain/installerScript.nsi')
shutil.copy('../gui/dlgChannels.ui','ilastikMain/dist/ilastikMain/gui/dlgChannels.ui')
shutil.copy('../gui/dlgFeature.ui','ilastikMain/dist/ilastikMain/gui/dlgFeature.ui')
shutil.copy('../gui/dlgProject.ui','ilastikMain/dist/ilastikMain/gui/dlgProject.ui')
shutil.copy('../gui/placeholder.png','ilastikMain/dist/ilastikMain/gui/placeholder.png')
shutil.copy('../gui/backGroundBrush.png','ilastikMain/dist/ilastikMain/gui/backGroundBrush.png')
shutil.copy('../gui/pyc.ico','ilastikMain/dist/ilastikMain/gui/pyc.ico')
print "Done"


