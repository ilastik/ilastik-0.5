#include "lasvmSingleKernel.hxx"


template<class T,class Kernel>
class testSvm : public laSvmSingleKernel<T,Kernel>
{
public:
    testSvm(typename Kernel::par_type kernel_par,
                      T C,double epsilon,
                      int precache_elements,bool verbose=false) : laSvmSingleKernel<T,Kernel>(kernel_par,C,epsilon,precache_elements,verbose){}

    //Active Learning releavance
    template<class array>
    double BorderSoftnessAL(const array& sample);
    template<class array>
    double W2_AL(const array& sample);
    template<class array>
    double testALCrit(const array& sample,int ID);
    //Speed find out which can be "fast-predicted" by which
    template<class array1,class array2>
    bool predictionSpeedUpTest(const array1& test_sample,const array2& known_sample,T known_f,double f_cutoff);
    template<class array1,class array2,class array3>
    bool predictionSpeedUpTest2(const array1& test_sample,const array2& known_sample1,const array3& known_sample2,T known_f1,T known_f2,double f_cutoff);
    //Statistics
    double ShrinkFactorByPairing(double eta);
    int throwOutsByMostDistant(const std::vector<std::vector<T> >& samples);
    void reset();
};

template<class T,class Kernel>
void testSvm<T,Kernel>::reset()
{
    while(!this->used_svs.empty())
    {
        int index=this->MakeNonSV(this->used_svs[0]);
        this->unlearned_data.push_back(index);
    }
}

template<class T,class Kernel>
template<class array1,class array2>
bool testSvm<T,Kernel>::predictionSpeedUpTest(const array1& test_sample,const array2& known_sample,T known_f,double f_cutoff)
{
    double dist=sqrt(2.0-2.0*this->kernel.compute(test_sample,known_sample,this->VLength));
    double w=sqrt(this->getW2());
    double max_dist=(fabs(known_f)-f_cutoff)/w;
    return dist<=max_dist;
}

template<class T,class Kernel>
template<class array1,class array2,class array3>
bool testSvm<T,Kernel>::predictionSpeedUpTest2(const array1& test_sample,const array2& known_sample1,const array3& known_sample2,T known_f1,T known_f2,double f_cutoff)
{
    if(known_f1*known_f2<0.0)
        return false;
    double w=sqrt(this->getW2());
    double L=sqrt(2.0-2.0*this->kernel.compute(known_sample1,known_sample2,this->VLength));
    double a=sqrt(2.0-2.0*this->kernel.compute(known_sample1,test_sample,this->VLength));
    double b=sqrt(2.0-2.0*this->kernel.compute(known_sample2,test_sample,this->VLength));
    double f_offset=0.5/L*sqrt(2*b*b*L*L-a*a*a*a+2*a*a*L*L+2*a*a*b*b-L*L*L*L-b*b*b*b);
    if(f_offset+0.0<(std::min(fabsf(known_f1),fabsf(known_f2))-f_cutoff)/w)
        return true;
    return false;
}


template<class T,class Kernel>
template<class array>
double testSvm<T,Kernel>::testALCrit(const array& sample,int id)
{
    if(id==0)
    {
        //smallest kernel sum
        double pos_sum=0.0;
        double neg_sum=0.0;
        double f=this->predictF(sample);

        std::vector<int>::iterator i;
        for(i=this->used_svs.begin();i!=this->used_svs.end();++i)
        {
            T k=DirectKernel(*i,sample);
            if(this->getSVLabel(*i)==1)
                pos_sum+=k;
            else
                neg_sum+=k;
        }
        //Probortion
        f=std::max(-1.0,std::min(1.0,f));
        f=(f+1.0)/2.0;
        return -pos_sum*f-neg_sum*(1.0-f);
        //return -std::max(pos_sum,neg_sum);
    }
    if(id==1)
    {
        //Biggest margin movement
        double f=this->predictF(sample);
        double w=sqrt(this->getW2());
        double closest_pos=0.0;
        double closest_neg=0.0;
        std::vector<int>::iterator i;
        for(i=this->used_svs.begin();i!=this->used_svs.end();++i)
        {
            if(SVs[*i].alpha==SVs[*i].cmin || SVs[*i].alpha==SVs[*i].cmax)
                continue;
            T k=DirectKernel(*i,sample);
            if(this->getSVLabel(*i)==1)
            {
                if(k>closest_pos)
                    closest_pos=k;
            }
            else
            {
                if(k>closest_neg)
                    closest_neg=k;
            }
        }
        double pos_dist=sqrt(1.0-closest_neg*closest_neg);
        double neg_dist=sqrt(1.0-closest_pos*closest_pos);
        pos_dist=pos_dist/2.0-f/w;
        neg_dist=neg_dist/2.0+f/w;
        return std::min(pos_dist,neg_dist);
    }
}

