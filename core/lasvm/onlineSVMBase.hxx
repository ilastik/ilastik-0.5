#include "labeldSample.hxx"
#include "svhandler.hxx"
#include <vector>
#include <stdexcept>

#ifndef ONLINE_SVM_BASE_INCLUDED
#define ONLINE_SVM_BASE_INCLUDED

using namespace std;

template<class NV,class SV,class Kernel>
class OnlineSVMBase : public SVHandler<NV,SV,typename Kernel::RowType,typename Kernel::float_type>
{
protected:
    typedef typename Kernel::float_type T;
    //Functions for SVHandler
    virtual void FillRow(vector<T>& row,int sv_index); 
    virtual void UpdateRow(vector<T>& row,int sv_index);
    //The data we are working with
    std::vector<labeled_sample<typename Kernel::float_type> > data;
    std::list<int> unused_data;
    //List of unlearned data
    std::vector<int> unlearned_data;
    //Lenth of a features vector
    int VLength;
public:
    std::list<int> used_svs;
    bool verbose;
    OnlineSVMBase(typename Kernel::par_type kernel_par,int precache_elements,bool verbose=false);
    virtual ~OnlineSVMBase()
    {
	for(int i=0;i<data.size();++i)
	    data[i].clear();
    }
    template<class array>
    T DirectKernel(int sv, const array& s1);
    Kernel kernel;
    //Add samples for training
    template<class feature_array,class label_array,class id_array>
    void addData(const feature_array& sample,const label_array& l,const id_array& unique_ids);
    //Remove samples from training
    template<class array>
    void removeData(const array& unique_ids);
    virtual void unlearnSV(int index)=0;
    virtual void finishRemoval()=0;
    virtual double getB()=0;
    //For the online estimate of the variance...
    //http://en.wikipedia.org/wiki/Algorithms_for_calculating_variance#On-line_algorithm
    void InitVarianceEstimate(int dims);
    void OnlineVarianceEstimate(vector<int>& inew);
    int num_samples;
    vector<T> mean;
    vector<T> M2;
public:
    vector<T> variance;
    
    //Get data
    inline int getSVLabel(int id)
    {
	return data[SVs[id].data_id].label;
    }
    inline int getNVLabel(int id)
    {
	return data[NVs[id].data_id].label;
    }
    inline 	T* getSVFeatures(int id)
    {
	return data[SVs[id].data_id].features;
    }
    inline T* getNVFeatures(int id)
    {
	return data[NVs[id].data_id].features;
    }
   
    //Standard svm features
    template<class array>
    int predictLabel(const array& sample);
    template<class array>
    double predictF(const array& sample);
    double getW2();
    int getSVcount();
    void getAlphas(vector<double>& ret);
    void getSVs(vector<vector<T> >& ret);
};

template<class NV,class SV,class Kernel>
void OnlineSVMBase<NV,SV,Kernel>::UpdateRow(vector<T>& row,int sv_index)
{}

template<class NV,class SV,class Kernel>
void OnlineSVMBase<NV,SV,Kernel>::FillRow(vector<T>& row,int sv_index)
{
    std::list<int>::iterator i;
    assert(!SVs[sv_index].Unused());//Make sure the sv_index vector is set
    for(i=this->used_svs.begin();i!=this->used_svs.end();++i)
    {
	row[*i]=this->kernel.compute(this->getSVFeatures(*i),
				     this->getSVFeatures(sv_index),this->VLength);
    }
    row[sv_index]=this->kernel.compute(this->getSVFeatures(sv_index),
				       this->getSVFeatures(sv_index),this->VLength);
}

template<class NV, class SV, class Kernel>
template<class array>
typename Kernel::float_type OnlineSVMBase<NV,SV,Kernel>::DirectKernel(int sv,const array & s1)
{
    return this->kernel.compute(this->getSVFeatures(sv),
                                s1,this->VLength);
}

template<class NV,class SV,class Kernel>
OnlineSVMBase<NV,SV,Kernel>::OnlineSVMBase(typename Kernel::par_type kernel_par,int precache_elements,bool verbose)
: SVHandler<NV,SV,typename Kernel::RowType,typename Kernel::float_type>(precache_elements,typename Kernel::RowType()) , kernel(kernel_par)
{
    this->verbose=verbose;
    this->VLength=-1;
}

template<class T>
int numSamples(const vector<vector<T> > & in)
{
    return in.size();
}

template<class array>
int numSamples(const array & in)
{
    return in.shape(0);
}

template<class T>
int numFeatures(const vector<vector<T> > & in)
{
    return in[0].size();
}

template<class array>
int numFeatures(const array& in)
{
    return in.shape(1);
}

