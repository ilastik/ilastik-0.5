#include <math.h>
#include <assert.h>
#include "Node.hxx"
#include <time.h>
#include <vector>
#include <queue>

#ifndef COVER_TREE_INCLUDED
#define COVER_TREE_INCLUDED

/* The three invariants of a cover tree:
 * 1. Nesting: C_i \in C_{i-1}
 * 2. Covering tree: \forall p \in C_{i-1} \exists q \in C_i s.t. d(p,q)<2^i and Node(q,i)=Parent(Node(p,i-1))
 * 3. Separation: \forall p,q \in C_i d(p,q) > 2^i
 *
 */

//#define OLD_IMPLEMENTATION

/** Helper structure for creating a CoverTree.
 *
 * This structure stores a point and a stack of all the distances to nodes above.
 */
template<class Point>
struct point_with_distances
{
    Point point;
    /** Stack of all distances to nodes above.*/
    std::vector<double> distances;
};

/** Helper function for removing from a std::vector<point_with_distances>
 * 
 * The function makes sure, that the distances stack is swapped, not copied.
 * It does not preserve the order in the vector.
 * @param a The vector from which an element is to be removed.
 * @param index The index of the element to remove.
 */
template<class Point>
inline void remove(std::vector<point_with_distances<Point> >& a,int index)
{
    std::swap(a[index].point,a.back().point);
    a[index].distances.swap(a.back().distances);
    a.pop_back();
}

/** CoverTree class.
 *
 * A cover tree is a tree with 3 invariants:
 * 1. (Inclusion): Every point at level i also appears at level i-1
 * 2. (Covering): The distance between a node at level i and its parents is at moste 2^(i+1)
 * 3. (Separation): All nodes at level i have a minimal distance of 2^i
 *
 * The interface requirements of Node are described by the Node class. If the
 * absoluteErrorKernelSum or DualAbsoluteErrorKernelSum functions are to be
 * used, the interface requirements also include the interface of
 * KernelSumNode.*/
template<class Node>
class CoverTree
{
public:
    /** Take over the point type from the node.*/
    typedef typename Node::point_type Point;
    /** Construct a cover tree.
     *
     * The DistFunctor must have a function "distance", which takes 2 points
     * and returns the distance between them.
     *
     * @param points array of points to construct the CoverTree from.
     * @param dist_functor instance with a "distance" function.
     * @param max_points The minimal number of points in a node, for which construction continues.
     * @param min_level The minimal level in the tree.
     */
    template<class DistFunctor,class array>
    CoverTree(array& points,const DistFunctor& dist_functor,int max_points=3,int min_level=-1000);


    /**Calculates the kernel sum for a point with a given maximal error.
     *
     * The error will not be bigger than epsilon*pointsInTree.
     * The required interface for the Functor is:
     *   - distance: The distance between point (first argument) and a point in the cover tree (second argument)
     *   - Kernel: The kernel value between point (first argument) and a point in the cover tree (second argument)
     *   - KernelError: The maximal error between point (first argument) and any point below node (seond argument) given a known distance (third argument)
     *   - SubTreeKernelSum: The approximated kernel sum for point (first argument) in the subtree below node (second argument)
     *
     * @param point The point to calculate the sum for.
     * @param functor The functor fulfilling the interface above.
     * @param epsilon The error bound.
     * @return The approximated kernel sum.
     */
    template<class Functor,class inPoint>
    double absoluteErrorKernelSum(const inPoint& point,const Functor& functor,double epsilon,double bias=0.0);
    /** Calculates the kernel sum for all points in a CoverTree given another CoverTree.
     *
     * The error will not be bigger than epsilo*pointInTree
     * The required interface for the Functor is:
     *   - distance: The distance between point (first argument) and a point in the cover tree (second argument)
     *   - Kernel: The kernel value between point (first argument) and a point in the cover tree (second argument)
     *   - DualKernelError: The maximal error between any point below node1 form the point tree (first argument) and any point below node2 (seond argument) given a known distance (third argument)
     *   - SubTreeKernelSum: The approximated kernel sum for point (first argument) in the subtree below node (second argument).
     *   - AddKernelSumToPoint: Add a given kenrel sum to point of the cover tree.
     *
     *   @param evalCoverTree The cover tree containing the points for which the sum should be evaluated.
     *   @param functor The functor fulfilling the interface above.
     *   @param epsilon The error bound.
     */
    template<class Functor,class Node2>
    void DualAbsoluteErrorKernelSum(CoverTree<Node2>& evalCoverTree,Functor& functor,double epsilon,double bias=0.0);

