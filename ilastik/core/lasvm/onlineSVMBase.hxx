#include "labeldSample.hxx"
#include "svhandler.hxx"
#include <vector>
#include <stdexcept>
#include <algorithm>
#include "garbage_vector.hxx"
#include "predictCoverTree.hxx"
#include "predictionSet.hxx"

#ifndef ONLINE_SVM_BASE_INCLUDED
#define ONLINE_SVM_BASE_INCLUDED


/** Base class for online SVMs. 
 * In addition to the SVHandler class, this class knows about a kernel, support
 * vector weights and feature data. It also introduces ways to combine (i.E. linear dependent) SVs.
 * the template parameters NV and SV are passed to the base class SVHandler.
 * In addition to the required interface in SVHandler, NV and SV require also the following properties.
 *   - alpha: The weight of the SV. Together with the kernel value, a prediction can be calculated.
 *   - data_id: Connects the NV/SV to data entry, in which the feature data, the label and the unique id (used for deleting data) is stored.
 *
 * The Kernel template parameter requires the following interface:
 *   - Kernel::RowType: The row type for the SVHandler to be used with the kernel.
 *   - Kernel::float_type: The precision type the kernel calculates with.
 *   - Kernel::par_type: The type of the (adjustable) kernel parameters.
 *   - setVariance(begin,end): The kernel might want to know about the variances of the data. It is informed about it with this function getting a range over the feature dimensions.
 *   - initParameters: After the variance has been set, the kernel is requested to make an initial guess for the kernel parameters.
 *   - compute: Getting to random access iterators to features and the number of features, the common kernel for 2 samples is computes.
 *
 *
 * \note
 * Only RBF kernels have really been tested. There are some features which require the kernel to be RBF.
 */
template<class NV,class SV,class Kernel>
class OnlineSVMBase : public SVHandler<NV,SV,typename Kernel::RowType>
{
public:
    typedef typename Kernel::float_type T;
    /** Instance of the kernel we are working with.*/
    Kernel kernel;
    /** Constructor.
     * @param kernel_par The kernel parameters to initialize the kernel with.
     * @param precache_elements Passed to SVHandler as overflowsize.
     * @param verbose If set to true, some verbose information is printed to std::cerr from time to time.
     */
    OnlineSVMBase(typename Kernel::par_type kernel_par,int precache_elements,bool verbose=false);
    virtual ~OnlineSVMBase()
    {
	for(int i=0;i<data.size();++i)
	    data[i].clear();
    }

    /** Add training data.
     * Add training data, which gets inserted in the list of unlearned NVs. If
     * the possible of removing single instances of the training data later
     * should exist, unique_ids must have an unique entry for every sample. If
     * removing is not needed, unique_ids is irrelevant.
     * @param sample An array of samples. It will be double indexed, meaning the i'th feature of the j'th sample should be returned by sample[j][i].
     * @param label_array An array of labels, which can be accessed with [] and has a size member function. All labels must be +1 or -1.
     * @param unique_ids Array of the same size as labels with a unique integer id for every sample. If removing of samples is not needed, the ids may not be unique.
     */
    template<class feature_array,class label_array,class id_array>
    void addData(const feature_array& sample,const label_array& l,const id_array& unique_ids);

    /** Remove training data.
     * Remove training data, inserted by addData identified by their unique ids.
     * @param unique_ids The unique ids (given when addData was called) of the instances to be removed.
     */
    template<class array>
    void removeData(const array& unique_ids);
    /** Derived from SVHanlder.
     * Fills the kernel row using Kernel::compute.
     */

    /** Initialize kernel parameters with a guess.
     * Calls the initParameters function of the kernel to set a initial of the parameters.
     */
    void startGuessKernelParameters();

    /** Predict decision function for a single sample.
     * Calculates the decision function for a given sample.
     * @param sample features of the sample, indexable with the [] operator.
     */
  template<class ResultArray>
  void predictF(SvmPredictionSet<T>& set,ResultArray& out);
    template<class array>
    double predictF(const array& sample);

