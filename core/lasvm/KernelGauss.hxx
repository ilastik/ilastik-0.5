#include <math.h>
#include <iostream>

using namespace std;

template<class T>
class KernelGauss
{
public:
    KernelGauss(T gamma){this->gamma=gamma;}
    static const int num_parameters=1;
    T gamma;
    vector<T> sigma;//Variance of all data
    T sigma_avg;
    template<class iter>
        inline void setVariance(const iter &begin,const iter& end);
    template<class iter1,class iter2>
    inline T compute(const iter1 &v1,const iter2 &v2,int length);
    template<class iter1,class iter2>
    inline void computeDerived(const iter1 &v1,const iter2 &v2,int length,vector<double> &dKernel);
    typedef T par_type;
    inline void updateKernelPar(const vector<double> &dKernel);
    inline void boundStepSize(vector<double>& s);
    inline void boundSteps(vector<double>& s);
    inline void resetOutOfBoundPar(vector<T>& variances);
    inline vector<double> getInitialStepSizes();
    inline vector<T> getLineSearchPoints(int index,T lower_bound=exp(-10.0),T upper_bound=exp(2.0));
    inline void setParameter(T value,int index);
};

template<class T>
template<class iter>
void KernelGauss<T>::setVariance(const iter& begin,const iter& end)
{
    sigma.clear();
    sigma=vector<T>(begin,end);
    for(int i=0;i<sigma.size();++i)
        sigma_avg+=sigma[i]/sigma.size();
}

template<class T>
void KernelGauss<T>::setParameter(T value,int index)
{
    gamma=value;
}

template<class T>
vector<T> KernelGauss<T>::getLineSearchPoints(int index,T lower_bound,T upper_bound)
{
    //Transform bounds
    lower_bound=log(lower_bound);
    upper_bound=log(upper_bound);

    vector<T> res;
    T x;
    for(x=lower_bound;x<=upper_bound;x+=1.0)
    {
        res.push_back(exp(x*sigma_avg));
    }
    return res;
}

template<class T>
vector<double> KernelGauss<T>::getInitialStepSizes()
{
    return vector<double>(1,sigma_avg);
}

template<class T>
void KernelGauss<T>::boundSteps(vector<double>& s)
{
    for(int i=0;i<s.size();++i)
    {
        if(s[i]<-sigma[i])
            s[i]=-sigma[i];
        if(s[i]>sigma[i])
            s[i]=sigma[i];
    }
}

template<class T>
void KernelGauss<T>::boundStepSize(vector<double>& s)
{
    s[0]=min(double(sigma_avg),s[0]);
    s[0]=max(0.0001*double(sigma_avg),s[0]);
}

template<class T>
template<class iter1,class iter2>
T KernelGauss<T>::compute(const iter1 &v1,const iter2 &v2,int length)
{
    T dot=0.0;
    for(int i=0;i<length;++i)
    {
        dot+=(v1[i]-v2[i])*(v1[i]-v2[i]);
    }
    return exp(-gamma*dot);
}
 
template<class T>
template<class iter1,class iter2>
void KernelGauss<T>::computeDerived(const iter1 &v1,const iter2 &v2,int length,vector<double>& dKernel)
{
    T dot=0.0;
    for(int i=0;i<length;++i)
        dot+=(v1[i]-v2[i])*(v1[i]-v2[i]);
    dKernel[0]=-dot*exp(-gamma*dot)*gamma*sigma_avg;
}

template<class T>
void KernelGauss<T>::updateKernelPar(const vector<double> &dKernel)
{
    gamma*=exp(dKernel[0]);
}

template<class T>
void KernelGauss<T>::resetOutOfBoundPar(vector<T>& variances)
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
    int num_parameters;
    KernelGaussMultiParams(vector<T>& pars)
    {
        num_parameters=pars.size();
        gammas=pars;
    }
    vector<T> sigma;//Variance of all data
    template<class iter>
        inline void setVariance(const iter &begin,const iter& end);
    template<class iter1,class iter2>
    inline T compute(const iter1 v1,const iter2 v2,int length);
    template<class iter1,class iter2>
    inline void computeDerived(const iter1 v1,const iter2 v2,int length,vector<double> &dKernel);
    typedef vector<T> par_type;
    par_type gammas;
    inline void updateKernelPar(const vector<double> &dKernel);
    inline void resetOutOfBoundPar(vector<T>& variances);
    inline void boundStepSize(vector<double>& s);
    inline void boundSteps(vector<double>& s);
    inline vector<double> getInitialStepSizes();
    inline vector<T> getLineSearchPoints(int index,T lower_bound=exp(-10.0),T upper_bound=exp(2.0));
    inline void setParameter(T value,int index);
};

template<class T>
template<class iter>
void KernelGaussMultiParams<T>::setVariance(const iter& begin,const iter& end)
{
    sigma.clear();
    sigma=vector<T>(begin,end);
}

template<class T>
void KernelGaussMultiParams<T>::setParameter(T value,int index)
{
    gammas[index]=value;
}

template<class T>
vector<T> KernelGaussMultiParams<T>::getLineSearchPoints(int index,T lower_bound,T upper_bound)
{
    //Tranform bounds
    lower_bound=log(lower_bound);
    upper_bound=log(upper_bound);

    vector<T> res;
    T x;
    for(x=lower_bound;x<=upper_bound;x+=1.0)
    {
        res.push_back(exp(x*sigma[index]));
    }
    return res;
}

template<class T>
vector<double> KernelGaussMultiParams<T>::getInitialStepSizes()
{
    return vector<double>(sigma.begin(),sigma.end());
}

template<class T>
void KernelGaussMultiParams<T>::boundSteps(vector<double>& s)
{
    for(int i=0;i<s.size();++i)
    {
        if(s[i]<-sigma[i])
            s[i]=-sigma[i];
        if(s[i]>sigma[i])
            s[i]=sigma[i];
    }
}

template<class T>
void KernelGaussMultiParams<T>::boundStepSize(vector<double>& s)
{
    for(int i=0;i<num_parameters;++i)
    {
        s[i]=min(1.0*sigma[i],s[i]);
        s[i]=max(0.0001*sigma[i],s[i]);
    }
}

template<class T>
template<class iter1,class iter2>
T KernelGaussMultiParams<T>::compute(const iter1 v1,const iter2 v2,int length)
{
    T dot=0.0;
    assert(length==num_parameters);
    for(int i=0;i<num_parameters;++i)
    {
        dot+=(v1[i]-v2[i])*(v1[i]-v2[i])*gammas[i];
    }
    return exp(-dot);
}

template<class T>
template<class iter1,class iter2>
void KernelGaussMultiParams<T>::computeDerived(const iter1 v1,const iter2 v2,int length,vector<double> &dKernel)
{
    T dot;
    T all_dot=0.0;
    assert(length==num_parameters);
    int i;
    for(i=0;i<num_parameters;++i)
    {
        dot=(v1[i]-v2[i])*(v1[i]-v2[i]);
        dKernel[i]=-dot*gammas[i]*sigma[i];
        all_dot+=dot*gammas[i];
    }
    T k=exp(-all_dot);
    for(i=0;i<num_parameters;++i)
    {
        dKernel[i]*=k;
    }
}

template<class T>
void KernelGaussMultiParams<T>::updateKernelPar(const vector<double> &dKernel)
{
    for(int i=0;i<num_parameters;++i)
    {
        gammas[i]*=exp(dKernel[i]);
    }
}

template<class T>
void KernelGaussMultiParams<T>::resetOutOfBoundPar(vector<T>& variances)
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

