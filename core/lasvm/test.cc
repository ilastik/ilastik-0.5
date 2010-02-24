//#include <string>
#include <cppunit/extensions/HelperMacros.h>
#include <cppunit/extensions/TestFactoryRegistry.h>
#include <cppunit/ui/text/TestRunner.h>
#include <cppunit/CompilerOutputter.h>
#include <iostream>
#include <stdlib.h>
#include <ctime>
#include "coverTree.hxx"
#include <time.h>
#include <fstream>
#include "../loadlibsvm.hxx"
#include <math.h>


using namespace std;

#define DIMS 20
#define NUM_SAMPLES 1000
#define epsilon 0.01


int evaluations;
//My nice little functor class
class KernelSumFunctor
{
public:
    double gamma;
    vector<double> KernelSums;
    vector<vector<double> > points;
    double distance(const int a,const int b) const
    {
        double res=0.0;
        for(int i=0;i<DIMS;++i)
            res+=(points[a][i]-points[b][i])*(points[a][i]-points[b][i]);
        return sqrt(res);
    }
    double Kernel(const int& a,const int& b,const double dist) const
    {
        return exp(-gamma*dist*dist);
    }

    double Kernel(const int& a,const int& b) const
    {
        return Kernel(a,b,distance(a,b));
    }
    double SubTreeKernelSum(const int& point,const KernelSumNode<int>* node,const double dist) const
    {
        ++evaluations;
        return Kernel(point,node->point,dist)*node->KernelWeight;
    }
    double KernelError(const int& point,const KernelSumNode<int>* node,const double dist) const
    {
        evaluations+=2;
        if(dist<node->max_dist)
            return 1000.0;
        double dist2=dist*dist;
        double center_val=exp(-gamma*dist*dist);
        double min_val=exp(-gamma*(dist-node->max_dist)*(dist-node->max_dist));
        double max_val=exp(-gamma*(dist+node->max_dist)*(dist+node->max_dist));
        return max(min_val-center_val,center_val-max_val);
    }
    double DualKernelError(const KernelSumNode<int>* node1,KernelSumNode<int>* node2,const double dist) const
    {
        evaluations+=2;
        if(dist<node1->max_dist+node2->max_dist)
            return 1000.0;
        double center_val=exp(-gamma*dist*dist);
        double min_dist=dist-node1->max_dist-node2->max_dist;
        double max_dist=dist+node1->max_dist+node2->max_dist;
        double min_val=exp(-gamma*min_dist*min_dist);
        double max_val=exp(-gamma*max_dist*max_dist);
        return max(min_val-center_val,center_val-max_val);
    }
    void AddKernelSumToPoint(const int p,double sum)
    {
        KernelSums[p]+=sum;
    }
};
//My new thing
template<class Point>
class SVMKernelSumNode : public Node<Point,SVMKernelSumNode<Point> >
{
public:
    SVMKernelSumNode(Point& point,int level) : Node<Point,SVMKernelSumNode<Point> >(point,level){}
    /** Number points below this node.*/
    double PosKernelWeight,NegKernelWeight;
    double max_pos_dist,max_neg_dist;
    double avg_pos_dist,avg_neg_dist;
    /** Calculates the final KernelWeight.*/
    template<class iterator>
    void finalizeNode(iterator begin,iterator end);
};

vector<double>* svm_weights;

template<class Point>
template<class iterator>
void SVMKernelSumNode<Point>::finalizeNode(iterator begin,iterator end)
{
    //Our kernel weight is the sum of of the KernelWeight below us.
    PosKernelWeight=NegKernelWeight=0.0;
    max_pos_dist=max_neg_dist=0.0;
    avg_pos_dist=avg_neg_dist=0.0;
    if(this->childs.empty())
    {
        for(int i=0;i<this->zero_children.size();++i)
        {
            this->PosKernelWeight+=max(0.0,(*svm_weights)[this->zero_children[i]]);
            this->NegKernelWeight+=min(0.0,(*svm_weights)[this->zero_children[i]]);
        }
        this->PosKernelWeight+=max(0.0,(*svm_weights)[this->point]);
        this->NegKernelWeight+=min(0.0,(*svm_weights)[this->point]);
    }
    for(int i=0;i<this->childs.size();++i)
    {
        PosKernelWeight+=((SVMKernelSumNode<Point>*)this->childs[i])->PosKernelWeight;
        NegKernelWeight+=((SVMKernelSumNode<Point>*)this->childs[i])->NegKernelWeight;
    }
    this->passedKernelSum=0.0;
    //Find the average and maximum distances
    for(;begin!=end;++begin)
    {
        if((*svm_weights)[begin->point]>0.0)
        {
            if(begin->distances.back()>max_pos_dist)
                max_pos_dist=begin->distances.back();
            avg_pos_dist+=(*svm_weights)[begin->point]*begin->distances.back();
        }
        else
        {
            if(begin->distances.back()>max_neg_dist)
                max_neg_dist=begin->distances.back();
            avg_neg_dist+=(*svm_weights)[begin->point]*begin->distances.back();
        }
    }
    avg_pos_dist/=PosKernelWeight;
    avg_neg_dist/=NegKernelWeight;
}