    /** Predicts the label of single sample.
     * Calculates the predicted label for a given sample.
     * @param sample features of the sample, indexable with the [] operator.
     */
    template<class array>
    int predictLabel(const array& sample);

    /** Predicts decision function for an array of samples using a CoverTree for the SVs.
     * Puts the SVs into a CoverTree and approximates F for all samples using the CoverTree.
     * @param samples array of samples, which can be double indexed doing samples[a][b] to get the feature b of sample a.
     * @param num_samples The number of samples in the samples array.
     * @param result Array of results, which will be filled using the [] operator.
     * @param epsilon Parameter controlling the precision of the approximation.
     * \note
     * The assumption for doing this is, that the kernel is a RBF kernel.
     */
  template<class ResultArray>
  void singleCoverTreePredictF(SvmPredictionSet<T>& samples,ResultArray& out,double epsilon);
  template<class ResultArray>
  void singleCoverTreeRangedPredictF(SvmPredictionSet<T>& samples,ResultArray& out,double epsilon,double delta,bool use_avg);

    /** Predicts decision function for an array of samples using a CoverTree for the SVs and a CoverTree for the samples.
     * Puts the SVs into a CoverTree and and samples in another CoverTree to
     * approximates F for all samples using the dual CoverTree Kernel
     * approximation algorithm.
     * @param samples array of samples, which can be double indexed doing samples[a][b] to get the feature b of sample a.
     * @param num_samples The number of samples in the samples array.
     * @param result Array of results, which will be filled using the [] operator.
     * @param epsilon Parameter controlling the precision of the approximation.
     * \note
     * The assumption for doing this is, that the kernel is a RBF kernel.
     *
     * \note
     * This function might be slow due to the building of the CoverTree of the
     * samples. In such a case singleCoverTreePredictF might be better suited.
     */
  template<class ResultArray>
  void dualCoverTreePredictF(SvmPredictionSet<T>& samples,ResultArray& out,double epsilon);

    /** Abstract function return the SVM bias.
     * The calculation of this bias depends the SVM implementation.
     * @return The SVM bias, added to the prediction function.
     */
    virtual double getB()=0;

    virtual void FillRow(std::vector<T>& row,int sv_index); 
    /** Derived form SVHandler.
     * Empty in this implementation. Derived classes might want to specify it.
     */
    virtual void UpdateRow(std::vector<T>& row,int sv_index);

    /**Searches and removes a data id from a combined sample.
     * @param vec The SV or NV from which it should be removed.
     * @param data_id The data id to remove.
     * @return true if the data_id has been found in a combined sample.
     */
    template<class vector>
    bool RemoveDataIDfromCombinedSample(vector& vec,int data_id);

    /** Abstract function for unlearning a support vector.
     * Before a SV is removed completely form the dataset (in removeData), this
     * function is called to unlearn the SV. How exactly a support vector is
     * unlearned depends on the SVM implementation. After removeData has
     * unlearnd all SVs to be removed, finishRemoval is also called.
     * @param index The index of the SV to unlearn.
     */
    virtual void unlearnSV(int index)=0;
   
    /** Abstract function for dealing with the removing of samples from combined SVs.
     * Whenever it becomes necessary to remove a sample from a combined SV
     * (in removeData), this function is called afterwards for letting the SVM
     * implementation repair the damage.
     * @param sv_index The index of combined SV.
     */
    virtual void OnDataIDRemovedFromSV(int sv_index)=0;

    /** Abstract function for dealing with the removing of samples from combined NVs.
     * Whenever it becomes necessary to remove a sample from a combined NV
     * (in removeData), this function is called afterwards for letting the SVM
     * implementation repair the damage.
     * @param nv_index The index of combined NV.
     */
    virtual void OnDataIDRemovedFromNV(int nv_index)=0;

    /** Abstract function called when removeData has finished removing all samples.
     */
    virtual void finishRemoval()=0;

