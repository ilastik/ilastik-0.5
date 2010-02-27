#include "svhandler.hxx"
#include "vectors.hxx"
#include "onlineSVMBase.hxx"
#include <float.h>
#include <vector>
#include <math.h>
#include <assert.h>
#include <stdexcept>
#include <vector>
#include <limits.h>


/**Implements the basic functionality of laSvm.
 * The interface requirements for the SV/NV additionally to those of OnlineSVMBase are:
 *   - cmin/cmax: properties for limiting the range of alpha.
 *   - g: g as described in the laSvm algorithm.
 */

template<class NV,class SV,class Kernel>
class laSvmBase : public OnlineSVMBase<NV,SV,Kernel>
{
public:
    typedef typename Kernel::float_type T;
    /** Construct the laSvm.
     * @param kernel_par Parameters to initialize the kenrel.
     * @param C penalty for the slack variables.
     * @param precached_elements Number of elements before kernel cache overruns.
     * @param verbose If set to true, verbose message will be printed to std::cerr.
     */
    laSvmBase(typename Kernel::par_type kernel_par,double C,double epsilon,int precache_elements,bool verbose=false);
    //laSvm Parameters
    /**C parameter, penalizing the slack variables.*/
    double C;
    /** epsilon, determine the maximum accuracy.*/
    double epsilon;

    /** Optimize two SVs.
     * @param imin The SV with the smaller g. Can be -1 for automatic selection.
     * @param imax The SV with the bigger g. Can be -1 for automatic selection.
     * @param second_order If set to true, uses second order information for candidate selection.
     */
    void optimize(int& imin, int &imax,bool second_order=true);

    /** Select vectors for optimization.
     * @param imin SV with the smaller g. Will only be overwritten if it is =-1
     * @param imax SV with the bigger g. Will only be overwritten if its is =-1
     * @param second_order If set to true, uses second order information for selection.
     */
    void choose_vectors(int& imin,int& imax,bool second_order=true);

    /** The process procedure as desribed in the laSvm algorithm.
     * @param sindex Index of the new SV candidate.
     * @param second_order If set to true, uses second order information for candidate selection.
     */
    int process(int sindex,bool second_order,double *old_g=0);

    /** The reprocess procedure as described in the laSvm algorithm.
     * @param second_order If set to true, uses second order information for candidate selection.
     */
    void reprocess(bool second_order);

    void setLinDepThreshold(double threshold)
    {
        this->linindep_threshold=threshold;
    }

    /** Do online epochs over unlearned training data.
     * Does online epochs as described in the laSvm algorithm.
     * The first epochs learns with the current unlearned data. Before any
     * following epoch, resample is called for collecting samples to train
     * with.
     * @param epochs The number of epochs to learn.
     * @param resample_methode The resample methode to use.
     * @param second_order If set to true, uses second order information for candidate selection.
     */
    void trainOnline(int epochs=2,int resample_methode=4,int resample_factor=1,bool second_order=false);

    /** Limits the update step for SVs imin and imax, such that cmin<=alpha<=cmax.
     */
    double limitStep(const double step,const int imin,const int imax) const;
    /** Finish step as described in the laSvm algorithm.
     * @param second_order If set to true, uses second order information for candidate selection.
     */
    void finish(bool second_order);

    /** Remove SVs from SV set, that are no support vectors anymore.*/
    void cleanSVs(bool radical=false);
    /** Shrinkage heuristic during finish. Remove all SVs from used_svs that are unlikely to violate KKT in the future.
     * RestoreUsedSVs has to be called to reclaim normal state of the SVM.*/
    void ShrinkUsedSVs();
    /** Restore the list of used svs after ShrinkUsedSVs has been called.*/
    void RestoreUsedSVs();

    /** Sets the SV with maximal and the SV with minimal g for the KKT conditions.*/
    void setMinMax_g();
    double min_g, max_g;
    int  min_g_index, max_g_index;
    bool minmax_dirty;

    /** Resample from NVs candidates for usage as SVs.
     * The resample strategie is selected by resample methode.
     * Everything found in the "always resample" border is used anyway.
     * @param inew The list into which new candidates are filled.
     * @param resample_methode The methode for how to resample.
     * @param new_svs For some methodes, the set of new SVs is needed and should be given by this parameter.
     */
    void resample(std::vector<int>& inew,int num,int resample_methode,const std::vector<int>& new_svs,const std::vector<double>& old_gs,int resample_factor);

    /** NVs close to the margin are likely to become SVs soon.
     * Because of this, there is a resample heuristic, which always resamples
     * those NVs which have been closest to the decision border when they have
     * been removed (or not inserted by process). We call the set of NVs which
     * are always resampled the resample border. The algorithm tries to always
     * keep 0.1 as many NVs as there are SVs in the resample border. The
     * heuristic for doing this adjust the distance to the margin, for which
     * NVs get into the set of always resampled NVs everytime NVs are
     * resampled. If this functions is not called, the resample border will not be used.
     * @param start_value The starting value for the distance to the margin.
     */
    void enableResampleBorder(double start_value=0.1);
    /** The distance to the margin for which NVs are always resampled.*/
    double resample_border;
    std::list<int> always_resample;