//Class for svm kernel sums
class SVMKernelSumFunctor
{
public:
    vector<double> predictions;
    vector<vector<double> > svm_points;
    vector<double> svm_weights;
    vector<vector<double> > pred_points;
    vector<int> pred_labels;
    double gamma;
    bool dist_construct_mode;
    bool use_avg_for_error;

    double distance(const int a,const int b) const
    {
        double res=0.0;
        if(dist_construct_mode)
            for(int i=0;i<svm_points[0].size();++i)
                res+=(svm_points[a][i]-svm_points[b][i])*(svm_points[a][i]-svm_points[b][i]);
        else
            for(int i=0;i<svm_points[0].size();++i)
                res+=(pred_points[a][i]-svm_points[b][i])*(pred_points[a][i]-svm_points[b][i]);
        return sqrt(gamma*res);
    }
    double Kernel(const int& a,const int& b,const double dist) const
    {
        return exp(-dist*dist)*svm_weights[b];
    }

    double Kernel(const int& a,const int& b) const
    {
        return Kernel(a,b,distance(a,b));
    }
    double kernelSumUpperBound(double max_dist,double avg_dist,double center_dist,double center_val) const
    {
        double turn_point=1.0/sqrt(2.0);
        if(turn_point>=center_dist)
        {
            //Concave
            return exp(-(center_dist-avg_dist)*(center_dist-avg_dist));
        }
        else
        {
            if(turn_point<=center_dist-max_dist)
            {
                //Convex
                return center_val+avg_dist/max_dist*(exp(-(center_dist-max_dist)*(center_dist-max_dist))-center_val);
            }
            else
            {
                //Complex :)
                double derivative=-2.0*(center_dist-max_dist)*exp(-(center_dist-max_dist)*(center_dist-max_dist));
                double max_val=exp(-(center_dist-max_dist)*(center_dist-max_dist));
                double y2=max(center_val,max_val+derivative*max_dist);
                return max_val+(y2-max_val)/max_dist*avg_dist;
            }
        }
    }
    double kernelSumLowerBound(double max_dist,double avg_dist,double center_dist,double center_val) const
    {
        double turn_point=1.0/sqrt(2.0);
        if(turn_point<=center_dist)
        {
            //Convex
            return exp(-(center_dist-avg_dist)*(center_dist-avg_dist));
        }
        else
        {
            if(turn_point>=center_dist+max_dist)
            {
                //Concave!
                return center_val+avg_dist/max_dist*(exp(-(center_dist+max_dist)*(center_dist+max_dist))-center_val);
            }
            else
            {
                //Complex :)
                double derivative=-2.0*(center_dist+max_dist)*exp(-(center_dist+max_dist)*(center_dist+max_dist));
                double min_val=exp(-(center_dist+max_dist)*(center_dist+max_dist));
                double y1=min(center_val,min_val-derivative*max_dist);
                double ret=min_val+(y1-min_val)/max_dist*avg_dist;
                return ret;
            }
        }
    }
    void getRangeLimits(int point,SVMKernelSumNode<int>* node,double dist,double &tmp_range_min,double& tmp_range_max) const
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
            double all_max_dist=max(node->max_pos_dist,node->max_neg_dist);
            double min_dist=dist-all_max_dist;
            double max_dist=dist+all_max_dist;
            if(min_dist<0)
                min_dist=0.0;
            double min_kernel=exp(-min_dist*min_dist);
            double max_kernel=exp(-max_dist*max_dist);

