import os, copy

print "PYTHON ILASTIK PRE-LAUNCHER ***************************"

exe = copy.copy(os.environ['EXECUTABLEPATH']).replace('/MacOS/ilastikMain', '')

#: '/Users/tkroeger/Desktop/buildilastik/work/ilastik/dist/ilastik.app/Contents/MacOS/ilastikMain'
os.environ['DYLD_FALLBACK_LIBRARY_PATH'] = exe + '/Resources/lib:' + exe + 'Resources/lib/python2.7/lib-dynload/vigra'
print os.environ