#include <stdlib.h>
#include <vector>
#include <list>
#include <iostream>
#include <math.h>
#include <assert.h>

#ifndef SVHANDLER_INCLUDED
#define SVHANDLER_INCLUDED

using namespace std;

template<class T>
inline void swap(T &a,T &b)
{
	T tmp = a;
	a     = b;
	b     = tmp;
}

//Support Vector handlder ...
//Rquired interface:
//NV, SV need:
//- cleanup
//- swap(with accordingly other one)
//- std constructor (empty)
//- SetData
//- copy constructor
//- GetLabel
//- Unused
template<class NV, class SV, class RowType,class T>
class SVHandler
{
public:
	//List of unsused slots
	std::list<int> unused_svs;    //SV slots not used
	std::list<int> unused_rows;   //kernel rows not used
	std::list<int> unused_non_svs;//non svs not used
	vector<int> sv_index_to_row;//Convert an SV index to an row
private:
	int GetSV();
	int GetRow();
	int GetNonSV();
public:

	//list of SVs
	vector<SV> support_vectors;
	//list of non SVs
	vector<NV> normal_vectors;
	
	//Cache of kernel between SVs
	vector<RowType> kcache;		
	//locked rows
	vector<int> row_locked;
	//maping row->sv
	vector<int> row_to_sv_index;
	//Initial size of the kernel
	int cacheSize;

	//The maximum elements the cache can hold
	int maxCacheElements;

	//Functions for filling and updating a row
	virtual void UpdateRow(RowType& row,int sv_index)=0;
	virtual void FillRow(RowType& row,int sv_index)=0;

	SVHandler(int overflowsize,RowType init_obj);
	virtual ~SVHandler();
	//Adds a vector, (not as SV), returns its index
	int AddSample(typename NV::init_param const p);
	void RemoveSample(int index);
	//Make an non sv vector an sv vector, returns its index	
	int MakeSV(int index);
	//Make a SV to an non sv
	int MakeNonSV(int index);
	//Returns the kernel row for an SV (and lock it!)
	RowType& GetKernelRow(int index);
	//Unlock the kernel row after it has been requested 
	void UnlockKernelRow(int index);
	//Invalidate all kernel rows (used when parameters change)
	void InvalidateCache();
};


template<class NV,class SV,class RowType, class T>
void SVHandler<NV,SV,RowType,T>::InvalidateCache()
{
	//Invalidate all rows
	for(int i=0;i<row_to_sv_index.size();++i)
	{
		if(row_to_sv_index[i]!=-1)
		{
			row_to_sv_index[i]=-1;
			unused_rows.push_back(i);
		}
	}
	for(int i=0;i<sv_index_to_row.size();++i)
	{
		sv_index_to_row[i]=-1;
	}
}

template<class NV, class SV, class RowType, class T>
int SVHandler<NV,SV,RowType,T>::GetSV()
{
	int result;
	//Maybe something free?
	if(!unused_svs.empty())
	{
		result=unused_svs.front();
		unused_svs.pop_front();
		assert(support_vectors[result].Unused());
	}
	else
	{
		result=support_vectors.size();
		support_vectors.push_back(SV());
		//React to overflow
		if(cacheSize*(sv_index_to_row.size())>maxCacheElements && cacheSize>2)
		{
			//Remove a kernel row
			int row=GetRow();
			kcache[row].swap(kcache[cacheSize-1]);
			row_to_sv_index[row]=row_to_sv_index[cacheSize-1];
			kcache[cacheSize-1].clear();
			row_to_sv_index[cacheSize-1]=-1;
			--cacheSize;
			for(int i=0;i<sv_index_to_row.size();++i)
				if(sv_index_to_row[i]==cacheSize)
				{
					sv_index_to_row[i]=row;
					break;
				}
			unused_rows.remove(cacheSize); //TODO: Can this be speed up?
		}
	}
	if(result>=sv_index_to_row.size())
	{
		sv_index_to_row.resize(result+1,-1);
		for(int i=0;i<sv_index_to_row.size();++i)
			if(sv_index_to_row[i]!=-1)
				kcache[sv_index_to_row[i]].resize(sv_index_to_row.size());
	}
	return result;
}

template<class NV, class SV, class RowType,class T>
int SVHandler<NV,SV,RowType,T>::GetRow()
{
	//Maybe something free?
	if(!unused_rows.empty())
	{
		int result=unused_rows.front();
		unused_rows.pop_front();
		if(kcache[result].size()<sv_index_to_row.size())
			kcache[result].resize(sv_index_to_row.size());
		return result;
	}
	//Take a random row
	int row;
	//TODO: Maybe there is a better choice
	for(row=rand() % cacheSize;row_locked[row]!=0;row=(row+1) % cacheSize);
	//Remove the sv->row entry
    assert(row_to_sv_index[row]>=0);
    assert(sv_index_to_row.size()>row_to_sv_index[row]);
	sv_index_to_row[row_to_sv_index[row]]=-1;
	row_to_sv_index[row]=-1;
	return row;
}

