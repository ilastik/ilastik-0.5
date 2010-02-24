#include <vector>

#ifndef VECTOR_INCLUDED
#define VECTOR_INCLUDED

template<class T>
struct Vector
{
    Vector()
    {
        data_id=unused_id;
    }
    void cleanup()
    {
        data_id=unused_id;
    }
    bool Unused()
    {
        return data_id==unused_id;
    }
    void Init(const int id)
    {
        cleanup();
        data_id=id;
    }
    int data_id;
    static const int unused_id=0xCFFFFFFF;
};

template<class T>
struct laSvmVector: public Vector<T>
{
    laSvmVector() : Vector<T>()
    {
        g=0.0;
    }
    double g;
};

template<class T> struct laSvmSupportVector;

template<class T>
struct laSvmNormalVector : public laSvmVector<T>
{
    typedef int init_param;
    void swap(laSvmSupportVector<T>& sv);
};

template<class T>
struct laSvmSupportVector : public laSvmVector<T>
{
    laSvmSupportVector() : laSvmVector<T>()
    {
        assert(this->Unused());
        change_id=0;
        cmin=0;cmax=0;alpha=0;
    }
    double cmin;
    double cmax;

    double alpha;
    int change_id; //Incremented everytime when the sv changes, needed for online prediction
    void swap(laSvmNormalVector<T>& nv);
};

/*
template<class T>
struct MultiKernelSupportVector : public SupportVector<T>
{
MultiKernelSupportVector(int num_SubKernels)
{
    subKernel_g.resize(num_SubKernels);
}
vector<T> subKernel_g;
};*/

template<class T>
void laSvmNormalVector<T>::swap(laSvmSupportVector<T>& sv)
{
    assert(this->Unused() || sv.Unused());
    int tmp=this->data_id;
    this->data_id=sv.data_id;
    sv.data_id=tmp;

    double tmp_g=this->g;
    this->g=sv.g;
    sv.g=tmp_g;

    sv.change_id++;
}

template<class T>
void laSvmSupportVector<T>::swap(laSvmNormalVector<T>& nv)
{
    assert(this->Unused() || nv.Unused());
    int tmp=this->data_id;
    this->data_id=nv.data_id;
    nv.data_id=tmp;

    double tmp_g=this->g;
    this->g=0.0;
    nv.g=tmp_g;

    change_id++;
}

//Same for huller
template<class T> struct hullerSupportVector;
template<class T>
struct hullerNormalVector : public Vector<T>
{
    typedef int init_param;
    void swap(hullerSupportVector<T>& sv);
};

template<class T>
struct hullerSupportVector : public Vector<T>
{
    void swap(hullerNormalVector<T>& nv);
    double alpha;
    double same_label_kernel_sum;
    double other_label_kernel_sum;
};

template<class T>
void hullerSupportVector<T>::swap(hullerNormalVector<T>& nv)
{
    assert(this->Unused() || nv.Unused());
    int tmp=this->data_id;
    this->data_id=nv.data_id;
    nv.data_id=tmp;
    this->same_label_kernel_sum=0.0;
    this->other_label_kernel_sum=0.0;
    this->alpha=0.0;
}

template<class T>
void hullerNormalVector<T>::swap(hullerSupportVector<T>& sv)
{
    sv.swap(*this);
} 

//THIS IS STUPID
//but I do not know a better way
#define SVs this->support_vectors
#define NVs this->normal_vectors

#endif 