    virtual void ComputeGradient(const std::vector<T>& row,const int sv_index)=0;
    virtual void UpdateGradients(const std::vector<T>& min_row,const std::vector<T>& max_row,const double step)=0;
    //Removing of support vectors
    /** Unlearns a SV by moving all of its "alpha" to closes other SVs.
     * @param index The index of the SV to unlearn.
     */
    virtual void unlearnSV(int index)
    {unlearnSV(index,0.0);}
    /** Unlearns a SV, but only unitls its alpha is <=max_alpha.
     * @param index The index of the SV to unlearn.
     * @param max_alpha The maximal alpha, the SV may have aftwerwards.
     */
    virtual void unlearnSV(int index,double max_alpha);
    /** Gets called when a data id is removed from a SV. Makes sure that
     * cmin<=alpha<=cmax is kept.
     * @param sv_index The index of the combined SV.
     */
    virtual void OnDataIDRemovedFromSV(int sv_index);
    /** Gets called when a data id is removed from a NV. Makes sure that
     * cmin<=alpha<=cmax is kept.
     * @param nv_index The index of the combined NV.
     */
    virtual void OnDataIDRemovedFromNV(int nv_index){}
    /** Recalculates all g.
     */
    virtual void finishRemoval();


    /**Combine 2 SVs to get a combined SV.
     * @param i index of the first SV.
     * @param j index of the second SV.
     * @param update_gradients Indicates if the gradients of all SVs should be updated.
     * @return index of the combined SV. If this is set to false, no gradients are guaranteed to be valid afterwards.
     */
    int CombineSVs(int i,int j,bool update_gradients=true);
    /**Split SVs out of combined SV.
     * @param comb_id index of the combined SV.
     * @param rem_ids vector of ids to remove from the combined SV.
     */
    void SplitSVs(int comb_id,std::vector<int>& rem_ids,bool update_gradients=true);
    /**Remove the gradient of an SV from all other SVs.
     * @param sv_id The index of the sv whos effect should be removed.
     */
    void RemoveGradient(int sv_id);
    /**Insert the gradient of an SV into all other SVs.
     * @param sv_id The index of the sv whos effect should be inserted.
     */
    void InsertGradient(int sv_id);
public:
    /** The threshold for combining linear independent SVs.*/
    double linindep_threshold;
    
public:
    /** Returns the B, needed for prediction in OnlineSVMBase.*/
    virtual double getB();

    /** Returns the Xis of the SVs.*/
    void getXis(std::vector<double>& res);
    /** Calculates and returns the XiAlphaBound.
     * @param rho The rho parameter.
     * @param smooth Indicates of the bound should be smoothed.
     */
    double XiAlphaBound(double rho=1.0,bool smooth=true);
    /**Get the squared distance between 2 samples.*/
    T getSquareDistance(int i,int j);
    double sig_b;
    double sig_a;


    int closestNV(int sv_index);
};

template<class NV,class SV,class Kernel>
laSvmBase<NV,SV,Kernel>::laSvmBase(typename Kernel::par_type kernel_par,double C, double epsilon, int precache_elements,bool verbose) :OnlineSVMBase<laSvmNormalVector<T>,laSvmSupportVector<T>,Kernel>(kernel_par,precache_elements)
{
    sig_b=-0.75;
    sig_a=10.0;
    this->VLength=-1;
    this->verbose=verbose;
    this->C=C;
    this->epsilon=epsilon;
    this->resample_border=0.0;
    this->num_samples=0;
    minmax_dirty=true;
    this->linindep_threshold=0.0;
    this->min_g_index=0;
    this->max_g_index=0;
}

template<class NV,class SV,class Kernel>
void laSvmBase<NV,SV,Kernel>::RemoveGradient(int sv_id)
{
    if(SVs[sv_id].alpha!=0.0)
    {
        std::vector<int>::iterator i;
        std::vector<T> &row=this->GetKernelRow(sv_id);
        for(i=this->used_svs.begin();i!=this->used_svs.end();++i)
        {
            SVs[*i].g+=SVs[sv_id].alpha*row[*i];
        }
        this->UnlockKernelRow(sv_id);
    }
}

template<class NV,class SV,class Kernel>
void laSvmBase<NV,SV,Kernel>::InsertGradient(int sv_id)
{
    std::vector<T> &row=this->GetKernelRow(sv_id);

    SVs[sv_id].g=this->getSVLabel(sv_id);
    std::vector<int>::iterator i;
    for(i=this->used_svs.begin();i!=this->used_svs.end();++i)
    {
        SVs[sv_id].g-=SVs[*i].alpha * row[*i];
        if(*i!=sv_id)
            SVs[*i].g-=SVs[sv_id].alpha * row[*i];
    }
    this->UnlockKernelRow(sv_id);
}

