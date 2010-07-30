//#include <cmath>
#include <math.h>
#include <iostream>
//#include "fastexp.h"

#define MY_EXP(x) exp(x)


template<class T>
class KernelGauss
{
public:
    typedef std::vector<T> RowType;
    typedef T float_type;
    
    
    KernelGauss(T gamma){this->gamma=gamma;}
    static const int num_parameters=1;
    T gamma;
    std::vector<T> sigma;//Variance of all data
    T sigma_avg;
    template<class iter>
        inline void setVariance(const iter &begin,const iter& end);
    template<class iter1,class iter2>
    inline T distance(const iter1 &v1,const iter2 &v2,int length);
    template<class iter1,class iter2>
    inline T compute(const iter1 &v1,const iter2 &v2,int length) const;
    T compute(T dist) const;
    template<class iter1,class iter2>
    inline void computeDerived(const iter1 &v1,const iter2 &v2,int length,std::vector<double> &dKernel);
    typedef T par_type;
    inline void updateKernelPar(const std::vector<double> &dKernel);
    inline void boundStepSize(std::vector<double>& s);
    inline void boundSteps(std::vector<double>& s);
    inline void resetOutOfBoundPar(std::vector<T>& variances);
    inline std::vector<double> getInitialStepSizes();
    inline std::vector<T> getLineSearchPoints(int index,T lower_bound=MY_EXP(-10.0),T upper_bound=MY_EXP(2.0));
    inline void setParameter(T value,int index);
};

template<class T>
template<class iter>
void KernelGauss<T>::setVariance(const iter& begin,const iter& end)
{
    sigma.clear();
    sigma=std::vector<T>(begin,end);
    for(int i=0;i<sigma.size();++i)
        sigma_avg+=sigma[i]/sigma.size();
}

template<class T>
void KernelGauss<T>::setParameter(T value,int index)
{
    gamma=value;
}

template<class T>
std::vector<T> KernelGauss<T>::getLineSearchPoints(int index,T lower_bound,T upper_bound)
{
    //Transform bounds
    lower_bound=log(lower_bound);
    upper_bound=log(upper_bound);

    std::vector<T> res;
    T x;
    for(x=lower_bound;x<=upper_bound;x+=1.0)
    {
        res.push_back(MY_EXP(x*sigma_avg));
    }
    return res;
}

template<class T>
std::vector<double> KernelGauss<T>::getInitialStepSizes()
{
    return std::vector<double>(1,1.0);
}

template<class T>
void KernelGauss<T>::boundSteps(std::vector<double>& s)
{
    for(int i=0;i<s.size();++i)
    {
        if(s[i]<-1.0)
            s[i]=-1.0;
        if(s[i]>1.0)
            s[i]=1.0;
    }
}

template<class T>
void KernelGauss<T>::boundStepSize(std::vector<double>& s)
{
    s[0]=std::min(1.0,s[0]);
    s[0]=std::max(0.00001,s[0]);
}

template<class T>
template<class iter1,class iter2>
T KernelGauss<T>::compute(const iter1 &v1,const iter2 &v2,int length) const
{
    T dot=0.0;
    for(int i=0;i<length;++i)
    {
        dot+=(v1[i]-v2[i])*(v1[i]-v2[i]);
    }
    return MY_EXP(-gamma*dot);
}

template<class T>
T KernelGauss<T>::compute(const T dist) const
{
    return MY_EXP(-dist*dist);
}

template<class T>
template<class iter1,class iter2>
T KernelGauss<T>::distance(const iter1 &v1,const iter2 &v2,int length)
{
    T dot=0.0;
    for(int i=0;i<length;++i)
    {
        dot+=(v1[i]-v2[i])*(v1[i]-v2[i]);
    }
    return sqrt(gamma*dot);
}
 
template<class T>
template<class iter1,class iter2>
void KernelGauss<T>::computeDerived(const iter1 &v1,const iter2 &v2,int length,std::vector<double>& dKernel)
{
    T dot=0.0;
    for(int i=0;i<length;++i)
        dot+=(v1[i]-v2[i])*(v1[i]-v2[i]);
    dKernel[0]=-dot*MY_EXP(-gamma*dot)*gamma;//*sigma_avg;
}

template<class T>
void KernelGauss<T>::updateKernelPar(const std::vector<double> &dKernel)
{
    gamma*=MY_EXP(dKernel[0]);
}

template<class T>
void KernelGauss<T>::resetOutOfBoundPar(std::vector<T>& variances)
{
    //The criteria is: log(gamma/var) \in [-12,3]
    //Since we have only one gamma, we take the average of all variances
    int i;
    T avg=0.0;
    for(i=0;i!=variances.size();++i)
    {
        avg+=variances[i];
    }
    avg/=variances.size();
    
    T crit=log(gamma/avg);
    if(crit>3.0)
        gamma=avg/variances.size();
    if(crit<-12.0)
        gamma=avg/variances.size();
}

template<class T>
class KernelGaussMultiParams
{
public:
    typedef std::vector<T> RowType;
    typedef T float_type;
    
