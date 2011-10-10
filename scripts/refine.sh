#rm -rf ilastik.app/Contents/Resources/lib/python2.7/ilastik
#cp -r ../ilastik ilastik.app/Contents/Resources/lib/python2.7/ilastik

cp -r batchProcessCellsCounting.py ilastik.app/Contents/MacOS/

rm -rf ilastik.app/Contents/Resources/lib/python2.7/ilastik/modules/automatic-segmentatation
rm -rf ilastik.app/Contents/Resources/lib/python2.7/ilastik/modules/interactive-console
rm -rf  ilastik.app/Contents/Resources/lib/python2.7/ilastik/modules/interactive-segmentation
rm -rf ilastik.app/Contents/Resources/lib/python2.7/ilastik/modules/unsupervised-decomposition



find ilastik.app -name \*.h5 | xargs rm
find ilastik.app -name \*.ilp | xargs rm
find ilastik.app -name \*.pkl| xargs rm
#hdiutil create -imagekey zlib-level=9 -srcfolder ilastik.app ilastik-cells-counting.dmg