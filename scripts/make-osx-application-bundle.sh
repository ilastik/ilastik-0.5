cd ..

rm -rf dist
rm -rf build
rm -rf ilastik.app
rm -rf scripts/ilastik.app

find . -name \*.pyc | xargs rm

INSTALL_DIR="~/ilastik_deps_build"
PYTHON_EXE="~/ilastik_deps_build/Frameworks/Python.framework/Versions/2.7/bin/python2.7"
#PYTHON_SITE_PACKAGES="$INSTALL_DIR/Frameworks/Python.framework/Versions/2.7/lib/python2.7/site-packages"

#export DYLD_LIBRARY_PATH="$INSTALL_DIR/lib:$PYTHON_SITE_PACKAGES/vigra"
export DYLD_FALLBACK_LIBRARY_PATH=~/ilastik_deps_build/lib:~/ilastik_deps_build/Frameworks/Python.framework/Versions/2.7/lib/python2.7/site-packages/vigra



~/ilastik_deps_build/Frameworks/Python.framework/Versions/2.7/bin/python2.7 setup_mac.py py2app --iconfile appIcon.icns

mv dist/ilastikMain.app dist/ilastik.app 

cp -rv ~/ilastik_deps_build/lib/qt_menu.nib dist/ilastik.app/Contents/Resources/
rm -rf dist/ilastik.app/Contents/Resources/qt.conf
touch dist/ilastik.app/Contents/Resources/qt.conf

cp -v appIcon.icns dist/ilastik.app/Contents/Resources

find dist/ilastik.app -name \*.h5 | xargs rm
find dist/ilastik.app -name \*.ilp | xargs rm
rm -f scripts/ilastik.dmg

#Dirty patch for saving tiff files with qt
#mkdir ilastik.app/Contents/plugins/
#mkdir ilastik.app/Contents/plugins/imageformats
#cp ~/ilastik_deps_build/plugins/imageformats/libqtiff.dylib ilastik.app/Contents/plugins/imageformats/






mv dist/ilastik.app scripts/
rm -rf dist
rm -rf build

cd scripts

#hdiutil create -imagekey zlib-level=9 -srcfolder ilastik.app ilastik.dmg
