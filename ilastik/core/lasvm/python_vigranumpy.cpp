#define PY_ARRAY_UNIQUE_SYMBOL lasvm_PyArray_API

#include <boost/python.hpp>
#include <vigra/numpy_array.hxx>
#include <vigra/numpy_array_converters.hxx>
#include <vigra/matrix.hxx>
#include <vector>
#include "svmTestFunctions.hxx"
#include "KernelGauss.hxx"
#include "predictionSet.hxx"
#include <Python.h>
#include <iostream>
#include <time.h>

#include <iostream>

using namespace boost::python;

template<class T,class Kernel>
void remove_data(testSvm<T,Kernel>& svm,
                 vigra::NumpyArray<1, int> unique_ids)
{
	//Convert to wanted format
	svm.removeData(unique_ids);
}
template<class T,class Kernel>
void add_data(testSvm<T,Kernel>& svm,
              vigra::NumpyArray<2,T> samples,
              vigra::NumpyArray<1,int> labels,
              vigra::NumpyArray<1,int> unique_ids)
{
    if(samples.shape(0)!=labels.shape(0))
        throw std::runtime_error("there must be as many labels as samples");
    if(samples.shape(0)!=unique_ids.shape(0))
        throw std::runtime_error("there must be as many ids as samples");
    svm.addData(samples,labels,unique_ids);
}

template<class T,class Kernel>
void train_online(testSvm<T,Kernel>& svm,
		  int epochs,
		  int resample_methode,
		  bool second_order)
{
    Py_BEGIN_ALLOW_THREADS
    svm.trainOnline(epochs,resample_methode,second_order);
    svm.finish(second_order);
    Py_END_ALLOW_THREADS
}

template<class T,class Kernel>
void train_online_old(testSvm<T,Kernel>& svm,
                      vigra::NumpyArray<2,T> samples,
                      vigra::NumpyArray<1,int> labels,
                      vigra::NumpyArray<1,int> unique_ids,
                      int epochs,
                      int resample_methode,
                      bool second_order)
{
	add_data(svm,samples,labels,unique_ids);
	train_online(svm,epochs,resample_methode,second_order);
}

template<class T,class Kernel>
void improve_solution(testSvm<T,Kernel>& svm)
{
    Py_BEGIN_ALLOW_THREADS
    svm.KernelOptimizationStep();
    Py_END_ALLOW_THREADS
}

template<class T,class Kernel>
vigra::NumpyAnyArray predictF(testSvm<T,Kernel>& svm,
                       SvmPredictionSet<T>& samples,
                       vigra::NumpyArray<1,double> res)
{
  res.reshapeIfEmpty(vigra::MultiArrayShape<1>::type(samples.features.size()), "lasvm::predictF(): Output array has wrong shape.");
    clock_t start=clock();
    Py_BEGIN_ALLOW_THREADS
    //Make predictions
    svm.predictF(samples,res);
    Py_END_ALLOW_THREADS
    double spend_time=(clock()-start)/double(CLOCKS_PER_SEC / 1000);
    std::cerr<<"INFO: "<<samples.features.size()<<" predictions took "<<spend_time<<"ms"<<std::endl;
    std::cerr<<"INFO: "<<svm.used_svs.size()<<" support vectors"<<std::endl;
    return res;
}

template<class T,class Kernel>
vigra::NumpyAnyArray predict(testSvm<T,Kernel>& svm,
			     SvmPredictionSet<T>& samples,
			     vigra::NumpyArray<1,int> res)
{
    clock_t start=clock();

    res.reshapeIfEmpty(vigra::MultiArrayShape<1>::type(samples.features.size()), "lasvm::predict(): Output array has wrong shape.");
    Py_BEGIN_ALLOW_THREADS
    //Make predictions
    int length=res.shape(0);
    for(int i=0;i<length;++i)
    {
        res[i]=svm.predictLabel(samples.features[i]);
    }
    double spend_time=(clock()-start)/double(CLOCKS_PER_SEC / 1000);
    std::cerr<<"INFO: "<<samples.features.size()<<" predictions took "<<spend_time<<"ms"<<std::endl;
    std::cerr<<"INFO: "<<svm.used_svs.size()<<" support vectors"<<std::endl;
    Py_END_ALLOW_THREADS
    return res;
}

