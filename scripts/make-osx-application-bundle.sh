cd ..

rm -rf dist
rm -rf build
rm -rf ilastik.app

find . -name \*.pyc | xargs rm

INSTALL_DIR="/ilastik"
PYTHON_EXE="$INSTALL_DIR/Frameworks/Python.framework/Versions/2.7/bin/python2.7"
PYTHON_SITE_PACKAGES="$INSTALL_DIR/Frameworks/Python.framework/Versions/2.7/lib/python2.7/site-packages"

export DYLD_LIBRARY_PATH="$INSTALL_DIR/lib:$PYTHON_SITE_PACKAGES/vigra"

$PYTHON_EXE setup_mac.py py2app --iconfile appIcon.icns

mv dist/ilastikMain.app dist/ilastik.app 

cp -rv /ilastik/lib/qt_menu.nib dist/ilastik.app/Contents/Resources/
rm -rf dist/ilastik.app/Contents/Resources/qt.conf
touch dist/ilastik.app/Contents/Resources/qt.conf

cp -v appIcon.icns dist/ilastik.app/Contents/Resources

find dist/ilastik.app -name \*.h5 | xargs rm
find dist/ilastik.app -name \*.ilp | xargs rm
rm -f dist/ilastik.dmg

mv dist/ilastik.app scripts/
rm -rf dist
rm -rf build

cd scripts

#hdiutil create -imagekey zlib-level=9 -srcfolder ilastik.app ilastik.dmg
