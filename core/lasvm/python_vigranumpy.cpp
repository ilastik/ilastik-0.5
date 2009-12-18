#define PY_ARRAY_UNIQUE_SYMBOL vigranumpytest_PyArray_API

#include "lasvmSingleKernel.hxx"
#include "KernelGauss.hxx"
#include <Python.h>
#include <boost/python.hpp>
#include <vigra/numpy_array.hxx>
#include <vigra/numpy_array_converters.hxx>
#include <vigra/matrix.hxx>
#include <iostream>

#include <iostream>
#include <vector>

using namespace boost::python;

template<class T,class Kernel>
void remove_data(laSvmSingleKernel<T,Kernel>& svm,
                 vigra::NumpyArray<1, int> unique_ids)
{
	//Convert to wanted format
	svm.removeData(unique_ids);
}
template<class T,class Kernel>
void add_data(laSvmSingleKernel<T,Kernel>& svm,
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
void train_online(laSvmSingleKernel<T,Kernel>& svm,
		  int epochs,
		  int resample_methode,
		  bool second_order)
{
	svm.trainOnline(epochs,resample_methode,second_order);
	svm.finish(second_order);
}

template<class T,class Kernel>
void train_online_old(laSvmSingleKernel<T,Kernel>& svm,
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
void improve_solution(laSvmSingleKernel<T,Kernel>& svm)
{
	svm.KernelOptimizationStep();
}

template<class T,class Kernel>
vigra::NumpyAnyArray predict(laSvmSingleKernel<T,Kernel>& svm,
                       vigra::NumpyArray<2,T> samples,
                       vigra::NumpyArray<1,int> res)
{
    res.reshapeIfEmpty(vigra::MultiArrayShape<1>::type(samples.shape(0)), "lasvm::predict(): Output array has wrong shape.");
    //Make predictions
    int length=res.shape(0);
    for(int i=0;i<length;++i)
    {
        T val=svm.predictF(rowVector(samples,i));
        if(val>0.0)
            res[i]=1;
        else
            res[i]=-1;
    }
    return res;
}
template<class T,class Kernel>
vigra::NumpyAnyArray predictF(laSvmSingleKernel<T,Kernel>& svm,
                       vigra::NumpyArray<2,T> samples,
                       vigra::NumpyArray<1,int> res)
{
    res.reshapeIfEmpty(vigra::MultiArrayShape<1>::type(samples.shape(0)), "lasvm::predict(): Output array has wrong shape.");
    //Make predictions
    int length=res.shape(0);
    for(int i=0;i<length;++i)
    {
        res[i]=svm.predictF(columnVector(samples,i));
    }
    return res;
}

template<class T,class Kernel>
int throwOutsByMostDistant(laSvmSingleKernel<T,Kernel>& svm,numeric::array& samples)
{
	int num_samples=PyArray_DIM(samples.ptr(),0);
	int num_features=PyArray_DIM(samples.ptr(),1);
	//Convert to wanted format
	vector<vector<T> > want_samples;
	int i,j;
	for(i=0;i<num_samples;++i)
	{
		want_samples.push_back(vector<T>(num_features));
		for(j=0;j<num_features;++j)
		{
			want_samples.back()[j]=extract<T>(samples[make_tuple(i,j)]);
		}
		
	}
	return svm.throwOutsByMostDistant(want_samples);
}

template<class T,class Kernel>
double getW2(laSvmSingleKernel<T,Kernel>& svm)
{
	return svm.getW2();
}

#define DIND1(a, i) *((double *) PyArray_GETPTR1(a, i))
#define DIND2(a, i, j) *((double *) PyArray_GETPTR2(a, i, j))
template<class T,class Kernel>
PyObject* getAlphas(laSvmSingleKernel<T,Kernel>& svm)
{
	vector<double> alphas;
	svm.getAlphas(alphas);
	npy_intp length=alphas.size();
	PyArrayObject* o=(PyArrayObject*)PyArray_SimpleNew(1,&length,NPY_DOUBLE);
	int i;
	for(i=0;i<alphas.size();++i)
	{
		DIND1(o,i)=alphas[i];
	}
	return PyArray_Return(o);
}

template<class T,class Kernel>
PyObject* getXis(laSvmSingleKernel<T,Kernel>& svm)
{
	vector<double> xis;
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
numeric::array getSVs(laSvmSingleKernel<T,Kernel>& svm)
{
	vector<vector<T> > svs;
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
numeric::array getXiAlphaDerived(laSvmSingleKernel<T,Kernel>& svm,double rho)
{
	vector<double> derives;
	svm.XiAlphaBoundDerivative(derives,rho);
	npy_intp length=derives.size();
	object obj(handle<>(PyArray_SimpleNew(1,&length,PyArray_DOUBLE)));
	numeric::array out=extract<numeric::array>(obj);

	for(int i=0;i<length;++i)
		out[make_tuple(i)]=derives[i];
	return out;
}

template<class T>
T getGamma(laSvmSingleKernel<T,KernelGauss<float> >& svm)
{
	return svm.kernel.gamma;
}

template<class T,class kernel>
T getVariance(laSvmSingleKernel<T,kernel>& svm,int index)
{
	return svm.variance[index];
}

template<class T>
T getGammaMultiParam(laSvmSingleKernel<T,KernelGaussMultiParams<float> >& svm,int index)
{
	return svm.kernel.gammas[index];
}
	
template<class T,class Kernel>
T getStepsize(laSvmSingleKernel<T,Kernel>& svm,int index)
{
	return svm.kernel_opt_step_size[index];
}


template<class T>
laSvmSingleKernel<T,KernelGaussMultiParams<float> >*
createLaSvmMultiPar(T gamma,
		    int num_features,
		    double C,double epsilon,
		    int precache_elements,bool verbose=false) 
{
    vector<T> gammas(num_features,gamma);
    return new laSvmSingleKernel<T,KernelGaussMultiParams<float> >(gammas,C,epsilon,precache_elements,verbose);
}

template<class T,class Kernel>
void optimizeKernelStep(laSvmSingleKernel<T,Kernel>& svm,int methode)
{
	switch(methode)
	{
	case 0:
		svm.KernelOptimizationStep(laSvmSingleKernel<T,Kernel>::GRAD_IND_STEP_SIZE_SIGN_ADAPTION);
		break;
	case 1:
		svm.KernelOptimizationStep(laSvmSingleKernel<T,Kernel>::NORMALIZED_GRAD_DESCENT);
		break;
	case 2:
		svm.KernelOptimizationStep(laSvmSingleKernel<T,Kernel>::INTERVALL_HALVING);
		break;
	case 3:
		svm.KernelOptimizationStep(laSvmSingleKernel<T,Kernel>::MIXED);
		break;
	}
}

BOOST_PYTHON_MODULE_INIT(lasvm)
{
    using namespace vigra;
    import_vigranumpy();

    class_<laSvmSingleKernel<float,KernelGauss<float> > >("laSvm",init<float,float,double,int,bool>())
        .def("addData",
             registerConverters(&add_data<float,KernelGauss<float> >))
        .def("removeData",&remove_data<float,KernelGauss<float> >)
        .def("trainOnline",
             registerConverters(&train_online_old<float,KernelGauss<float> >))
        .def("fastLearn",
             registerConverters(&train_online<float,KernelGauss<float> >))
        .def("deepLearn",
             registerConverters(&improve_solution<float,KernelGauss<float> >))
        .def("finish",
             registerConverters(&laSvmSingleKernel<float,KernelGauss<float> >::finish))
        .def("predict",
             registerConverters(&predict<float,KernelGauss<float> >),
             (boost::python::arg("samples"),boost::python::arg("result")=object()),
             "do prediction")
        .def("predictF",
             registerConverters(&predictF<float,KernelGauss<float> >),
             (boost::python::arg("samples"),boost::python::arg("result")=object()))
        .def("getW2",
             registerConverters(&getW2<float,KernelGauss<float> >))
        .def("getXiAlphaBound",
             registerConverters(&laSvmSingleKernel<float,KernelGauss<float> >::XiAlphaBound))
        .def("getAlphas",
             registerConverters(&getAlphas<float,KernelGauss<float> >))
        .def("getXis",
             registerConverters(&getXis<float,KernelGauss<float> >))
        .def("getSVs",
             registerConverters(&getSVs<float,KernelGauss<float> >))
        .def("optimizeKernelStep",
             registerConverters(&optimizeKernelStep<float,KernelGauss<float> >))
        .def("gamma",
             registerConverters(&getGamma<float>))
        .def("variance",
             registerConverters(&getVariance<float,KernelGauss<float> >))
        .def("enableResampleBorder",
             registerConverters(&laSvmSingleKernel<float,KernelGauss<float> >::enableResampleBorder))
        .def("stepsize",
             registerConverters(&getStepsize<float,KernelGauss<float> >))
        .def("shrinkFactorByPairing",
             registerConverters(&laSvmSingleKernel<float,KernelGauss<float> >::ShrinkFactorByPairing))
        .def("getXiAlphaDerived",
             registerConverters(&getXiAlphaDerived<float,KernelGauss<float> >));

    class_<laSvmSingleKernel<float,KernelGaussMultiParams<float> > >("laSvmMultiPar",
                                                                     no_init)
        .def("addData",
             registerConverters(&add_data<float,KernelGaussMultiParams<float> >))
        .def("shrinkFactorByPairing",
             registerConverters(&laSvmSingleKernel<float,KernelGaussMultiParams<float> >::ShrinkFactorByPairing))
        .def("removeData",
             registerConverters(&remove_data<float,KernelGaussMultiParams<float> >))
        .def("trainOnline",
             registerConverters(&train_online_old<float,KernelGaussMultiParams<float> >))
        .def("fastLearn",
             registerConverters(&train_online<float,KernelGaussMultiParams<float> >))
        .def("deepLearn",
             registerConverters(&improve_solution<float,KernelGaussMultiParams<float> >))
        .def("finish",
             registerConverters(&laSvmSingleKernel<float,KernelGaussMultiParams<float> >::finish))
        .def("predict",
             registerConverters(&predict<float,KernelGaussMultiParams<float> >),
             (boost::python::arg("samples"),boost::python::arg("result")=object()))
        .def("predictF",
             registerConverters(&predictF<float,KernelGaussMultiParams<float> >),
             (boost::python::arg("samples"),boost::python::arg("result")=object()))
        .def("getW2",
             registerConverters(&getW2<float,KernelGaussMultiParams<float> >))
        .def("getXiAlphaBound",
             registerConverters(&laSvmSingleKernel<float,KernelGaussMultiParams<float> >::XiAlphaBound))
        .def("getAlphas",
             registerConverters(&getAlphas<float,KernelGaussMultiParams<float> >))
        .def("getXis",
             registerConverters(&getXis<float,KernelGaussMultiParams<float> >))
        .def("getSVs",
             registerConverters(&getSVs<float,KernelGaussMultiParams<float> >))
        .def("optimizeKernelStep",
             registerConverters(&optimizeKernelStep<float,KernelGaussMultiParams<float> >))
        .def("gamma",
             registerConverters(&getGammaMultiParam<float>))
        .def("variance",
             registerConverters(&getVariance<float,KernelGaussMultiParams<float> >))
        .def("enableResampleBorder",
             registerConverters(&laSvmSingleKernel<float,KernelGaussMultiParams<float> >::enableResampleBorder))
        .def("stepsize",
             registerConverters(&getStepsize<float,KernelGaussMultiParams<float> >))
        .def("throwOutsByMostDistant",
             registerConverters(&throwOutsByMostDistant<float,KernelGaussMultiParams<float> >))
        .def("getXiAlphaDerived",
             registerConverters(&getXiAlphaDerived<float,KernelGaussMultiParams<float> >));
    def("createLaSvmMultiPar",&createLaSvmMultiPar<float>,return_value_policy<manage_new_object>());
}
