#!/usr/bin/env python
# -*- coding: utf-8 -*-

#    Copyright 2010 L Fiaschi, T Kroeger, M Nullmaier C Sommer, C Straehle, U Koethe, FA Hamprecht. 
#    All rights reserved.
#    
#    Redistribution and use in source and binary forms, with or without modification, are
#    permitted provided that the following conditions are met:
#    
#       1. Redistributions of source code must retain the above copyright notice, this list of
#          conditions and the following disclaimer.
#    
#       2. Redistributions in binary form must reproduce the above copyright notice, this list
#          of conditions and the following disclaimer in the documentation and/or other materials
#          provided with the distribution.
#    
#    THIS SOFTWARE IS PROVIDED BY THE ABOVE COPYRIGHT HOLDERS ``AS IS'' AND ANY EXPRESS OR IMPLIED
#    WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND
#    FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE ABOVE COPYRIGHT HOLDERS OR
#    CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
#    CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
#    SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON
#    ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING
#    NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF
#    ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
#    
#    The views and conclusions contained in the software and documentation are those of the
#    authors and should not be interpreted as representing official policies, either expressed
#    or implied, of their employers.

import __builtin__
import urllib2, os, sys, tarfile, shutil
from hashlib import md5
import platform
import multiprocessing
 
#using http://www.pytips.com/2010/5/29/a-quick-md5sum-equivalent-in-python
#using http://stackoverflow.com/questions/22676/how-do-i-download-a-file-over-http-using-python
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

def download(url, file_name='', correctMD5sum=''):
    if file_name == '':
        file_name = url.split('/')[-1]
  
    if os.path.exists(file_name) :#and md5sum != '':
        if 1: #md5sum(file_name) == correctMD5sum:
            print 'file \'%s\' already downloaded, md5sum matches' % file_name
            return
    
    url=str(url)
    print "Downloading file from", url    
    u = urllib2.urlopen(url)
    f = open(file_name, 'w')
    meta = u.info()
    file_size = int(meta.getheaders("Content-Length")[0])
    print "Downloading: %s Bytes: %s" % (file_name, file_size)

    file_size_dl = 0
    block_sz = 8192
    while True:
        buffer = u.read(block_sz)
        if not buffer:
            break

        file_size_dl += block_sz
        f.write(buffer)
        status = r"%10d  [%3.2f%%]" % (file_size_dl, file_size_dl * 100. / file_size)
        status = status + chr(8)*(len(status)+1)
        print status,

    f.close()

class Package:
    src_uri = ''
    correctMD5sum  = ''
    workdir = ''
    patches = []
    patch_commands = []
    prefix = installDir
    
    def __init__(self):
        self.filename = self.src_uri.split('/')[-1]
        
        self.download()
        if 'download' in sys.argv[0]:
          return

        self.unpack()
        self.configure()
        self.make()
        self.makeInstall()
        self.test()
    
    def gmake(self, parallel = multiprocessing.cpu_count()):
        temp= 'make -j'+str(parallel)
        self.system(temp)
    
    def system(self, cmd):
        cmd = cd+' work/' + self.workdir + ' && ' + cmd
        print "Package.system('%s')" % cmd
        ret = os.system(cmd)
        if ret != 0:
        	raise RuntimeError("Failed to execute '%s'" % cmd)
    
    def download(self):
        if self.src_uri.endswith(".git") or self.src_uri[0:6] == "file:/":
            if not os.path.exists('distfiles/'+self.workdir):
                print "* cloning from git"
                os.system(cd+' distfiles && '+git+' clone ' + self.src_uri + ' ' + self.workdir)
            else:
                print "* update from git"
                os.system(cd+' distfiles/'+self.workdir + ' && '+git+' pull')
        elif self.src_uri.startswith('hg://'):
            src = self.src_uri[5:]
            if not os.path.exists('distfiles/'+self.workdir):
                print "* cloning from hg"
                str=cd+' distfiles && '+hg+' clone ' + src + ' ' + self.workdir
                print str
                os.system(str)
            else:
                print "* update from hg"
                os.system(cd+' distfiles/'+self.workdir + ' && '+hg+' update')
        else:
            download(self.src_uri, 'distfiles/'+self.filename, self.correctMD5sum)
        
    def unpack(self, copyToWork=True):
        print "* unpacking ", self.filename, "to", 'work' + '/' + self.workdir
        if os.path.exists('work' + '/' + self.workdir): shutil.rmtree('work' + '/' + self.workdir)

        if  self.src_uri.endswith('.git') or self.src_uri.startswith('hg://') or self.src_uri[0:6] == "file:/":
            if copyToWork:
                cmd = "cp -r distfiles/"+self.workdir+" work/"+self.workdir
                print "* Copying to work directory via '%s'" % cmd,
                os.system(cmd)
                print " ... done"
            else:
                cmd = "mkdir work/" + self.workdir
                print "* Creating empty work directory via '%s'" % cmd
                os.system(cmd)
        
        if self.filename.find('.tar') > -1:

            tar = tarfile.open('distfiles/' + self.filename)
            tar.extractall('work')
            #print "The directory",
            #self.system(pwd)
            #print "contains",
            #self.system(ls)
            
        for patch in self.patches:
            print "* applying patch", patch
            self.system('patch --forward -p0 < ../../files/' + patch)
        
        for cmd in self.patch_commands:
            print "* applying patch command", cmd
            self.system(cmd)

    def configure(self):
        print "* Configuring the Package"
        if platform.system() == "Darwin":
            cmd = self.configure_darwin()
        else:
            cmd = self.configure_linux()
        self.system(cmd)
        
    def make(self):
        self.gmake()
        
    def makeInstall(self):
        self.system(make+" install")
    
    def test(self):
        pass