    //**********************************************************************
    // Helper function
    //**********************************************************************

    /** Internal recursive implementation of the creation of the CoverTree.*/
    template<class DistFunctor,class array>
    Node* recursive_create_cover_tree_imp(Point& root_point,
                                                       int level,double max_dist,
                                                       array& points,
                                                       const int range_min,
                                                       const int range_max,
                                                       int &consumed_limit,
                                                       const DistFunctor& dist_functor);

    /** calculate the level, specified by the distance.
     *
     * @param dist The distance to get the level from.
     * @return The desired level.
     */
    int getLevelFromDist(double dist);
     
    /** Helper function for recursive_create_cover_tree_imp.
     *
     * Moves all points, which can be included by level into close_points and
     * returns the maximal distance of them.
     * @param points_to_insert The set of points to split from.
     * @param close_points The set of points to insert close points to.
     * @param level The level defining the slit distance.
     * @param max_dist The preset maximal distance, of which the return value may not be lower.
     * @return the maximal distance of any point in close_points.
     */
    template<class array>
    double split_close_points(array &points,int range_min,int range_max,int& split_point,int level,double max_dist=0.0);
    
    /**Helper function for recursive_create_cover_tree_imp.
     *
     * Same as split_close_points but also calculates the distances and inserts
     * them into the stack of the points returned in out_points.*/
    template<class array,class DistFunctor>
    double split_close_points_with_dist(Point& point,array& points,int range_min,int range_max,int& split_point,bool close_to_end,int level,const DistFunctor &df,double max_dist=0.0);

    /** Helper function for DualAbsoluteErrorKernelSum.
     *
     * Evaluates the kernel between all nodes below currentNode1 and currentNode2 and adds the to the points.
     * @param currentNode1 node of the kernel points CoverTree.
     * @param currentNode2 node of the CoverTree containing the points to evaluate.
     * @param passedKernelSum addition sum to add to all points.
     * @param functor The functor fulfilling the interface specified in DualAbsoluteErrorKernelSum.*/
    template<class Functor,class Node2>
    void DualRestEvaluate(Node *currentNode1,Node2* currentNode2,double passedKernelSum,Functor& functor);

    /** Helper function for DualAbsoluteErrorKernelSum.
     *
     * Adds the kernelSum to all points below currentNode2.
     * @param currentNode2 node of the CoverTree containing the points to evaluate.
     * @param kernelSum Sum to add to the points.
     * @param functor The functor fulfilling the interface specified in DualAbsoluteErrorKernelSum.*/
    template<class Functor,class Node2>
    void DualPushKernelSum(Node2* currentNode2,double kernelSum,Functor& functor);
    /**The top level node.*/
    Node* RootNode;

    /**Stored parameter from the constructor.*/
    int min_level;
    /**Stored parameter from the constructor.*/
    int max_points;
    //Testing
    template<class Functor,class inPoint>
    double svmMarginKernelSum(const inPoint& point,const Functor& functor,double epsilon,double delta,double bias=0.0);
};

template<class Point,class Node,class DistFunctor>
double getMaxDist(Point& point,Node* node,const DistFunctor& df)
{
    double res=df.distance(node->point,point);
    for(int i=0;i<node->zero_children.size();++i)
    {
        res=max(res,df.distance(node->zero_children[i],point));
    }
    for(int i=0;i<node->childs.size();++i)
        res=max(res,getMaxDist(point,node->childs[i],df));
    return res;
}

/**Construct the cover tree.
 */
