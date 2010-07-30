#ifndef GARBAGE_VECTOR_INCLUDED
#define GARBAGE_VECTOR_INCLUDED

/**
 */
#include<vector>
#include<list>
#include<algorithm>
#include<assert.h>

template<class type>
class garbage_vector
{
    std::vector<type> vector;
    std::list<int> unused_elements;
public:
    size_t size() const;
    int getFreeIndex();
    void freeIndex(int index);
    type& operator[](int index);
    const type& operator[](int index) const;
};

template<class type>
size_t garbage_vector<type>::size() const
{
    return vector.size();
}

template<class type>
int garbage_vector<type>::getFreeIndex() 
{
    int result;
    if(unused_elements.empty())
    {
        result=vector.size();
        vector.resize(result+1);
    }
    else
    {
        result=unused_elements.front();
        unused_elements.pop_front();
    }
    return result;
}

template<class type>
void garbage_vector<type>::freeIndex(int index)
{
    unused_elements.push_back(index);
}

template<class type>
type& garbage_vector<type>::operator[](int index)
{
    return vector[index];
}

template<class type>
const type& garbage_vector<type>::operator[](int index) const
{
    return vector[index];
}

#endif 
