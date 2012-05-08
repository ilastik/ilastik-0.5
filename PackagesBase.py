#!/usr/bin/env python
# -*- coding: utf-8 -*-

import __builtin__
import os, sys, tarfile, shutil, fileinput
from hashlib import md5
import platform
import multiprocessing

from PackagesAux import md5sum, download
 
class Package:
    src_uri = ''
    workdir = ''
    prefix = installDir
    patches = []
    patch_commands = []
    replaceDarwin = []
    
    def __init__(self):        
        self.download()
        self.unpack()
        if self.replaceDarwin and platform.system() == "Darwin":
            self.replaceALinesInFile(self.replaceDarwin)
        self.configure()
        self.make()
        self.makeInstall()
        self.fixOrTest()
        
    def gmake(self, parallel = multiprocessing.cpu_count()):
        temp= 'make -j'+str(parallel)
        self.system(temp)
        
    def system(self, cmd):
        cmd = 'cd work/' + self.workdir + ' && ' + cmd
        print "Package.system('%s')" % cmd
        ret = os.system(cmd)
        if ret != 0:
            raise RuntimeError("Failed to execute '%s'" % cmd)
    
    def download(self):
        self.filename = download(self.src_uri)

    def unpack(self):
        if  self.src_uri.endswith('.git'):
            self.workdir = self.filename
            if os.path.exists('work' + '/' + self.workdir): 
                shutil.rmtree('work' + '/' + self.workdir)
            cmd = "cp -r distfiles/"+self.workdir+" work/"+self.workdir
            print "* Copying to work directory via '%s'" % cmd,
            os.system(cmd)
            print " ... done"
        else:
            t = tarfile.open(self.filename, 'r')
            self.workdir = t.getnames()[0]
            if '/' in self.workdir:
                self.workdir = self.workdir.split('/')
                self.workdir = self.workdir[0]
            print ("* unpacking ", self.filename, "to",
                   'work' + '/' + self.workdir)
            if os.path.exists('work' + '/' + self.workdir): 
                shutil.rmtree('work' + '/' + self.workdir)
            if (self.filename.find('.tar') > -1 or
                self.filename.find('.tgz') > -1):
                tar = tarfile.open(self.filename)
                tar.extractall('work')
            
        for patch in self.patches:
            print "* applying patch", patch
            self.system('patch --forward -p0 < ../../files/' + patch)
        
        for cmd in self.patch_commands:
            print "* applying patch command", cmd
            self.system(cmd)
            
    def replaceALinesInFile(self, data):
        os.system('pwd')
        for line in fileinput.input('work/' + self.workdir + '/' + data[0],
                                    inplace=1):
            for lines in data[1:]:
                if lines[0] in line:
                    line = lines[1]
            sys.stdout.write(line)
            
    def configure(self):
        print "* Configuring the Package"
        cmd = self.configure_all()
        try:
            if platform.system() == "Darwin":
                cmd += self.configure_darwin()
            else:
                cmd += self.configure_linux()
        except AttributeError:
            pass


        py_path = (self.prefix + '/Frameworks/Python.framework/Versions/2.7/')
        for index, item in enumerate(cmd):
            for ch in [('($prefix)',        self.prefix),
                       ('($pythonHeaders)', self.prefix
                        + '/Frameworks/Python.framework/Headers'),
                       ('($pythonVersionPath)', self.prefix
                        + '/Frameworks/Python.framework/Versions/2.7'),
                       ('($pythonlib)', py_path + 'lib/libpython2.7.dylib'),
                       ('($pythonBinaryPath)', py_path + 'bin'),
                       ('($pythonIncludePath)', py_path + 'include/python2.7'),
                       ('($pythonHeadersPath)', self.prefix
                                     + '/Frameworks/Python.framework/Headers'),
                       ('($pythonSharePath)', py_path + 'share'),
                       ('($pythonExecutable)', py_path + 'bin/python'),
                       ('($packageWorkDir)', self.workdir),
                       ]:
                if ch[0] in item:
                    item = item.replace(ch[0], ch[1])
                    cmd[index] = item
        cmd = ' '.join(cmd)
        self.system(cmd)
            
    def make(self):
        self.gmake()
        
    def makeInstall(self):
        self.system("make install")

    def fixOrTest(self):
        pass