template<class Node>
template<class DistFunctor,class array>
CoverTree<Node>::CoverTree(array& points,const DistFunctor& dist_functor,int max_points,int min_level)
{
    this->min_level=min_level;
    this->max_points=max_points;
    RootNode=0;
    //Find out all distances to points[0] and the maximum
    double max_dist=0.0;
    std::vector<point_with_distances<Point> > points_to_insert;
    points_to_insert.resize(points.size()-1);
    for(int i=1;i<points.size();++i)
    {
        points_to_insert[i-1].point=points[i];
        points_to_insert[i-1].distances.push_back(dist_functor.distance(points[0],points[i]));
        if(points_to_insert[i-1].distances.back()>max_dist)
            max_dist=points_to_insert[i-1].distances.back();
    }
#ifndef OLD_IMPLEMENTATION
    int start_level=getLevelFromDist(max_dist)+1;
#else
    int start_level=getLevelFromDist(max_dist);
#endif
    clock_t start=clock();
    int range_min=0;
    int range_max=points_to_insert.size();
    int consumed_range=0;
    RootNode=recursive_create_cover_tree_imp(points[0],start_level,max_dist,points_to_insert,range_min,range_max,consumed_range,dist_functor);
    std::cerr<<"Constructing basic cover tree took:"<<double(clock()-start)/CLOCKS_PER_SEC<<std::endl;

    start=clock();
    //FillDistances(RootNode,dist_functor);
    //std::cerr<<"Fill distances took:"<<double(clock()-start)/CLOCKS_PER_SEC<<std::endl;
    assert(range_max==consumed_range);
}

template<class array>
void swap_distpoints(array& points,int a,int b)
{
    std::swap(points[a].point,points[b].point);
    points[a].distances.swap(points[b].distances);
}

#ifndef OLD_IMPLEMENTATION
template<class Node>
template<class DistFunctor,class array>
Node* CoverTree<Node>::recursive_create_cover_tree_imp(Point& root_point,
                                                       int level,double max_dist,
                                                       array& points,
                                                       const int range_min,
                                                       const int range_max,
                                                       int &consumed_limit,
                                                       const DistFunctor& dist_functor)
{
    //We are now concerned only about the points between range_min and range_max. We will set the consumed limit such that
    //range_min-consumed are the consumed points and cosnumed_limit-range_max are the not touched points
    Node *root_node=new Node(root_point,level);
    //Are we at the lowest level?
    if(range_max-range_min<=max_points || level<=min_level)
    {
        for(int i=range_min;i<range_max;++i)
            root_node->zero_children.push_back(points[i].point);
        consumed_limit=range_max;
        root_node->finalizeNode(points.begin()+range_min,points.begin()+range_max);
        return root_node;
    }
    //My current level is choosen ,so that everything fits into 2^(level+1) => getLevelFromDist<=level
    int new_level=level-1;
    //Split our range, such that range_min-must_consume could be inserted in this child, and must_consume-range_max is not touched for sure
    int must_consume_limit;
    double new_max_dist=split_close_points(points,range_min,range_max,must_consume_limit,new_level+1);
    Node* child_node=recursive_create_cover_tree_imp(root_point,
                                                     new_level,new_max_dist,
                                                     points,
                                                     range_min,must_consume_limit,
                                                     consumed_limit,
                                                     dist_functor);
    //Now, everything form range_min-cosumed_limit is consumed,everythong from consumed_limit-must_consume_limit must be consumed
    //(because it can not co-exist on this level with other nodes) and must_consume_limit-range_max is untouched
    if(must_consume_limit==consumed_limit)
    {
        //Nothing else to consume, yeah!
        delete root_node;
        return child_node;
    }
    //Add the firs child
    root_node->addChild(child_node);
    //While there are points to consume
    //The order are: [consumed | must_consume | untouched] within points
    while(must_consume_limit!=consumed_limit)
    {
        //The points we must consume are also points, that do not at all conflict below
        //use the first as out new point
        Point new_root_point=points[consumed_limit].point;
        assert(dist_functor.distance(new_root_point,root_point)<=pow(2.0,level));
        //Add it to the consumed set
        ++consumed_limit;
        //Find out which are close enough to be candidates and also add the distance to the new root point
        //For this we split "must_consume", so that consume candidates from "must_consume" are at the end and
        //consume candidates from not_inserted are at the beginning of not inserted
        //[consumed | must_consume | must_consume && insert_candidates | not_inserted && insert_candidates | not inserted]
        int new_range_min,new_range_max;
        new_max_dist=split_close_points_with_dist(new_root_point,
                                                  points,
                                                  consumed_limit,
                                                  must_consume_limit,
                                                  new_range_min,
                                                  true, //For putting close points at the latter part
                                                  new_level+1,dist_functor);
        new_max_dist=split_close_points_with_dist(new_root_point,
                                                  points,
                                                  must_consume_limit,
                                                  range_max,
                                                  new_range_max,
                                                  false, //For putting close points at the former part
                                                  new_level+1,dist_functor,new_max_dist);
        //Try to insert
        int new_consumed_limit;
        child_node=recursive_create_cover_tree_imp(new_root_point,
                                                   new_level,
                                                   new_max_dist,
                                                   points,
                                                   new_range_min,
                                                   new_range_max,
                                                   new_consumed_limit,
                                                   dist_functor);
        root_node->addChild(child_node);
        //Add the consumed ones to our consumed list
        for(int i=new_range_min;i<new_consumed_limit;++i)
        {
            points[i].distances.pop_back();
            swap_distpoints(points,consumed_limit,i);
            ++consumed_limit;
        }
        //Now we must split the returned new candidates between those which still have to be consumed and can be returned
        //(they are between new_consumed_limit and new_range-max)
        // -> insert_candidates is the set we will return
        // -> must_consume is the set we still have to consume
        double must_consume_threshold=pow(2.0,level);
        while(new_consumed_limit!=new_range_max)
        {
            points[new_consumed_limit].distances.pop_back();
            if(points[new_consumed_limit].distances.back()>must_consume_threshold)
            {
                //Put it into not inserted set
                --new_range_max;
                swap_distpoints(points,new_consumed_limit,new_range_max);
            }
            else
            {
                //Make sure it will end up in must_cosnume
                ++new_consumed_limit;
            }
        }
        must_consume_limit=new_consumed_limit;
    }
    //Set the maximum distance
    root_node->finalizeNode(points.begin()+range_min,points.begin()+consumed_limit);
    return root_node;
}

