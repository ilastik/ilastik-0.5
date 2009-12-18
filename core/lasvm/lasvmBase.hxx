#include "svhandler.hxx"
#include "vectors.hxx"
#include "onlineSVMBase.hxx"
#include <float.h>
#include <vector>
#include <math.h>
#include <assert.h>
#include <stdexcept>

using namespace std;


template<class T,class Kernel>
class laSvmBase : public OnlineSVMBase<laSvmNormalVector<T>,laSvmSupportVector<T>,Kernel>
{
protected:
    virtual void ComputeGradient(const vector<T>& row,const int sv_index)=0;
    virtual void UpdateGradients(const vector<T>& min_row,const vector<T>& max_row,const double step)=0;
    //Removing of support vectors
    virtual void unlearnSV(int index);
    virtual void finishRemoval();

public:
    laSvmBase(typename Kernel::par_type kernel_par,double C,double epsilon,int precache_elements,bool verbose=false);
    //Train all unlearned samples online
    void trainOnline(int epochs=2,int resample_methode=4,bool second_order=false);
    void enableResampleBorder(double start_value=0.1);
protected:
    bool first_time;
    //Parameter C
    double C;
    double epsilon;
    //Indicates, if minimax has to do something
    bool minmax_dirty;
    //Find the minimum and maximum g
    void setMinMax_g();
    double min_g, max_g;
    int  min_g_index, max_g_index;
    //Border for those vectors, we resample every time
    double resample_border;
    //A list of those
    std::list<int> always_resample;
public:
    virtual double getB();

    void getXis(vector<double>& res);
    double XiAlphaBound(double rho=1.0,bool smooth=true);
    //optimize a pair if indices,  returns which have been optimized (only change when they are -1)
    void optimize(int& imin, int &imax,bool second_order=true);
    void choose_vectors(int& imin,int& imax,bool second_order=true);
    double limitStep(const double step,const int imin,const int imax) const;
    int process(int sindex,bool second_order);
    void reprocess(bool second_order);
    //Remove unused SVs
    void cleanSVs();
    //Remove from used_svs those, which are on the border
    void ShrinkUsedSVs();
    void RestoreUsedSVs();
public:
    void finish(bool second_order);
protected:

    void checkCapacity();
    //Get the squared distance between 2 samples
    T getSquareDistance(int i,int j);

    void resample(vector<int>& inew,int num,int resample_methode,const vector<int>& new_svs);
    //Known labels
    vector<int> labels;

    //We keep track of the SV slots that are used. Carefull: this may not be the same as all unused SVs (see finish)
    //std::list<int> used_svs;

};


template<class T,class Kernel>
void laSvmBase<T,Kernel>::finishRemoval()
{
    //Recalculate gradients
    std::list<int>::iterator iter;
    for (iter=this->used_svs.begin();iter!=this->used_svs.end();++iter)
    {
        ComputeGradient(this->GetKernelRow(*iter),*iter);
        this->UnlockKernelRow(*iter);
    }
}

template<class T,class Kernel>
void laSvmBase<T,Kernel>::unlearnSV(int index)
{
    //Remove a SV ...
    vector<T> &row=this->GetKernelRow(index);
    double rest_alpha=SVs[index].alpha;
    SVs[index].alpha=0.0;
    //Put the alpha on other SVs
    while (rest_alpha>0.0)
    {
        int max_kernel=0;
        //Find the closest partner
        for (int m=0;m<SVs.size();++m)
        {
            if (SVs[m].Unused())
                continue;
            if (row[m]>row[max_kernel])
                max_kernel=m;
        }
        row[max_kernel]=0;
        //Move as much alpha as possible
        if (this->getSVLabel(max_kernel)==this->getSVLabel(index))
        {
            //add
            double transition=max(rest_alpha,SVs[max_kernel].cmax-SVs[max_kernel].alpha);
            rest_alpha-=transition;
            SVs[max_kernel].alpha+=transition;
        }
        else
        {
            //sub
            double transition=max(rest_alpha,SVs[max_kernel].alpha-SVs[max_kernel].cmin);
            rest_alpha-=transition;
            SVs[max_kernel].alpha-=transition;
        }
    }
    this->UnlockKernelRow(index);
}


