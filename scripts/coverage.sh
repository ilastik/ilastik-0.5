find . -name \*.pyc | xargs rm
nosetests  --with-coverage --cover-erase 
if [ ! -d /etc/portage ]; then
    python-coverage html -d coverage
else
    coverage html -i -d coverage
fi

