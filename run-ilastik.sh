# Absolute path to this script. /home/user/bin/foo.sh	
SCRIPT=$(readlink -f $0)
# Absolute path this script is in. /home/user/bin
SCRIPTPATH=`dirname $SCRIPT`

#PYTHONPATH=. gdb --args /usr/bin/python $SCRIPTPATH/ilastik/ilastikMain.py
PYTHONPATH=. python $SCRIPTPATH/ilastik/ilastikMain.py
