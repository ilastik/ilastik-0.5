#include <eigen2/Eigen/Core>
#include <eigen2/Eigen/LU>
USING_PART_OF_NAMESPACE_EIGEN
#include "lasvmBase.hxx"
#include <algorithm>

/**This class builds up on laSvmBase and assumes, that a kernel row
 * (Kernel::RowType) is an array of values floats (or doubles) that can be
 * accessed using the [] operator. Also SV::g and NV::g are float types and
 * Kernel values as well as labels can be added to them.
 */ 
template<class T,class Kernel>
class laSvmSingleKernel : public laSvmBase<laSvmNormalVector<T>, laSvmSupportVector<T>, Kernel>
{
public:
    /** Construct the laSvm.
     * @param kernel_par Parameters to initialize the kenrel.
     * @param C penalty for the slack variables.
     * @param precached_elements Number of elements before kernel cache overruns.
     * @param verbose If set to true, verbose message will be printed to std::cerr.
     */
    laSvmSingleKernel(typename Kernel::par_type kernel_par,
                      T C,double epsilon,
                      int precache_elements,bool verbose=false) 
        : laSvmBase<laSvmNormalVector<T>,laSvmSupportVector<T>,Kernel>(kernel_par,C,epsilon,precache_elements,verbose) 
    {
        this->kernel_opt_step_size.clear();
        this->last_derivatives.resize(this->kernel.num_parameters,0.0);
        this->lower_bounds.resize(this->kernel.num_parameters,-1000000.0);
        this->upper_bounds.resize(this->kernel.num_parameters,10000000.0);
        this->close_mode.resize(this->kernel.num_parameters,false);
    }
    /** Recalculates all kernel values and updates the SV gradients.*/
    void RecomputeKernel();
    /** Calculate the Xi-Alpha bound derivative of the kernel parameters given
     * the current SVM solution.
     * @param res The resulting derivatives of the kernel parameters will be filled into this array.
     * @oaram rho The rho parameter for the Xi Alpha bound.
     */
    void XiAlphaBoundDerivative(std::vector<double>& res,double rho=1.0,bool include_db=true);
    void XiAlphaBoundDerivativeExact(std::vector<double>& res,double rho);
    enum grad_methode
    {
        GRAD_IND_STEP_SIZE_SIGN_ADAPTION=0,
        NORMALIZED_GRAD_DESCENT,
	GRAD_DESCENT,
        INTERVALL_HALVING,
        MIXED
    };
    void KernelOptimizationStep(grad_methode methode=GRAD_IND_STEP_SIZE_SIGN_ADAPTION,bool include_db=false);
    void RestartOptimization();
    virtual void ComputeGradient(const std::vector<T>& row,const int sv_index);
    virtual void UpdateGradients(const std::vector<T>& min_row,const std::vector<T>& max_row,const double step);
    void ReFindPairs(bool threshold_increased);
    double GetLinindepThresholdForSVNum(int sv_num);
public:
    std::vector<double> kernel_opt_step_size;
    //The derivatives of the last optimization step
    std::vector<double> last_derivatives;
    //For intervall halving
    std::vector<double> lower_bounds;
    std::vector<double> upper_bounds;
    //For mixed
    std::vector<bool> close_mode;

};


