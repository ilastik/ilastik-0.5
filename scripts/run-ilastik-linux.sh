#!/bin/bash
ILASTIK_SCRIPT=$(readlink -f $0)
PREFIX=$(dirname $ILASTIK_SCRIPT)

export LD_LIBRARY_PATH=$PREFIX/lib
export PATH=$PREFIX/bin:$PATH
export PYTHONPATH=$PREFIX:$PREFIX/lib:$PREFX/lib/python2.7/site-packages
$PREFIX/bin/python2.7 $PREFIX/ilastik/ilastikMain.py