    /** Makes a NV to a SV and adds it to the list of used_svs.
     * @param nv_index The index of the NV to make sv.
     * @return The index of the new SV.
     */
    int MakeSV(int nv_index);

    /** Makes a SV to a NV and removes it from the list of used_svs.
     * @param sv_index the index of the SV to make NV.
     * @return The index of the new NV.
     */
    int MakeNonSV(int sv_index);

    /** Makes a SV to a NV and removes it from the list of used_svs.
     * In this function, a hint where in used_svs the SV is placed speeds up
     * the procedure.
     * @param sv_index The index of the SV to make NV.
     * @param used_sv_index The index in used SV this SV occupies.
     * @return The index of the new NV.
     */
    int MakeNonSV(int sv_index,int used_svs_index);
    int MakeNonSV(int sv_index,std::vector<int>::iterator& used_svs_iterator);

    /** List of SVs currently in use.
     * Some SVM implementations might also abuse this list, but removing it SVs
     * from it for which "Unused()" does not return true.
     * In such a case they should be aware that all predict functions expect
     * used_svs to be valid.
     */
    std::vector<int> used_svs;

    /** Feature data of samples. */
    garbage_vector<labeled_sample<typename Kernel::float_type> > data;
    
    /** For Linear independent SVM, the "combined" data points.*/
    garbage_vector<combined_sample<typename Kernel::float_type> > combined_samples;

    /** List of unlearned normal vectors.*/
    std::vector<int> unlearned_data;

    /** If set to true, many functions give verbose message to stderr.*/
    bool verbose;
    //Lenth of a features vector
    int VLength;
public:
    /** Caclculates the kernel between a sample and a sv.
     * @param sv Index of the SV we are interested int.
     * @param s1 Array of the features of the sample.
     * @return The evaluated kernel.
     */
    template<class array>
    T DirectKernel(int sv, const array& s1);

    /**For the online estimate of the variance.
     * Implemented after
     * http://en.wikipedia.org/wiki/Algorithms_for_calculating_variance#On-line_algorithm
     * This initialize the variance estimation and is called the first time data is added.
     */
    void InitVarianceEstimate(int dims);
    /**Updates the online estimate of the variance.
     * Implemented after
     * http://en.wikipedia.org/wiki/Algorithms_for_calculating_variance#On-line_algorithm
     */
    void OnlineVarianceEstimate(std::vector<int>& inew);
    //Parameter for variance estimation
    int num_samples;
    std::vector<T> mean;
    std::vector<T> M2;
    std::vector<T> variance;
public:
    
    //Get data
    /** Get the label of a SV.
     * @param id The index of the SV.
     */
    inline int getSVLabel(int id)
    {
        if(SVs[id].data_id>=0)
            return data[SVs[id].data_id].label;
        else
            return combined_samples[-(SVs[id].data_id+1)].label;
    }
    /** Get the label of a NV.
     * @param id The index of the NV.
     */
    inline int getNVLabel(int id)
    {
        if(NVs[id].data_id>=0)
            return data[NVs[id].data_id].label;
        else
            return combined_samples[-(NVs[id].data_id+1)].label;
    }
    /** Get the features of a SV as C array.
     * @param id The index of the SV
     */
  inline T* getFeatures(const SV* sv)
  {
    if(sv->data_id>=0)
      return data[sv->data_id].features;
    else
      return combined_samples[-(sv->data_id+1)].features;
  }
    inline T* getSVFeatures(int id)
    {
      return getFeatures(&SVs[id]);
    }
    /** Get the features of a NV as C array.
     * @param id The index of the NV
     */
    inline T* getNVFeatures(int id)
    {
        if(NVs[id].data_id>=0)
            return data[NVs[id].data_id].features;
        else
            return combined_samples[-(NVs[id].data_id+1)].features;
    }
    /** Return the number of samples combined in a SV.
     * For a normal SV this is 1. For combined SVs this is >1.
     * @param id The id of the SV.
     * @return The desired number of samples.
     */
    int NumSamplesInSV(int id);
  
