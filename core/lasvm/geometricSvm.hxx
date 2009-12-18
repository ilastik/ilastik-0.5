#include "onlineSVMBase.hxx"
#include "vectors.hxx"


using namespace std;
/** General base class for geometric svms with soft margin. Makes sure everything is
 * ok.
 */
template<class NV,class SV,class Kernel>
class geometricSVM : public OnlineSVMBase<NV,SV,Kernel>
{
    typedef typename Kernel::float_type T;
public:
    //TODO: These have to be written
    void unlearnSV(int index){};
    void finishRemoval(){};
    double getB(){};
    geometricSVM(typename Kernel::par_type kernel_par,int precache_elements,bool verbose);
    //Data ...
    //Current shrink factor
    double shrink_factor_;
    
    //Scalar product between centers
    double dot_centers_;
    //Sample counts
    int pos_svs;
    int neg_svs;
  
    //Update center and similar to make a support vector really a support vector
    void HardenSV(int index);
    //The removal of a support vector also requires some updates
    void RemoveSV(int index);
    //Calculate the intial dot products
    void RecalculateDots();
    //Get the shrinked dot product (kernel)
    inline T shrinkedKernel(int i,int j,T val);
};

template<class NV,class SV,class Kernel>
typename Kernel::float_type geometricSVM<NV,SV,Kernel>::shrinkedKernel(int i,int j,T val)
{
    double i_svs=this->getSVLabel(i)==1?pos_svs:neg_svs;
    double j_svs=this->getSVLabel(j)==1?pos_svs:neg_svs;
    if(this->getSVLabel(i)==this->getSVLabel(j))
    {
        return shrink_factor_*shrink_factor_*val
        +(1.0-shrink_factor_)*(1.0-shrink_factor_)*1.0 //RBF is assumed here
        +shrink_factor_*(1.0-shrink_factor_)*(SVs[i].same_label_kernel_sum+SVs[j].same_label_kernel_sum)/i_svs;
    }
    else
    {
        return shrink_factor_*shrink_factor_*val
        +(1.0-shrink_factor_)*(1.0-shrink_factor_)*dot_centers_
        +shrink_factor_*(1.0-shrink_factor_)*(SVs[i].other_label_kernel_sum/i_svs+SVs[j].other_label_kernel_sum/j_svs);
    }
}

template<class NV,class SV,class Kernel>
geometricSVM<NV,SV,Kernel>::geometricSVM(typename Kernel::par_type kernel_par,int precache_elements,bool verbose)
:OnlineSVMBase<NV,SV,Kernel>(kernel_par,precache_elements,verbose)
{
   this->shrink_factor_=1.0; 
   this->dot_centers_=0.0;
   this->pos_svs=0;
   this->neg_svs=0;
}

template<class NV,class SV,class Kernel>
void geometricSVM<NV,SV,Kernel>::RecalculateDots()
{
    std::list<int>::iterator i;
    pos_svs=0;
    neg_svs=0;
    //Count the number of positive and negativ svs
    for(i=this->used_svs.begin();i!=this->used_svs.end();++i)
        if(this->getSVLabel(*i)==1)
            pos_svs++;
        else
            neg_svs++;
    dot_centers_=0.0;
    for(i=this->used_svs.begin();i!=this->used_svs.end();++i)
    {
	//Get the sum
	SVs[*i].same_label_kernel_sum=0.0;
	SVs[*i].other_label_kernel_sum=0.0;
	std::list<int>::iterator ii;
	for(ii=this->used_svs.begin();ii!=this->used_svs.end();++ii)
	{
	    std::vector<typename Kernel::float_type> &row=this->GetKernelRow(*i);
	    if(this->getSVLabel(*i)!=this->getSVLabel(*ii))
	    {
                SVs[*i].other_label_kernel_sum+=row[*ii];
		//Add to the centers
		if(this->getSVLabel(*i)==1 && this->getSVLabel(*ii)==-1)
		{
		    dot_centers_+=row[*ii]/pos_svs;
		}
	    }
	    else
	    {
                SVs[*i].same_label_kernel_sum+=row[*ii];
	    }
	}
    }
    dot_centers_/=(neg_svs);
}

