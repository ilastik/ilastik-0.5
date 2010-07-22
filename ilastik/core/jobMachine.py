import os, sys
import threading
import traceback

try:
    from PyQt4 import QtCore
    ThreadBase = QtCore.QThread
    have_qt = True
except:
    ThreadBase = threading.Thread
    have_qt = False


from collections import deque

#detectCPUS function is shamelessly copied from the intertubes
def detectCPUs():
    # Linux, Unix and MacOS:
    if hasattr(os, "sysconf"):
       if os.sysconf_names.has_key("SC_NPROCESSORS_ONLN"):
           # Linux & Unix:
           ncpus = os.sysconf("SC_NPROCESSORS_ONLN")
           if isinstance(ncpus, int) and ncpus > 0:
               return ncpus
       else: # OSX:
           return int(os.popen2("sysctl -n hw.ncpu")[1].read())
    # Windows:
    if os.environ.has_key("NUMBER_OF_PROCESSORS"):
           ncpus = int(os.environ["NUMBER_OF_PROCESSORS"]);
           if ncpus > 0:
               return ncpus
    return 1 # Default


class IlastikJob():
    def __init__(self, target, args):
        self.target = target
        self.args = args
        
    def run(self, machine):
        worker = machine.workers.pop()
        worker.process(self.target, self.args, machine)
        self.target = None
        self.args = None


class JobMachineWorker(ThreadBase):
    def __init__(self):
        ThreadBase.__init__(self)
        self.event = threading.Event()
        self.event.clear()
        self.stopped = False
        self.start()
        if have_qt:
            self.setPriority(QtCore.QThread.LowPriority)
        
    def run(self):
        while self.stopped is False:
            self.event.wait()
            self.event.clear()
            if self.stopped is False:
                try:
                    result = self.target(*self.args)
                    self.machine.results.append(result)
                except Exception, e:
                    print e
                    traceback.print_exc(file=sys.stdout)
                    
                self.machine.workers.append(self) #reappend me to the deque of available workers, IlastikJob popped me at the beginning
                self.machine.sem.release() # the semaphore is required in the JobMachine, we release it here when finished
        self.quit()
                    
    def process(self, target, args, machine):
        #this function gets called from outside the thread and is non blocking
        self.machine = machine
        self.target = target
        self.args = args
        self.event.set()

class JobMachineWorkerUnthreaded(object):
    def __init__(self):
        pass
    
    def process(self, target, args, machine):
        result = target(*args)
        machine.results.append(result)
        machine.workers.append(self)
        machine.sem.release()      

class JobMachine(object):
    """
    The JobMachine class can be used to easily parallelize non dependent tasks that can not block
    each other, e.g. it is usable for DataLevel parallelism 
    """
    
    def __init__(self):
        self.results = deque()
    
    def process(self, jobs):
        """this function is blocking"""
        
        self.numWorkers = GLOBAL_WM.threads
        self.sem = threading.Semaphore(self.numWorkers)
        self.workers = deque()
        for i in range(self.numWorkers):
            worker = GLOBAL_WM.workerPool[i]
            #TODO: only append free workers !
            self.workers.append(worker)
        
        #do the work
        while len(jobs) > 0:
            self.sem.acquire()
            job = jobs.pop()
            job.run(self)
            
        #make sure all workers finished:    
        for i in range(self.numWorkers):
            self.sem.acquire()

        #release the semaphore finally:    
        for i in range(self.numWorkers):
            self.sem.release()            
        
        results = self.results
        self.results = deque()    
        return results
    


class WorkerManager(object):
    def __init__(self):
        self.cpus = detectCPUs()
        self.workerPool = deque()
        if os.environ.has_key("NUMBER_OF_PROCESSORS"):
            self.setThreadCount(self.cpus + 1) #don't use threading under windows for now
        else:
            self.setThreadCount(self.cpus + 1)
        
    def setThreadCount(self, threadCount):
        self.stopWorkers()
        if threadCount == 0:
            self.threads = 1
            worker = JobMachineWorkerUnthreaded()
            self.workerPool.append(worker)
        else:
            self.threads = threadCount
            for i in range(threadCount):
                worker = JobMachineWorker()
                self.workerPool.append(worker)
            
        
    def stopWorkers(self):
        for i,w in enumerate(self.workerPool):
            if not issubclass(w.__class__,JobMachineWorkerUnthreaded):
                print "stopping worker thread ", str(i)
                w.stopped = True
                w.event.set()
                w.wait()
        self.workerPool.clear()
        
    def __del__(self):
        self.stopWorkers()

GLOBAL_WM = WorkerManager()

########################################################################################
def testFunction(s1, s2):
    print s1,s2 
    return "Result " +  s2

def test():
    """simple JobMachine test and usage example"""
    machine = JobMachine()
    jobs = []
    
    #first round
    for i in range(10):
        job = IlastikJob(testFunction, ["Processing task ",str(i)])
        jobs.append(job)

    results = machine.process(jobs)
    print "finished:"
    
    for r in results:
        print r

    GLOBAL_WM.setThreadCount(0) #set unthreaded mode
    
    #second round
    for i in range(10):
        job = IlastikJob(testFunction, ["#2 Processing task ",str(i)])
        jobs.append(job)

    results = machine.process(jobs)
    print "finished:"
    
    for r in results:
        print r

if __name__ == "__main__":
    test()