            min_pos=node->PosKernelWeight*max_kernel;
            max_pos=node->PosKernelWeight*min_kernel;
            min_neg=node->NegKernelWeight*max_kernel;
            max_neg=node->NegKernelWeight*min_kernel;
        }
        tmp_range_min=max_neg+min_pos;
        tmp_range_max=max_pos+min_neg;
    }
    double SubTreeKernelSum(const int& point,const SVMKernelSumNode<int>* node,const double dist) const
    {
        ++evaluations;
        return Kernel(point,node->point,dist)*(node->PosKernelWeight+node->NegKernelWeight);
    }
    double KernelError(const int& point,const SVMKernelSumNode<int>* node,const double dist) const
    {
        evaluations+=2;
        double all_max_dist=max(node->max_pos_dist,node->max_neg_dist);
        if(dist<all_max_dist)
            return 1000.0;
        double dist2=dist*dist;
        double center_val=exp(-dist*dist);
        double min_val=exp(-(dist-all_max_dist)*(dist-all_max_dist));
        double max_val=exp(-(dist+all_max_dist)*(dist+all_max_dist));
        return max(min_val-center_val,center_val-max_val);
    }
    double DualKernelError(const SVMKernelSumNode<int>* node1,SVMKernelSumNode<int>* node2,const double dist) const
    {
        evaluations+=2;
        double all_max_dist1=max(node1->max_pos_dist,node1->max_neg_dist);
        double all_max_dist2=max(node2->max_pos_dist,node2->max_neg_dist);
        if(dist<all_max_dist1+all_max_dist2)
            return 1000.0;
        double center_val=exp(-dist*dist);
        double min_dist=dist-all_max_dist1-all_max_dist2;
        double max_dist=dist+all_max_dist1+all_max_dist2;
        double min_val=exp(-min_dist*min_dist);
        double max_val=exp(-max_dist*max_dist);
        return max(min_val-center_val,center_val-max_val);
    }
    void AddKernelSumToPoint(const int p,double sum)
    {
        predictions[p]+=sum;
    }
};

class coverTreeTest : public CppUnit::TestFixture
{
    CPPUNIT_TEST_SUITE(coverTreeTest);
    CPPUNIT_TEST(testCoverTree);
    CPPUNIT_TEST(testApproxKernelSum);
    CPPUNIT_TEST(testDualApproxKernelSum);
    CPPUNIT_TEST(testSVMKernelSum);
    CPPUNIT_TEST_SUITE_END();
public:
    KernelSumFunctor kf;
    SVMKernelSumFunctor svm_kf;

    //For testing the invarients, get the biggest distance of a point to all points in a node
    double realMaxDist(MaxDistNode<int> *node,int p)
    {
        double res=kf.distance(node->point,p);
        for(int i=0;i<node->childs.size();++i)
            res=max(res,realMaxDist((MaxDistNode<int>*)node->childs[i],p));
        for(int i=0;i<node->zero_children.size();++i)
            res=max(res,kf.distance(node->zero_children[i],p));
        return res;
    }

