#!/usr/bin/env python
# -*- coding: utf-8 -*-

#    Copyright 2010 L Fiaschi, T Kroeger, M Nullmeier C Sommer, C Straehle, U Koethe, FA Hamprecht. 
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

import sys, re, os

def br():
    sys.stdout.write('#')
    for i in range(79):
        sys.stdout.write('*')
    sys.stdout.write('\n')

def spacedText(t):
    pos = 0
    sys.stdout.write('# ')
    pos += 2

    for i in range(len(t)):
        sys.stdout.write("%s " % t[i])
        pos += 2
    for i in range(pos, 79):
        sys.stdout.write(' ')
    sys.stdout.write('*\n')

#c = sys.argv[1]
#br()
#spacedText(c)
#br()

os.system("cp '%s' /tmp/file.py" % (sys.argv[1]))
f = open('/tmp/file.py', 'r')
lines = f.readlines()

g = open(sys.argv[1], 'w')
sys.stdout = g

comment = False
for n, l in enumerate(lines):
    for i in range(l.count('"""')):
        comment = not comment
        
    if comment:
        sys.stdout.write(l)
        continue
    
    classRegEx = re.search("class ([\w]+)(\([\w]+\))?", l)
    if classRegEx or l.find("__main__") > 0:
        text = ''
        if classRegEx:
            text = classRegEx.group(1)
        else:
            text = 'if __name__ == "__main__"'
        
        commentRegEx = re.search("^[\s]*#", l)
        if commentRegEx:
            sys.stdout.write(l)
            continue #this is just a comment
        
        if n>2 and lines[n-2].startswith('#******') > 0:
            sys.stdout.write(l)
            continue
        else:
            br()
            spacedText(text)
            br()
            sys.stdout.write("\n")
    
    sys.stdout.write(l)