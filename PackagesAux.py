#!/usr/bin/env python
# -*- coding: utf-8 -*-

import __builtin__
import urllib2, os, shutil, urlparse, re, subprocess, json
from hashlib import md5
 
#using http://www.pytips.com/2010/5/29/a-quick-md5sum-equivalent-in-python
#using http://stackoverflow.com/questions/22676/
#             how-do-i-download-a-file-over-http-using-python
def md5sum(filename, buf_size=8192):
    m = md5()
    # the with statement makes sure the file will be closed 
    with open(filename) as f:
        # We read the file in small chunk until EOF
        data = f.read(buf_size)
        while data:
            # We had data to the md5 hash
            m.update(data)
            data = f.read(buf_size)
    # We return the md5 hash in hexadecimal format
    return m.hexdigest()

def git_pull(url, directory, tree_ish):
    if not os.path.exists(directory):
        print "* cloning from git"
        os.system('git clone ' + url + ' ' + directory)
    # test if the commit named 'tree_ish' is missing from the local git repo:
    if subprocess.call('cd ' + directory + ' && git rev-parse --quiet --no-revs'
                       + ' --symbolic-full-name --verify '
                       + tree_ish, shell = True):
        print "* update from git"
        os.system('cd ' + directory + ' && git pull')

def git_archive(directory, tree_ish, output_file):
    # expressly disallow relative names.
    suffix = re.split('[\^\@\~]', tree_ish.split('/')[-1])[0]
    branches = subprocess.check_output('cd ' + directory + ' && git branch',
                                       shell = True).splitlines()
    branches = [(name.strip(" *")) for name in branches]
    branches.append('HEAD___')
    print(branches)
    if (suffix in branches):
        raise NameError('relative commit names disallowed for ilastik build')
    os.system('git archive -o ' + output_file + ' --remote='
              + directory + ' ' + tree_ish)

# 3 things: a)  the JSON entry "archive": the canonical name of the build script
#           b)  the name of the downloaded file, usually versioned a la 'x.y.z'
#           c)  the sha1sum, to be added to the JSON data
# a file once donloaded (b)) is not supposed to be overwritten
# or downloaded more than once

def download(url, directory, download_file, sha1_sum = ""):
        if os.path.exists(download_file):
            # check sha1sum
            print 'file \'%s\' already downloaded' % download_file
        else:
            with open(download_file, 'wb') as f:
                print "Downloading file from", url
                try:
                    r = urllib2.urlopen(urllib2.Request(url))
                    shutil.copyfileobj(r, f)
                finally:
                    r.close()
            # check sha1sum
            # write sha1sum file: sha1sum + " " + download_file >> sha1.sum



repo_file_name = "repo-table.json"
try:
    with open(repo_file_name) as repo_file:
        repo_data = json.load(repo_file)
except ValueError as e:
    print("Invalid JSON syntax in file '" + repo_file_name + "':")
    print(e)
    print("probably a stray ',': consider running\n\t"
          + "perl -pi -0777 -ne 's/(\s*,)+(\s*[\}\]])/\\2/g' repo-table.json")

os.chdir('/export/home/users/mip/ilastik/build/repos') # be script argument...
for package in repo_data:
    directory = package["pkg"]
    print(directory)
    url = package["uri_all"]
    archive = package["archive"]
    if url.startswith("git://"):
       ## tag = "xyz.123" # via release control file
        tag = "HEAD" # via release control file
        git_pull(url, directory, tag)
        print("Using git repository " + directory + ", commit "
              + tag + ", for ilastik build:")
        archive_path = '/tmp/tartest/' + archive
        git_archive(directory, tag, archive_path)
    # tar file download_name with name archive
    else:
        download_name = url.split('/')[-1]
        download(url, directory, download_name)
        archive_path = directory + "/" + download_name
    # tar file archive_path with name archive


