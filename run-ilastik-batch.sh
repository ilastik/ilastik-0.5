if [ -z "$1" ]
then
        echo "Usage: --config_file=<json-file>"
		exit 0
fi

export LD_LIBRARY_PATH=`pwd`/lib:$LD_LIBRARY_PATH
python ilastik/modules/classification/core/batchprocess.py $@
