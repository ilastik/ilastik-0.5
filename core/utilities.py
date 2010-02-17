def irange(sequence):
    return zip(xrange(len(sequence)), sequence)
 
def debug(*args):
    if True:
        print args
        
def irangeIfTrue(sequence):
    res = []
    for ind, val in irange(sequence):
        if val:
            res.append(ind)
    return res
            
        