template<class NV,class SV,class Kernel>
void laSvmBase<NV,SV,Kernel>::SplitSVs(int comb_sv,std::vector<int>& rem_ids,bool update_gradients)
{
    //Remove the gradient of this one
    if(update_gradients)
        RemoveGradient(comb_sv);
    //Store the alpha for every one of them and cmax
    T single_alpha=SVs[comb_sv].alpha/this->NumSamplesInSV(comb_sv);
    T single_cmax=SVs[comb_sv].cmax/this->NumSamplesInSV(comb_sv);
    T single_cmin=SVs[comb_sv].cmin/this->NumSamplesInSV(comb_sv);
    SVs[comb_sv].alpha=0.0;

    //Remove all the data ids ..
    for(int i=0;i<rem_ids.size();++i)
    {
        //Still a combined one?
        if(SVs[comb_sv].data_id<0)
        {
            //Remove it ..
            bool removed=RemoveDataIDfromCombinedSample(SVs[comb_sv],rem_ids[i]);
            assert(removed);
        }
        else
        {
            assert(i==rem_ids.size()-1); //We should only end here with the last item
            assert(rem_ids.back()==SVs[comb_sv].data_id);
            rem_ids.pop_back();          //When we are here, the last element of rem_ids will be reinserted in a "special" way
        }
    }
    //Add all the svs ..
    for(int i=0;i<rem_ids.size();++i)
    {
        //Make the new an sv-vector
        int new_sv_index=this->AddSample(rem_ids[i]);
        new_sv_index=this->MakeSV(new_sv_index);
        //Set its properties
        SVs[new_sv_index].alpha=single_alpha;
        SVs[new_sv_index].cmax=single_cmax;
        SVs[new_sv_index].cmin=single_cmin;
        //Reincorporate its gradient
        if(update_gradients)
            InsertGradient(new_sv_index);
    }
    //Reinsert the combined vector
    SVs[comb_sv].alpha=single_alpha*this->NumSamplesInSV(comb_sv);
    SVs[comb_sv].cmin=single_cmin*this->NumSamplesInSV(comb_sv);
    SVs[comb_sv].cmax=single_cmax*this->NumSamplesInSV(comb_sv);
    if(update_gradients)
    {
        this->RecalculateKernelRow(comb_sv);
        InsertGradient(comb_sv);
    }
}

template<class NV,class SV,class Kernel>
int laSvmBase<NV,SV,Kernel>::CombineSVs(int i,int j,bool update_gradients)
{

    std::vector<int>::iterator list_i;

#ifndef NDEBUG
    if(this->getSVLabel(i)!=this->getSVLabel(j))
    {
        throw std::runtime_error("I can not combine samples of different labels");
    }
#endif
    //At this point, we know we have to combine
    //Make the old disappear in all the g's
    if(update_gradients)
        for(int remove_index=i;remove_index!=2*j-i;remove_index+=(j-i))
        {
            RemoveGradient(remove_index);
        }
    //Create the new Vector
    int new_data_id=this->combined_samples.getFreeIndex();
    this->combined_samples[new_data_id].clear();
    this->combined_samples[new_data_id].label=this->getSVLabel(i);
    double new_cmin=SVs[i].cmin+SVs[j].cmin;
    double new_cmax=SVs[i].cmax+SVs[j].cmax;
    double new_alpha=SVs[i].alpha+SVs[j].alpha;

    //Push the old data ids into this sample
    if(SVs[i].data_id>=0)
    {
        this->combined_samples[new_data_id].data_ids.push_back(SVs[i].data_id);
    }
    else
    {
        this->combined_samples[new_data_id].data_ids.insert(this->combined_samples[new_data_id].data_ids.end(),
                                                            this->combined_samples[-(SVs[i].data_id+1)].data_ids.begin(),
                                                            this->combined_samples[-(SVs[i].data_id+1)].data_ids.end());
        this->combined_samples[-(SVs[i].data_id+1)].clear();
    }
    if(SVs[j].data_id>=0)
    {
        this->combined_samples[new_data_id].data_ids.push_back(SVs[j].data_id);
    }
    else
    {
        this->combined_samples[new_data_id].data_ids.insert(this->combined_samples[new_data_id].data_ids.end(),
                                                            this->combined_samples[-(SVs[j].data_id+1)].data_ids.begin(),
                                                            this->combined_samples[-(SVs[j].data_id+1)].data_ids.end());
        this->combined_samples[-(SVs[j].data_id+1)].clear();
    }
    this->combined_samples[new_data_id].rebuild(this->data,this->VLength);
    //Completely remove the olds
    int tmp=this->MakeNonSV(i);
    this->RemoveSample(tmp);
    tmp=this->MakeNonSV(j);
    this->RemoveSample(tmp);
    //Make the new an sv-vector
    int new_sv_index=this->AddSample(-new_data_id-1);
    new_sv_index=this->MakeSV(new_sv_index);
    //Set its cmax, cmin,alpha
    SVs[new_sv_index].cmin=new_cmin;
    SVs[new_sv_index].cmax=new_cmax;
    SVs[new_sv_index].alpha=new_alpha;
    //Update gs with the new sv
    SVs[new_sv_index].g=0;
    if(update_gradients)
    {
        InsertGradient(new_sv_index);
    }

    return new_sv_index;
}
template<class NV,class SV,class Kernel>
void laSvmBase<NV,SV,Kernel>::finishRemoval()
{
    //Recalculate gradients
    std::vector<int>::iterator iter;
    for (iter=this->used_svs.begin();iter!=this->used_svs.end();++iter)
    {
        ComputeGradient(this->GetKernelRow(*iter),*iter);
        this->UnlockKernelRow(*iter);
    }
}

template<class NV,class SV,class Kernel>
void laSvmBase<NV,SV,Kernel>::OnDataIDRemovedFromSV(int sv_index)
{
    if(SVs[sv_index].cmin==0.0)
        SVs[sv_index].cmax-=this->C;
    else
        SVs[sv_index].cmin+=this->C;
    unlearnSV(sv_index,SVs[sv_index].cmax-SVs[sv_index].cmin);
}