#else
/** Recursive construct a cover tree.
 * The three template parameters are and must fullfill:
 * Point: class for a point in the tree. Must be swapable, and it should be possible to efficiently
 *
 *
 * */
template<class Node>
template<class DistFunctor, class array>
Node* CoverTree<Node>::recursive_create_cover_tree_imp(Point& point,int level,double max_dist,array& points_to_insert,const DistFunctor& dist_functor)
{
    //We create the childs of root_node. The level of the childs is at maximum root_node.level-1, and the maximum distance to the root node point of all points is root_node.max_dist
    Node* root_node=new Node(point,level);
    root_node->max_dist=max_dist;
    if(points_to_insert.size()<=max_points || level<=min_level)
    {
        for(int i=0;i<points_to_insert.size();++i)
            root_node->zero_children.push_back(points_to_insert[i].point);
        root_node->finalizeNode();
        return root_node;
    }
    //We already know one sure child -> the same child (with root_point as point)
    //Split off all points, it can not cover in the next level
    array close_points;
    double child_max_dist=split_close_points(points_to_insert,close_points,level-1);
    //With our way of calculating the level, it can not be that there are no unhandled points
    assert(!points_to_insert.empty());
    //Make all remaining points to insert the problem of the next level (they can be handled for sure)
    int child_level=getLevelFromDist(child_max_dist);

    assert(child_level<level);

    Node* child_node=recursive_create_cover_tree_imp(point,child_level,child_max_dist,close_points,dist_functor);
    root_node->addChild(child_node);

    //OK, create the nodes based on the rest of the points
    while(!points_to_insert.empty())
    {
        //Empty the close points
        close_points.clear();
        //Pick some (well choosen) point as the root point
        Point new_root_point=points_to_insert[0].point;
        remove(points_to_insert,0);
        //We need the distances to this point
        recalculate_distances(new_root_point,points_to_insert,dist_functor);

        child_max_dist=split_close_points(points_to_insert,close_points,level-1);
        child_level=getLevelFromDist(child_max_dist);

        child_node=recursive_create_cover_tree_imp(new_root_point,child_level,child_max_dist,close_points,dist_functor);
        root_node->addChild(child_node);
    }
    root_node->finalizeNode();
    return root_node;
}
#endif

