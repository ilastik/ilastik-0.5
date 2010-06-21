from classifierBase import * 

#class ClassifierVW(ClassifierBase):
#    def __init__(self, features=None, labels=None, tmpFolder='.', regressorFile='vopalVabbitRegressor', trainFile='tmp_svm_light_file', testFile='tmp_svm_light_file_test', predictFile='tmp_svm_light_output'):
#        ClassifierBase.__init__(self)
#        self.tmpFolder = tmpFolder
#        myjoin = lambda p,f: "%s/%s" % (p,f)
#        self.regressorFile = myjoin(tmpFolder, regressorFile)
#        self.trainFile = myjoin(tmpFolder, trainFile)
#        self.predictFile = myjoin(tmpFolder, predictFile)
#        self.testFile = myjoin(tmpFolder, testFile)
#
#        if 'win' in sys.platform:
#            self.trainCommand = 'c:/cygwin/bin/bash -c "./vw %s"'
#            self.predictCommand = 'c:/cygwin/bin/bash -c "./vw %s"'
#
#        elif 'linux' in sys.platform:
#            self.trainCommand = './vw %s'
#            self.predictCommand = './vw %s'
#        else:
#            print "ClassifierVW: Unkown platform"
#
#        self.train(features, labels)
#
#
#    def train(self, train_data, train_labels):
#        #export the data
#        ClassificationImpex.exportToSVMLight(train_data, train_labels, self.trainFile, True)
#
#        options = " -d %s -f %s" % (self.trainFile, self.regressorFile)
#        print self.trainCommand % options
#        os.system(self.trainCommand % options)
#
#
#
#
#
#    def predict(self, test_data):
#        ClassificationImpex.exportToSVMLightNoLabels(test_data, self.testFile, True)
#        options = " -t -d %s -i %s  -p %s" % (self.testFile, self.regressorFile, self.predictFile)
#        print options
#        os.system(self.predictCommand % options)
#        res = ClassificationImpex.readSVMLightClassification(self.predictFile)
#        res.shape = res.shape[0],-1
#        res = numpy.concatenate((res,1-res),axis=1)
#        return res