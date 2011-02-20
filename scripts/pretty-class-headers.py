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