template<class Node>
template<class array,class DistFunctor>
double CoverTree<Node>::split_close_points_with_dist(Point& point,array& points,int range_min,int range_max,int& split_point,bool close_to_end,int level,const DistFunctor &df,double max_dist)
{
    double split_dist=pow(2.0,level);

    int i=0;
    split_point=range_min;
    while(split_point!=range_max)
    {
        double dist=df.distance(point,points[split_point].point);
        if(dist<=split_dist)
        {
            if(dist>max_dist)
                max_dist=dist;
            points[split_point].distances.push_back(dist);
        }
        //Check which set to insert
        if( (dist<=split_dist) != close_to_end)
        {
            //Put to start
            ++split_point;
        }
        else
        {
            //Put to end
            --range_max;
            swap_distpoints(points,split_point,range_max);
        }
    }
    return max_dist;
}

template<class Node>
template<class array>
double CoverTree<Node>::split_close_points(array &points,int range_min,int range_max,int &split_point,const int level,double max_dist)
{
    double split_dist=pow(2.0,level);

    split_point=range_min;
    while(split_point!=range_max)
    {
        if(points[split_point].distances.back()>split_dist)
        {
            //Insert into far points
            --range_max;
            swap_distpoints(points,split_point,range_max);
        }
        else
        {
            if(points[split_point].distances.back()>max_dist)
                max_dist=points[split_point].distances.back();
            ++split_point; //Insert into close points
        }
    }
    return max_dist;
}

/*template<class Node>
template<class array,class DistFunctor>
void CoverTree<Node>::recalculate_distances(Point& point,array& points_to_insert,const DistFunctor& dist_functor)
{
    for(int i=0;i<points_to_insert.size();++i)
    {
        points_to_insert[i].distance=dist_functor.distance(point,points_to_insert[i].point);
    }
}*/

template<class Node>
int CoverTree<Node>::getLevelFromDist(double dist)
{
   int res=ceil(log(dist)/log(2.0));
   return res;
}

template<class Node>
struct svmMarginStackEntry
{
    svmMarginStackEntry(Node* n,double d,double rmin,double rmax)
    {node=n;dist=d;range_min=rmin;range_max=rmax;}
    Node* node;
    double dist;
    double range_min;
    double range_max;
};

template<class Node>
class CompareFunctor
{
public:
    bool operator()(svmMarginStackEntry<Node>& x,svmMarginStackEntry<Node>& y)
    {
        return (x.range_max-x.range_min)<(y.range_max-y.range_min);
    }
};

template<class Node>
template<class Functor,class inPoint>
double CoverTree<Node>::svmMarginKernelSum(const inPoint& point,const Functor& functor,double epsilon,double delta,double bias)
{
    std::priority_queue<svmMarginStackEntry<Node>,std::vector<svmMarginStackEntry<Node> >,CompareFunctor<Node> > queue;
    double range_min=0.0;
    double range_max=0.0;
    double distance=functor.distance(point,RootNode->point);
    functor.getRangeLimits(point,RootNode,distance,range_min,range_max);
    queue.push(svmMarginStackEntry<Node>(RootNode,distance,range_min-bias,range_max-bias));
    Node* currentNode;
    while(!queue.empty())
    {
        //Remove this one
        svmMarginStackEntry<Node> s=queue.top();
        queue.pop();
        range_min-=s.range_min;
        range_max-=s.range_max;
        distance=s.dist;
        currentNode=s.node;
        //Can we go deeper?
        if(!currentNode->childs.empty())
        {
            double tmp_range_min,tmp_range_max;
            for(int i=0;i<currentNode->childs.size();++i)
            {
                double dist=(i==0)?distance:functor.distance(point,currentNode->childs[i]->point);
                functor.getRangeLimits(point,(Node*)currentNode->childs[i],dist,tmp_range_min,tmp_range_max);
                queue.push(svmMarginStackEntry<Node>((Node*)currentNode->childs[i],dist,tmp_range_min,tmp_range_max));
                range_min+=tmp_range_min;
                range_max+=tmp_range_max;
            }
        }
        else
        {
            //Nothing to do but adding the kernel sums
            double k=functor.Kernel(point,currentNode->point,distance);
            range_min+=k;
            range_max+=k;
            for(int i=0;i<currentNode->zero_children.size();++i)
            {
                k=functor.Kernel(point,currentNode->zero_children[i]);
                range_min+=k;
                range_max+=k;
            }
        }
        //Stop if the range is exact enough
        if(range_min>=epsilon || range_max<=-epsilon || (range_max-range_min)<=delta)
        {
            //std::cerr<<"Breaking"<<std::endl;
            //std::cerr<<"range_min="<<range_min<<std::endl;
            //std::cerr<<"range_max="<<range_max<<std::endl;
            break;
        }
    }
    //std::cerr<<"Returning"<<std::endl;
    //std::cerr<<"range_min="<<range_min<<std::endl;
    //std::cerr<<"range_max="<<range_max<<std::endl;
    return (range_min+range_max)/2.0;
}

