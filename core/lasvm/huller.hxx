#include "geometricSvm.hxx"
#include "vectors.hxx"

template<class Kernel>
class hullerSVM : public geometricSVM<hullerNormalVector<typename Kernel::float_type>,hullerSupportVector<typename Kernel::float_type>,Kernel>
{
    typedef typename Kernel::float_type T;
public:
    hullerSVM(typename Kernel::par_type param,
              int cache_size,
              bool verbose) 
              : geometricSVM<hullerNormalVector<typename Kernel::float_type>,hullerSupportVector<typename Kernel::float_type>,Kernel>(param,cache_size,verbose)
    { };
    //These are for the un-reduced problem
    double XPXP_;
    double XNXN_;
    double XNXP_;
   
    //For reducing the problem
    double XP_own_kernel_sum_;
    double XP_other_kernel_sum_;
    double XN_own_kernel_sum_;
    double XN_other_kernel_sum_;
   
    void XPxk_and_XNxk(const vector<T>& row,const int index,T& XPxk,T &XNxk) const;
    inline double shrinkedXPXP() const;
    inline double shrinkedXNXN() const;
    inline double shrinkedXNXP() const;
    
    //Recalculate all of the aboves 
    void Recalculate();
    //Take a sv into the set
    void huller_HardenSV(int index);
};

template<class Kernel>
double hullerSVM<Kernel>::shrinkedXPXP() const
{
   return this->shrink_factor_*this->shrink_factor_*XPXP_
   +(1.0-this->shrink_factor_)*(1.0-this->shrink_factor_)*1.0 //RBF assumption
   +this->shrink_factor_*(1.0-this->shrink_factor_)*(2*XP_own_kernel_sum_/this->pos_svs);
}

template<class Kernel>
double hullerSVM<Kernel>::shrinkedXNXN() const
{
   return this->shrink_factor_*this->shrink_factor_*XNXN_
   +(1.0-this->shrink_factor_)*(1.0-this->shrink_factor_)*1.0 //RBF assumption
   +this->shrink_factor_*(1.0-this->shrink_factor_)*(2*XN_own_kernel_sum_/this->neg_svs);
}

template<class Kernel>
double hullerSVM<Kernel>::shrinkedXNXP() const
{
   return this->shrink_factor_*this->shrink_factor_*XNXP_
   +(1.0-this->shrink_factor_)*(1.0-this->shrink_factor_)*this->dot_centers_
   +this->shrink_factor_*(1.0-this->shrink_factor_)*(XP_other_kernel_sum_/this->neg_svs+XN_other_kernel_sum_/this->pos_svs);
}
    

template<class Kernel>
void hullerSVM<Kernel>::XPxk_and_XNxk(const vector<T>& row,const int index,T& XPxk,T &XNxk) const
{
    XPxk=0.0;
    XNxk=0.0;
    std::list<int>::iterator list_i;
    for(list_i=this->used_svs.begin();list_i!=this->used_svs.end();++list_i)
    {
        if(this->getSVLabel(*list_i)==1)
            XPxk+=SVs[*list_i].alpha*this->shrinkedKernel(*list_i,index,row[*list_i]);
        else
            XNxk+=SVs[*list_i].alpha*this->shrinkedKernel(*list_i,index,row[*list_i]);
    }
}

template<class Kernel>
void hullerSVM<Kernel>::huller_HardenSV(int index)
{
    this->HardenSV(index);
    //Als harden the XN and XP kernel sums
    std::list<int>::iterator list_i;
    std::vector<T> &row=this->GetKernelRow(index);
    if(this->getSVLabel(index)==1)
    {
        for(list_i=this->used_svs.begin();list_i!=this->used_svs.end();++list_i)
        {
            if(this->getSVLabel(*list_i)==1)
            {
                XP_own_kernel_sum_+=SVs[*list_i].alpha*row[*list_i];
            }
            else
            {
                XN_other_kernel_sum_+=SVs[*list_i].alpha*row[*list_i];
            }
        }
    }
    else
    {
        for(list_i=this->used_svs.begin();list_i!=this->used_svs.end();++list_i)
        {
            if(this->getSVLabel(*list_i)==1)
            {
                XP_other_kernel_sum_+=SVs[*list_i].alpha*row[*list_i];
            }
            else
            {
                XN_own_kernel_sum_+=SVs[*list_i].alpha*row[*list_i];
            }
        }
    }
    this->UnlockKernelRow(index);
}

template<class Kernel>
void hullerSVM<Kernel>::Recalculate()
{
    int i;
    std::list<int>::iterator list_i,list_ii;
    XPXP_=0.0;
    XNXN_=0.0;
    XNXP_=0.0;
    for(list_i=this->used_svs.begin();list_i!=this->used_svs.end();++list_i)
    {
	std::vector<T> &row=this->GetKernelRow(*list_i);
	for(list_ii=this->used_svs.begin();list_ii!=this->used_svs.end();++list_ii)
	{
	    if(this->getSVLabel(*list_i)==1 && this->getSVLabel(*list_ii))
	    {
		XNXP_+=SVs[*list_i].alpha*SVs[*list_ii].alpha*row[*list_ii];
	    }
	    else if(this->getSVLabel(*list_i)==this->getSVLabel(*list_ii))
	    {
		double val=SVs[*list_i].alpha*SVs[*list_ii].alpha*row[*list_ii];
		if(this->getSVLabel(*list_i)==1)
		    XPXP_+=val;
		else
		    XNXN_+=val;
	    }
	}
	this->UnlockKernelRow(*list_i);
    }
    //Calculae dots with centers
    XP_own_kernel_sum_=0.0;
    XP_other_kernel_sum_=0.0;
    XN_own_kernel_sum_=0.0;
    XN_other_kernel_sum_=0.0;
    for(list_i=this->used_svs.begin();list_i!=this->used_svs.end();++list_i)
    {
        std::vector<T> &row=this->GetKernelRow(*list_i);
        for(list_ii=this->used_svs.begin();list_ii!=this->used_svs.end();++list_ii)
        {
            if(this->getSVLabel(*list_i)!=this->getSVLabel(*list_ii))
            {
                if(this->getSVLabel(*list_i)==1)
                    XP_other_kernel_sum_+=row[*list_ii]*SVs[*list_i].alpha;
                else
                    XN_other_kernel_sum_+=row[*list_ii]*SVs[*list_ii].alpha;
            }
            else
            {
               if(this->getSVLabel(*list_i)==1)
                   XP_own_kernel_sum_+=row[*list_ii]*SVs[*list_i].alpha;
               else
                   XP_own_kernel_sum_+=row[*list_ii]*SVs[*list_i].alpha;
            }
        }
        this->UnlockKernelRow(*list_i);
    }
    this->RecalculateDots();
}