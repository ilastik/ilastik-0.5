#ifndef PREDICT_COVER_TREE_INCLUDED
#define PREDICT_COVER_TREE_INCLUDED
#include "cover-tree/coverTree.hxx"
#include "cover-tree/Node.hxx"

//Node class with all information for a svm kernel sum

template<class SV>
class SvmKernelSumNode : public Node<SV*,SvmKernelSumNode<SV> >
{
public:
    typedef SV* point_type;
    SvmKernelSumNode(SV* point,int level) : Node<SV*,SvmKernelSumNode<SV> >(point,level){}
    //Kernel sum passed below
    double passedKernelSum;
    //Kernel sums below
    double PosKernelWeight,NegKernelWeight;
    double max_pos_dist,max_neg_dist;
    double max_dist;
    double avg_pos_dist,avg_neg_dist;
    //Finalize the node
    template<class iterator>
    void finalizeNode(iterator begin,iterator end);

};

template<class SV>
template<class iterator>
void SvmKernelSumNode<SV>::finalizeNode(iterator begin,iterator end)
{
    //Our kernel weight is the sum of of the KernelWeight below us.
    PosKernelWeight=NegKernelWeight=0.0;
    max_pos_dist=max_neg_dist=0.0;
    avg_pos_dist=avg_neg_dist=0.0;
    if(this->childs.empty())
    {
        for(int i=0;i<this->zero_children.size();++i)
        {
            this->PosKernelWeight+=std::max(0.0,this->zero_children[i]->alpha);
            this->NegKernelWeight+=std::min(0.0,this->zero_children[i]->alpha);
        }
        this->PosKernelWeight+=std::max(0.0,this->point->alpha);
        this->NegKernelWeight+=std::min(0.0,this->point->alpha);
    }
    for(int i=0;i<this->childs.size();++i)
    {
        PosKernelWeight+=((SvmKernelSumNode<SV>*)this->childs[i])->PosKernelWeight;
        NegKernelWeight+=((SvmKernelSumNode<SV>*)this->childs[i])->NegKernelWeight;
    }
    this->passedKernelSum=0.0;
    //Find the average and maximum distances
    for(;begin!=end;++begin)
    {
        if(begin->point->alpha>0.0)
        {
            if(begin->distances.back()>max_pos_dist)
                max_pos_dist=begin->distances.back();
            avg_pos_dist+=begin->point->alpha*begin->distances.back();
        }
        else
        {
            if(begin->distances.back()>max_neg_dist)
                max_neg_dist=begin->distances.back();
            avg_neg_dist+=begin->point->alpha*begin->distances.back();
        }
    }
    avg_pos_dist/=PosKernelWeight;
    avg_neg_dist/=NegKernelWeight;
    max_dist=std::max(max_neg_dist,max_pos_dist);
};

//We want to use vector<vector> similar to MultiArray. Therefor we need rowVector
template<class T>
const std::vector<T>& rowVector(const std::vector<std::vector<T> >& a,int index)
{
    return a[index];
}