    /* The three invariants of a cover tree:
     * 1. Nesting: C_i \in C_{i-1}
     * 2. Covering tree: \forall p \in C_{i-1} \exists q \in C_i s.t. d(p,q)<2^i and Node(q,i)=Parent(Node(p,i-1))
     * 3. Separation: \forall p,q \in C_i d(p,q) > 2^i
     *
     */
    //Test Invariant 1 & and 2 and other stuff that can be tested recursive
    void testInvariantsOneAndTwo(MaxDistNode<int> *node)
    {
        //1. Nesting (this node must be the first child)
        if(!node->childs.empty())
            CPPUNIT_ASSERT(node->point==node->childs[0]->point);
        //2. Covering: childs may not be more then 2^i away
        double dist=pow(2.0,node->level);
        CPPUNIT_ASSERT(node->max_dist<=dist*2.0);
        for(int i=0;i<node->childs.size();++i)
        {
            CPPUNIT_ASSERT(kf.distance(node->point,node->childs[i]->point)<=dist);
            CPPUNIT_ASSERT(node->level>node->childs[i]->level);
        }
        //2.B zero childs must be withing max dist
        for(int i=0;i<node->zero_children.size();++i)
            CPPUNIT_ASSERT(kf.distance(node->point,node->zero_children[i])<=node->max_dist);
        //2.C there are either zero childs or real children
        if(!node->zero_children.empty())
            CPPUNIT_ASSERT(node->childs.empty());
        //2.D if there are children, there is more than one
        if(!node->childs.empty())
            CPPUNIT_ASSERT(node->childs.size()+node->childs[0]->zero_children.size()>1);
        //4 Test that max dist is true!
        double real_max_dist=realMaxDist(node,node->point);
        CPPUNIT_ASSERT(fabs(node->max_dist-real_max_dist)<=0.0001);

        if(node->zero_children.empty())
        {
            for(int i=0;i<node->childs.size();++i)
                testInvariantsOneAndTwo((MaxDistNode<int>*)node->childs[i]);
        }
    }
    //Test invariant 3 (seperation)
    void testInvariantThree(MaxDistNode<int>* root_node)
    {
        vector<MaxDistNode<int>*> nodes_to_test;
        vector<MaxDistNode<int>*> tested_nodes;
        nodes_to_test.push_back(root_node);
        //3. Speration, all nodes of one level must be more the 2^(i-1) away
        while(!nodes_to_test.empty())
        {
            MaxDistNode<int>* node=nodes_to_test.back();
            nodes_to_test.pop_back();
            for(int i=0;i<tested_nodes.size();++i)
            {
                if(node->level==tested_nodes[i]->level)
                {
                    CPPUNIT_ASSERT(kf.distance(node->point,tested_nodes[i]->point)>=pow(2,node->level-1));
                }
            }
            tested_nodes.push_back(node);
            for(int i=0;i<node->childs.size();++i)
                nodes_to_test.push_back((MaxDistNode<int>*)node->childs[i]);
        }
    }
    //count the number of occurences of a certain point, not counting the self-childs
    int countOccurences(int point, MaxDistNode<int>* root_node,bool include_root_node)
    {
        int count=0;
        if(root_node->point==point && include_root_node)
            ++count;
        for(int i=0;i<root_node->zero_children.size();++i)
        {
            if(root_node->zero_children[i]==point)
                ++count;
        }
        for(int i=0;i<root_node->childs.size();++i)
        {
            count+=countOccurences(point,(MaxDistNode<int>*)root_node->childs[i],i!=0);
        }
        return count;
    }
    //Some extra tests for a good CoverTree
    void extraTests(MaxDistNode<int>* root_node)
    {
        //Test that every element occures only ones
        for(int i=0;i<kf.points.size();++i)
        {
            int o=countOccurences(i,root_node,true);
            CPPUNIT_ASSERT(o==1);
        }
    }


    void setUp()
    {
        //Create random data for kernel sum
        kf.gamma=10.0;
        ofstream o("points.txt");
        for(int i=0;i<NUM_SAMPLES;++i)
        {
            vector<double> point;
            for(int j=0;j<DIMS;++j)
            {
                double val=double(rand())/RAND_MAX;
                o<<val<<"\t";
                point.push_back(val);
            }
            kf.points.push_back(point);
            o<<std::endl;
        }
        o.close();
        //Load SVM data for svm sum
        load_libsvm_dataset("./svm_model",svm_kf.svm_weights,svm_kf.svm_points,true,&svm_kf.gamma);
        load_libsvm_dataset("./svm_test",svm_kf.pred_labels,svm_kf.pred_points);
        svm_weights=&svm_kf.svm_weights;
    }

    void testCoverTree()
    {
        //Construct the cover tree
        clock_t start=clock();
        std::vector<int> indexes(NUM_SAMPLES);
        for(int i=0;i<NUM_SAMPLES;++i)
            indexes[i]=i;
        CoverTree<MaxDistNode<int> > ct(indexes,kf);
        double time=double(clock()-start)/CLOCKS_PER_SEC;
        std::cerr<<"Build time: "<<time<<std::endl;
        //Test the invariants
        testInvariantsOneAndTwo(ct.RootNode);
        testInvariantThree(ct.RootNode);
        extraTests(ct.RootNode);
    }
    
