#include <stdlib.h>
#include <vector>
#include <list>
#include <iostream>
#include <math.h>
#include <assert.h>
#include <stdexcept>
#include <stdlib.h>
#include <stdio.h>
#include <sstream>

#ifndef SVHANDLER_INCLUDED
#define SVHANDLER_INCLUDED

/** Handler for a set of vectors which can be moved between support vectors and normal vectors.
 *
 * For the support vectors, a kernel cache is stored and handled, making sure it does not extend a given size.
 * The NV template parameter defines a class for storing normal vectors, the SV
 * template parameters for support vectors. A NV/SV can be unused.
 * Their common required interface is:
 *   - cleanup(): Make the NV/SV unused.
 *   - swap(other_type): Swap the NV with an SV or an SV with an NV (for making normal vectors SVs and vica verse).
 *   - std constructor: for creating and unsused NV/SV.
 *   - copy constructor
 *   - Unused(): Indicating of a NV/SV is currently used.
 * In addition, NV requires
 *   - NV::init_param: parameter type for initializing a NV with a value.
 *
 * In addition, the RowType template parameter defines a class for a kernel
 * Row. It is a template parameter because special SVM types might require to
 * store more than the Kernel value in a kernel row (a Multi kernel SVM i.E.
 * might want store a set of kernel values). 
 * But it is assumed, that a kernel row is a array of kernel values. When a
 * kernel row for a certain SV is computed, existing kernel rows for earlier
 * SVs might be completed using the [] operator.
 * The required interface for a kernel row is:
 *   - size: returns the size (length) of the row.
 *   - resize(length): resize the row to fit a specific length.
 *   - swap(other_row): swap a row with another one.
            this->row_locked[this->sv_index_to_row[index]]++;
            this->UpdateRow(this->kcache[this->sv_index_to_row[index]],index);
            kcache[sv_index_to_row[index]];
 *   - operator[]: It must be possible to write row1[a]=row2[b] to complete transposed values.
 *
 * A derived class must implement FillRow.
*/
template<class NV, class SV, class RowType>
class SVHandler
{
public:
	/** Constructor.
	 *
	 * @param Defines at what number of SVs the cache starts to overflow. The maximum memory requirement is than overflowSize^2*size(row_element).
	 * @param init_obj object for initializing the (empty!) kernel rows in std::vector::resize.
	 */
	SVHandler(int overflowsize,RowType init_obj);
	virtual ~SVHandler();

	/** Add a vector (normal vector).
	 * To add a SV, add a NV and make it an SV using MakeSV.
	 * @param p Parameter to initialize the NV with. Should be the data (i.E. feature vector) related to that NV.
	 * @return the index of the newly created vector (it can accessed with normal_vectors[index] now).
	 */
	int AddSample(typename NV::init_param const p);

	/** Remove a normal vector.
	 * Removes a normal vector completely, freeing its space. If a support
	 * vector is to be removed, it has to be made a normal vector before.
	 * @param index The index of the NV to remove.
	 */
	void RemoveSample(int index);

	/**Make an non sv vector an sv vector, returns its index	
	 * @param index The index of the NV.
	 * @return The index of the newly created SV.
	*/
	int MakeSV(int index);

	/** Make an SV to an NV. returns its index.
	 * @param index The index of the SV.
	 * @return The index of the newly created NV.
	 */
	int MakeNonSV(int index);

	/** Returns the kernel row for an SV (and lock it!)
	 * Creates (if necessary) the kernel row, or returns it from cache.
	 * The kernel row will be locked and MUST be unlocked by UnlockKernelRow
	 * when done.
	 * @param index The index of the SV to get the kernel row from.
	 * @return Reference to the requested kernel row.
	 */
	RowType& GetKernelRow(int index);

	/**Unlock the kernel row after it has been requested.
	 * After a call to GetKernelRow, the row must be unlocked afterwards (when not used anymore).
	 *
	 * @param index Index of SV for which the kernel row will be unlocked.
	 */
	void UnlockKernelRow(int index);

	/** Invalidate all kernel rows.
	 * Used when parameters change (and all rows must be recalculated).
	 */
	void InvalidateCache();
	/**Recalculate a kernel row.
	 * When a SV has changed, this has to be called to keep cache in sync.
	 */
	void RecalculateKernelRow(int index);

	/** List of SVs.
	 * Derived classes should access the support vectors with this list. A
	 * macro SVs us used for convinienc.
	 */
        std::vector<SV> support_vectors;

	/** List of NVs.
	 * Derived classes should access the normal vectors with this list. A
	 * macro NVs us used for convinienc.
	 */
        std::vector<NV> normal_vectors;

	/** Abstract function for filling a kernel row.
	 * This function must be implemented in derived classes and will be called
	 * whenever a kernel row must be recalculated.
	 * @param row Reference to the row to fill.
	 * @param sv_index The index of the SV for which this row is.
	 */
	virtual void FillRow(RowType& row,int sv_index)=0;
	/** Abstract function for updating a kernel row.
	 * For some types of kernel row, the values might have to be updated before usage.
	 * The row is garanteed to be fill before with FillRow.
	 * @param row The row to update.
	 * @param sv_idnex The index of the SV for which this row is.
	 */
	virtual void UpdateRow(RowType& row,int sv_index)=0;