    /** Reverse search for a SV fitting to a data_id.
     * @param The data_id to search for.
     * @return -1 if data has not been found in SVs, otherwise the index of the SV.
     */
    int getSVfromDataID(int data_id);

    /**Calculates ||W||^2.
     * @return ||W||^2
     */
    double getW2();

    /** Returns the alphas of the SVs.
     * Fills the output array with the current alphas of the SVs.
     * @param ret Array in which the alphas will be stored.
     */
    void getAlphas(std::vector<double>& ret);
    /** Returns the SVs.
     * Fills the output array with the crrent SVs.
     * @param ret array to be filled.
     */
    void getSVs(std::vector<std::vector<T> >& ret);

  //Debug information for prediction
  int num_exp;
  int num_dist;
};


template<class NV,class SV,class Kernel>
void OnlineSVMBase<NV,SV,Kernel>::UpdateRow(std::vector<T>& row,int sv_index)
{}

template<class NV,class SV,class Kernel>
void OnlineSVMBase<NV,SV,Kernel>::FillRow(std::vector<T>& row,int sv_index)
{
    int i;
    assert(!SVs[sv_index].Unused());                                  //Make sure the sv_index vector is set
    for(i=0;i!=SVs.size();++i)
    {
        if(SVs[i].Unused())
            continue;
	row[i]=this->kernel.compute(this->getSVFeatures(i),
				     this->getSVFeatures(sv_index),
                                     this->VLength);
    }
    row[sv_index]=this->kernel.compute(this->getSVFeatures(sv_index),
				       this->getSVFeatures(sv_index),
                                       this->VLength);
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
: SVHandler<NV,SV,typename Kernel::RowType>(precache_elements,typename Kernel::RowType()) , kernel(kernel_par)
{
    this->verbose=verbose;
    this->VLength=-1;
}

template<class T>
int numSamples(const std::vector<std::vector<T> > & in)
{
    return in.size();
}

template<class array>
int numSamples(const array & in)
{
    return in.shape(0);
}

template<class T>
int numFeatures(const std::vector<std::vector<T> > & in)
{
    return in[0].size();
}

template<class array>
int numFeatures(const array& in)
{
    return in.shape(1);
}

template<class NV,class SV,class Kernel>
void OnlineSVMBase<NV,SV,Kernel>::startGuessKernelParameters()
{
    kernel.setVariance(this->variance.begin(),this->variance.end());
    kernel.initParameters();
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
	int data_id=data.getFreeIndex();
	data[data_id].setData(samples,i,VLength,labels[i],unique_ids[i]);
	int id=this->AddSample(data_id);
	unlearned_data.push_back(id);
	inew.push_back(id);
    }
    this->OnlineVarianceEstimate(inew);
}

template<class NV,class SV,class Kernel>
int OnlineSVMBase<NV,SV,Kernel>::getSVfromDataID(int data_id)
{
    std::vector<int>::iterator i;
    for(i=this->used_svs.begin();i!=this->used_svs.end();++i)
    {
        if(SVs[*i].data_id==data_id)
            return *i;
        if(SVs[*i].data_id<0)
        {
            int sv_data_id=-(SVs[*i].data_id+1);
            if(std::find(this->combined_samples[-(SVs[*i].data_id+1)].data_ids.begin(),
                         this->combined_samples[-(SVs[*i].data_id+1)].data_ids.end(),data_id)!=this->combined_samples[-(SVs[*i].data_id+1)].data_ids.end())
                return *i;
        }
    }
    return -1;
}