    int num_parameters;
    KernelGaussMultiParams(std::vector<T>& pars)
    {
        num_parameters=pars.size();
        gammas=pars;
    }
    std::vector<T> sigma;//Variance of all data
    template<class iter>
        inline void setVariance(const iter &begin,const iter& end);
    void initParameters();
    template<class iter1,class iter2>
    inline T compute(const iter1 v1,const iter2 v2,int length) const;
    inline T compute(const T dist) const;
    template<class iter1,class iter2>
    inline T distance(const iter1 &v1,const iter2 &v2,int length);
    template<class iter1,class iter2>
    inline void computeDerived(const iter1 v1,const iter2 v2,int length,std::vector<double> &dKernel);
    typedef std::vector<T> par_type;
    par_type gammas;
    inline void updateKernelPar(const std::vector<double> &dKernel);
    inline void resetOutOfBoundPar(std::vector<T>& variances);
    inline void boundStepSize(std::vector<double>& s);
    inline void boundSteps(std::vector<double>& s);
    inline std::vector<double> getInitialStepSizes();
    inline std::vector<T> getLineSearchPoints(int index,T lower_bound=MY_EXP(-10.0),T upper_bound=MY_EXP(2.0));
    inline void setParameter(T value,int index);
};

template<class T>
template<class iter>
void KernelGaussMultiParams<T>::setVariance(const iter& begin,const iter& end)
{
    sigma.clear();
    sigma=std::vector<T>(begin,end);
}

template<class T>
void KernelGaussMultiParams<T>::initParameters()
{
    for(int i=0;i<sigma.size();++i)
    {
        if(sigma[i]>0.0)
            gammas[i]=1.0/(sigma[i]*sigma.size());
        else
            gammas[i]=0.0;
    }
}

template<class T>
void KernelGaussMultiParams<T>::setParameter(T value,int index)
{
    gammas[index]=value;
}

template<class T>
std::vector<T> KernelGaussMultiParams<T>::getLineSearchPoints(int index,T lower_bound,T upper_bound)
{
    //Tranform bounds
    lower_bound=log(lower_bound);
    upper_bound=log(upper_bound);

    std::vector<T> res;
    T x;
    for(x=lower_bound;x<=upper_bound;x+=1.0)
    {
        res.push_back(MY_EXP(x*sigma[index]));
    }
    return res;
}

template<class T>
std::vector<double> KernelGaussMultiParams<T>::getInitialStepSizes()
{
    return std::vector<double>(sigma.size(),1.0);
}

template<class T>
void KernelGaussMultiParams<T>::boundSteps(std::vector<double>& s)
{
    for(int i=0;i<s.size();++i)
    {
        if(s[i]<-1.0)
            s[i]=-1.0;
        if(s[i]>1.0)
            s[i]=1.0;
    }
}

template<class T>
void KernelGaussMultiParams<T>::boundStepSize(std::vector<double>& s)
{
    for(int i=0;i<num_parameters;++i)
    {
        s[i]=std::min(1.0,s[i]);
        s[i]=std::max(0.00001,s[i]);
    }
}

template<class T>
template<class iter1,class iter2>
T KernelGaussMultiParams<T>::distance(const iter1 &v1,const iter2 &v2,int length)
{
    T dot=0.0;
    for(int i=0;i<num_parameters;++i)
    {
        dot+=(v1[i]-v2[i])*(v1[i]-v2[i])*gammas[i];
    }
    return sqrt(dot);
}

template<class T>
template<class iter1,class iter2>
T KernelGaussMultiParams<T>::compute(const iter1 v1,const iter2 v2,int length) const
{
    T dot=0.0;
    assert(length==num_parameters);
    for(int i=0;i<num_parameters;++i)
    {
        dot+=(v1[i]-v2[i])*(v1[i]-v2[i])*gammas[i];
    }
    return MY_EXP(-dot);
}

template<class T>
T KernelGaussMultiParams<T>::compute(T dist) const
{
    return MY_EXP(-dist*dist);
}

template<class T>
template<class iter1,class iter2>
void KernelGaussMultiParams<T>::computeDerived(const iter1 v1,const iter2 v2,int length,std::vector<double> &dKernel)
{
    T dot;
    T all_dot=0.0;
    assert(length==num_parameters);
    int i;
    for(i=0;i<num_parameters;++i)
    {
        dot=(v1[i]-v2[i])*(v1[i]-v2[i]);
        dKernel[i]=-dot*gammas[i];//*sigma[i];
        all_dot+=dot*gammas[i];
    }
    T k=MY_EXP(-all_dot);
    for(i=0;i<num_parameters;++i)
    {
        dKernel[i]*=k;
    }
}

template<class T>
void KernelGaussMultiParams<T>::updateKernelPar(const std::vector<double> &dKernel)
{
    std::cerr<<"Updating with:" <<std::endl;
    for(int i=0;i<num_parameters;++i)
    {
        std::cerr<<dKernel[i]<<"\t";
        gammas[i]*=MY_EXP(dKernel[i]);
    }
    std::cerr<<std::endl;
}

template<class T>
void KernelGaussMultiParams<T>::resetOutOfBoundPar(std::vector<T>& variances)
{
    //The criteria is: log(gamma/var) \in [-12,3]
    int i;
    for(i=0;i<variances.size();++i)
    {
        T crit=log(gammas[i]/variances[i]);
        if(crit>3.0)
            gammas[i]=variances[i]/variances.size();
        if(crit<-12.0)
            gammas[i]=variances[i]/variances.size();
    }
}