	/*******************************
	 * Internal data
	 *******************************/
	//List of unsused slots
	std::list<int> unused_svs;    //SV slots not used
	std::list<int> unused_rows;   //kernel rows not used
	std::list<int> unused_non_svs;//non svs not used
        std::vector<int> sv_index_to_row;//Convert an SV index to an row
	
	//Cache of kernel between SVs
        std::vector<RowType> kcache;		
	//locked rows
        std::vector<int> row_locked;
	//maping row->sv
        std::vector<int> row_to_sv_index;
	//Initial size of the kernel
	int cacheSize;
	//The maximum elements the cache can hold
	int maxCacheElements;


public:
	/** Internal function for getting a place for a new SV.
	 * Returns an index of an free SV.
	 * @return The desired index.
	 */
	int GetSV();
	/** Internal function for getting a place for a new row.
	 * Returns an index of an free row.
	 * @return The desired index.
	 */
	int GetRow();
	/** Internal function for getting a place for a new NV.
	 * Returns an index of an free NV.
	 * @return The desired index.
	 */
	int GetNonSV();
};

template<class NV, class SV, class RowType>
SVHandler<NV,SV,RowType>::SVHandler(int overflowsize,RowType init_obj)
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

template<class NV, class SV, class RowType>
SVHandler<NV,SV,RowType>::~SVHandler()
{
	int i;
	for(i=0;i<normal_vectors.size();++i)
		normal_vectors[i].cleanup();
	for(i=0;i<support_vectors.size();++i)	
		support_vectors[i].cleanup();
}


template<class NV,class SV,class RowType>
void SVHandler<NV,SV,RowType>::InvalidateCache()
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



template<class NV, class SV, class RowType>
int SVHandler<NV,SV,RowType>::AddSample(typename NV::init_param const p)
{
	int index=GetNonSV();
	normal_vectors[index].Init(p);
	return index;
}

template<class NV,class SV,class RowType>
void SVHandler<NV,SV,RowType>::RemoveSample(int index)
{
	normal_vectors[index].cleanup();
	unused_non_svs.push_back(index);
}

template<class NV,class SV,class RowType>
void SVHandler<NV,SV,RowType>::RecalculateKernelRow(int index)
{
	//Invalidate it ...
	if(sv_index_to_row[index]>=0)
	{
		int row=sv_index_to_row[index];
		sv_index_to_row[index]=-1;
		row_to_sv_index[row]=-1;
		unused_rows.push_back(row);
	}
	//Re-get the row and fill the transposed
	RowType& row=GetKernelRow(index);
	for(int i=0;i<sv_index_to_row.size();++i)
	{
		if(sv_index_to_row[i]!=-1)
		{
			assert(!support_vectors[i].Unused());
			kcache[sv_index_to_row[i]][index]=row[i];
		}
	}
	UnlockKernelRow(index);
}

//Make an non sv vector an sv vector, returns its index	
template<class NV, class SV, class RowType>
int SVHandler<NV,SV,RowType>::MakeSV(int index)
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
	UnlockKernelRow(sv_index);
	return sv_index;
}

//Make a SV to an non sv
template<class NV, class SV, class RowType>
int SVHandler<NV,SV,RowType>::MakeNonSV(int index)
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
template<class NV, class SV, class RowType>
RowType& SVHandler<NV,SV,RowType>::GetKernelRow(int index)
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
	assert(index>=0);
    row_to_sv_index[row]=index;
    FillRow(kcache[row],index);
    row_locked[row]++;
    return kcache[row];
}
template<class NV, class SV, class RowType>
void SVHandler<NV,SV,RowType>::UnlockKernelRow(int index)
{
    if(sv_index_to_row[index]>=0)
        row_locked[sv_index_to_row[index]]--;
}

template<class NV, class SV, class RowType>
int SVHandler<NV,SV,RowType>::GetSV()
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
		if(cacheSize*(sv_index_to_row.size())>maxCacheElements && cacheSize>3)
		{
			//Remove a kernel row
			//Make sure the las row index is -1
			if(row_to_sv_index[cacheSize-1]!=-1)
			{
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
			}
			else
				--cacheSize;
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

template<class NV, class SV, class RowType>
int SVHandler<NV,SV,RowType>::GetRow()
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
	int start_row=rand() % cacheSize; 
	for(row=start_row;row_locked[row]!=0;row=(row+1) % cacheSize)
	{
#ifdef DEBUG
		if(((row+1) % cacheSize)==start_row)
                {
                    std::stringstream stream;
                    stream<<"No more free rows (cacheSize="<<cacheSize<<")";
                    throw std::runtime_error(stream.str());
                }
#endif

	}
	//Remove the sv->row entry
    assert(row_to_sv_index[row]>=0);
    assert(sv_index_to_row.size()>row_to_sv_index[row]);
	sv_index_to_row[row_to_sv_index[row]]=-1;
	row_to_sv_index[row]=-1;
	return row;
}

template<class NV, class SV, class RowType>
int SVHandler<NV,SV,RowType>::GetNonSV()
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
#endif

