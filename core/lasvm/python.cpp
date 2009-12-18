#define PY_ARRAY_UNIQUE_SYMBOL lasvm_PyArray_API

#include "lasvmSingleKernel.hxx"
#include "KernelGauss.hxx"

#include <boost/python.hpp>
#include <boost/python/numeric.hpp>
#include <boost/python/tuple.hpp>
#include <numpy/arrayobject.h>
#include <Python.h>

#include <iostream>
#include <vector>

using namespace boost::python;
using namespace std;


template<class T,class Kernel>
void remove_data(laSvmSingleKernel<T,Kernel>& svm,
			  numeric::array& unique_ids)
{
	int num_samples=PyArray_DIM(unique_ids.ptr(),0);
	//Convert to wanted format
	vector<int> want_ids;
	int i;
	for(i=0;i<num_samples;++i)
		want_ids.push_back(extract<int>(unique_ids[make_tuple(i)]));
	svm.removeData(want_ids);
}
template<class T,class Kernel>
void add_data(laSvmSingleKernel<T,Kernel>& svm,
			  numeric::array& samples,
			  numeric::array& labels,
			  numeric::array& unique_ids)
{
	int num_samples=PyArray_DIM(samples.ptr(),0);
	int num_features=PyArray_DIM(samples.ptr(),1);
	if(PyArray_DIM(labels.ptr(),0)!=num_samples)
		throw std::runtime_error("labels and samples must have same count");
	//Convert to wanted format
	vector<vector<T> > want_samples;
	vector<int> want_labels;
	vector<int> want_ids;
	int i,j;
	for(i=0;i<num_samples;++i)
	{
		want_samples.push_back(vector<T>(num_features));
		for(j=0;j<num_features;++j)
		{
			want_samples.back()[j]=extract<T>(samples[make_tuple(i,j)]);
		}
		
	}
	for(i=0;i<num_samples;++i)
		want_labels.push_back(extract<T>(labels[make_tuple(i)]));
	std::cerr<<"Begining with ids"<<std::endl;
	for(i=0;i<num_samples;++i)
		want_ids.push_back((int)extract<T>(unique_ids[make_tuple(i)]));
	svm.addData(want_samples,want_labels,want_ids);
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
			  numeric::array& samples,
			  numeric::array& labels,
			  numeric::array& unique_ids,
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
numeric::array predict(laSvmSingleKernel<T,Kernel>& svm,
			numeric::array& samples)
{
	//Make output
	npy_intp length[2];
	length[0]=PyArray_DIM(samples.ptr(),0);
	length[1]=PyArray_DIM(samples.ptr(),1);
	object obj(handle<>(PyArray_SimpleNew(1,&length[0],PyArray_INT)));
	numeric::array out=extract<numeric::array>(obj);

	//Make predictions
	vector<T> sample(length[1]);

	for(int i=0;i<length[0];++i)
	{
		for(int j=0;j<length[1];++j)
			sample[j]=extract<T>(samples[make_tuple(i,j)]);
		T val=svm.predictF(sample);
		if(val>0.0)
			out[make_tuple(i)]=1;
		else
			out[make_tuple(i)]=-1;
	}
	return out;
}
template<class T,class Kernel>
numeric::array predictF(laSvmSingleKernel<T,Kernel>& svm,
			numeric::array& samples)
{
	//Make output
	npy_intp length[2];
	length[0]=PyArray_DIM(samples.ptr(),0);
	length[1]=PyArray_DIM(samples.ptr(),1);
	object obj(handle<>(PyArray_SimpleNew(1,&length[0],PyArray_DOUBLE)));
	numeric::array out=extract<numeric::array>(obj);

	//Make predictions
	vector<T> sample(length[1]);

	for(int i=0;i<length[0];++i)
	{
		for(int j=0;j<length[1];++j)
			sample[j]=extract<T>(samples[make_tuple(i,j)]);
		out[make_tuple(i)]=svm.predictF(sample);
	}
	return out;
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


BOOST_PYTHON_MODULE(lasvm)
{
	import_array();
	numeric::array::set_module_and_type("numpy", "ndarray");

	class_<laSvmSingleKernel<float,KernelGauss<float> > >("laSvm",init<float,float,double,int,bool>())
		.def("addData",&add_data<float,KernelGauss<float> >)
		.def("removeData",&remove_data<float,KernelGauss<float> >)
		.def("trainOnline",&train_online_old<float,KernelGauss<float> >)
		.def("fastLearn",&train_online<float,KernelGauss<float> >)
		.def("deepLearn",&improve_solution<float,KernelGauss<float> >)
		.def("finish",&laSvmSingleKernel<float,KernelGauss<float> >::finish)
		.def("predict",&predict<float,KernelGauss<float> >)
		.def("predictF",&predictF<float,KernelGauss<float> >)
		.def("getW2",&getW2<float,KernelGauss<float> >)
		.def("getXiAlphaBound",&laSvmSingleKernel<float,KernelGauss<float> >::XiAlphaBound)
		.def("getAlphas",&getAlphas<float,KernelGauss<float> >)
		.def("getXis",&getXis<float,KernelGauss<float> >)
		.def("getSVs",&getSVs<float,KernelGauss<float> >)
		.def("optimizeKernelStep",&optimizeKernelStep<float,KernelGauss<float> >)
		.def("gamma",&getGamma<float>)
		.def("variance",&getVariance<float,KernelGauss<float> >)
		.def("enableResampleBorder",&laSvmSingleKernel<float,KernelGauss<float> >::enableResampleBorder)
		.def("stepsize",&getStepsize<float,KernelGauss<float> >)
		.def("shrinkFactorByPairing",&laSvmSingleKernel<float,KernelGauss<float> >::ShrinkFactorByPairing)
		.def("getXiAlphaDerived",&getXiAlphaDerived<float,KernelGauss<float> >);

	class_<laSvmSingleKernel<float,KernelGaussMultiParams<float> > >("laSvmMultiPar",
																	 no_init)
		.def("addData",&add_data<float,KernelGaussMultiParams<float> >)
		.def("shrinkFactorByPairing",&laSvmSingleKernel<float,KernelGaussMultiParams<float> >::ShrinkFactorByPairing)
		.def("removeData",&remove_data<float,KernelGaussMultiParams<float> >)
		.def("trainOnline",&train_online_old<float,KernelGaussMultiParams<float> >)
		.def("fastLearn",&train_online<float,KernelGaussMultiParams<float> >)
		.def("deepLearn",&improve_solution<float,KernelGaussMultiParams<float> >)
		.def("finish",&laSvmSingleKernel<float,KernelGaussMultiParams<float> >::finish)
		.def("predict",&predict<float,KernelGaussMultiParams<float> >)
		.def("predictF",&predictF<float,KernelGaussMultiParams<float> >)
		.def("getW2",&getW2<float,KernelGaussMultiParams<float> >)
		.def("getXiAlphaBound",&laSvmSingleKernel<float,KernelGaussMultiParams<float> >::XiAlphaBound)
		.def("getAlphas",&getAlphas<float,KernelGaussMultiParams<float> >)
		.def("getXis",&getXis<float,KernelGaussMultiParams<float> >)
		.def("getSVs",&getSVs<float,KernelGaussMultiParams<float> >)
		.def("optimizeKernelStep",&optimizeKernelStep<float,KernelGaussMultiParams<float> >)
		.def("gamma",&getGammaMultiParam<float>)
		.def("variance",&getVariance<float,KernelGaussMultiParams<float> >)
		.def("enableResampleBorder",&laSvmSingleKernel<float,KernelGaussMultiParams<float> >::enableResampleBorder)
		.def("stepsize",&getStepsize<float,KernelGaussMultiParams<float> >)
		.def("throwOutsByMostDistant",&throwOutsByMostDistant<float,KernelGaussMultiParams<float> >)
		.def("getXiAlphaDerived",&getXiAlphaDerived<float,KernelGaussMultiParams<float> >);
	def("createLaSvmMultiPar",&createLaSvmMultiPar<float>,return_value_policy<manage_new_object>());
}