template<class T,class Kernel>
vigra::NumpyAnyArray pythonPredictFsingleCoverTree(testSvm<T,Kernel>& svm,
						   SvmPredictionSet<T>& samples,double epsilon,
						   vigra::NumpyArray<1,double> res)
{

  res.reshapeIfEmpty(vigra::MultiArrayShape<1>::type(samples.features.size()), "lasvm::predictF(): Output array has wrong shape.");
    Py_BEGIN_ALLOW_THREADS
    clock_t start=clock();
    svm.singleCoverTreePredictF(samples,res,epsilon);
    double spend_time=(clock()-start)/double(CLOCKS_PER_SEC / 1000);
    std::cerr<<"INFO: "<<samples.features.size()<<" predictions (single cover tree) took "<<spend_time<<"ms"<<std::endl;
    std::cerr<<"INFO: "<<svm.used_svs.size()<<" support vectors"<<std::endl;
    Py_END_ALLOW_THREADS
    return res;
}

template<class T,class Kernel>
vigra::NumpyAnyArray pythonPredictFRangedSingleCoverTree(testSvm<T,Kernel>& svm,
							 SvmPredictionSet<T>& samples,
							 double epsilon,double delta,bool use_avg,
							 vigra::NumpyArray<1,T> res)
{

  res.reshapeIfEmpty(vigra::MultiArrayShape<1>::type(samples.features.size()), "lasvm::predictF(): Output array has wrong shape.");
    Py_BEGIN_ALLOW_THREADS
    clock_t start=clock();
    svm.singleCoverTreeRangedPredictF(samples,res,epsilon,delta,use_avg);
    double spend_time=(clock()-start)/double(CLOCKS_PER_SEC / 1000);
    std::cerr<<"INFO: "<<samples.features.size()<<" predictions (single cover tree) took "<<spend_time<<"ms"<<std::endl;
    std::cerr<<"INFO: "<<svm.used_svs.size()<<" support vectors"<<std::endl;
    Py_END_ALLOW_THREADS
    return res;
}

template<class T,class Kernel>
vigra::NumpyAnyArray pythonPredictFdualCoverTree(testSvm<T,Kernel>& svm,
                                           SvmPredictionSet<T>& samples,
					   double epsilon,
                                           vigra::NumpyArray<1,T> res)
{

  res.reshapeIfEmpty(vigra::MultiArrayShape<1>::type(samples.features.size()), "lasvm::predictF(): Output array has wrong shape.");
    Py_BEGIN_ALLOW_THREADS
    clock_t start=clock();
    svm.dualCoverTreePredictF(samples,res,epsilon);
    double spend_time=(clock()-start)/double(CLOCKS_PER_SEC / 1000);
    std::cerr<<"INFO: "<<samples.features.size()<<" predictions (dual cover tree) took "<<spend_time<<"ms"<<std::endl;
    std::cerr<<"INFO: "<<svm.used_svs.size()<<" support vectors"<<std::endl;
    Py_END_ALLOW_THREADS
    return res;
}



template<class T,class Kernel>
vigra::NumpyAnyArray softBorderAL(testSvm<T,Kernel>& svm,
                                  vigra::NumpyArray<2,T> samples,
                                  vigra::NumpyArray<1,double> res)
{
  res.reshapeIfEmpty(vigra::MultiArrayShape<1>::type(samples.shape(0)), "lasvm::softBorderAL(): Output array has wrong shape.");
    int length=res.shape(0);
    for(int i=0;i<length;++i)
    {
        res[i]=svm.BorderSoftnessAL(rowVector(samples,i));
    }
    return res;
}

template<class T,class Kernel>
vigra::NumpyAnyArray W2_AL(testSvm<T,Kernel>& svm,
			   vigra::NumpyArray<2,T>& samples,
                                  vigra::NumpyArray<1,double> res)
{
  res.reshapeIfEmpty(vigra::MultiArrayShape<1>::type(samples.shape(0)), "lasvm::softBorderAL(): Output array has wrong shape.");
    int length=res.shape(0);
    for(int i=0;i<length;++i)
    {
        res[i]=svm.W2_AL(rowVector(samples,i));
    }
    return res;
}