template<class NV,class SV,class Kernel>
template<class feature_array,class label_array,class id_array>
void OnlineSVMBase<NV,SV,Kernel>::addData(const feature_array & samples,const label_array& labels,const id_array& unique_ids)
{
    std::vector<int> inew;
    
    int i;
    for(i=0;i<numSamples(samples);++i)
    {
	if(this->VLength==-1)
	{
	    this->VLength=numFeatures(samples);
	    InitVarianceEstimate(this->VLength);
	}
	//Insert Sample
	int data_id;
	if(unused_data.empty())
	{
	    data_id=data.size();
	    data.push_back(labeled_sample<T>());
	}
	else
	{
	    data_id=unused_data.front();
	    unused_data.pop_front();
	}
	data[data_id].setData(samples,i,VLength,labels[i],unique_ids[i]);
	int id=this->AddSample(data_id);
	unlearned_data.push_back(id);
	inew.push_back(id);
    }
    this->OnlineVarianceEstimate(inew);
}

template<class NV,class SV,class Kernel>
template<class array>
void OnlineSVMBase<NV,SV,Kernel>::removeData(const array & unique_ids)
{
    for(int i=0;i<unique_ids.size();++i)
    {
	int data_id=-1;
	int j;
	for(j=0;j<data.size();++j)
	{
	    if(data[j].unique_id==unique_ids[i])
	    {
		data_id=j;
		break;
	    }
	}
	if(data_id==-1)
	    throw runtime_error("Trying to remove data_id, that does not exist");
	//Well, it will be unusued
	unused_data.push_back(data_id);
	//Search at SVs
	bool found=false;
	for(j=0;found==false && j<SVs.size();++j)
	{
	    if(SVs[j].Unused())
		continue;
	    if(SVs[j].data_id==data_id)
	    {
		unlearnSV(j);
		//Remove sv
		int non_index=this->MakeNonSV(j);
		this->RemoveSample(non_index);
		found=true;
	    }
	    //Search non svs
	    for(j=0;found==false && j<NVs.size();++j)
	    {
		if(NVs[j].Unused())
		    continue;
		if(NVs[j].data_id==data_id)
		{
		    this->RemoveSample(j);
		    found=true;
		}
	    }
	}
    }
    this->finishRemoval();
}

template<class NV,class SV,class Kernel>
void OnlineSVMBase<NV,SV,Kernel>::InitVarianceEstimate(int dims)
{
    mean.resize(dims,0.0);
    variance.resize(dims,1.0);
    M2.resize(dims,0.0);
}

template<class NV,class SV,class Kernel>
void OnlineSVMBase<NV,SV,Kernel>::OnlineVarianceEstimate(vector<int>& inew)
{
    vector<int>::iterator i;
    int ii;
    for(i=inew.begin();i!=inew.end();++i)
    {
	++num_samples;
	for(ii=0;ii<variance.size();++ii)
	{
	    T delta=data[NVs[*i].data_id].features[ii]-mean[ii];
	    mean[ii]+=delta/num_samples;
	    M2[ii]+=delta*(data[NVs[*i].data_id].features[ii]-mean[ii]);
	}
    }
    for(ii=0;ii<variance.size();++ii)
	variance[ii]=M2[ii]/(num_samples-1);
}

template<class NV,class SV,class Kernel>
template<class array>
int OnlineSVMBase<NV,SV,Kernel>::predictLabel(const array& sample)
{
    if(predictF(sample)>0.0)
	return 1;
    else
	return -1;
}

template<class NV,class SV,class Kernel>
template<class array>
double OnlineSVMBase<NV,SV,Kernel>::predictF(const array& sample)
{
    double f=-this->getB();
    std::list<int>::iterator i;
    for(i=this->used_svs.begin();i!=this->used_svs.end();++i)
    {
	assert(!SVs[*i].Unused());
	f+=DirectKernel(*i,sample)*SVs[*i].alpha;
    }
    return f;
}

template<class NV,class SV,class Kernel>
int OnlineSVMBase<NV,SV,Kernel>::getSVcount()
{
    return this->used_svs.size();
}

template<class NV,class SV,class Kernel>
void OnlineSVMBase<NV,SV,Kernel>::getAlphas(vector<double>& ret)
{
    ret.clear();
    std::list<int>::iterator i;
    for(i=this->used_svs.begin();i!=this->used_svs.end();++i)
    {
	ret.push_back(SVs[*i].alpha);
    }
}

template<class NV,class SV,class Kernel>
void OnlineSVMBase<NV,SV,Kernel>::getSVs(vector<vector<T> >& ret)
{
    ret.clear();
    vector<T> tmp;
    std::list<int>::iterator i;
    for(i=this->used_svs.begin();i!=this->used_svs.end();++i)
    {
	tmp.clear();
	for(int j=0;j!=this->VLength;++j)
	{
	    tmp.push_back(data[SVs[*i].data_id].features[j]);
	}
	ret.push_back(tmp);
    }
}

template<class NV,class SV,class Kernel>
double OnlineSVMBase<NV,SV,Kernel>::getW2()
{
    std::list<int>::iterator i,j;
    double result=0.0;
    for(i=this->used_svs.begin();i!=this->used_svs.end();++i)
    {
	typename Kernel::RowType& row=this->GetKernelRow(*i);
	for(j=this->used_svs.begin();j!=this->used_svs.end();++j)
	{
	    result+=row[*j]*SVs[*i].alpha*SVs[*j].alpha;
	}
	this->UnlockKernelRow(*i);
    }
    return result;
}

#endif
