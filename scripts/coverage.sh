find . -name \*.pyc | xargs rm -rf
find . -name \*,cover | xargs rm -rf
rm -rf coverage; mkdir coverage
nosetests  --with-coverage --cover-erase --cover-package=ilastik 
if [ ! -d /etc/portage ]; then
    python-coverage html -d coverage
else
    coverage html -i -d coverage
fi

