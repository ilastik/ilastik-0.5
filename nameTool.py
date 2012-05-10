#!/usr/bin/env python
# -*- coding: utf-8 -*-

import __builtin__
import platform
import urllib2, os, sys, tarfile, shutil

c = sys.argv
item = c[1]
item = item.replace("--prefix=", "")
__builtin__.installDir = item

class NameTool(object):
    def __init__(self):
        print "\033[95m################################################\n############install_name_toll fixes#############\n################################################\n\033[0m"
        self.getFiles()
        self.setInstallNameTool('outputSo.txt')
        self.setInstallNameTool('outputDylib.txt')
        print "\033[95m################################################\n################################################\n################################################\n\033[0m"
    
    def system(self, cmd):
        cmd = 'cd ' + installDir + ' && ' + cmd
        ret = os.system(cmd)
        if ret != 0:
            raise RuntimeError("Failed to execute '%s'" % cmd)
        
    def getFiles(self):
        os.system('find ' + installDir + ' -name *.so > outputSo.txt')
        os.system('find ' + installDir + ' -name *.dylib > outputDylib.txt')
        
    def findFile(self, fileName, file):
        os.system('find ' + installDir + ' -name ' + fileName + ' > tempFilePath.txt')
        file_txt = open("tempFilePath.txt", "r")
        lines = file_txt.readlines()
        if len(lines) == 0:
            return None
        if len(lines) == 1:
            if lines[0].endswith("\n"):
                line = lines[0][:-1]
                return line
        if len(lines) == 2:
            if 'vigra-ilastik-05' in file and 'vigra-ilastik-05' in lines[0]:
                if lines[0].endswith("\n"):
                    line = lines[0][:-1]
                    return line
            elif 'vigra-ilastik-05' in file and 'vigra-ilastik-05' in lines[1]:
                if lines[0].endswith("\n"):
                    line = lines[1][:-1]
                    return line
            elif not 'vigra-ilastik-05' in file and not 'vigra-ilastik-05' in lines[0]:
                if lines[0].endswith("\n"):
                    line = lines[0][:-1]
                    return line
            elif not 'vigra-ilastik-05' in file and not 'vigra-ilastik-05' in lines[1]:
                if lines[0].endswith("\n"):
                    line = lines[1][:-1]
                    return line
            raise Exception("!!!!!!!!!! Warning ", file, " ", lines)
                    
                    
                    
        file_txt.close()
    def setInstallNameTool(self, txt_file):
        so_txt = open(txt_file, "r")
        lines = so_txt.readlines()
        for line in lines:
            if line.endswith('\n'):
                line = line[:-1]
            os.system('otool -L ' + line + " > temp.txt")
            
            temp_txt = open("temp.txt", "r")
            tempLines = temp_txt.readlines()
            for tempLine in tempLines:
                if tempLine.endswith('\n'):
                    tempLine = tempLine[:-1]
                if tempLine.startswith('\t'):
                    tempLine = tempLine[1:]
                tempLine = tempLine.split(" ")
                tempLine = tempLine[0]
                if tempLine in line and not '/' in tempLine:
                    print "\033[94m%s\033[0m" % line
                    print "setting -id from " + "\033[91m%s\033[0m" % tempLine
                    print "to "   + "\033[92m%s\033[0m\n" % line
                    os.system('install_name_tool -id ' + line + " " + line)
                if tempLine in line and tempLine.startswith('/Users/opetra/'):
                    print "\033[94m%s\033[0m" % line
                    print "setting -id from " + "\033[91m%s\033[0m" % tempLine
                    print "to "   + "\033[92m%s\033[0m\n" % line
                    os.system('install_name_tool -id ' + line + " " + line)
                if not tempLine in line and not '/' in tempLine:
                    path = self.findFile(tempLine, line)
                    if path:
                        print "\033[94m%s\033[0m" % line
                        print "changing " + "\033[91m%s\033[0m" % tempLine
                        print "to "   + "\033[92m%s\033[0m\n" % path
                        os.system('install_name_tool -change ' + tempLine + ' ' + path + ' ' + line)
                if not tempLine in line and tempLine.startswith('/Users/opetra/'):
                    tmp = tempLine.split('/')
                    tmp = tmp[-1]
                    path = self.findFile(tmp, line)
                    if path: 
                        print "\033[94m%s\033[0m" % line
                        print "changing " + "\033[91m%s\033[0m" % tempLine
                        print "to "   + "\033[92m%s\033[0m\n" % path
                        os.system('install_name_tool -change ' + tempLine + ' ' + path + ' ' + line)
            temp_txt.close()

if __name__ == "__main__":
    NameTool()