template<class T,class RowType>
void laSvmBase<T,RowType>::getXis(vector<double> &res)
{
    res.clear();
    std::list<int>::iterator i;

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

template<class T,class RowType>
T laSvmBase<T,RowType>::getSquareDistance(int i,int j)
{
    T square=0.0;
    for (int dim=0;dim<this->VLength;++dim)
    {
        T tmp=this->data[i].features[dim]-this->data[j].features[dim];
        square+=tmp*tmp;
    }
    return square;
}

template<class T,class Kernel>
laSvmBase<T,Kernel>::laSvmBase(typename Kernel::par_type kernel_par,double C, double epsilon, int precache_elements,bool verbose) :OnlineSVMBase<laSvmNormalVector<T>,laSvmSupportVector<T>,Kernel>(kernel_par,precache_elements)
{
    this->VLength=-1;
    this->first_time=true;
    this->verbose=verbose;
    this->C=C;
    this->epsilon=epsilon;
    this->resample_border=0.0;
    this->num_samples=0;
    minmax_dirty=true;
}

template<class T,class RowType>
void laSvmBase<T,RowType>::enableResampleBorder(double start_value)
{
    resample_border=start_value;
}




template<class T,class RowType>
double laSvmBase<T,RowType>::XiAlphaBound(double rho,bool smooth)
{
    //Assumptions here are: K(x,x)=1
    //Everything can be misclassified for which alpha*(1-min_k)-2*alpha*min(K)+error>=1
    double result=0;
    std::list<int>::iterator i;
    for (i=this->used_svs.begin();i!=this->used_svs.end();++i)
    {
        double alpha=fabsf(SVs[*i].alpha);
        double label=this->getSVLabel(*i);
        double f=label-SVs[*i].g-this->getB();
        double error=1-label*f;
        if (error<0.0)
            error=0.0;
        double term=alpha*rho+error;
        if (smooth)
        {
            const double a=10.0;
            const double b=-0.7;
            result+=1.0/(1.0+exp(-a*(term+b)));
        }
        else
        {
            if (term>=1)
                result+=1;
        }
    }
    return result;
}

template<class T,class RowType>
double laSvmBase<T,RowType>::getB()
{
    this->setMinMax_g();
    return -(max_g+min_g)/2.0;
}

void inline remove(vector<int>& vec,int i)
{
    vec[i]=vec[vec.size()-1];
    vec.pop_back();
}

template<class T,class RowType>
void laSvmBase<T,RowType>::trainOnline(int epochs,int resample_methode,bool second_order)
{
    int i;
    int num_new_samples=this->unlearned_data.size();;
    //Estimate the variance
    if (first_time)
    {
        if (this->unlearned_data.size()==0)
        {
            cerr<<"WARNING: I can not start before I got one instance of each class first"<<endl;
            return;
        }
    }

    //Add 5 if each class to balance the initial set
    int c1=0,c2=0;
    if (first_time)
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
            cerr<<"WARNING: I can not start before I got one instance of each class first"<<endl;
            cerr<<"WARNING: I got "<<c1<<" of class1 and "<<c2<<" of class2"<<endl;
            return;
        }
    }
    first_time=false;

    vector<int> new_svs;
    //Go through epochs
    for (i=0;i<epochs;++i)
    {
        if (this->verbose)
            cerr<<"INFO: Starting epcoch "<<i<<" with "<<this->unlearned_data.size()<<" samples"<<endl;
        while (!this->unlearned_data.empty())
        {
            if (this->verbose && (this->unlearned_data.size() % 100 ==0))
                cerr<<"INFO: "<<this->unlearned_data.size()<<" samples left"<<endl;
            int index=rand() % this->unlearned_data.size(); //This one we gonna learn
            //Learn it
            int sv_index=process(this->unlearned_data[index],second_order);
            if (sv_index>=0)
            {
                new_svs.push_back(sv_index);
            }
            remove(this->unlearned_data,index);

            //Do a rprocess
            reprocess(second_order);
        }
        //Resample if nessasry
        if (i!=epochs-1)
        {
            resample(this->unlearned_data,num_new_samples,resample_methode,new_svs);
        }
    }
}