template<class Node>
struct absoluteErrorStackEntry
{
    absoluteErrorStackEntry(Node* n,double d)
    {node=n;dist=d;}
    Node* node;
    double dist;
};


template<class Node>
template<class Functor,class inPoint>
double CoverTree<Node>::absoluteErrorKernelSum(const inPoint& point,const Functor& functor,double epsilon,double bias)
{
    double sum=bias;
    std::vector<absoluteErrorStackEntry<Node> > stack;
    stack.push_back(absoluteErrorStackEntry<Node>(RootNode,functor.distance(point,RootNode->point)));

    while(!stack.empty())
    {
        Node* currentNode=stack.back().node;
        double currentDist=stack.back().dist;
        stack.pop_back();
        //Check all children
        int i;
        if(!currentNode->childs.empty())
        for(i=0;i<currentNode->childs.size();++i)
        {
            double dist=(i==0)?currentDist:functor.distance(point,currentNode->childs[i]->point);
            if(functor.KernelError(point,(Node*)currentNode->childs[i],dist) >= epsilon)
                stack.push_back(absoluteErrorStackEntry<Node>((Node*)currentNode->childs[i],dist));
            else
            {
                sum+=functor.SubTreeKernelSum(point,(Node*)currentNode->childs[i],dist);
            }
        }
        else
        {
            //All the way down! At everything
            for(int i=0;i<currentNode->zero_children.size();++i)
            {
                sum+=functor.Kernel(point,currentNode->zero_children[i]);
            }
            sum+=functor.Kernel(point,currentNode->point,currentDist);
        }
    }
    return sum;
}

template<class Node1,class Node2>
struct DualAbsoluteErrorStackEntry
{
    DualAbsoluteErrorStackEntry(Node1* n1,Node2* n2,double d)
    {node1=n1;node2=n2;dist=d;}
    Node1* node1;
    Node2* node2;
    double dist;
};

template<class Node>
template<class Functor,class Node2>
void CoverTree<Node>::DualRestEvaluate(Node *currentNode1,Node2* currentNode2,double passedKernelSum,Functor& functor)
{
    if(currentNode2->childs.empty())
    {
        //Add for own point
        functor.AddKernelSumToPoint(currentNode2->point,passedKernelSum+functor.Kernel(currentNode2->point,currentNode1->point));
        for(int i=0;i<currentNode1->zero_children.size();++i)
        {
            functor.AddKernelSumToPoint(currentNode2->point,functor.Kernel(currentNode2->point,currentNode1->zero_children[i]));
        }
        //Add to all zero childrens
        for(int j=0;j<currentNode2->zero_children.size();++j)
        {
            functor.AddKernelSumToPoint(currentNode2->zero_children[j],passedKernelSum+functor.Kernel(currentNode2->zero_children[j],currentNode1->point));
            for(int i=0;i<currentNode1->zero_children.size();++i)
                functor.AddKernelSumToPoint(currentNode2->zero_children[j],functor.Kernel(currentNode2->zero_children[j],currentNode1->zero_children[i]));
        }
    }
    else
    {
        for(int i=0;i<currentNode2->childs.size();++i)
            DualRestEvaluate(currentNode1,(Node2*)currentNode2->childs[i],passedKernelSum,functor);
    }
}