template<class NV,class SV,class Kernel>
void laSvmBase<NV,SV,Kernel>::unlearnSV(int index,double max_alpha)
{
    if(fabs(SVs[index].alpha)<max_alpha)
        return;
    minmax_dirty=true;
    //Remove a SV ...
    std::vector<T> &row=this->GetKernelRow(index);
    double rest_alpha=SVs[index].alpha;
    if(rest_alpha>0.0)
        rest_alpha-=max_alpha;
    else
        rest_alpha+=max_alpha;
    SVs[index].alpha-=rest_alpha;

    double this_label=this->getSVLabel(index);
    //Put the alpha on other SVs
    while(rest_alpha*this_label>0.0)
    {
        int max_kernel=-1;
        //Find the closest partner
        for (int m=0;m<SVs.size();++m)
        {
            if (SVs[m].Unused())
                continue;
            if(m==index)
                continue;
            if(this->getSVLabel(index)==1 && SVs[m].alpha==SVs[m].cmax)
                continue;
            if(this->getSVLabel(index)==-1 && SVs[m].alpha==SVs[m].cmin)
                continue;
            if (max_kernel==-1 || row[m]>row[max_kernel])
                max_kernel=m;
        }
        //Move as much alpha as possible
        double transition;
        if(this->getSVLabel(index)==1)
            transition=std::min(rest_alpha,SVs[max_kernel].cmax-SVs[max_kernel].alpha);
        else
            transition=std::max(rest_alpha,SVs[max_kernel].cmin-SVs[max_kernel].alpha);
        rest_alpha-=transition;
        SVs[max_kernel].alpha+=transition;
    }
    this->UnlockKernelRow(index);
}


template<class NV,class SV,class Kernel>
void laSvmBase<NV,SV,Kernel>::getXis(std::vector<double> &res)
{
    res.clear();
    std::vector<int>::iterator i;

    this->setMinMax_g();
    double b=(min_g+max_g)/2.0;
    for (i=this->used_svs.begin();i!=this->used_svs.end();++i)
    {
        double label=this->getSVLabel(*i);
        double f=label-SVs[*i].g+b;
        double error=1-label*f;
        res.push_back(error);
    }
}

template<class NV,class SV,class Kernel>
typename Kernel::float_type laSvmBase<NV,SV,Kernel>::getSquareDistance(int i,int j)
{
    T square=0.0;
    for (int dim=0;dim<this->VLength;++dim)
    {
        T tmp=this->data[i].features[dim]-this->data[j].features[dim];
        square+=tmp*tmp;
    }
    return square;
}


template<class NV,class SV,class Kernel>
void laSvmBase<NV,SV,Kernel>::enableResampleBorder(double start_value)
{
    resample_border=start_value;
}



template<class NV,class SV,class Kernel>
double laSvmBase<NV,SV,Kernel>::XiAlphaBound(double rho,bool smooth)
{
    //Assumptions here are: K(x,x)=1
    //Everything can be misclassified for which alpha*(1-min_k)-2*alpha*min(K)+error>=1
    double result=0;
    std::vector<int>::iterator i;
    for (i=this->used_svs.begin();i!=this->used_svs.end();++i)
    {
        double alpha=fabsf(SVs[*i].alpha);
        double label=this->getSVLabel(*i);
        double f=label-SVs[*i].g-this->getB();
        double error=1-label*f;
        double num_samples=this->NumSamplesInSV(*i);
        if(SVs[*i].data_id<0)
        if (error<0.0)
            error=0.0;
        double term=alpha*rho+error;
        if (smooth)
        {
            result+=1.0/(1.0+exp(-sig_a*(term+sig_b)))*num_samples;
        }
        else
        {
            if (term>=1)
                result+=num_samples;
        }
    }
    return result;
}

template<class NV,class SV,class Kernel>
double laSvmBase<NV,SV,Kernel>::getB()
{
    this->setMinMax_g();
    return -(max_g+min_g)/2.0;
}

void inline remove(std::vector<int>& vec,int i)
{
    vec[i]=vec[vec.size()-1];
    vec.pop_back();
}

template<class NV,class SV,class Kernel>
void laSvmBase<NV,SV,Kernel>::trainOnline(int epochs,int resample_methode,int resample_factor,bool second_order)
{
    int i;
    int num_new_samples=this->unlearned_data.size();;
    //Estimate the variance
    if (this->used_svs.size()==0)
    {
        if (this->unlearned_data.size()==0)
        {
            std::cerr<<"WARNING: I can not start before I got one instance of each class first"<<std::endl;
            return;
        }
    }

    //Add 5 if each class to balance the initial set
    int c1=0,c2=0;
    if (this->used_svs.size()<2)
    {
        for (i=0;i<this->unlearned_data.size();++i)
        {
            int label=this->getNVLabel(this->unlearned_data[i]);
            if (label==-1 && c1<5) {
                c1++;
                process(this->unlearned_data[i],second_order);
                remove(this->unlearned_data,i--);
                continue;
            }
            if (label==+1 && c2<5) {
                c2++;
                process(this->unlearned_data[i],second_order);
                remove(this->unlearned_data,i--);
                continue;
            }
            if (c1>=5 && c2>=5) break;
        }

        //Check if it worked
        if (c1==0 || c2==0)
        {
            std::cerr<<"WARNING: I can not start before I got one instance of each class first"<<std::endl;
            std::cerr<<"WARNING: I got "<<c1<<" of class1 and "<<c2<<" of class2"<<std::endl;
            return;
        }
    }

    std::vector<int> new_svs;
    std::vector<double> new_svs_original_g;
    //Go through epochs
    for (i=0;i<epochs;++i)
    {
        if (this->verbose)
            std::cerr<<"INFO: Starting epcoch "<<i<<" with "<<this->unlearned_data.size()<<" samples"<<std::endl;
        while (!this->unlearned_data.empty())
        {
            if (this->verbose && (this->unlearned_data.size() % 100 ==0))
                std::cerr<<"INFO: "<<this->unlearned_data.size()<<" samples left"<<std::endl;
            int index=rand() % this->unlearned_data.size(); //This one we gonna learn
            //Learn it
            double old_g;
            int sv_index=process(this->unlearned_data[index],second_order,&old_g);
            if (sv_index>=0)
            {
                new_svs.push_back(sv_index);
                new_svs_original_g.push_back(old_g);
            }
            remove(this->unlearned_data,index);

            //Do a rprocess
            reprocess(second_order);
        }
        //Resample if nessasry
        if (i!=epochs-1)
        {
            resample(this->unlearned_data,num_new_samples,resample_methode,new_svs,new_svs_original_g,resample_factor);
        }
    }
}

