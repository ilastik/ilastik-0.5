# -*- coding: utf-8 -*-

import __builtin__
import sys, urllib2, os, shutil, urlparse, re, subprocess, json, hashlib
import argparse, tarfile, inspect



def git_clone(url, directory):
    if not os.path.exists(directory):
        print "* cloning from git"
        os.system('git clone ' + url + ' ' + directory)

def git_pull(url, directory):
    print "* update from git"
    os.system('cd ' + directory + ' && git pull')

def git_clone_pull(url, directory):
    git_clone(url, directory)
    git_pull(url, directory)

def git_update(url, directory, tree_ish):
    git_clone(url, directory)
    # test if the commit named 'tree_ish' is missing from the local git repo:
    if subprocess.call('cd ' + directory + ' && git rev-parse --quiet --no-revs'
                       + ' --symbolic-full-name --verify '
                       + tree_ish, shell = True):
        git_pull(url, directory)

def main():
    git_update(url, directory, tag)
    print("Using git repository " + directory + ", commit "
          + tag + ", for ilastik build system:")
    archive_path = tar_dir + archive
    os.system('cd ' + directory + ' && git archive ' + tree_ish + '|tar xf -')


if __name__ == '__main__':
    main()