//Predict functor, for the needed functions in the cover tree
//We give this functor to the StdKernelSumFunctor and StdDualKernelSumFunctor
//- distances between svs
//- distances between predict datas
//- kernel between svs and predict data
//- adding to the sum of predict datas
int num_exp;
int num_dist;
template<class SVM,class SV,class array1,class array2>
class predictFunctor
{
public:
    array1* predict_vectors;
    array2* result;
    SVM* svm;
    bool use_avg_for_error;
    //debug info
    predictFunctor(SVM* svm,array1* pv,array2* res)
    {
        this->svm=svm;
        this->predict_vectors=pv;
        this->result=res;
        this->use_avg_for_error=true;
    }
    double distance(const SV* a,const SV* b) const
    {
        ++num_dist;
        return svm->kernel.distance(svm->getFeatures(a),svm->getFeatures(b),svm->VLength);
    }
    double distance(const int a,const int b) const
    {
        ++num_dist;
        return svm->kernel.distance(rowVector(*predict_vectors,a),rowVector(*predict_vectors,b),svm->VLength);
    }
    double distance(const int b,const SV* a) const
    {
        ++num_dist;
        return svm->kernel.distance(svm->getFeatures(a),rowVector(*predict_vectors,b),svm->VLength);
    }
    double Kernel(const int b,const SV* a,double dist) const
    {
        ++num_exp;
        return svm->kernel.compute(dist)*a->alpha;
    }
    double Kernel(const int b,const SV* a) const
    {
        ++num_exp;
	++num_dist;
        return svm->kernel.compute(svm->getFeatures(a),rowVector(*predict_vectors,b),svm->VLength)*a->alpha;
    }
    void AddKernelSumToPoint(const int a,double sum)
    {
        (*result)[a]+=sum;
    }
    double plainKernel(double dist) const
    {
        ++num_exp; 
        return svm->kernel.compute(dist);
    }
    double KernelError(int point,SvmKernelSumNode<SV>* node,const double dist) const
    {
        if(dist<node->max_dist)
            return 1000.0;
        double center_val=plainKernel(dist);
        double min_val=plainKernel(dist-node->max_dist);
        double max_val=plainKernel(dist+node->max_dist);
        return std::max(min_val-center_val,center_val-max_val);
    }
    double DualKernelError(const MaxDistNode<int>* node1,const SvmKernelSumNode<SV>* node2,const double dist) const
    {
        if(dist<node1->max_dist+node2->max_dist)
            return 1000.0;
        double center_val=plainKernel(dist);
        double min_val=plainKernel(dist-node1->max_dist-node2->max_dist);
        double max_val=plainKernel(dist+node1->max_dist+node2->max_dist);
        return std::max(min_val-center_val,center_val-max_val);
    }
    double SubTreeKernelSum(int point,const SvmKernelSumNode<SV>* node,double dist) const
    {
        return plainKernel(dist)*(node->PosKernelWeight+node->NegKernelWeight);
    }
    //Upper bound (based on average distance)
    double kernelSumUpperBound(double max_dist,double avg_dist,double center_dist,double center_val) const
    {
        //Special case: If we go over the origin, take the origin
        if(max_dist>center_dist)
            return 1.0;
        double turn_point=1.0/sqrt(2.0);
        if(turn_point>=center_dist)
        {
            //Concave
	    ++num_exp;
            return exp(-(center_dist-avg_dist)*(center_dist-avg_dist));
        }
        else
        {
            if(turn_point<=center_dist-max_dist)
            {
                //Convex
      	        ++num_exp;
                return center_val+avg_dist/max_dist*(exp(-(center_dist-max_dist)*(center_dist-max_dist))-center_val);
            }
            else
            {
                //Complex :)
      	        num_exp+=2;
                double derivative=-2.0*(center_dist-max_dist)*exp(-(center_dist-max_dist)*(center_dist-max_dist));
                double max_val=exp(-(center_dist-max_dist)*(center_dist-max_dist));
                double y2=std::max(center_val,max_val+derivative*max_dist);
                return max_val+(y2-max_val)/max_dist*avg_dist;
            }
        }
    }
    //Lower bound (based on average distance)
    double kernelSumLowerBound(double max_dist,double avg_dist,double center_dist,double center_val) const
    {
        double turn_point=1.0/sqrt(2.0);
        if(turn_point<=center_dist)
        {
            //Convex
            ++num_exp;
            return exp(-(center_dist+avg_dist)*(center_dist+avg_dist));
        }
        else
        {
            if(turn_point>=center_dist+max_dist)
            {
                //Concave!
	        ++num_exp;
                return center_val+avg_dist/max_dist*(exp(-(center_dist+max_dist)*(center_dist+max_dist))-center_val);
            }
            else
            {
                //Complex :)
                num_exp+=2;
                double derivative=-2.0*(center_dist+max_dist)*exp(-(center_dist+max_dist)*(center_dist+max_dist));
                double min_val=exp(-(center_dist+max_dist)*(center_dist+max_dist));
                double y1=std::min(center_val,min_val-derivative*max_dist);
                double ret=min_val+(y1-min_val)/max_dist*avg_dist;
                return ret;
            }
        }
    }
    void getRangeLimits(int point,SvmKernelSumNode<SV>* node,double dist,double &tmp_range_min,double& tmp_range_max) const
    {
        double max_neg,min_neg,max_pos,min_pos;
        if(use_avg_for_error)
        {
            double center_val=exp(-dist*dist);
            //check for upper bounds
            if(node->max_neg_dist>0.0)
            {
                min_neg=kernelSumLowerBound(node->max_neg_dist,node->avg_neg_dist,dist,center_val);
                if(node->max_neg_dist<dist)
                    max_neg=kernelSumUpperBound(node->max_neg_dist,node->avg_neg_dist,dist,center_val);
                else
                    max_neg=1.0;
            }
            else
                max_neg=min_neg=center_val;
            //Check lower bound
            if(node->max_pos_dist>0.0)
            {
                min_pos=kernelSumLowerBound(node->max_pos_dist,node->avg_pos_dist,dist,center_val);
                if(node->max_pos_dist<dist)
                    max_pos=kernelSumUpperBound(node->max_pos_dist,node->avg_pos_dist,dist,center_val);
                else
                    max_pos=1.0;
            }
            else
                max_pos=min_pos=center_val;

            min_neg*=node->NegKernelWeight;
            max_neg*=node->NegKernelWeight;
            min_pos*=node->PosKernelWeight;
            max_pos*=node->PosKernelWeight;
        }
        else
        {
            double all_max_dist=std::max(node->max_pos_dist,node->max_neg_dist);
            double min_dist=dist-all_max_dist;
            double max_dist=dist+all_max_dist;
            if(min_dist<0)
                min_dist=0.0;
	    num_exp+=2;
            double min_kernel=exp(-min_dist*min_dist);
            double max_kernel=exp(-max_dist*max_dist);

            min_pos=node->PosKernelWeight*max_kernel;
            max_pos=node->PosKernelWeight*min_kernel;
            min_neg=node->NegKernelWeight*max_kernel;
            max_neg=node->NegKernelWeight*min_kernel;
        }

        //Debug tests
        /*double all_max_dist=std::max(node->max_pos_dist,node->max_neg_dist);
        double min_dist=dist-all_max_dist;
        if(min_dist<0)
            min_dist=0.0;
        double max_dist=dist+all_max_dist;
        double max_kernel=exp(-min_dist*min_dist);
        double min_kernel=exp(-max_dist*max_dist);
        std::cerr<<"dist="<<dist<<std::endl;
        std::cerr<<"min_dist="<<min_dist<<std::endl;
        std::cerr<<"max_dist="<<max_dist<<std::endl;
        std::cerr<<"pos_avg_dist="<<node->avg_pos_dist<<std::endl;
        std::cerr<<"neg_avg_dist="<<node->avg_neg_dist<<std::endl;
        std::cerr<<"max_kernel="<<max_kernel<<std::endl;
        std::cerr<<"min_kernel="<<min_kernel<<std::endl;
        std::cerr<<"PosKernelWeight="<<node->PosKernelWeight<<std::endl;
        std::cerr<<"NegKernelWeight="<<node->NegKernelWeight<<std::endl;
        std::cerr<<"min_pos="<<min_pos<<std::endl;
        std::cerr<<"max_pos="<<max_pos<<std::endl;
        std::cerr<<"min_neg="<<min_neg<<std::endl;
        std::cerr<<"max_neg="<<max_neg<<std::endl;
        assert(min_pos>=node->PosKernelWeight*min_kernel);
        assert(max_pos<=node->PosKernelWeight*max_kernel);
        assert(min_neg<=node->NegKernelWeight*min_kernel);
        assert(max_neg>=node->NegKernelWeight*max_kernel);*/

        tmp_range_min=max_neg+min_pos;
        tmp_range_max=max_pos+min_neg;
    }
};

#endif


