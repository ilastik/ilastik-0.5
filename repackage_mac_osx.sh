python setup_mac.py py2app
install_name_tool -change "/Users/lfiaschi/Library/Frameworks/Python.framework/Versions/2.7/Python" "@executable_path/../Frameworks/Python.framework/Versions/2.7/Python" /Users/lfiaschi/phd/workspace/ilastik-github/dist/ilastikMain.app/Contents/Resources/lib/python2.7/lib-dynload/vigra/vigranumpycore.so

install_name_tool -change "libboost_python.dylib" "@executable_path/../Frameworks/libboost_python.dylib" /Users/lfiaschi/phd/workspace/ilastik-github/dist/ilastikMain.app/Contents/Resources/lib/python2.7/lib-dynload/vigra/vigranumpycore.so

rm -rf dist/ilastikMain.app/Contents/Resources/lib/python2.7/ilastik/modules/interactive_console
rm -rf  dist/ilastikMain.app/Contents/Resources/lib/python2.7/ilastik/modules/cells_module
rm -rf dist/ilastikMain.app/Contents/Resources/lib/python2.7/ilastik/modules/unsupervised_decomposition
rm -rf dist/ilastikMain.app/Contents/Resources/lib/python2.7/ilastik/modules/automatic_segmentation
rm -rf dist/ilastikMain.app/Contents/Resources/lib/python2.7/ilastik/modules/connected_components
rm -rf dist/ilastikMain.app/Contents/Resources/lib/python2.7/ilastik/modules/interactive_segmentation
rm -rf dist/ilastikMain.app/Contents/Resources/lib/python2.7/ilastik/modules/interactive_segmentation
rm -rf dist/ilastik.app/Contents/Resources/lib/python2.7/ilastik/modules/object_picking



cp appIcon.icns dist/ilastikMain.app/Contents/Resources/PythonApplet.icns
rm ilastik-0.5-v0.5.06.rc5-x86-64.dmg
mv dist/ilastikMain.app dist/ilastik.app
hdiutil create -imagekey zlib-level=9 -srcfolder dist/ilastik.app ilastik-0.5-v0.5.06.rc5-x86-64.dmg