template<class T,class Kernel>
void laSvmSingleKernel<T,Kernel>::XiAlphaBoundDerivativeExact(std::vector<double>& res,double rho)
{
    this->setMinMax_g();
    double b=(this->min_g+this->max_g)/2.0;
    //Set the size of the output
    res.resize(this->kernel.num_parameters,0.0);
    std::vector<int>::iterator i,j;
    std::vector<double> derivatives(this->kernel.num_parameters,0.0);
    std::vector<double> dKernel(this->kernel.num_parameters);

    //We have to remove all vectors to close to each other, to avoid problems (invertibility of B)
    std::vector<int> original_used_svs=this->used_svs;
    for(int i=0;i<this->used_svs.size();++i)
    {
        std::vector<T>& row=this->GetKernelRow(this->used_svs[i]);
        for(int j=i+1;j<this->used_svs.size();++j)
        {
            if(1.0-row[this->used_svs[j]]*row[this->used_svs[j]]<this->linindep_threshold)
            {
                //Throw them out!
                this->used_svs[j]=this->used_svs.back();
                this->used_svs.pop_back();
                this->used_svs[i]=this->used_svs.back();
                this->used_svs.pop_back();
                --i;//Make sure we do this one again!
                break;
            }
        }
    }

    //Get B
    MatrixXd B((int)this->used_svs.size()+1,(int)this->used_svs.size()+1);
    //Fill it
    for(int i=0;i<this->used_svs.size();++i)
    {
        if(this->getSVLabel(this->used_svs[i])*SVs[this->used_svs[i]].alpha==(SVs[this->used_svs[i]].cmax-SVs[this->used_svs[i]].cmin))
        {
            //Fill the column with zeros and a one at the right place
            for(int j=0;j<this->used_svs.size()+1;++j)
            {
                B(j,i)=0.0;
            }
            B(i,i)=1.0;
        }
        else
        {
            //Copy K
            std::vector<T> &row=this->GetKernelRow(this->used_svs[i]);
            for(int j=0;j<this->used_svs.size();++j)
            {
                B(j,i)=row[this->used_svs[j]];
            }
            B(this->used_svs.size(),i)=1.0;
            this->UnlockKernelRow(this->used_svs[i]);
        }
    }
    //Fill the last column
    for(int j=0;j<this->used_svs.size();++j)
    {
        B(j,this->used_svs.size())=1.0;
    }
    B(this->used_svs.size(),this->used_svs.size())=1.0; //This only holds, if all other entries of the last row are 0 (to keep the matrix invertible)
    for(int j=0;j<this->used_svs.size();++j)
        if(B(this->used_svs.size(),j)!=0.0)
            B(this->used_svs.size(),this->used_svs.size())=0.0; //Inevitability is given without us cheating
    //Get the inverse
    MatrixXd BInv((int)this->used_svs.size()+1,(int)this->used_svs. size()+1);
    B.computeInverse(&BInv);
    //std::cerr<<"B="<<std::endl<<B<<std::endl;
    //std::cerr<<"BInv="<<std::endl<<BInv<<std::endl;
    MatrixXd Test=B*BInv;
    for(int i=0;i<this->used_svs.size();++i)
    {
        for(int j=0;j<this->used_svs.size();++j)
        {
            if(i==j)
            {
                if(fabsf(Test(i,j)-1.0)>0.001)
                {
                    std::cerr<<B<<std::endl;
                    std::cerr<<BInv<<std::endl;
                    std::cerr<<"Found none 1 diagonal entry: "<<Test(i,i)<<std::endl;
                    throw std::runtime_error("None id matrix");
                }
            }
            else
            {
                if(fabsf(Test(i,j))>0.001)
                {
                    std::cerr<<"Found none 0 entry: "<<Test(i,j)<<std::endl;
                    throw std::runtime_error("None id matrix");
                }
            }
        }
    }
    //Store all kernel derivatives in matrixes
    std::vector<MatrixXd> KDer((int)this->kernel.num_parameters,MatrixXd((int)this->used_svs.size()+1,(int)this->used_svs.size()+1));
    for(int i=0;i<this->used_svs.size();++i)
    {
        for(int j=0;j<this->used_svs.size();++j)
        {
            this->kernel.computeDerived(this->getSVFeatures(this->used_svs[i]),this->getSVFeatures(this->used_svs[j]),this->VLength,dKernel);
            for(int kp=0;kp<this->kernel.num_parameters;++kp)
            {
                KDer[kp](j,i)=dKernel[kp];
            }
        }
    }
    //Fill a alpha vector
    VectorXd alphas(this->used_svs.size()+1);
    for(int i=0;i<this->used_svs.size();++i)
    {
        alphas[i]=SVs[this->used_svs[i]].alpha;
    }
    alphas[this->used_svs.size()]=b;
    //Compute the derivative
    for(int kp=0;kp<this->kernel.num_parameters;++kp)
    {
        VectorXd beta=-BInv*(KDer[kp]*alphas);
        for(int i=0;i<this->used_svs.size();++i)
        {
            double label=this->getSVLabel(this->used_svs[i]);
            double f=label-SVs[this->used_svs[i]].g+b;
            double xi=1-label*f;
            double num_samples=this->NumSamplesInSV(this->used_svs[i]);
            //Calculate the sigmoid
            double alpha=fabsf(SVs[this->used_svs[i]].alpha);
            double term=rho*alpha+xi;
            double sig=1.0/(1.0+exp(-this->sig_a*(term+this->sig_b)));
            //Behave according to what we are
            if(this->getSVLabel(this->used_svs[i])*SVs[this->used_svs[i]].alpha==(SVs[this->used_svs[i]].cmax-SVs[this->used_svs[i]].cmin))
            {
                //This effects xi! (d_alpha=0)
                res[kp]+=sig*(1-sig)*this->sig_a*beta(i)*label*num_samples;
            }
            else
            {
                //This effects alpha!
                //Our special handling of alpha (letting alpha<0) needs us to multiply the label to it
                res[kp]+=sig*(1-sig)*this->sig_a*rho*beta(i)*label*num_samples;
            }
        }
    }
    //Restore used svs
    this->used_svs=original_used_svs;
}