template<class T,class Kernel>
vigra::NumpyAnyArray testALCrit(testSvm<T,Kernel>& svm,
                                  vigra::NumpyArray<2,T> samples,int id,
                                  vigra::NumpyArray<1,double> res)
{
    res.reshapeIfEmpty(vigra::MultiArrayShape<1>::type(samples.shape(0)), "lasvm::softBorderAL(): Output array has wrong shape.");
    int length=res.shape(0);
    for(int i=0;i<length;++i)
    {
        res[i]=svm.testALCrit(rowVector(samples,i),id);
    }
    return res;
}

template<class T,class Kernel>
int throwOutsByMostDistant(testSvm<T,Kernel>& svm,numeric::array& samples)
{
	int num_samples=PyArray_DIM(samples.ptr(),0);
	int num_features=PyArray_DIM(samples.ptr(),1);
	//Convert to wanted format
	std::vector<std::vector<T> > want_samples;
	int i,j;
	for(i=0;i<num_samples;++i)
	{
		want_samples.push_back(std::vector<T>(num_features));
		for(j=0;j<num_features;++j)
		{
			want_samples.back()[j]=extract<T>(samples[make_tuple(i,j)]);
		}
		
	}
	return svm.throwOutsByMostDistant(want_samples);
}

template<class T,class Kernel>
double getW2(testSvm<T,Kernel>& svm)
{
	return svm.getW2();
}

#define DIND1(a, i) *((double *) PyArray_GETPTR1(a, i))
#define DIND2(a, i, j) *((double *) PyArray_GETPTR2(a, i, j))
template<class T,class Kernel>
PyObject* getAlphas(testSvm<T,Kernel>& svm)
{
	std::vector<double> alphas;
	npy_intp length[2];
	length[0]=svm.used_svs.size();
	length[1]=3;
	PyArrayObject* o=(PyArrayObject*)PyArray_SimpleNew(2,length,NPY_DOUBLE);
	int i;
	for(i=0;i<svm.used_svs.size();++i)
	{
		DIND2(o,i,0)=svm.support_vectors[i].alpha;
		DIND2(o,i,1)=svm.support_vectors[i].cmin;
                DIND2(o,i,2)=svm.support_vectors[i].cmax;
	}
	return PyArray_Return(o);
}

template<class T,class Kernel>
PyObject* getXis(testSvm<T,Kernel>& svm)
{
	std::vector<double> xis;
	svm.getXis(xis);
	npy_intp length=xis.size();
	PyArrayObject* o=(PyArrayObject*)PyArray_SimpleNew(1,&length,NPY_DOUBLE);
	int i;
	for(i=0;i<xis.size();++i)
	{
		T tmp=xis[i];
		DIND1(o,i)=tmp;
	}
	return PyArray_Return(o);
}

template<class T,class Kernel>
numeric::array getSVs(testSvm<T,Kernel>& svm)
{
	std::vector<std::vector<T> > svs;
	svm.getSVs(svs);
	npy_intp length[2];
	length[0]=svs.size();
	length[1]=svs[0].size();
	object obj(handle<>(PyArray_SimpleNew(2,length,PyArray_DOUBLE)));
	numeric::array out=extract<numeric::array>(obj);

	for(int i=0;i<length[0];++i)
		for(int j=0;j<length[1];++j)
			out[make_tuple(i,j)]=svs[i][j];
	return out;
}

template<class T,class Kernel>
vigra::NumpyAnyArray getXiAlphaDerived(testSvm<T,Kernel>& svm,double rho,bool include_db,vigra::NumpyArray<1,T> res)
{
    std::vector<double> derives;
    svm.XiAlphaBoundDerivative(derives,rho,include_db);
    res.reshapeIfEmpty(vigra::MultiArrayShape<1>::type(derives.size()), "lasvm::getXiAlphaDerived(): Output array has wrong shape.");

    for(int i=0;i<derives.size();++i)
        res[i]=derives[i];
    return res;
}