template<class NV,class SV, class Kernel>
int laSvmBase<NV,SV,Kernel>::closestNV(int sv_index)
{
    T min_dist=FLT_MAX;
    int closest=rand() % NVs.size();
    T dist;
    for (int a=0;a<NVs.size();++a)
    {
        if (NVs[a].Unused())
        {
            continue;
        }
        if (this->getSVLabel(sv_index)==this->getNVLabel(a))
        {
            continue;
        }
        dist=getSquareDistance(SVs[sv_index].data_id,NVs[a].data_id);
        if (dist<min_dist)
        {
            min_dist=dist;
            closest=a;
        }
    }
    return closest;
}

template<class NV,class SV,class Kernel>
void laSvmBase<NV,SV,Kernel>::resample(std::vector<int>& inew,int num,int resample_methode,const std::vector<int>& used_svs,const std::vector<double>& old_gs,int resample_factor)
{
    double const wanted_resample_ratio=0.1;
    //We want |always_resample|/|SVs|=0.1, adjust resample_border accordingly
    if (resample_border!=0.0)
    {
        double current_ratio=double(always_resample.size())/double(this->used_svs.size());
        double factor=0.1/current_ratio;
        factor=std::min(factor,2.0);
        factor=std::max(factor,0.5);
        resample_border*=factor;
        resample_border=std::min(resample_border,10.0);
    }
    //Move the "always resample" thing into inew
    if (resample_methode!=0)
    {
        while (!always_resample.empty())
        {
            inew.push_back(always_resample.front());
            always_resample.pop_front();
        }
    }
    else
    {
        //Everything is resampled, so do not worry ...
        always_resample.clear();
    }
    //Does resampling make sense?
    if (NVs.size()-inew.size()<num)
        resample_methode=0;
    int i;
    switch (resample_methode)
    {
    case 0:
        //Everything
        for (i=0;i<NVs.size();++i)
        {
            if (!NVs[i].Unused())
                inew.push_back(i);
        }
        break;
    case 1:
        //Random samples, as many as news times resample factor
        for (i=0;i<num*resample_factor;++i)
        {
            int index=rand() % NVs.size();
            if (!NVs[index].Unused())
                inew.push_back(index);
        }
        break;
    case 2:
        //Resample the closest, to the support vectors
        for (i=0;i<used_svs.size();++i)
        {
            if (SVs[used_svs[i]].Unused())
                continue;
            inew.push_back(closestNV(used_svs[i]));
        }
        //And resample as many as random as have not been support vectors
        for (i=0;i<(num-used_svs.size())*resample_factor;++i)
        {
            int index=rand() % NVs.size();
            if (!NVs[index].Unused())
                inew.push_back(index);
        }
        break;
    case 3:
        //Resample close to those, that have been wrongly classified
        int num_random=num-used_svs.size();
        double b=-this->getB();
        for(i=0;i<used_svs.size();++i)
        {
            if(SVs[used_svs[i]].Unused())
            {
                num_random++;
                continue;
            }
            double f=this->getSVLabel(used_svs[i])-old_gs[i]+b;
            if(this->getSVLabel(used_svs[i])*f<0.0)
            {
                //Find closest
                inew.push_back(closestNV(used_svs[i]));
            }
            else
                num_random++;
        }
        //And resample as many as random as have not included above
        for (i=0;i<(num-used_svs.size())*resample_factor;++i)
        {
            int index=rand() % NVs.size();
            if (!NVs[index].Unused())
                inew.push_back(index);
        }
        break;

    }
}