template<class NV,class SV,class Kernel>
template<class vector>
bool OnlineSVMBase<NV,SV,Kernel>::RemoveDataIDfromCombinedSample(vector& vec,int data_id)
{
    assert(vec.data_id<0);
    int comb_id=-(vec.data_id+1);
    bool found=false;
    //Search for the data id and remove
    for(int j=0;j<this->combined_samples[comb_id].data_ids.size();++j)
    {
        if(this->combined_samples[comb_id].data_ids[j]==data_id)
        {
            this->combined_samples[comb_id].data_ids[j]=this->combined_samples[comb_id].data_ids.back();
            this->combined_samples[comb_id].data_ids.pop_back();
            found=true;
            break;
        }
    }
    //Look if we make a normal vector out of this
    if(found)
    {
        if(this->combined_samples[comb_id].data_ids.size()>1)
        {
            this->combined_samples[comb_id].rebuild(this->data,this->VLength);
        }
        else
        {
            //OK, we have to make a normal vector out of it
            vec.data_id=this->combined_samples[comb_id].data_ids[0];

            this->combined_samples[comb_id].clear();
            this->combined_samples.freeIndex(comb_id);
        }
    }
    return found;
}

template<class NV,class SV,class Kernel>
template<class array>
void OnlineSVMBase<NV,SV,Kernel>::removeData(const array & unique_ids)
{
    for(int i=0;i<unique_ids.size();++i)
    {
	int data_id=0;
	bool found=false;
	int j;
	for(j=0;j<data.size();++j)
	{
	    if(data[j].unique_id==unique_ids[i] && data[j].features!=0)
	    {
                found=true;
		data_id=j;
		break;
	    }
	}
#ifdef DEBUG
        if(found!=true)
            throw std::runtime_error("Trying to remove a sample that has not been inserts (unique id not found)");
#endif
	//Well, it will be unusued
        data[data_id].clear();
        data.freeIndex(data_id);
	//Search at SVs
        found=false;
        int sv_index=this->getSVfromDataID(data_id);
        if(sv_index>=0)
        {
            if(SVs[sv_index].data_id>=0)
	    {
		unlearnSV(sv_index);
		//Remove sv
		int non_index=this->MakeNonSV(sv_index);
		this->RemoveSample(non_index);
	    }
            else
            {
                //Remove from the data ids
                RemoveDataIDfromCombinedSample(SVs[sv_index],data_id);
                this->RecalculateKernelRow(sv_index);
                OnDataIDRemovedFromSV(sv_index);
            }
            found=true;
        }
        //Search non svs
        for(j=0;found==false && j<NVs.size();++j)
        {
            if(NVs[j].Unused())
                continue;
            if(NVs[j].data_id>=0)
            {
                if(NVs[j].data_id==data_id)
                {
                    this->RemoveSample(j);
                    found=true;
                }
            }
            else
            {
                found=RemoveDataIDfromCombinedSample(NVs[j],data_id);
                if(found)
                    OnDataIDRemovedFromNV(j);
            }
        }
        assert(found);
    }
    this->finishRemoval();
}

template<class NV,class SV,class Kernel>
void OnlineSVMBase<NV,SV,Kernel>::InitVarianceEstimate(int dims)
{
    mean.resize(dims,0.0);
    variance.resize(dims,1.0);
    M2.resize(dims,0.0);
    num_samples=0;
}

template<class NV,class SV,class Kernel>
void OnlineSVMBase<NV,SV,Kernel>::OnlineVarianceEstimate(std::vector<int>& inew)
{
    std::vector<int>::iterator i;
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
    double f=-this->getB();
    std::vector<int>::iterator i;
    for(i=this->used_svs.begin();i!=this->used_svs.end();++i)
    {
        if(SVs[*i].alpha==0.0)
            continue;
        f+=DirectKernel(*i,sample)*SVs[*i].alpha;
    }
    if(f>0.0)
	return 1;
    else
	return -1;
}

template<class NV,class SV,class Kernel>
template<class array>
double OnlineSVMBase<NV,SV,Kernel>::predictF(const array& sample)
{
    double f=-this->getB();
    this->num_exp=0;
    this->num_dist=0;
    std::vector<int>::iterator i;
    for(i=this->used_svs.begin();i!=this->used_svs.end();++i)
    {
        if(SVs[*i].alpha==0.0)
            continue;
        f+=DirectKernel(*i,sample)*SVs[*i].alpha;
	++this->num_exp;
	++this->num_dist;
    }
    return f;
}


