PREFIX="."

export LD_LIBRARY_PATH=$PREFIX/lib
export PATH=$PREFIX/bin:$PATH
export PYTHONPATH=.:$PREFIX/lib:$PREFX/lib/python2.7/site-packages
$PREFIX/bin/python2.7 ilastik/ilastikMain.py