template<class NV,class SV,class Kernel>
void laSvmBase<NV,SV,Kernel>::setMinMax_g()
{
    if (minmax_dirty || SVs[min_g_index].Unused() || SVs[max_g_index].Unused())
    {
        minmax_dirty=false;

        min_g=FLT_MAX;
        max_g=-FLT_MAX;
        min_g_index=-1;
        max_g_index=-1;
        std::vector<int>::iterator i;
        for (i=this->used_svs.begin();i!=this->used_svs.end();++i)
        {
            assert(!SVs[*i].Unused());
            if (SVs[*i].g<min_g && SVs[*i].alpha>SVs[*i].cmin)
            {
                min_g=SVs[*i].g;
                min_g_index=*i;
            }
            if (SVs[*i].g>max_g && SVs[*i].alpha<SVs[*i].cmax)
            {
                max_g=SVs[*i].g;
                max_g_index=*i;
            }
        }
    }
    //Assert if they are unused
    assert(min_g_index==-1 || !SVs[min_g_index].Unused());
    assert(max_g_index==-1 || !SVs[max_g_index].Unused());
    //This sometimes happens when there are only error vectors ...
    /*if(max_g<min_g)
    {
    	//Search for a SV, it should prevent this ...
    	std::list<int>::iterator i;
    	cout<<"OK, this means we search for the reason of this ..."<<endl;
    	cout<<"min_g="<<min_g<<endl;
    	cout<<"max_g="<<max_g<<endl;
    	int support_vectors=0;
    	int error_vectors=0;
    	int normal_vectors=0;
    	for(i=used_svs.begin();i!=used_svs.end();++i)
    	{
    		if(SVs[*i].alpha==0)
    			normal_vectors++;
    		else
    			if(SVs[*i].alpha==SVs[*i].cmin || SVs[*i].alpha==SVs[*i].cmax)
    				error_vectors++;
    			else
    				normal_vectors++;
    		bool found=false;
    		if(SVs[*i].alpha>SVs[*i].cmin && SVs[*i].alpha<SVs[*i].cmax)
    		{
    			found=true;
    			cout<<"Found one:"<<endl;
    			cout<<SVs[*i].g<<endl;
    		}
    	}
    	cout<<"normal_vectors:"<<normal_vectors<<endl;
    	cout<<"error vectors:"<<error_vectors<<endl;
    	cout<<"svs:"<<support_vectors<<endl;

    }*/
}

template<class NV,class SV,class Kernel>
void laSvmBase<NV,SV,Kernel>::cleanSVs(bool radical)
{
    setMinMax_g();

    int i=0;
    while (i!=this->used_svs.size())
    {
        int sv_index=this->used_svs[i];
        assert(!SVs[sv_index].Unused());
        if (SVs[sv_index].alpha==0.0) //Check if alpha==0 (otherwise no way we throw it out)
        {
            if ((radical || SVs[sv_index].g>=max_g && 0>=SVs[sv_index].cmax) ||
                    (SVs[sv_index].g<=min_g && 0<=SVs[sv_index].cmin))
            {
                //std::cerr<<"REMOVING "<<*i<<std::endl;
                assert(radical || sv_index!=min_g_index || max_g<=min_g); //This should not happen because of the min, max criteria
                assert(radical || sv_index!=max_g_index || max_g<=min_g);
                //Check if it is within a certain margin
                bool resample=false;
                if ((0>=SVs[sv_index].cmax) && (SVs[sv_index].g<=max_g+resample_border) ||
                    (0<=SVs[sv_index].cmin) && (SVs[sv_index].g>=min_g-resample_border))
                    resample=true;

                int index=this->MakeNonSV(sv_index,i);
                if (resample)
                    always_resample.push_back(index);
                continue;
            }
        }
        ++i;
   }
    //Check if we threw out the min or maximum g
    if (SVs[min_g_index].Unused() || SVs[max_g_index].Unused())
        minmax_dirty=true;
}

template<class NV,class SV,class Kernel>
int laSvmBase<NV,SV,Kernel>::process(int index,bool second_order,double* old_g)
{
    //Stop if non valid index
    if (NVs[index].Unused())
        return -1;
    setMinMax_g();
    int y=this->getNVLabel(index);
    //Check for correct label
#ifdef DEBUG
    if (y*y!=1)
        throw std::runtime_error("y must be +1 or -1");
#endif
    //Make it an SV and get row (with the SVHandler function because we do not yet want to add it to used svs)
    int sv_index=SVHandler<laSvmNormalVector<T>,laSvmSupportVector<T>,typename Kernel::RowType>::MakeSV(index);
    std::vector<T>& row=this->GetKernelRow(sv_index);
    double set_C=C;
    if(SVs[sv_index].data_id<0)
        set_C*=this->combined_samples[-(SVs[sv_index].data_id+1)].data_ids.size();
    //Set its data
    if (y<0)
    {
        SVs[sv_index].cmin=-set_C;
        SVs[sv_index].cmax=0;
    }
    else
    {
        SVs[sv_index].cmin=0;
        SVs[sv_index].cmax=set_C;
    }
    SVs[sv_index].alpha=0.0;
    //Check for linear independence
    //WARNING: this works only with RBF
    std::vector<int>::iterator i;
    bool combined=false;
    for(i=this->used_svs.begin();i!=this->used_svs.end();++i)
    {
        if(y==this->getSVLabel(*i))
        {
            if(1.0-row[*i]*row[*i]<linindep_threshold)
            {
                this->UnlockKernelRow(sv_index);
                int saved_i=*i; //Because it gets corrupted by the next line
                this->used_svs.push_back(sv_index);
                sv_index=CombineSVs(saved_i,sv_index);
                minmax_dirty=true;
                if(old_g)
                    *old_g=SVs[sv_index].g;
                return sv_index;
            } 
        }
    }
    //Compute the gradient of it
    ComputeGradient(row,sv_index);
    if(old_g)
        *old_g=SVs[sv_index].g;
    this->UnlockKernelRow(sv_index);
    //Test if this can be a violating pair with anyone
    if (min_g<max_g)
        if ((y>0 && SVs[sv_index].g<min_g) || (y<0 && SVs[sv_index].g>max_g))
        {
            int index=SVHandler<laSvmNormalVector<T>,laSvmSupportVector<T>,typename Kernel::RowType>::MakeNonSV(sv_index);
            //Is it within the border?
            if ((y>0 && NVs[index].g>min_g-resample_border) || (y<0 && NVs[index].g<max_g+resample_border))
                always_resample.push_back(index);
            return -1;
        }
    //Inserted!
    this->used_svs.push_back(sv_index);
    //Update minMaxG with it, so that we do not have to make it dirty
    if (SVs[sv_index].g<min_g && SVs[sv_index].alpha>SVs[sv_index].cmin)
    {
        min_g=SVs[sv_index].g;
        min_g_index=sv_index;
    }
    if (SVs[sv_index].g>max_g && SVs[sv_index].alpha<SVs[sv_index].cmax)
    {
        max_g=SVs[sv_index].g;
        max_g_index=sv_index;
    }
    
    //Optimize it
    int dummy=-1;
    if (y>0)
        optimize(dummy,sv_index,second_order);
    else
        optimize(sv_index,dummy,second_order);
    return sv_index;
}