template<class NV,class SV,class Kernel>
template<class ResultArray>
void OnlineSVMBase<NV,SV,Kernel>::predictF(SvmPredictionSet<T>& set,ResultArray& out)
{
    double b=-this->getB();
    this->num_exp=0;
    this->num_dist=0;
    for(int i=0;i<out.size();++i)
    {
        out[i]=b;
    }
    std::vector<int>::iterator i;
    for(i=this->used_svs.begin();i!=this->used_svs.end();++i)
    {
	assert(!SVs[*i].Unused());
        if(SVs[*i].alpha==0.0)
            continue;
        for(int j=0;j<out.size();++j)
        {
            out[j]+=DirectKernel(*i,set.features[j])*SVs[*i].alpha;
	    ++this->num_exp;
	    ++this->num_dist;
        }
    }
}


template<class NV,class SV,class Kernel>
template<class ResultArray>
void OnlineSVMBase<NV,SV,Kernel>::singleCoverTreeRangedPredictF(SvmPredictionSet<T>& samples,
								ResultArray& out,
								double epsilon,double delta,bool use_avg)
{
    //We need out dist functor
  typedef predictFunctor<OnlineSVMBase<NV,SV,Kernel>,SV,std::vector<std::vector<T> >,ResultArray> predictFunctor_type;
    predictFunctor_type pf(this,&samples.features,&out);
    pf.use_avg_for_error=use_avg;
    //Construct the SVs cover tree
    std::vector<SV*> ct_svs;
    std::vector<int>::iterator i;
    for(i=this->used_svs.begin();i!=used_svs.end();++i)
    {
        if(SVs[*i].alpha!=0.0)
            ct_svs.push_back(&SVs[*i]);
    }
    CoverTree<SvmKernelSumNode<SV> > ct(ct_svs,pf);
    //Predict all of them
    double bias=-this->getB();
    ::num_exp=0;
    ::num_dist=0;
    for(int i=0;i<out.size();++i)
        out[i]=ct.svmMarginKernelSum(i,pf,epsilon,delta,bias);
    this->num_exp=::num_exp;
    this->num_dist=::num_dist;
}

template<class NV,class SV,class Kernel>
template<class ResultArray>
void OnlineSVMBase<NV,SV,Kernel>::singleCoverTreePredictF(SvmPredictionSet<T>& samples,
							  ResultArray& out,
							  double epsilon)
{
    //We need out dist functor
    typedef predictFunctor<OnlineSVMBase<NV,SV,Kernel>,SV,std::vector<std::vector<T> >,ResultArray> predictFunctor_type;
    predictFunctor_type pf(this,&samples.features,&out);
    //Construct the SVs cover tree
    std::vector<SV*> ct_svs;
    std::vector<int>::iterator i;
    for(i=this->used_svs.begin();i!=used_svs.end();++i)
    {
        if(SVs[*i].alpha!=0.0)
            ct_svs.push_back(&SVs[*i]);
    }
    CoverTree<SvmKernelSumNode<SV> > ct(ct_svs,pf);
    //Predict all of them
    double bias=-this->getB();
    ::num_exp=0;
    ::num_dist=0;
    for(int i=0;i<out.size();++i)
        out[i]=ct.absoluteErrorKernelSum(i,pf,epsilon,bias);
    this->num_exp=::num_exp;
    this->num_dist=::num_dist;
}