template<class Node>
template<class Functor,class Node2>
void CoverTree<Node>::DualPushKernelSum(Node2* currentNode2,double kernelSum,Functor& functor)
{
    if(currentNode2->childs.empty())
    {
        functor.AddKernelSumToPoint(currentNode2->point,kernelSum);
        for(int j=0;j<currentNode2->zero_children.size();++j)
        {
            functor.AddKernelSumToPoint(currentNode2->zero_children[j],kernelSum);
        }
    }
    else
    {
        for(int i=0;i<currentNode2->childs.size();++i)
            DualPushKernelSum(currentNode2->childs[i],kernelSum,functor);
    }
}


template<class Node>
template<class Functor,class Node2>
void CoverTree<Node>::DualAbsoluteErrorKernelSum(CoverTree<Node2>& evalCoverTree,Functor& functor,double epsilon,double bias)
{
    std::vector<DualAbsoluteErrorStackEntry<Node,Node2> > stack;
    evalCoverTree.RootNode->passedKernelSum=bias;
    stack.push_back(DualAbsoluteErrorStackEntry<Node,Node2>(RootNode,evalCoverTree.RootNode,functor.distance(evalCoverTree.RootNode->point,RootNode->point)));
    Node* currentNode1;
    Node2* currentNode2;
    double currentDist;

    while(!stack.empty())
    {
        currentNode1=stack.back().node1;
        currentNode2=stack.back().node2;
        currentDist=stack.back().dist;
        stack.pop_back();

        if(currentNode1->childs.empty())
        {
            //Rest evaluate everythin in currentNode2
            DualRestEvaluate(currentNode1,currentNode2,currentNode2->passedKernelSum,functor);
            //passedKernelSum has been taking care of
            currentNode2->passedKernelSum=0.0;
        }
        else
        {
            //SOLVED BUG: if currentNode2 has not children, we have to go down in current Node1
            if(currentNode2->level<currentNode1->level || currentNode2->childs.empty())
            {
                //Go down in currentNode1.level
                //using this variable, we make the passed_kernel_sum will reach its points
                bool node2_pushed=false;
                for(int i=0;i<currentNode1->childs.size();++i)
                {
                    double dist=(i==0)?currentDist:functor.distance(currentNode2->point,((Node*)currentNode1->childs[i])->point);
                    if(functor.DualKernelError(currentNode2,(Node*)currentNode1->childs[i],dist)>epsilon)
                    {
                        stack.push_back(DualAbsoluteErrorStackEntry<Node,Node2>((Node*)currentNode1->childs[i],currentNode2,dist));
                        node2_pushed=true;
                    }
                    else
                    {
                        //Add down in current Node2 the sum
                        currentNode2->passedKernelSum+=functor.SubTreeKernelSum(currentNode2->point,(Node*)currentNode1->childs[i],dist);
                    }
                }
                //if(node2_pushed==false)
                {
                    //make sure the passed kernel sum reaches its destination
                    if(currentNode2->passedKernelSum!=0.0)
                    {
                        DualPushKernelSum(currentNode2,currentNode2->passedKernelSum,functor);
                        currentNode2->passedKernelSum=0.0;
                    }
                }
            }
            else
            {
                //Go down in currentNode2.level
                for(int i=0;i<currentNode2->childs.size();++i)
                {
                    double dist=(i==0)?currentDist:functor.distance(((Node2*)currentNode2->childs[i])->point,currentNode1->point);
                    ((Node2*)currentNode2->childs[i])->passedKernelSum+=currentNode2->passedKernelSum;
#if 0
                    stack.push_back(DualAbsoluteErrorStackEntry<Node,Node2>(currentNode1,((Node2*)currentNode2->childs[i]),dist));
#else
                    if(functor.DualKernelError((Node2*)currentNode2->childs[i],currentNode1,dist)>epsilon)
                    {
                        stack.push_back(DualAbsoluteErrorStackEntry<Node,Node2>(currentNode1,((Node2*)currentNode2->childs[i]),dist));
                    }
                    else
                    {
                        //Well, prune this child
                        DualPushKernelSum(((Node2*)currentNode2->childs[i]),
                                          ((Node2*)currentNode2->childs[i])->passedKernelSum+functor.SubTreeKernelSum(currentNode2->childs[i]->point,currentNode1,dist),
                                          functor);
                        currentNode2->childs[i]->passedKernelSum=0.0;
                    }
#endif
                }
                //Since out KernelSum has been passed, reset it
                currentNode2->passedKernelSum=0.0;
            }
        }
    }
}

#endif