template<class T,class Kernel>
void laSvmSingleKernel<T,Kernel>::XiAlphaBoundDerivative(std::vector<double>& res,double rho,bool include_db)
{
    this->setMinMax_g();
    double b=(this->min_g+this->max_g)/2.0;
    //Set the size of the output
    res.resize(this->kernel.num_parameters,0.0);
    std::vector<int>::iterator i,j;
    std::vector<double> derivatives(this->kernel.num_parameters,0.0);
    std::vector<double> dKernel(this->kernel.num_parameters);

    std::vector<double> db(this->kernel.num_parameters,0.0);
    //Calculate db
#if 0
    if(include_db)
        for(i=this->used_svs.begin();i!=this->used_svs.end();++i)
        {
            for(j=this->used_svs.begin();j!=this->used_svs.end();++j)
            {
                if(this->getSVLabel(*i)==this->getSVLabel(*j))
                {
                    this->kernel.computeDerived(this->data[SVs[*i].data_id].features,
                                          this->data[SVs[*j].data_id].features,
                                          this->VLength,
                                          dKernel);
                    for(int kp=0;kp<this->kernel.num_parameters;++kp)
                        db[kp]+=0.5*this->getSVLabel(*i)*SVs[*i].alpha*SVs[*j].alpha*dKernel[kp];
                }
            }
        }
#else
    if(include_db)
    {
        double included_gis=0.0;
        for(i=this->used_svs.begin();i!=this->used_svs.end();++i)
        {
            if(SVs[*i].alpha==SVs[*i].cmin || SVs[*i].alpha==SVs[*i].cmax)
                continue;
            included_gis+=1.0;
            //Get d g_i
            for(j=this->used_svs.begin();j!=this->used_svs.end();++j)
            {
                this->kernel.computeDerived(this->getSVFeatures(*i),
                                            this->getSVFeatures(*j),
                                            this->VLength,
                                            dKernel);
                for(int kp=0;kp<this->kernel.num_parameters;++kp)
                {
                    db[kp]+=SVs[*j].alpha*dKernel[kp];
                }
            }
        }
        if(included_gis>0.0)
            for(int kp=0;kp<this->kernel.num_parameters;++kp)
                db[kp]/=included_gis;
    }
#endif
    /*std::cerr<<"db=";
    for(int kp=0;kp<this->kernel.num_parameters;++kp)
        std::cerr<<db[kp]<<",";
    std::cerr<<std::endl;*/
    assert(db==db);

    for(i=this->used_svs.begin();i!=this->used_svs.end();++i)
    {
        int kp;
        double label=this->data[SVs[*i].data_id].label;
        double f=label-SVs[*i].g+b;
        double xi=1-label*f;
        double num_samples=this->NumSamplesInSV(*i);

        for(kp=0;kp<this->kernel.num_parameters;++kp)
        {
            derivatives[kp]=0.0-db[kp];
        }
        for(j=this->used_svs.begin();j!=this->used_svs.end();++j)
        {
            this->kernel.computeDerived(this->getSVFeatures(*i),this->getSVFeatures(*j),this->VLength,dKernel);

            for(kp=0;kp<this->kernel.num_parameters;++kp)
                derivatives[kp]-=dKernel[kp]*SVs[*j].alpha;
        }
        //Calculate the sigmoid
        double alpha=fabsf(SVs[*i].alpha);
        double term=rho*alpha+xi;
        double sig=1.0/(1.0+exp(-this->sig_a*(term+this->sig_b)));
        //Behave according to what we are ...
        if(fabs(alpha-fabs(SVs[*i].cmin-SVs[*i].cmax))<0.001)
        {
            //This affects xi! (d_alpha=0)
            for(kp=0;kp<this->kernel.num_parameters;++kp)
                res[kp]+=sig*(1-sig)*this->sig_a*derivatives[kp]*label * num_samples;
        }
        else
        {
            //This effects alpha!
            //Our special handling of alpha (letting alpha<0) needs us to multiply the label to it
            for(kp=0;kp<this->kernel.num_parameters;++kp)
                res[kp]+=sig*(1-sig)*this->sig_a*rho*derivatives[kp]*label * num_samples;
        }
    }
}