template<class T,class Kernel>
template<class array>
double testSvm<T,Kernel>::W2_AL(const array& sample)
{
    double f=this->predictF(sample);
    double b=-this->getB();
    double g_pos=1.0-f+b;
    double g_neg=-1.0-f+b;
    double alpha_t_pos=1.0-f;
    if(alpha_t_pos<0.0)
        alpha_t_pos=0.0;
    double alpha_t_neg=-1.0-f;
    if(alpha_t_neg>0.0)
        alpha_t_neg=0.0;
    double g=f+this->getB();
    std::vector<int>::iterator i;
    double delta_w_pos=alpha_t_pos*(1.0-b);
    double delta_w_neg=alpha_t_neg*(-1.0-b);
    for(i=this->used_svs.begin();i!=this->used_svs.end();++i)
    {
	assert(!SVs[*i].Unused());
        T k=DirectKernel(*i,sample);
        double delta_alpha_pos=-alpha_t_pos*k;
        double delta_alpha_neg=-alpha_t_neg*k;
        delta_w_pos+=delta_alpha_pos*(this->getSVLabel(*i)-SVs[*i].g);
        delta_w_neg+=delta_alpha_neg*(this->getSVLabel(*i)-SVs[*i].g);
    }
    //We do not believe in negative progress
    delta_w_pos=std::max(0.0,delta_w_pos);
    delta_w_neg=std::max(0.0,delta_w_neg);
    //Probortion
    f=std::max(-1.0,std::min(1.0,f));
    f=(f+1.0)/2.0;
    return delta_w_pos*f+delta_w_neg*(1.0-f);
    //best worse case?
    return std::min(delta_w_pos,delta_w_neg);
}

template<class T,class Kernel>
template<class array>
double testSvm<T,Kernel>::BorderSoftnessAL(const array& sample)
{
    //We start by prediction of f
    double f=this->predictF(sample);
    //Alphas we would (about) gain
    double alpha_pos=0.0;
    double alpha_neg=0.0;

    std::vector<int>::iterator i;
    for(i=this->used_svs.begin();i!=this->used_svs.end();++i)
    {
        double denom=2.0-2.0*DirectKernel(*i,sample);
        double gmin=0;
        double gmax_pos=1.0-f;
        double gmax_neg=-1.0-f;
        alpha_pos+=(gmax_pos-gmin)/denom;
        alpha_neg-=(gmax_neg-gmin)/denom;
    }
    return -std::max(alpha_pos,alpha_neg);
}

template<class T,class Kernel>
int testSvm<T,Kernel>::throwOutsByMostDistant(const std::vector<std::vector<T> >& samples)
{
    int best_pos_count=0;
    int best_neg_count=0;

    int i;
    double w=sqrt(this->getW2());
    for(i=0;i<samples.size();++i)
    {
        int count=0;
        double pred=predictF(samples[i]);
        double b_dist;
        if(fabs(pred)<1.0)
            continue;
        if(pred>0.0)
            b_dist=(pred-1.0)/w;
        else
            b_dist=(-pred-1.0)/w;
        //Check against all others
        int j;
        std::cerr<<"b_dist="<<b_dist<<std::endl;
        for(j=0;j<samples.size();++j)
        {
            double dist=sqrt(2.0-2.0*this->kernel.compute(samples[i].begin(),samples[j].begin(),this->VLength));
            if(dist<b_dist)
                count++;
        }
        if(pred>1.0)
        {
            if(count>best_pos_count)
                best_pos_count=count;
        }
        else
        {
            if(count>best_neg_count)
                best_neg_count=count;
        }

    }
    return best_pos_count+best_neg_count;
}

template<class T,class Kernel>
double testSvm<T,Kernel>::ShrinkFactorByPairing(double eta)
{
    std::vector<int>::iterator sv_i,sv_ii;
    int pair_count=0;
    for(sv_i=this->used_svs.begin();sv_i!=this->used_svs.end();++sv_i)
    {
        std::vector<T> &row=this->GetKernelRow(*sv_i);
        for(sv_ii=this->used_svs.begin();sv_ii!=this->used_svs.end();++sv_ii)
        {
            if(*sv_ii==*sv_i)
                continue;
            if((1-row[*sv_ii]*row[*sv_ii])<eta)
                pair_count++;
        }
        this->UnlockKernelRow(*sv_i);
    }
    return pair_count/(2.0*this->used_svs.size());
}
