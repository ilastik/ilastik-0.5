#!/usr/bin/env python
# -*- coding: utf-8 -*-

import __builtin__
import os, sys, tarfile, zipfile, shutil, fileinput
from hashlib import md5
import platform
import multiprocessing

from PackagesAux import md5sum, download
 
class Package:
    src_file = ''
    workdir = ''
    prefix = installDir
    patches = []
    patch_commands = []
    replaceDarwin = []
    
    def __init__(self, name):        
        self.package_name = name
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
        sys.stdout.flush()
        ret = os.system(cmd)
        if ret != 0:
            raise RuntimeError("Failed to execute '%s'" % cmd)
    
    def unpack(self):
        archive = None
        if self.src_file.endswith('.zip'):
            archive = zipfile.ZipFile(self.src_file)
            self.workdir = archive.namelist()[0]
        else:
            archive = tarfile.open(self.src_file)
            self.workdir = archive.getnames()[0]

        if '/' in self.workdir:
            self.workdir = self.workdir.split('/')
            self.workdir = self.workdir[0]
        archive_dir = 'work' + '/' + self.workdir
        print "* unpacking ", self.src_file, "to", archive_dir
        if os.path.exists(archive_dir):
            shutil.rmtree(archive_dir)

        archive.extractall('work')
        archive.close()
            
        for patch in self.patches:
            print "* applying patch", patch
            self.system('patch --forward -p0 < ../../files/' + patch)
        
        for cmd in self.patch_commands:
            print "* applying patch command", cmd
            self.system(cmd)
            
    def replaceALinesInFile(self, data):
        sys.stdout.flush()
        os.system('pwd')
        for line in fileinput.input('work/' + self.workdir + '/' + data[0],
                                    inplace=1):
            for lines in data[1:]:
                if lines[0] in line:
                    line = lines[1]
            sys.stdout.write(line)
            
    def configure(self):
        print "* Configuring package", self.package_name
        cmd = self.configure_all()
        try:
            if platform.system() == "Linux":
                cmd += self.configure_linux()
            if platform.system() == "Darwin":
                cmd += self.configure_darwin()
        except AttributeError:
            pass

        if platform.system() == "Linux":
            pythonVersionPath = (self.prefix + '/')
            dll_suffix = '.so'
        if platform.system() == "Darwin":
            pythonVersionPath = (self.prefix
                                 + '/Frameworks/Python.framework/Versions/'
                                 + pythonVersion + '/')
            dll_suffix = '.dylib'

        replace_list_all = [
            ('($prefix)',        self.prefix),
            ('($pythonBinaryPath)', pythonVersionPath + 'bin'),
            ('($pythonIncludePath)', pythonVersionPath + 'include/python'
                                                       + pythonVersion),
            ('($pythonSharePath)', pythonVersionPath + 'share'),
            ('($pythonExecutable)', pythonVersionPath + 'bin/python'),
            ('($packageWorkDir)', self.workdir),
            ('($pythonSitePackages)', pythonVersionPath + 'lib/python'
                                      + pythonVersion  + "/site-packages"),
            ('($dll_suffix)', dll_suffix),
            ('($pythonlib)', pythonVersionPath + 'lib/libpython' + pythonVersion
                                                                 + dll_suffix)]

        replace_list_linux = [
            ('($pythonHeadersPath)', pythonVersionPath + 'include/python'
                                                       + pythonVersion),
            ('($pythonVersionPath)', pythonVersionPath[:-1])]

        replace_list_darwin = [
            ('($pythonHeadersPath)', self.prefix
                         + '/Frameworks/Python.framework/Headers'),
            ('($pythonVersionPath)', self.prefix
                    + '/Frameworks/Python.framework/Versions/' + pythonVersion)]
                         
        if platform.system() == "Linux":
            replace_list_all.extend(replace_list_linux)
        if platform.system() == "Darwin":
            replace_list_all.extend(replace_list_darwin)

        for index, item in enumerate(cmd):
            for ch in replace_list_all:
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
