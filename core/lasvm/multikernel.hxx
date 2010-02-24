#include <stdlib.h>
#include <vector>
#include <list>
#include <iostream>
#include <math.h>
#include <assert.h>

using namespace std;

template<class T>
inline void swap(T &a,T &b)
{
	T tmp = a;
	a     = b;
	b     = tmp;
}

//A row in the kernel cache, holding all the sub-kernel results and the weighted sum
template<class T>
class MultiKernelCacheRow
{
	friend class vector<T>;
public:
	vector<vector<T> > SubKernelRows;
	vector<T> WeightedRow;	
private:
	MultiKernelCacheRow(int num_subkernels);
	MultiKernelCacheRow(const MultiKernelCacheRow<T>& c);
	int num_SubKernels;
	vector<bool> SubKernelRowDirty;
	bool AnySubKernelRowDirty; //or of all of the above
	bool WeightedRowDirty;
	void WeightsChanged();
	void SubKernelChanged(int index);
	void swap(MultiKernelCacheRow<T>& other);
	void clear();
	void resize(int size);
	void FillTransposed(int other_index,int my_index,MultiKernelCacheRow& row);

	class ElementProxy
	{
	public:
		MultiKernelCacheRow<T>* father;
		int elementIndex;	
		ElementProxy(MultiKernelCacheRow<T>* f,int i)
		{
			father       = f;
			elementIndex = i;
		}
		void operator=(ElementProxy& o)
		{
			assert(!o.father->AnySubKernelRowDirty);
			assert(!o.father->WeightedRowDirty);
			for(int i=0;i<father->num_SubKernels;++i)
			{
				father->SubKernelRows[i][elementIndex]=o.father->SubKernelRows[i][o.elementIndex];
			}
			father->WeightedRow[elementIndex]=o.father->WeightedRow[o.elementIndex];
		}
	};
public:
	ElementProxy operator[](int index)
	{
		return ElementProxy(this,index);
	}
};

template<class T>
MultiKernelCacheRow<T>::MultiKernelCacheRow(int num_subkernels)
{
	this->num_SubKernels=num_subkernels;
	SubKernelRows.clear();
	WeightedRow.clear();
	SubKernelRowDirty.clear();

	SubKernelRows.resize(num_subkernels);
	SubKernelRowDirty.resize(num_subkernels,true);

	AnySubKernelRowDirty = true;
	WeightedRowDirty     = true;
}

template<class T>
MultiKernelCacheRow<T>::MultiKernelCacheRow(MultiKernelCacheRow<T>& o)
{
	MultiKernelCacheRow(o.num_SubKernels);
}


template<class T>
void MultiKernelCacheRow<T>::swap(MultiKernelCacheRow<T>& other)
{
	SubKernelRows.swap(other.SubKernelRows);
	WeightedRow.swap(other.WeightedRow);
	SubKernelRowDirty.swap(other.SubKernelRowDirty);
	assert(num_SubKernels==other.num_SubKernels);
	swap(AnySubKernelRowDirty,other.AnySubKernelRowDirty);
	swap(WeightedRowDirty,other.WeightedRowDirty);
}

template<class T>
void MultiKernelCacheRow<T>::clear()
{
	SubKernelRows.clear();
	WeightedRow.clear();
	SubKernelRowDirty.clear();
	num_SubKernels=0;
}

template<class T>
void MultiKernelCacheRow<T>::resize(int size)
{
	for(int i=0;i<num_SubKernels;++i)
	{
		SubKernelRows[i].resize(size);
	}
	WeightedRow.resize(size);
}

template<class T>
void MultiKernelCacheRow<T>::WeightsChanged()
{
	WeightedRowDirty=true;
}

template<class T>
void MultiKernelCacheRow<T>::SubKernelChanged(int index)
{
	AnySubKernelRowDirty     = true;
	SubKernelRowDirty[index] =true;
}

template<class T>
void MultiKernelCacheRow<T>::FillTransposed(int other_index,int my_index,MultiKernelCacheRow<T>& row)
{
	WeightedRow[other_index]=row[my_index];
	for(int i=0;i<num_SubKernels;++i)
		SubKernelRows[other_index]=row[my_index];

}