template<class T,class Kernel>
void laSvmSingleKernel<T,Kernel>::RestartOptimization()
{
  for(int i=0;i<this->kernel_opt_step_size.size();++i)
    {
      if(this->kernel_opt_step_size[i]<0.5)
	this->kernel_opt_step_size[i]=0.5;
    }
}

template<class T,class Kernel>
void laSvmSingleKernel<T,Kernel>::KernelOptimizationStep(grad_methode methode,bool include_db)
{
    int i;
    //Make sure online prediction set do not screw up ...
    for(i=0;i<this->used_svs.size();++i)
        ++SVs[this->used_svs[i]].change_id;
    
    this->kernel.setVariance(this->variance.begin(),this->variance.end());
    if(this->kernel_opt_step_size.empty())
    {
        this->kernel_opt_step_size=this->kernel.getInitialStepSizes();
        std::cerr<<"Setting intial step sizes: "<<std::endl;
        for(int i=0;i<this->kernel_opt_step_size.size();++i)
            std::cerr<<this->kernel_opt_step_size[i]<<"\t";
        std::cerr<<std::endl;
    }
    //Make sure solutions is correct
    this->finish(true);
     //What is our bound before
    double bound_before=this->XiAlphaBound(2.0,true);

    //Get the derivative
    std::vector<double> der;
    XiAlphaBoundDerivative(der,2.0,include_db);

    //The step that will be filled
    std::vector<double> step(der.size());

    //Do something depending on methode ...
    const double grow_factor=1.1;
    const double shrink_factor=0.6;
    double norm=0.0;
    switch(methode)
    {
    case GRAD_IND_STEP_SIZE_SIGN_ADAPTION:
        //Adapt step sizes based on signes and fill step
        for(i=0;i<kernel_opt_step_size.size();++i)
        {
            std::cerr<<"Last der="<<last_derivatives[i]<<", this der="<<der[i]<<std::endl;
            if(der[i]*last_derivatives[i]>0.0)
                kernel_opt_step_size[i]*=grow_factor;
            else
                kernel_opt_step_size[i]*=shrink_factor;
        }
        std::cerr<<"Modified: "<<std::endl;
        for(int i=0;i<this->kernel_opt_step_size.size();++i)
            std::cerr<<this->kernel_opt_step_size[i]<<"\t";
        std::cerr<<std::endl;
        //Let kernel apply bounds
        this->kernel.boundStepSize(kernel_opt_step_size);
        std::cerr<<"Bound: "<<std::endl;
        for(int i=0;i<this->kernel_opt_step_size.size();++i)
            std::cerr<<this->kernel_opt_step_size[i]<<"\t";
        std::cerr<<std::endl;
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
        {
            step[i]=-der[i]*kernel_opt_step_size[i]/norm;
        }
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
        this->kernel.boundSteps(step);
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
        this->kernel.boundSteps(step);
        break;
    }

    //Update the kernel
    this->kernel.updateKernelPar(step);
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
double laSvmSingleKernel<T,Kernel>::GetLinindepThresholdForSVNum(int sv_num)
{
  if(this->used_svs.size()<=sv_num+sv_num/20)
    {
      return this->linindep_threshold;
    }
  //A list of the highest common kernel par of SVs
  std::vector<T> highest_common_k(this->used_svs.size(),0.0);
  for(unsigned int i=0;i!=this->used_svs.size();++i)
    {
      std::vector<T> &row=this->GetKernelRow(this->used_svs[i]);
      for(unsigned int j=i+1;j!=this->used_svs.size();++j)
	{
	  if(this->getSVLabel(this->used_svs[i])!=this->getSVLabel(this->used_svs[j]))
	    continue;  
	  if(row[this->used_svs[j]]>highest_common_k[i])
	    highest_common_k[i]=row[this->used_svs[j]];
	  if(row[this->used_svs[j]]>highest_common_k[j])
	    highest_common_k[j]=row[this->used_svs[j]];
	}
      this->UnlockKernelRow(this->used_svs[i]);
    }
  //Sort the k's
  std::sort(highest_common_k.begin(),highest_common_k.end());
  //Find the highest jump around wanted number
 
  int want_index=sv_num-sv_num/20; 
  for(int i=sv_num-sv_num/20;i<std::min(sv_num+sv_num/20,int(this->used_svs.size()-1));++i)
    {
      if((highest_common_k[i]-highest_common_k[i-1])>(highest_common_k[want_index]-highest_common_k[want_index-1]))
        want_index=i;
    }
  //Get the K in question
  T k=(highest_common_k[want_index]+highest_common_k[want_index-1])/2.0;
  return 1-k*k;
}

template<class T,class Kernel>
void laSvmSingleKernel<T,Kernel>::ReFindPairs(bool threshold_increased)
{
  if(threshold_increased)
    {
      //Find new pairs
      std::vector<int> cons_svs=this->used_svs;
      for(unsigned int i=0;i<cons_svs.size();++i)
	{
	  if(cons_svs[i]==INT_MAX)
	    continue;
	  std::vector<T> &row=this->GetKernelRow(cons_svs[i]);
	  for(unsigned int j=i+1;j<cons_svs.size() && cons_svs[i]!=INT_MAX;++j)
	    {   
	      if(cons_svs[j]==INT_MAX)
		continue;
	      if(this->getSVLabel(cons_svs[i])==this->getSVLabel(cons_svs[j]))
		{
		  if(1.0-row[cons_svs[j]]*row[cons_svs[j]]<this->linindep_threshold)
		    {
		      //Combine these two
		      this->UnlockKernelRow(cons_svs[i]);
		      int new_sv_index=this->CombineSVs(cons_svs[i],cons_svs[j]);
		      //Set the j to this new guy
		      cons_svs[j]=new_sv_index;
		      //And remove the i
		      cons_svs[i]=INT_MAX;
		    }
		}
	    }
	  //Did we already unlock the row?
	  if(cons_svs[i]!=INT_MAX)
	    this->UnlockKernelRow(cons_svs[i]);
	}
    }
  else
    {
      //Split pairs
      std::vector<int> used_svs_cp=this->used_svs;
      for(std::vector<int>::iterator i=used_svs_cp.begin();i!=used_svs_cp.end();++i)
	{
	  int data_id=SVs[*i].data_id;
	  if(data_id<0)
	    {
	      //A combined sample ...
	      std::vector<int> removes;
	      this->combined_samples[-(data_id+1)].testCoherence(this->kernel,this->data,this->VLength,this->linindep_threshold,removes);
	      //Remove them
	      if(removes.size()>0)
                this->SplitSVs(*i,removes,false);
	    }
	}
    }
}

template<class T,class Kernel>
void laSvmSingleKernel<T,Kernel>::RecomputeKernel()
{
    std::vector<int>::iterator i,j;
    //Search for pairs that have to be separated
    this->ReFindPairs(false);
    //Invalidate current kernel
    this->InvalidateCache();
    //Things to store for combining vectors
    std::list<std::pair<int,int> > combines;
    //Update all gradients ... man this takes long I guess
    for(int ii=0;ii!=this->used_svs.size();++ii)
    {
        std::vector<T> &row=this->GetKernelRow(this->used_svs[ii]);
        //Compute the gradient and save ...
        ComputeGradient(row,this->used_svs[ii]);
        this->UnlockKernelRow(this->used_svs[ii]);
    }

    //Fulfill the combines
    this->ReFindPairs(true);

    this->minmax_dirty=true;
}

template<class T,class Kernel>
void laSvmSingleKernel<T,Kernel>::ComputeGradient(const std::vector<T>& row,const int sv_index)
{
    SVs[sv_index].g=this->getSVLabel(sv_index);
    std::vector<int>::iterator i;
    for(i=this->used_svs.begin();i!=this->used_svs.end();++i)
    { 
        SVs[sv_index].g-=SVs[*i].alpha * row[*i];
    }
}

template<class T,class Kernel>
void laSvmSingleKernel<T,Kernel>::UpdateGradients(const std::vector<T>& min_row,const std::vector<T>& max_row,const double step)
{
    std::vector<int>::iterator i;
    for(i=this->used_svs.begin();i!=this->used_svs.end();++i)
    {
        assert(!SVs[*i].Unused());
        SVs[*i].g -= step * (max_row[*i]-min_row[*i]);
    }
}

