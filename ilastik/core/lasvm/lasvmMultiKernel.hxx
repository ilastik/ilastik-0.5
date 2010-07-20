#include "lasvmBase.hxx"

template<class T, class Kernel>
class laSvmMultiKernel : public laSvmBase<T, MultiKernelRow<T> >
{
public:
    laSvmMultiKernel(vector<typename Kernel::par_type> kernel_pars,T C double epsilon, int precahce_elements, bool verbose=false) : laSvmBase<T, MultiKernelRow<T> >(C,epislon,precache_elements,verbose)
    {
        this->kernel_pars=kernel_pars;
        beta.resize(kernel_pars.size(),1.0/kernel_pars.size());
    }
protected:
    virtual void ComputeGradient(const MultiKernelRow<T>& row, const int sv_index);
    virtual void UpdateGradients(const MultiKernelRow<T>& min_row, const MultiKernelRow<T>& max_row, const T step);
    virtual void FillRow(MultiKernelRow<T>& row,int sv_index);
    virtual void UpdateRow(MultiKernelRow<T>& row,int sv_index);
    virtual T DirectKernel(int sv,const vector<T>& vec);
    vector<typename Kernel::par_type> kernel_pars;
    vector<T> beta;
};

template<class T,class Kernel>
void ComputeGradient(const MultiKernelRow<T>& row,const int sv_index)
{
    int j;
    list<int>::iterator i;
    SVs[sv_index].g=0.0;
    ******************
    for(j=0;j<beta.size();++j)
    {
        SVs[sv_index].subKernel_g=0.0;
        for(i=used_svs.begin();i!=used_svs.end();++i)
        {
            SVs[sv_index].subKernel_g-=SVs[*i].alpha * row.SubKernelRows[j][*i];
        }
    }
}

template<class T,class Kernel>
T laSvmMultiKernel<T,Kernel>::DirectKernel(int sv,const MultiKernelRow<T>& vec)
{
    T ret=0.0;
    for(int i=0;i<beta.size();++i)
    {
        ret+=beta[i]*Kernel::compute(vec,SVs[sv].m_features,this->VLength,kernel_pars[i]);
    }
    return ret;
}

template<class T,class Kernel>
void laSvmMultiKernel<T,Kernel>::FillRow(MultiKernelRow<T>& row,int sv_index)
{
    list<int>::itetator i;
    assert(!SVs[sv_index].Unused());
    for(i=this->used_svs.begin();i!=this->used_svs.end();++i)
    {
        int j;
        row.WeightedRow[*i]=0.0;
        for(j=0;j<betas.size();++j)
        {
            row.SubKernelRows[j][*i]=Kernel::compute(SVs[*i].m_features,SVs[sv_index].m_features,this->VLength,kernel_pars[j]);
            row.WeightedRow[*i]+=row.SubKernelRows[j][*i];
            row.SubKernelRowDirty[j]=false;
        }
    }
    row.AnySubKernelRowDirty=false;
    row.WeigtedRowDirty=false;
}

template<class T,class Kernel>
void laSvmMultiKernel<T,Kernel>::UpdateRow(MultiKernelRow<T>& row,int sv_index)
{
    int j;
    list<int>::itetrator i;

    if(row.AnySubKernelRowDirty)
    {
        for(j=0;j<betas.size();++j)
        {
            if(row.SubKernelRowDirty[j])
            {
                for(i=this->used_svs.begin();i!=this->used_svs.end();++i)
                {
                    row.SubKernelRows[j][*i]=Kernel::compute(SVs[*i].m_features,SVs[sv_index].m_feaures,this->VLength,kernel_pars[j]);
                }
                row.SubKernelRowDirty[j]=false;
            }
        }
        row.AnySubKernelRowDirty=false;
    }
    if(row.WeightedRowDirty)
    {
        for(i=this-<used_svs.begin();i!=this->used_svs.end();++i)
        {
            row.WeightedRow[*i]=0.0;
            for(j=0;j<betas.size();++j)
            {
                row.WeightedRow[*i]+=betas[j]*row.SubKernelRow[j][*i];
            }
        }
        row.WeigthedRowDirty=false;
    }
}