template<class NV, class SV, class RowType,class T>
int SVHandler<NV,SV,RowType,T>::GetNonSV()
{
	//Maybe something free?
	if(!unused_non_svs.empty())
	{
		int result=unused_non_svs.front();
		unused_non_svs.pop_front();
		return result;
	}
	normal_vectors.push_back(NV());
	return normal_vectors.size()-1;
}

template<class NV, class SV, class RowType,class T>
SVHandler<NV,SV,RowType,T>::SVHandler(int overflowsize,RowType init_obj)
{
	this->cacheSize=overflowsize;
	this->maxCacheElements=overflowsize*overflowsize;
	//Initilize everything with overflowsize
	kcache.resize(cacheSize,init_obj);
	row_locked.resize(cacheSize,0);
	row_to_sv_index.resize(cacheSize,-1);
	support_vectors.resize(cacheSize,SV());
	//sv_index_to_row.resize(cacheSize,-1);
	int i;
	for(i=0;i<cacheSize;++i)
	{
		kcache[i].resize(cacheSize);
		unused_rows.push_back(i);
		unused_svs.push_back(i);
	}	
}

template<class NV, class SV, class RowType,class T>
SVHandler<NV,SV,RowType,T>::~SVHandler()
{
	int i;
	for(i=0;i<normal_vectors.size();++i)
		normal_vectors[i].cleanup();
	for(i=0;i<support_vectors.size();++i)	
		support_vectors[i].cleanup();
}

template<class NV, class SV, class RowType, class T>
int SVHandler<NV,SV,RowType,T>::AddSample(typename NV::init_param const p)
{
	int index=GetNonSV();
	normal_vectors[index].Init(p);
	return index;
}

template<class NV,class SV,class RowType, class T>
void SVHandler<NV,SV,RowType,T>::RemoveSample(int index)
{
	normal_vectors[index].cleanup();
	unused_non_svs.push_back(index);
}

//Make an non sv vector an sv vector, returns its index	
template<class NV, class SV, class RowType,class T>
int SVHandler<NV,SV,RowType,T>::MakeSV(int index)
{
	int sv_index=GetSV();
	support_vectors[sv_index].swap(normal_vectors[index]);
	unused_non_svs.push_back(index);
	sv_index_to_row[sv_index]=-1;
	//Get the row to fill the transponiert
	RowType& row=GetKernelRow(sv_index);	
	int i;
	for(i=0;i<sv_index_to_row.size();++i)
	{
		if(sv_index_to_row[i]!=-1)
		{
			assert(!support_vectors[i].Unused());
			kcache[sv_index_to_row[i]][sv_index]=row[i];
			//kcache[sv_index_to_row[i]].FillTransposed(sv_index,i,row);
		}
	}
	return sv_index;
}

//Make a SV to an non sv
template<class NV, class SV, class RowType,class T>
int SVHandler<NV,SV,RowType,T>::MakeNonSV(int index)
{
	int non_sv_index=GetNonSV();
	normal_vectors[non_sv_index].swap(support_vectors[index]);
	unused_svs.push_front(index);
	if(sv_index_to_row[index]>=0)
	{
		row_to_sv_index[sv_index_to_row[index]]=-1;
		unused_rows.push_front(sv_index_to_row[index]);
	}
	sv_index_to_row[index]=-1;
	return non_sv_index;
}

//Returns the kernel row for an SV
template<class NV, class SV, class RowType,class T>
RowType& SVHandler<NV,SV,RowType,T>::GetKernelRow(int index)
{
    //Maybe it's just there?
    if(sv_index_to_row[index]>=0)
    {
        row_locked[sv_index_to_row[index]]++;
        UpdateRow(kcache[sv_index_to_row[index]],index);
        return kcache[sv_index_to_row[index]];
    }
    //OK, we have to create it
    int row=GetRow();
    sv_index_to_row[index]=row;
    row_to_sv_index[row]=index;
    FillRow(kcache[row],index);
    row_locked[row]++;
    return kcache[row];
}
template<class NV, class SV, class RowType,class T>
void SVHandler<NV,SV,RowType,T>::UnlockKernelRow(int index)
{
    if(sv_index_to_row[index]>=0)
        row_locked[sv_index_to_row[index]]--;
}

#endif