template<class T,class Kernel>
vigra::NumpyAnyArray getXiAlphaDerivedExact(testSvm<T,Kernel>& svm,double rho,vigra::NumpyArray<1,T> res)
{
    std::vector<double> derives;
    svm.XiAlphaBoundDerivativeExact(derives,rho);
    res.reshapeIfEmpty(vigra::MultiArrayShape<1>::type(derives.size()), "lasvm::getXiAlphaDerivedExact(): Output array has wrong shape.");

    for(int i=0;i<derives.size();++i)
        res[i]=derives[i];
    return res;
}

template<class T>
T getGamma(testSvm<T,KernelGauss<T> >& svm)
{
	return svm.kernel.gamma;
}

template<class T,class kernel>
T getVariance(testSvm<T,kernel>& svm,int index)
{
	return svm.variance[index];
}

template<class T>
T getGammaMultiParam(testSvm<T,KernelGaussMultiParams<T> >& svm,int index)
{
	return svm.kernel.gammas[index];
}
	
template<class T,class Kernel>
T getStepsize(testSvm<T,Kernel>& svm,int index)
{
	return svm.kernel_opt_step_size[index];
}


template<class T>
testSvm<T,KernelGaussMultiParams<T> >*
createLaSvmMultiPar(T gamma,
		    int num_features,
		    double C,double epsilon,
		    int precache_elements,bool verbose=false) 
{
    std::vector<T> gammas(num_features,gamma);
    return new testSvm<T,KernelGaussMultiParams<T> >(gammas,C,epsilon,precache_elements,verbose);
}

template<class T,class Kernel>
void optimizeKernelStep(testSvm<T,Kernel>& svm,int methode,bool include_db)
{
	switch(methode)
	{
	case 0:
		svm.KernelOptimizationStep(testSvm<T,Kernel>::GRAD_IND_STEP_SIZE_SIGN_ADAPTION,include_db);
		break;
	case 1:
		svm.KernelOptimizationStep(testSvm<T,Kernel>::NORMALIZED_GRAD_DESCENT,include_db);
		break;
	case 2:
		svm.KernelOptimizationStep(testSvm<T,Kernel>::INTERVALL_HALVING,include_db);
		break;
	case 3:
		svm.KernelOptimizationStep(testSvm<T,Kernel>::MIXED,include_db);
		break;
	}
}

