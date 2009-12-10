#include "lasvmBase.hxx"
#include <algorithm>

template<class T,class Kernel>
class laSvmSingleKernel : public laSvmBase<T,vector<T> >
{
public:
    laSvmSingleKernel(typename Kernel::par_type kernel_par,
                      T C,double epsilon,
                      int precache_elements,bool verbose=false) 
        : laSvmBase<T,vector<T> >(C,epsilon,precache_elements,verbose) 
          , kernel(kernel_par)
    {
        this->kernel_opt_step_size.clear();
        this->last_derivatives.resize(kernel.num_parameters,0.0);
        this->lower_bounds.resize(kernel.num_parameters,-1000000.0);
        this->upper_bounds.resize(kernel.num_parameters,10000000.0);
        this->close_mode.resize(kernel.num_parameters,false);
    }
    void RecomputeKernel();
    void XiAlphaBoundDerivative(vector<double>& res,double rho=1.0);
    enum grad_methode
    {
        GRAD_IND_STEP_SIZE_SIGN_ADAPTION=0,
        NORMALIZED_GRAD_DESCENT,
        INTERVALL_HALVING,
        MIXED
    };
    void KernelOptimizationStep(grad_methode methode=GRAD_IND_STEP_SIZE_SIGN_ADAPTION);
protected:
    virtual void ComputeGradient(const vector<T>& row,const int sv_index);
    virtual void UpdateGradients(const vector<T>& min_row,const vector<T>& max_row,const double step);
    virtual void FillRow(vector<T>& row,int sv_index); 
    virtual void UpdateRow(vector<T>& row,int sv_index);
    virtual T DirectKernel(int sv,const vector<T>& vec);
public:
    vector<double> kernel_opt_step_size;
    //The derivatives of the last optimization step
    vector<double> last_derivatives;
    //For intervall halving
    vector<double> lower_bounds;
    vector<double> upper_bounds;
    //For mixed
    vector<bool> close_mode;
    Kernel kernel;

    //Statistics
    double ShrinkFactorByPairing(double eta);
    int throwOutsByMostDistant(const vector<vector<T> >& samples);
};

template<class T,class RowType>
int laSvmSingleKernel<T,RowType>::throwOutsByMostDistant(const vector<vector<T> >& samples)
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
            double dist=sqrt(2.0-2.0*kernel.compute(samples[i].begin(),samples[j].begin(),this->VLength));
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