template<class T,class RowType>
void laSvmBase<T,RowType>::resample(vector<int>& inew,int num,int resample_methode,const vector<int>& new_svs)
{
    double const wanted_resample_ratio=0.1;
    //We want |always_resample|/|SVs|=0.1, adjust resample_border accordingly
    if (resample_border!=0.0)
    {
        double current_ratio=double(always_resample.size())/double(this->used_svs.size());
        double factor=0.1/current_ratio;
        factor=min(factor,2.0);
        factor=max(factor,0.5);
        resample_border*=factor;
        resample_border=min(resample_border,10.0);
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
    int i,a;
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
        //Random samples, as many as news
        for (i=0;i<num;++i)
        {
            int index=rand() % NVs.size();
            if (!NVs[index].Unused())
                inew.push_back(index);
        }
        break;
    case 2:
        //Resample the closest, to the support vectors
        for (i=0;i<new_svs.size();++i)
        {
            if (SVs[new_svs[i]].Unused())
                continue;
            T min_dist=FLT_MAX;
            int closest=rand() % NVs.size();
            T dist;
            for (a=0;a<NVs.size();++a)
            {
                if (NVs[a].Unused())
                {
                    continue;
                }
                if (this->getSVLabel(new_svs[i])==this->getNVLabel(a))
                {
                    continue;
                }
                dist=getSquareDistance(SVs[new_svs[i]].data_id,NVs[a].data_id);
                if (dist<min_dist)
                {
                    min_dist=dist;
                    closest=a;
                }
            }
            inew.push_back(closest);
        }
        break;
    }
}