    void testApproxKernelSum()
    {
        std::vector<int> indexes(NUM_SAMPLES);
        for(int i=0;i<NUM_SAMPLES;++i)
            indexes[i]=i;
        CoverTree<KernelSumNode<int> > ct(indexes,kf);
        evaluations=0;
        double max_error=0.0;
        for(int j=0;j<100;++j)
        {
            int index=rand() % NUM_SAMPLES;
            evaluations=0;
            double approx_sum=ct.absoluteErrorKernelSum(index,kf,epsilon);

            double correct_sum=0.0;
            for(int i=0;i<NUM_SAMPLES;++i)
                correct_sum+=kf.Kernel(index,i);
            if(fabs(approx_sum-correct_sum)>max_error)
                max_error=fabs(approx_sum-correct_sum);
            CPPUNIT_ASSERT(fabs(approx_sum-correct_sum)<=NUM_SAMPLES*epsilon);
        }
    }

    void testDualApproxKernelSum()
    {
        std::vector<int> indexes(NUM_SAMPLES);
        for(int i=0;i<NUM_SAMPLES;++i)
            indexes[i]=i;
        CoverTree<KernelSumNode<int> > ct(indexes,kf);
        kf.KernelSums.clear();
        kf.KernelSums.resize(NUM_SAMPLES,0.0);
        evaluations=0;
        ct.DualAbsoluteErrorKernelSum(ct,kf,epsilon);
        for(int j=0;j<NUM_SAMPLES;++j)
        {
            double correct_sum=0.0;
            for(int i=0;i<NUM_SAMPLES;++i)
                correct_sum+=kf.Kernel(j,i);
            CPPUNIT_ASSERT(fabs(correct_sum-kf.KernelSums[j])<=NUM_SAMPLES*epsilon);
        }
    }

    void testSVMKernelSum()
    {
        std::vector<int> indexes(svm_kf.svm_points.size());
        for(int i=0;i<svm_kf.svm_points.size();++i)
            indexes[i]=i;
        svm_kf.dist_construct_mode=true;
        CoverTree<SVMKernelSumNode<int> > ct(indexes,svm_kf);
        svm_kf.dist_construct_mode=false;

        svm_kf.predictions.clear();
        svm_kf.predictions.resize(svm_kf.pred_points.size(),0);

        for(int i=0;i<svm_kf.pred_points.size();++i)
        {
            svm_kf.use_avg_for_error=true;
            //std::cout<<"Doing approx sum"<<std::endl;
            double approx_sum_with_avg=ct.svmMarginKernelSum(i,svm_kf,0.5,0.1);
            svm_kf.use_avg_for_error=false;
            double approx_sum_wo_avg=ct.svmMarginKernelSum(i,svm_kf,0.5,0.1);
            double correct_sum=0.0;
            //std::cerr<<"Doing correct sum"<<std::endl;
            for(int j=0;j<svm_kf.svm_points.size();++j)
            {
                correct_sum+=svm_kf.Kernel(i,j);
            }
            std::cerr<<"Approx sum with avg="<<approx_sum_with_avg<<", approx sum wo avg="<<approx_sum_wo_avg<<", correct_sum="<<correct_sum<<std::endl;
            if(approx_sum_with_avg>=0.5)
                CPPUNIT_ASSERT(correct_sum>=0.4);
            if(approx_sum_with_avg<=-0.5)
                CPPUNIT_ASSERT(correct_sum<=-0.4);
            if(approx_sum_wo_avg>=0.5)
                CPPUNIT_ASSERT(correct_sum>=0.4);
            if(approx_sum_wo_avg<=-0.5)
                CPPUNIT_ASSERT(correct_sum<=-0.4);

            if(approx_sum_with_avg<0.5 && approx_sum_with_avg>-0.5)
            {
                CPPUNIT_ASSERT(fabs(approx_sum_with_avg-correct_sum)<0.1);
            }
            if(approx_sum_wo_avg<0.5 && approx_sum_wo_avg>-0.5)
            {
                CPPUNIT_ASSERT(fabs(approx_sum_wo_avg-correct_sum)<0.1);
            }
        }
    }
};

CPPUNIT_TEST_SUITE_REGISTRATION(coverTreeTest);

int main( int argc, char **argv)
{
    CppUnit::TextUi::TestRunner runner;
    CppUnit::TestFactoryRegistry &registry = CppUnit::TestFactoryRegistry::getRegistry();
    runner.addTest( registry.makeTest() );
    runner.setOutputter( new CppUnit::CompilerOutputter( &runner.result(),std::cerr ) );
    runner.run();
    return 0;
}