template<class T,class RowType>
double laSvmSingleKernel<T,RowType>::ShrinkFactorByPairing(double eta)
{
    list<int>::iterator sv_i,sv_ii;
    int pair_count=0;
    for(sv_i=this->used_svs.begin();sv_i!=this->used_svs.end();++sv_i)
    {
        vector<T> &row=this->GetKernelRow(*sv_i);
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

template<class T,class Kernel>
void laSvmSingleKernel<T,Kernel>::XiAlphaBoundDerivative(vector<double>& res,double rho)
{
    const double sig_b=-0.7;
    const double sig_a=10.0;
    this->setMinMax_g();
    double b=(this->min_g+this->max_g)/2.0;
    //Set the size of the output
    res.resize(kernel.num_parameters,0.0);
    list<int>::iterator i,j;
    vector<double> derivatives(kernel.num_parameters,0.0);
    vector<double> dKernel(kernel.num_parameters);
    for(i=this->used_svs.begin();i!=this->used_svs.end();++i)
    {
        int kp;
        double label=this->data[SVs[*i].data_id].label;
        double f=label-SVs[*i].g+b;
        double xi=1-label*f;

        for(kp=0;kp<kernel.num_parameters;++kp)
        {
            derivatives[kp]=0.0;
        }
        for(j=this->used_svs.begin();j!=this->used_svs.end();++j)
        {
            kernel.computeDerived(this->data[SVs[*i].data_id].features,this->data[SVs[*j].data_id].features,this->VLength,dKernel);

            for(kp=0;kp<kernel.num_parameters;++kp)
                derivatives[kp]-=dKernel[kp]*SVs[*j].alpha;
        }
        //Calculate the sigmoid
        double alpha=fabsf(SVs[*i].alpha);
        double term=rho*alpha+xi;
        double sig=1.0/(1.0+exp(-sig_a*(term+sig_b)));
        //Behave according to what we are ...
        if(fabs(alpha-fabs(SVs[*i].cmin-SVs[*i].cmax))<0.001)
        {
            //This affects xi! (d_alpha=0)
            for(kp=0;kp<kernel.num_parameters;++kp)
                res[kp]+=sig*(1-sig)*sig_a*derivatives[kp]*label;
        }
        else
        {
            //This effects alpha!
            //Our special handling of alpha (letting alpha<0) needs us to multiply the label to it
            for(kp=0;kp<kernel.num_parameters;++kp)
                res[kp]+=sig*(1-sig)*sig_a*rho*derivatives[kp]*label;
        }
    }
}

template<class T,class Kernel>
void laSvmSingleKernel<T,Kernel>::KernelOptimizationStep(grad_methode methode)
{
    kernel.setVariance(this->variance.begin(),this->variance.end());
    if(this->kernel_opt_step_size.empty())
        this->kernel_opt_step_size=kernel.getInitialStepSizes();
    int i;
    //Make sure solutions is correct
    this->finish(true);
     //What is our bound before
    double bound_before=this->XiAlphaBound(0.0,true);

    //Get the derivative
    vector<double> der;
    XiAlphaBoundDerivative(der);

    //The step that will be filled
    vector<double> step(der.size());

    //Do something depending on methode ...
    const double grow_factor=1.1;
    const double shrink_factor=0.9;
    double norm=0.0;
    switch(methode)
    {
    case GRAD_IND_STEP_SIZE_SIGN_ADAPTION:
        //Adapt step sizes based on signes and fill step
        for(i=0;i<kernel_opt_step_size.size();++i)
        {
            if(der[i]*last_derivatives[i]>0.0)
                kernel_opt_step_size[i]*=grow_factor;
            else
                kernel_opt_step_size[i]*=shrink_factor;
        }
        //Let kernel apply bounds
        kernel.boundStepSize(kernel_opt_step_size);
        //Fill step
        for(i=0;i<step.size();++i)
        {
            if(der[i]<0.0)
                step[i]=kernel_opt_step_size[i];
            else
                step[i]=-kernel_opt_step_size[i];
        }
        break;
    case NORMALIZED_GRAD_DESCENT:
        //normalize step size
        for(i=0;i<der.size();++i)
            norm+=der[i]*der[i];
        norm=sqrt(norm);
        if(norm<0.001)
            return;
        //normalize the step size
        for(i=0;i<der.size();++i)
            step[i]=-der[i]*kernel_opt_step_size[i]/norm;
        break;
    case INTERVALL_HALVING:
        //Adjust upper or lower bound and make the step
        for(i=0;i<der.size();++i)
        {
            if(der[i]<0.0)
                lower_bounds[i]=0.0;
            else
                upper_bounds[i]=0.0;
            //step
            step[i]=(lower_bounds[i]+upper_bounds[i])/2.0;
        }
        //Limit the steps
        kernel.boundSteps(step);
        //Shift the bounds
        for(i=0;i<der.size();++i)
        {
            lower_bounds[i]+=step[i]-0.2;
            upper_bounds[i]+=step[i]+0.2;
        }
        break;
    case MIXED:
        //Set step size according to "close_mode"
        for(i=0;i<der.size();++i)
        {
            if(close_mode[i])
            {
                //Adjust step size
                if(der[i]*last_derivatives[i]>0.0)
                    kernel_opt_step_size[i]*=grow_factor;
                else
                    kernel_opt_step_size[i]*=shrink_factor;
                step[i]=-kernel_opt_step_size[i]*der[i];
            }
            else
            {
                if(der[i]>0)
                    step[i]=-1000000.0;
                else
                    step[i]=10000000.0;
                //Go to close mode?
                if(der[i]*last_derivatives[i]<0.0)
                {
                    close_mode[i]=true;
                    //A good choice of starting stepsize ...
                    kernel_opt_step_size[i]=0.7/fabs(der[i]);
                }
            }
        }
        //Limit the step
        kernel.boundSteps(step);
        break;
    }

    //Update the kernel
    kernel.updateKernelPar(step);
    RecomputeKernel();
    //Retrain all
    this->trainOnline(2,0,true);
    this->finish(true);

    //After bound
    double bound_after=this->XiAlphaBound(0.0,true);

    switch(methode)
    {
    case NORMALIZED_GRAD_DESCENT:
        double factor;
        if(bound_after>=bound_before)
            factor=shrink_factor;
        else
            factor=grow_factor;
        for(i=0;i<der.size();++i)
        {
            kernel_opt_step_size[i]*=factor;
        }
        break;
    }

    //Remember derivatives for next step
    last_derivatives=der;
}

template<class T,class Kernel>
void laSvmSingleKernel<T,Kernel>::RecomputeKernel()
{
    //Invalidate current kernel
    this->InvalidateCache();
    //Update all gradients ... man this takes long I guess
    list<int>::iterator i;
    for(i=this->used_svs.begin();i!=this->used_svs.end();++i)
    {
        vector<T> &row=this->GetKernelRow(*i);
        ComputeGradient(row,*i);
        this->UnlockKernelRow(*i);
    }
    this->minmax_dirty=true;
}

template<class T,class Kernel>
T laSvmSingleKernel<T,Kernel>::DirectKernel(int sv,const vector<T>& vec)
{
    return kernel.compute(vec,this->getSVFeatures(sv),this->VLength);
}

template<class T,class Kernel>
void laSvmSingleKernel<T,Kernel>::UpdateRow(vector<T>& row,int sv_index)
{}

template<class T,class Kernel>
void laSvmSingleKernel<T,Kernel>::FillRow(vector<T>& row,int sv_index)
{
    list<int>::iterator i;
    assert(!SVs[sv_index].Unused());//Make sure the sv_index vector is set
    for(i=this->used_svs.begin();i!=this->used_svs.end();++i)
    {
        row[*i]=kernel.compute(this->getSVFeatures(*i),
                               this->getSVFeatures(sv_index),this->VLength);
    }
    row[sv_index]=kernel.compute(this->getSVFeatures(sv_index),
                           this->getSVFeatures(sv_index),this->VLength);
}

template<class T,class Kernel>
void laSvmSingleKernel<T,Kernel>::ComputeGradient(const vector<T>& row,const int sv_index)
{
    SVs[sv_index].g=this->getSVLabel(sv_index);
    list<int>::iterator i;
    for(i=this->used_svs.begin();i!=this->used_svs.end();++i)
    { 
        SVs[sv_index].g-=SVs[*i].alpha * row[*i];
    }
}

template<class T,class Kernel>
void laSvmSingleKernel<T,Kernel>::UpdateGradients(const vector<T>& min_row,const vector<T>& max_row,const double step)
{
    list<int>::iterator i;
    for(i=this->used_svs.begin();i!=this->used_svs.end();++i)
    {
        assert(!SVs[*i].Unused());
        SVs[*i].g -= step * (max_row[*i]-min_row[*i]);
    }
}

