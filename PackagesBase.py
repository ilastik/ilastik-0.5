#!/usr/bin/env python
# -*- coding: utf-8 -*-

import __builtin__
import urllib2, os, sys, tarfile, shutil, urlparse, fileinput
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

def download(url, fileName=None):
    if url.endswith(".git"):
        workDir = url.split('/')
        workDir = workDir[-1]
        workDir = workDir.split('.')
        workDir = workDir[0]
        if not os.path.exists('distfiles/'+workDir):
            print "* cloning from git"
            os.system('cd distfiles && git clone ' + url + ' ' + workDir)
        else:
            print "* update from git"
            os.system('cd distfiles/'+workDir + ' && git pull')
        return workDir
    def getFileName(url,openUrl):
        if 'Content-Disposition' in openUrl.info():
            # If the response has Content-Disposition, try to get filename from it
            cd = dict(map(
                lambda x: x.strip().split('=') if '=' in x else (x.strip(),''),
                openUrl.info()['Content-Disposition'].split(';')))
            if 'filename' in cd:
                filename = cd['filename'].strip("\"'")
                if filename: return filename
        # if no filename was found above, parse it out of the final URL.
        return os.path.basename(urlparse.urlsplit(openUrl.url)[2])

    r = urllib2.urlopen(urllib2.Request(url))
    try:
        fileName = fileName or getFileName(url,r)
        if os.path.exists(fileName):
            print 'file \'%s\' already downloaded' % fileName
        else:
            with open(fileName, 'wb') as f:
                print "Downloading file from", url
                shutil.copyfileobj(r, f)
    finally:
        r.close()
        return fileName

class Package:
    src_uri = ''
    workdir = ''
    prefix = installDir
    patches = []
    patch_commands = []
    replaceLines = []
    
    def __init__(self):        
        self.download()
        self.unpack()
        if self.replaceLines:
            self.replaceALinesInFile(self.replaceLines)
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
            print "* unpacking ", self.filename, "to", 'work' + '/' + self.workdir
            if os.path.exists('work' + '/' + self.workdir): 
                shutil.rmtree('work' + '/' + self.workdir)
            if self.filename.find('.tar') > -1 or self.filename.find('.tgz') > -1:
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
        for line in fileinput.input('work/'+self.workdir+'/'+data[0], inplace=1):
            for lines in data[1:]:
                if lines[0] in line:
                    line = lines[1]
            sys.stdout.write(line)
            
    def configure(self):
        print "* Configuring the Package"
        if platform.system() == "Darwin":
            cmd = self.configure_darwin()
        else:
            cmd = self.configure_linux()
        for index, item in enumerate(cmd):
            for ch in [('($prefix)',        self.prefix),
                       ('($pythonHeaders)', self.prefix + '/Frameworks/Python.framework/Headers'),
                       ('($pythonVersionPath)', self.prefix + '/Frameworks/Python.framework/Versions/2.7'), 
                       ('($pythonlib)',     self.prefix + '/Frameworks/Python.framework/Versions/2.7/lib/libpython2.7.dylib'),
                       ('($pythonBinaryPath)',     self.prefix + '/Frameworks/Python.framework/Versions/2.7/bin'),
                       ('($pythonIncludePath)',     self.prefix + '/Frameworks/Python.framework/Versions/2.7/include/python2.7'),
                       ('($pythonSharePath)',     self.prefix + '/Frameworks/Python.framework/Versions/2.7/share'),
                       ('($pythonExecutable)',     self.prefix + '/Frameworks/Python.framework/Versions/2.7/bin/python'),
                       ('($packageWorkDir)',     self.workdir),
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
    