template<class T,class RowType>
void laSvmBase<T,RowType>::setMinMax_g()
{
    if (minmax_dirty)
    {
        minmax_dirty=false;

        min_g=FLT_MAX;
        max_g=-FLT_MAX;
        min_g_index=-1;
        max_g_index=-1;
        std::list<int>::iterator i;
        for (i=this->used_svs.begin();i!=this->used_svs.end();++i)
        {
            if (SVs[*i].Unused())
                continue;
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

template<class T,class RowType>
void laSvmBase<T,RowType>::cleanSVs()
{
    setMinMax_g();

    std::list<int>::iterator i=this->used_svs.begin();
    while (i!=this->used_svs.end())
    {
        assert(!SVs[*i].Unused());
        if (SVs[*i].alpha==0.0) //Check if alpha==0 (otherwise no way we throw it out)
        {
            if ((SVs[*i].g>=max_g && 0>=SVs[*i].cmax) ||
                    (SVs[*i].g<=min_g && 0<=SVs[*i].cmin))
            {
                assert(*i!=min_g_index || max_g<=min_g); //This should not happen because of the min, max criteria
                assert(*i!=max_g_index || max_g<=min_g);
                //Check if it is within a certain margin
                bool resample=false;
                if ((0>=SVs[*i].cmax) && (SVs[*i].g<=max_g+resample_border) ||
                        (0<=SVs[*i].cmin) && (SVs[*i].g>=min_g-resample_border))
                    resample=true;

                int index=this->MakeNonSV(*i);
                if (resample)
                    always_resample.push_back(index);
                i=this->used_svs.erase(i);
                continue;
            }
        }
        ++i;
    }
    //Check if we threw out the min or maximum g
    if (SVs[min_g_index].Unused() || SVs[max_g_index].Unused())
        minmax_dirty=true;
}

template<class T,class RowType>
int laSvmBase<T,RowType>::process(int index,bool second_order)
{
    //Stop if non valid index
    if (NVs[index].Unused())
        return -1;
    setMinMax_g();
    int y=this->getNVLabel(index);
    //Check for correct label
    if (y*y!=1)
        throw std::runtime_error("y must be +1 or -1");
    //Make it an SV and get row
    int sv_index=this->MakeSV(index);
    vector<T>& row=this->GetKernelRow(sv_index);

    //Compute the gradient of it
    SVs[sv_index].alpha=0.0;
    ComputeGradient(row,sv_index);
    this->UnlockKernelRow(sv_index);
    //Test if this can be a violating pair with anyone
    if (min_g<max_g)
        if ((y>0 && SVs[sv_index].g<min_g) || (y<0 && SVs[sv_index].g>max_g))
        {
            int index=this->MakeNonSV(sv_index);
            //Is it within the border?
            if ((y>0 && NVs[index].g>min_g-resample_border) || (y<0 && NVs[index].g<max_g+resample_border))
                always_resample.push_back(index);
            return -1;
        }
    //Inserted!
    this->used_svs.push_back(sv_index);
    if (y<0)
    {
        SVs[sv_index].cmin=-C;
        SVs[sv_index].cmax=0;
    }
    else
    {
        SVs[sv_index].cmin=0;
        SVs[sv_index].cmax=C;
    }
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

template<class T,class RowType>
void laSvmBase<T,RowType>::reprocess(bool second_order)
{
    int dummy1=-1;
    int dummy2=-1;
    optimize(dummy1,dummy2,second_order);
    cleanSVs();
}

template<class T,class RowType>
void laSvmBase<T,RowType>::ShrinkUsedSVs()
{
    setMinMax_g();
    std::list<int>::iterator i=this->used_svs.begin();
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

template<class T,class RowType>
void laSvmBase<T,RowType>::RestoreUsedSVs()
{
    int i;
    vector<bool> already_used;
    already_used.resize(this->sv_index_to_row.size(),false);
    for (std::list<int>::iterator i=this->used_svs.begin();i!=this->used_svs.end();++i)
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

template<class T,class RowType>
void laSvmBase<T,RowType>::finish(bool second_order)
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
            next_shrink+=min(1000,(int)this->sv_index_to_row.size());
        }
        int dummy1,dummy2;
        dummy1 = -1;
        dummy2 =-1;
        optimize(dummy1,dummy2,second_order);
        error=max_g-min_g;
        if (error>epsilon && (dummy1==-1 || dummy2==-1))
        {
            throw std::runtime_error("Error selecting training samples");
        }
    }
    RestoreUsedSVs();
    cleanSVs();
}

template<class T,class RowType>
void laSvmBase<T,RowType>::choose_vectors(int& imin,int& imax,bool second_order)
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
        vector<T>& row=this->GetKernelRow(known_index);
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
        std::list<int>::iterator i;
        for (i=this->used_svs.begin();i!=this->used_svs.end();++i)
        {
            assert(!SVs[*i].Unused());
            //Wir stellen g_i-g_j/(K_ii+K_jj-2*K_ij) es als Z/N da
            double N=2.0-2.0*row[*i];
            double Z=SVs[*i].g-known_g;
            if (imin<0) //It is the other way around than
                Z=-Z;
            if (N!=0.0)
            {
                double mu=Z/N;
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

template<class T,class RowType>
double laSvmBase<T,RowType>::limitStep(const double step,const int imin,const int imax) const
{
    //Determine maximal step by applying the min criteria (make sure we do no step over cmin or cmax)
    double step_limit;
    double new_step=step;
    assert(step>=0.0);
    if (step>=0.0)
    {
        step_limit=SVs[imin].alpha-SVs[imin].cmin;
        new_step=min(new_step,step_limit);
        step_limit=SVs[imax].cmax-SVs[imax].alpha;
        new_step=min(new_step,step_limit);
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

template<class T,class RowType>
void laSvmBase<T,RowType>::optimize(int& imin,int& imax,bool second_order)
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
    vector<T>& min_row=this->GetKernelRow(imin);
    vector<T>& max_row=this->GetKernelRow(imax);
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
    else if (denom+FLT_EPSILON<=0.0)
    {
        //OK, this may not be. The non digonal are bigger than the digonal
        throw std::runtime_error("Kernel is not position (negative curvature)");
    }
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


