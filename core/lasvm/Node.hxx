#include<stdexcept>

#ifndef COVER_TREE_NODE_INCLUDED
#define COVER_TREE_NODE_INCLUDED

/** Base class for a node in the cover tree.
 *
 * The "Node" template parameter of CoverTree can be of any type. But most of
 * the function of the required interface are unlikely to be reimplemented
 * differently. There are no requirements to the Point template parameter. But
 * it should be fastly copyable.*/
template<class Point,class SubType>
class Node
{
public:
    /** We inform the cover tree about the type of a point*/
    typedef Point point_type;

    /** The point associated with this node.*/
    Point point;

    /**Construct that node and simply copy the parameters.
     *
     * @param point The point to be used for the node.
     * @param level the level at which the node is inserted.
     * @param max_dist The maximal distance of anything below.
     */
    Node(Point& point,int level);
    virtual ~Node();

    /**Add a child to the set of childs.
     *
     * @param c The subtree-child to be inserted.*/
    void addChild(SubType* c);

    /**The level in the tree.*/
    int level;
    /**For the DualAbsoluteErrorKernelSum, the kernel sum mussed be passed down
     * the cover tree. That is done in this variable.*/
    double passedKernelSum;
    /** List of children.*/
    std::vector<SubType* > childs;
    /** List of points that stay within this level, because we reached the
     * minimum level are the minimal number of points.*/
    std::vector<Point> zero_children;
    /** When a node is finish (no children will be added anymore), this
     * function is called. It does nothing in this base implementation.*/
    template<class iterator>
    void finalizeNode(iterator begin,iterator end)
    {
        std::runtime_error("function finalizeNode() not defined");
    }
};

template<class Point,class SubType>
Node<Point,SubType>::Node(Point& point,int level)
{
    this->point=point;
    this->level=level;
    childs.clear();
}

template<class Point,class SubType>
Node<Point,SubType>::~Node()
{
    for(int i=0;i<childs.size();++i)
        delete childs[i];
    childs.clear();
}

template<class Point,class SubType>
void Node<Point,SubType>::addChild(SubType* c)
{
    childs.push_back(c);
}

/** Node class, adding the information of the maximum distant child to the base node.
 * Most error functors should expect this node instead of the base node.
 */
template<class Point>
class MaxDistNode : public Node<Point,MaxDistNode<Point> >
{
public:
    /** We inform the cover tree about the type of a point*/
    typedef Point point_type;
    typedef Node<Point,MaxDistNode<Point> > BT;
    /**Construct that node and simply copy the parameters.
     *
     * @param point The point to be used for the node.
     * @param level the level at which the node is inserted.
     */
    MaxDistNode(Point& point,int level) : BT(point,level){}

    double max_dist;

    /** When a node is finish (no children will be added anymore), this
     * function is called. It finds the maximum distance of any child.*/
    template<class iterator>
    void finalizeNode(iterator begin,iterator end)
    {
        max_dist=0.0;
        while(begin!=end)
        {
            if(begin->distances.back()>max_dist)
                max_dist=begin->distances.back();
            ++begin;
        }
    }
};

/** Node class which can be used for calculation approximated kernel sums (CoverTree::absoluteErrorKernelSum).
 *
 * This class only works for kernel sums, where every kernel is weighted by one.
 */
template<class Point>
class KernelSumNode : public MaxDistNode<Point>
{
public:
    /** We inform the cover tree about the type of a point*/
    typedef Point point_type;
    KernelSumNode(Point& point,int level) : MaxDistNode<Point>(point,level){}
    /** Number points below this node.*/
    int KernelWeight;
    /** Calculates the final KernelWeight.*/
    template<class iterator>
    void finalizeNode(iterator begin,iterator end);
};

template<class Point>
template<class iterator>
void KernelSumNode<Point>::finalizeNode(iterator begin,iterator end)
{
    MaxDistNode<Point>::finalizeNode(begin,end);
    //Our kernel weight is the sum of of the KernelWeight below us.
    KernelWeight=0;
    if(this->childs.empty())
        KernelWeight=1+this->zero_children.size();
    for(int i=0;i<this->childs.size();++i)
    {
        KernelWeight+=((KernelSumNode<Point>*)this->childs[i])->KernelWeight;
    }
    this->passedKernelSum=0.0;
}

#endif