template<class SV,class NV,class T>
void geometricSVM<SV,NV,T>::RemoveSV(int index)
{
    //We need the row
    std::vector<T> &row=this->GetKernelRow(index);
    //Compute <x,m_y> (scalar product with other side)
    std::list<int>::iterator i;
    
    //Find the futhest away variables
    double max_dist1=0.0;
    double max_dist2=0.0;
    
    //Some variable for use in the loop
    double this_label_sv_count=this->GetSVLabel(index)==1?pos_svs:neg_svs;
    double other_label_sv_count=this->getSVLabel(index)==-1?pos_svs:neg_svs;

    double dot_centers__scale=(this_label_sv_count)*(this->GetSVLabel(index)==1?neg_svs:pos_svs);
    double dist;
    for(i=this->used_svs.begin();i!=this->used_svs.end();++i)
    {
	if(this->GetSVLabel(index)!=this->GetSVLabel(*i))
	{
	    SVs[*i].other_label_kernel_sum-=row[*i];

	    dot_centers_-=row[*i]/dot_centers__scale;
	    
	    //Test max_dist1 (assumption here is RBF!)
	    dist=2.0-2.0*SVs[*i].same_label_kernel_sum/=other_label_sv_count;
	    if(dist>max_dist1)
		max_dist1=dist;
	}
	else
	{
	    SVs[*i].same_label_kernel_sum-=row[*i];
	    dist=2.0-2.0*SVs[*i].same_label_kernel_sum/=this_label_sv_count;
	    if(dist>max_dist2)
		max_dist2=dist;
	}
    }
    this->UnlockKernelRow(index);
    dot_centers_*=this_label_sv_count/(this_label_sv_count-1.0);

    if(this->GetSVLabel(index)==1)
    {
	--pos_svs;
    }
    else
    {
	--neg_svs;
    }
    //Do we have to increase the shrink factor?
    if(sqrt(dot_centers_)>shrink_factor_*(sqrt(max_dist1)+sqrt(max_dist2)))
    {
	shrink_factor_=sqrt(dot_centers_)/(sqrt(max_dist1)+sqrt(max_dist2));
    }
}

template<class SV,class NV,class Kernel>
void geometricSVM<SV,NV,Kernel>::HardenSV(int index)
{
    //We need the row
    std::vector<typename Kernel::float_type> &row=this->GetKernelRow(index);
    //Compute <x,m_y> (scalar product with other side)
    std::list<int>::iterator i;
    SVs[index].same_label_kernel_sum=0.0;
    SVs[index].other_label_kernel_sum=0.0;
    
    //Find the furthest away variables
    double max_dist1=0.0;
    double max_dist2=0.0;
    
    //Some variable for use in the loop
    double this_label_sv_count=this->getSVLabel(index)==1?pos_svs:neg_svs;
    double other_label_sv_count=this->getSVLabel(index)==-1?pos_svs:neg_svs;

    dot_centers_*=this_label_sv_count/(this_label_sv_count+1.0);
    double dot_centers__scale=(this_label_sv_count+1.0)*(this->getSVLabel(index)==1?neg_svs:pos_svs);
    double dist;
    for(i=this->used_svs.begin();i!=this->used_svs.end();++i)
    {
	if(this->getSVLabel(index)!=this->getSVLabel(*i))
	{
	    SVs[index].other_label_kernel_sum+=row[*i];
	    SVs[*i].other_label_kernel_sum+=row[*i];

	    dot_centers_+=row[*i]/dot_centers__scale;
	    
	    //Test max_dist1 (assumption here is RBF!)
	    dist=2.0-2.0*SVs[*i].same_label_kernel_sum/other_label_sv_count;

	    if(dist>max_dist1)
		max_dist1=dist;
	}
	else
	{
	    SVs[index].same_label_kernel_sum+=row[*i];
            if(index!=*i)
                SVs[*i].same_label_kernel_sum+=row[*i];
	    //Test max_dist2 (assumption here is RBF!)
	    dist=2.0-2.0*SVs[*i].same_label_kernel_sum/(this_label_sv_count+1.0);
	    if(dist>max_dist2)
		max_dist2=dist;
	}
    }
    this->UnlockKernelRow(index);
    //Check our distance ...
    dist=2.0-2.0*SVs[index].same_label_kernel_sum/(this_label_sv_count+1.0);
    if(dist>max_dist2)
	max_dist2=dist;
    if(this->getSVLabel(index)==1)
    {
	++pos_svs;
    }
    else
    {
	++neg_svs;
    }
    //Do we have to decrease the shrink factor?
    if(sqrt(dot_centers_)<shrink_factor_*(sqrt(max_dist1)+sqrt(max_dist2)))
    {
	shrink_factor_=sqrt(dot_centers_)/(sqrt(max_dist1)+sqrt(max_dist2));
    }
}