template<class T>
void defineLASVMs(const char* name_single,const char* name_multi,const char* name_pred_set)
{
    using namespace vigra;

    class_<SvmPredictionSet<T> >(name_pred_set,init<vigra::NumpyArray<2,T> >());

    class_<testSvm<T,KernelGauss<T> > >(name_single,init<T,T,double,int,bool>())
        .def("addData",
             registerConverters(&add_data<T,KernelGauss<T> >))
        .def("removeData",&remove_data<T,KernelGauss<T> >)
        .def("trainOnline",
             registerConverters(&train_online_old<T,KernelGauss<T> >))
        .def("fastLearn",
             registerConverters(&train_online<T,KernelGauss<T> >))
        .def("deepLearn",
             registerConverters(&improve_solution<T,KernelGauss<T> >))
        .def("finish",
             registerConverters(&testSvm<T,KernelGauss<T> >::finish))
        .def("predict",
             registerConverters(&predict<T,KernelGauss<T> >),
             (boost::python::arg("samples"),boost::python::arg("result")=object()),
             "do prediction")
        .def("predictF",
             registerConverters(&predictF<T,KernelGauss<T> >),
             (boost::python::arg("samples"),boost::python::arg("result")=object()))
        .def("softBorderAL",
             registerConverters(&softBorderAL<T,KernelGauss<T> >),
             (boost::python::arg("samples"),boost::python::arg("result")=object()))
        .def("getW2",
             registerConverters(&getW2<T,KernelGauss<T> >))
        .def("getXiAlphaBound",
             registerConverters(&testSvm<T,KernelGauss<T> >::XiAlphaBound))
        .def("getB",
             registerConverters(&testSvm<T,KernelGauss<T> >::getB))
        .def("getAlphas",
             registerConverters(&getAlphas<T,KernelGauss<T> >))
        .def("getXis",
             registerConverters(&getXis<T,KernelGauss<T> >))
        .def("getSVs",
             registerConverters(&getSVs<T,KernelGauss<T> >))
        .def("optimizeKernelStep",
             registerConverters(&optimizeKernelStep<T,KernelGauss<T> >))
        .def("gamma",
             registerConverters(&getGamma<T>))
        .def("variance",
             registerConverters(&getVariance<T,KernelGauss<T> >))
        .def("enableResampleBorder",
             registerConverters(&testSvm<T,KernelGauss<T> >::enableResampleBorder))
        .def("enableLindepThreshold",
             registerConverters(&testSvm<T,KernelGauss<T> >::setLinDepThreshold))
        .def("stepsize",
             registerConverters(&getStepsize<T,KernelGauss<T> >))
        .def("shrinkFactorByPairing",
             registerConverters(&testSvm<T,KernelGauss<T> >::ShrinkFactorByPairing))
        .def("cleanSVs",
             registerConverters(&testSvm<T,KernelGauss<T> >::cleanSVs))
        .def("getXiAlphaDerived",
             registerConverters(&getXiAlphaDerived<T,KernelGauss<T> >),
             (boost::python::arg("rho"),boost::python::arg("include_db"),boost::python::arg("result")=object()))
        .def("getXiAlphaDerivedExact",
             registerConverters(&getXiAlphaDerivedExact<T,KernelGauss<T> >),
             (boost::python::arg("rho"),boost::python::arg("result")=object()))
        .def("reset",
             &testSvm<T,KernelGauss<T> >::reset)
        .def_readwrite("epsilon",
                       &testSvm<T,KernelGauss<T> >::epsilon)
        .def_readwrite("sig_b",
                       &testSvm<T,KernelGauss<T> >::sig_b)
        .def_readwrite("sig_a",
                       &testSvm<T,KernelGauss<T> >::sig_a)
        .def_readonly("num_dist",
		      &testSvm<T,KernelGauss<T> >::num_dist)
        .def_readonly("num_exp",
		      &testSvm<T,KernelGauss<T> >::num_exp);

    class_<testSvm<T,KernelGaussMultiParams<T> > >(name_multi,
                                                                     no_init)
        .def("addData",
             registerConverters(&add_data<T,KernelGaussMultiParams<T> >))
        .def("startGuessParameters",
             &testSvm<T,KernelGaussMultiParams<T> >::startGuessKernelParameters)
        .def("shrinkFactorByPairing",
             registerConverters(&testSvm<T,KernelGaussMultiParams<T> >::ShrinkFactorByPairing))
        .def("cleanSVs",
             registerConverters(&testSvm<T,KernelGaussMultiParams<T> >::cleanSVs))
        .def("removeData",
             registerConverters(&remove_data<T,KernelGaussMultiParams<T> >))
        .def("trainOnline",
             registerConverters(&train_online_old<T,KernelGaussMultiParams<T> >))
        .def("fastLearn",
             registerConverters(&train_online<T,KernelGaussMultiParams<T> >))
        .def("deepLearn",
             registerConverters(&improve_solution<T,KernelGaussMultiParams<T> >))
        .def("finish",
             registerConverters(&testSvm<T,KernelGaussMultiParams<T> >::finish))
        .def("predict",
             registerConverters(&predict<T,KernelGaussMultiParams<T> >),
             (boost::python::arg("samples"),boost::python::arg("result")=object()))
        .def("predictF",
             registerConverters(&predictF<T,KernelGaussMultiParams<T> >),
             (boost::python::arg("samples"),boost::python::arg("result")=object()))
        .def("predictFsingleCoverTree",
             registerConverters(&pythonPredictFsingleCoverTree<T,KernelGaussMultiParams<T> >),
             (boost::python::arg("samples"),boost::python::arg("epsilon"),boost::python::arg("result")=object()))
        .def("predictFRangedSingleCoverTree",
             registerConverters(&pythonPredictFRangedSingleCoverTree<T,KernelGaussMultiParams<T> >),
             (boost::python::arg("samples"),boost::python::arg("epsilon"),boost::python::arg("delta"),boost::python::arg("use_avg"),boost::python::arg("result")=object()))
        .def("predictFdualCoverTree",
             registerConverters(&pythonPredictFdualCoverTree<T,KernelGaussMultiParams<T> >),
             (boost::python::arg("samples"),boost::python::arg("epsilon"),boost::python::arg("result")=object()))
        .def("softBorderAL",
             registerConverters(&softBorderAL<T,KernelGaussMultiParams<T> >),
             (boost::python::arg("samples"),boost::python::arg("result")=object()))
        .def("W2_AL",
             registerConverters(&W2_AL<T,KernelGaussMultiParams<T> >),
             (boost::python::arg("samples"),boost::python::arg("result")=object()))
        .def("testALCrit",
             registerConverters(&testALCrit<T,KernelGaussMultiParams<T> >),
             (boost::python::arg("samples"),boost::python::arg("result")=object()))
        .def("getW2",
             registerConverters(&getW2<T,KernelGaussMultiParams<T> >))
        .def("getXiAlphaBound",
             registerConverters(&testSvm<T,KernelGaussMultiParams<T> >::XiAlphaBound))
        .def("getB",
             registerConverters(&testSvm<T,KernelGaussMultiParams<T> >::getB))
        .def("getAlphas",
             registerConverters(&getAlphas<T,KernelGaussMultiParams<T> >))
        .def("getXis",
             registerConverters(&getXis<T,KernelGaussMultiParams<T> >))
        .def("getSVs",
             registerConverters(&getSVs<T,KernelGaussMultiParams<T> >))
        .def("optimizeKernelStep",
             registerConverters(&optimizeKernelStep<T,KernelGaussMultiParams<T> >))
        .def("gamma",
             registerConverters(&getGammaMultiParam<T>))
        .def("variance",
             registerConverters(&getVariance<T,KernelGaussMultiParams<T> >))
        .def("enableResampleBorder",
             registerConverters(&testSvm<T,KernelGaussMultiParams<T> >::enableResampleBorder))
        .def("enableLindepThreshold",
             registerConverters(&testSvm<T,KernelGaussMultiParams<T> >::setLinDepThreshold))
        .def("stepsize",
             registerConverters(&getStepsize<T,KernelGaussMultiParams<T> >))
        .def("throwOutsByMostDistant",
             registerConverters(&throwOutsByMostDistant<T,KernelGaussMultiParams<T> >))
        .def("getXiAlphaDerived",
             registerConverters(&getXiAlphaDerived<T,KernelGaussMultiParams<T> >),
             (boost::python::arg("rho"),boost::python::arg("include_db"),boost::python::arg("result")=object()))
        .def("getXiAlphaDerivedExact",
             registerConverters(&getXiAlphaDerivedExact<T,KernelGaussMultiParams<T> >),
             (boost::python::arg("rho"),boost::python::arg("result")=object()))
        .def("reset",
             &testSvm<T,KernelGaussMultiParams<T> >::reset)
        .def("ReFindPairs",
	     &testSvm<T,KernelGaussMultiParams<T> >::ReFindPairs)
        .def("GetOptimalLinIndepTreshold",
	     &testSvm<T,KernelGaussMultiParams<T> >::GetLinindepThresholdForSVNum)
        .def("RestartOptimization",
	     &testSvm<T,KernelGaussMultiParams<T> >::RestartOptimization)
        .def_readwrite("epsilon",
                       &testSvm<T,KernelGaussMultiParams<T> >::epsilon)
        .def_readwrite("sig_b",
                       &testSvm<T,KernelGaussMultiParams<T> >::sig_b)
        .def_readwrite("sig_a",
                       &testSvm<T,KernelGaussMultiParams<T> >::sig_a)
        .def_readwrite("num_dist",
                       &testSvm<T,KernelGaussMultiParams<T> >::num_dist)
        .def_readwrite("num_exp",
                       &testSvm<T,KernelGaussMultiParams<T> >::num_exp);
    def(name_multi,&createLaSvmMultiPar<T>,return_value_policy<manage_new_object>());
}

BOOST_PYTHON_MODULE_INIT(lasvm)
{
    vigra::import_vigranumpy();
    defineLASVMs<float>("laSvm","laSvmMultiParams","SVM_PredSet");
    defineLASVMs<double>("laSvmD","laSvmMultiParamsD","SVM_PredSetD");
}