template<class NV,class SV,class Kernel>
template<class ResultArray>
void OnlineSVMBase<NV,SV,Kernel>::dualCoverTreePredictF(SvmPredictionSet<T>& samples,ResultArray& out,double epsilon)
{
    //We need out dist functor
  typedef predictFunctor<OnlineSVMBase<NV,SV,Kernel>,SV,std::vector<std::vector<T> >,ResultArray> predictFunctor_type;
    predictFunctor_type pf(this,&samples.features,&out);
    //Construct the SVs cover tree
    std::vector<SV*> ct_svs;
    std::vector<int>::iterator i;
    for(i=this->used_svs.begin();i!=used_svs.end();++i)
    {
        //if(SVs[*i].alpha!=0.0)
            ct_svs.push_back(&SVs[*i]);
    }
    CoverTree<SvmKernelSumNode<SV> > ct(ct_svs,pf);
    //Construct the predict cover tree
    clock_t start=clock();
    std::vector<int> predict_ids;
    for(int i=0;i<num_samples;++i)
        predict_ids.push_back(i);
    CoverTree<MaxDistNode<int> > ct_pred(predict_ids,pf);
    double time=double(clock()-start)/CLOCKS_PER_SEC;
    if(this->verbose)
        std::cerr<<"INFO: construction of the prediction cover tree took "<<time<<"s"<<std::endl;
    //Predict all of them
    double bias=-this->getB();
    ::num_exp=0;
    ::num_dist=0;
    ct.DualAbsoluteErrorKernelSum(ct_pred,pf,epsilon,bias);
    this->num_exp=::num_exp;
    this->num_dist=::num_dist;
}

template<class NV,class SV,class Kernel>
double OnlineSVMBase<NV,SV,Kernel>::getW2()
{
    std::vector<int>::iterator i,j;
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

template<class NV,class SV,class Kernel>
int OnlineSVMBase<NV,SV,Kernel>::MakeSV(int nv_index)
{
    int sv_index=SVHandler<NV,SV,typename Kernel::RowType>::MakeSV(nv_index);
    used_svs.push_back(sv_index);
    return sv_index;
}

template<class NV,class SV,class Kernel>
int OnlineSVMBase<NV,SV,Kernel>::MakeNonSV(int sv_index)
{
    int nv_index=SVHandler<NV,SV,typename Kernel::RowType>::MakeNonSV(sv_index);
    for(int i=0;i<used_svs.size();++i)
    {
        if(used_svs[i]==sv_index)
        {
            used_svs[i]=used_svs.back();
            used_svs.pop_back();
            return nv_index;
        }
    }
#ifdef DEBUG
    throw std::runtime_error("Trying to remove SV not in used_svs");
#endif
}

template<class NV,class SV,class Kernel>
int OnlineSVMBase<NV,SV,Kernel>::MakeNonSV(int sv_index,int used_sv_index)
{
    assert(used_svs[used_sv_index]==sv_index);
    used_svs[used_sv_index]=used_svs.back();
    used_svs.pop_back();
    return SVHandler<NV,SV,typename Kernel::RowType>::MakeNonSV(sv_index);
}

template<class NV,class SV,class Kernel>
int OnlineSVMBase<NV,SV,Kernel>::MakeNonSV(int sv_index,std::vector<int>::iterator& used_sv_iterator)
{
    assert(*used_sv_iterator==sv_index);
    *used_sv_iterator=used_svs.back();
    used_svs.pop_back();
    return SVHandler<NV,SV,typename Kernel::RowType>::MakeNonSV(sv_index);
}

template<class NV,class SV,class Kernel>
int OnlineSVMBase<NV,SV,Kernel>::NumSamplesInSV(int id)
{
    if(SVs[id].data_id>=0)
        return 1;
    else
        return this->combined_samples[-(SVs[id].data_id+1)].data_ids.size();
}

template<class NV,class SV,class Kernel>
void OnlineSVMBase<NV,SV,Kernel>::getAlphas(std::vector<double>& ret)
{
    ret.clear();
    std::vector<int>::iterator i;
    for(i=this->used_svs.begin();i!=this->used_svs.end();++i)
    {
	ret.push_back(SVs[*i].alpha);
    }
}

template<class NV,class SV,class Kernel>
void OnlineSVMBase<NV,SV,Kernel>::getSVs(std::vector<std::vector<T> >& ret)
{
    ret.clear();
    std::vector<T> tmp;
    std::vector<int>::iterator i;
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
#endif