template<class NV,class SV,class Kernel>
void laSvmBase<NV,SV,Kernel>::reprocess(bool second_order)
{
    int dummy1=-1;
    int dummy2=-1;
    optimize(dummy1,dummy2,second_order);
    cleanSVs();
}

template<class NV,class SV,class Kernel>
void laSvmBase<NV,SV,Kernel>::ShrinkUsedSVs()
{
    setMinMax_g();
    std::vector<int>::iterator i=this->used_svs.begin();
    while (i!=this->used_svs.end())
    {
        assert(!SVs[*i].Unused());
        if (SVs[*i].g>=max_g && SVs[*i].alpha>=SVs[*i].cmax)
        {
            i=this->used_svs.erase(i);
            continue;
        }
        if (SVs[*i].g<=min_g && SVs[*i].alpha<=SVs[*i].cmin)
        {
            i=this->used_svs.erase(i);
            continue;
        }
        ++i;
    }
}

template<class NV,class SV,class Kernel>
void laSvmBase<NV,SV,Kernel>::RestoreUsedSVs()
{
    int i;
    std::vector<bool> already_used;
    already_used.resize(this->sv_index_to_row.size(),false);
    for (std::vector<int>::iterator i=this->used_svs.begin();i!=this->used_svs.end();++i)
    {
        assert(!already_used[*i]);
        already_used[*i]=true;
    }
    //Restore list
    std::list<int> new_used;
    for (i=0;i<this->sv_index_to_row.size();++i)
    {
        if (!SVs[i].Unused() && already_used[i]==false)
        {
            this->used_svs.push_back(i);
            new_used.push_back(i);
        }
    }
    //Recalculate gradients
    std::list<int>::iterator iter;
    for (iter=new_used.begin();iter!=new_used.end();++iter)
    {
        ComputeGradient(this->GetKernelRow(*iter),*iter);
        this->UnlockKernelRow(*iter);
    }
}

template<class NV,class SV,class Kernel>
void laSvmBase<NV,SV,Kernel>::finish(bool second_order)
{
    int iter=0;
    int next_shrink=0;

    double error=max_g-min_g;
    int dummy1=-1;
    int dummy2=-1;
    while (error>epsilon)
    {
        if (iter>=next_shrink)
        {
            ShrinkUsedSVs();
            next_shrink+=std::min(1000,(int)this->sv_index_to_row.size());
        }
        int dummy1,dummy2;
        dummy1 = -1;
        dummy2 =-1;
        optimize(dummy1,dummy2,second_order);
        error=max_g-min_g;
#ifdef DEBUG
        if (error>epsilon && (dummy1==-1 || dummy2==-1))
        {
            throw std::runtime_error("Error selecting training samples");
        }
#endif
    }
    RestoreUsedSVs();
    cleanSVs(true);
    if(this->verbose)
        std::cerr<<"INFO: #svs="<<this->used_svs.size()<<", cacheSize="<<this->cacheSize<<std::endl;
}

