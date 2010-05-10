# -*- mode: python -*-
a = Analysis([os.path.join(HOMEPATH,'support\\_mountzlib.py'), os.path.join(HOMEPATH,'support\\useUnicode.py'), 'ilastikMain.py'],
             pathex=['C:\\Users\\csommer\\ilastik\\trunk\\src'])
pyz = PYZ(a.pure)
exe = EXE(pyz,
          a.scripts,
          exclude_binaries=1,
          name=os.path.join('build\\pyi.win32\\ilastikMain', 'ilastikMain.exe'),
          debug=False,
		  icon='python.exe,0',
          strip=False,
          upx=True,
          console=True )
coll = COLLECT( exe,
               a.binaries,
               a.zipfiles,
               a.datas,
			   [('installerScript.nsi', 'installerScript.nsi','DATA'),
			    ('gui/dlgChannels.ui', 'gui/dlgChannels.ui','DATA'),
				('gui/dlgFeature.ui', 'gui/dlgFeature.ui','DATA'),
				('gui/dlgProject.ui', 'gui/dlgProject.ui','DATA'),
				('gui/placeholder.png', 'gui/placeholder.png','DATA'),
				('gui/backGroundBrush.png', 'gui/backGroundBrush.png','DATA')],
               strip=False,
               upx=True,
               name=os.path.join('dist', 'ilastikMain'))
			   
import shutil
print "#"*30
print "Post build events"
print "-> Copy icons ",
shutil.copytree('gui/icons','ilastikMain/dist/ilastikMain/gui/icons', ignore=shutil.ignore_patterns('.svn'))
print "Done",