template<class NV,class SV,class Kernel>
void laSvmBase<NV,SV,Kernel>::choose_vectors(int& imin,int& imax,bool second_order)
{
    if (second_order)
    {
        //Select working set by second order selection
        if (imin < 0 && imax < 0)
        {
            //Determine maximum and minimum g
            setMinMax_g();
            //Test which has more effect
            if (max_g > -min_g)
                imax=max_g_index;
            else
                imin=min_g_index;
        }
        //The following asserts make sure, that the step can only be positive!
        if (imax<0)
            assert(imin==min_g_index || SVs[imin].alpha==0.0);
        if (imin<0)
            assert(imax==max_g_index || SVs[imax].alpha==0.0);
        //OK, now we know that one of imin, imax is not -1
        int known_index;//The index we already set
        if (imax<0)
            known_index=imin;
        else
            known_index=imax;
        assert(!SVs[known_index].Unused()); //Assert if this just can not be
        /*if(verbose)
        {
        	cerr<<"INFO:";
        	if(imax<0)
        		cerr<<" imin="<<imin<<endl;
        	else
        		cerr<<" imax="<<imax<<endl;
        }*/
        double known_g=SVs[known_index].g;
        assert(known_g==SVs[known_index].g);
        std::vector<T>& row=this->GetKernelRow(known_index);
        //The optimum is at mu=(g_i-g_j)/(K_ii-2*K_ij-K_jj)
        //The Progress is supposed to be: (g_i-g_j)^2/(2*(K_ii-2*K_ij+K_jj))
        //That is P=1/2*(K_ii-2*K_ij+K_jj)*mu*mu
        //We try to maximise this one. Since we use gaussion kernel!!! We know, that K_ii=K_jj=1
        double best_gain=0.0;
        int best_index=-1;

        assert(fabs(known_g-SVs[known_index].g)<0.001);
        if (imin<0)
        {
            assert(SVs[known_index].alpha!=SVs[known_index].cmax);
        }
        else
        {
            assert(SVs[known_index].alpha!=SVs[known_index].cmin);
        }
        std::vector<int>::iterator i;
        for (i=this->used_svs.begin();i!=this->used_svs.end();++i)
        {
            assert(!SVs[*i].Unused());
            //Wir stellen g_i-g_j/(K_ii+K_jj-2*K_ij) es als Z/N da
            double N=2.0-2.0*row[*i];
            double Z=SVs[*i].g-known_g;
            if(fabs(Z)<=epsilon) //Does not make sense to optimize svs that are already very close together
                continue;
            if (imin<0) //It is the other way around than
                Z=-Z;
            double mu;
            if (N!=0.0)
            {
                mu=Z/N;
            }
            else
            {
                mu=(Z<0.0?-std::numeric_limits<float>::max():std::numeric_limits<float>::max());
            }
            //The choice of our first vector dictates, that mu must nu>=0 and mu=0 means, no gain
            if (mu<=0)
                continue;
            assert(Z>=0);
            //In which direction would we be moving, and can it?
#if 1
            if (imin<0)
            {
                if (SVs[*i].alpha==SVs[*i].cmin)
                    continue;
            }
            else
            {
                if (SVs[*i].alpha==SVs[*i].cmax)
                    continue;
            }
#else //Turn out that this is slower ...
            if (imin<0)
                mu=limitStep(mu,*i,known_index);
            else
                mu=limitStep(mu,known_index,*i);
#endif
            double gain= Z * mu;
            if (gain>best_gain)
            {
                best_gain=gain;
                best_index=*i;
            }
        }
        this->UnlockKernelRow(known_index);
        /*cout<<"Expected gain: "<<best_gain<<" (best_gain==0.0)="<<(best_gain==0.0)<<endl;
        cout<<"min_g_index="<<min_g_index<<", max_g_index="<<max_g_index<<endl;
        cout<<"min_g="<<min_g<<", max_g="<<max_g<<endl;*/
        //assert(best_gain!=0.0 || min_g>=max_g);
        //Fill the unkown
        if (imax<0)
        {
            imax=best_index;
        }
        else
        {
            assert(imin<0);
            imin=best_index;
        }
    }
    else
    {
        //Normal way of testing it, max violating pair
        setMinMax_g();
        if (imin<0)
            imin=min_g_index;
        if (imax<0)
            imax=max_g_index;
    }
}

template<class NV,class SV,class Kernel>
double laSvmBase<NV,SV,Kernel>::limitStep(const double step,const int imin,const int imax) const
{
    //Determine maximal step by applying the min criteria (make sure we do no step over cmin or cmax)
    double step_limit;
    double new_step=step;
    assert(step>=0.0);
    if (step>=0.0)
    {
        step_limit=SVs[imin].alpha-SVs[imin].cmin;
        new_step=std::min(new_step,step_limit);
        step_limit=SVs[imax].cmax-SVs[imax].alpha;
        new_step=std::min(new_step,step_limit);
    }
    /*else
    {
    	step_limit=SVs[imax].cmin-SVs[imax].alpha;
    	new_step=max(new_step,step_limit);
    	step_limit=SVs[imin].alpha-SVs[imin].cmax;
    	new_step=max(new_step,step_limit);
    }*/
    return new_step;
}

template<class NV,class SV,class Kernel>
void laSvmBase<NV,SV,Kernel>::optimize(int& imin,int& imax,bool second_order)
{
    //Choose the vectors to optimize
    setMinMax_g();
    double error=max_g-min_g;
    if (error<=epsilon)
    {
        return;
    }

    choose_vectors(imin,imax,second_order);

    if (imin<0 || imax<0)
    {
        return;
    }
    minmax_dirty=true;
    //OK, now the optimization is:
    //lambda=min(g_i-g_j/(K_ii+K_jj-2*K_ij),B_i-alpha_i,alpha_i-A_j)
    //TODO: respect order of getting indexes
    //denominator
    std::vector<T>& min_row=this->GetKernelRow(imin);
    std::vector<T>& max_row=this->GetKernelRow(imax);
    //T denom=2.0-2.0*min_row[imax];
    double denom=min_row[imin]+max_row[imax]-min_row[imax]-max_row[imin];
    double step=FLT_MAX;
    double gmin=SVs[imin].g;
    double gmax=SVs[imax].g;
    assert(denom>=0);
    if (denom>=FLT_EPSILON)
    {
        step=(gmax-gmin)/denom;
    }
#ifdef DEBUG
    else if (denom+FLT_EPSILON<=0.0)
    {
        //OK, this may not be. The non digonal are bigger than the digonal
        throw std::runtime_error("Kernel is not position (negative curvature)");
    }
#endif
    //Determin maximal step by applying the min criteria (make sure we do no step over cmin or cmax)
    assert(step>0.0);
    step=limitStep(step,imin,imax);
    assert(step!=0.0);
    //Perform updates
    SVs[imax].alpha += step;
    SVs[imin].alpha -= step;
    std::list<int>::iterator i;

    UpdateGradients(min_row,max_row,step);
    minmax_dirty=true;

    this->UnlockKernelRow(imin);
    this->UnlockKernelRow(imax);
}


