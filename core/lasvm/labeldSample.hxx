#include <float.h>
#include <vector>
#ifndef LABELD_SAMPLE_INCLUDED
#define LABELD_SAMPLE_INCLUDED


/** Class for a labeled sample handled for by the SVM.
 * This class holds together the unique id, label and features of a sample.
 */
template<class T>
class labeled_sample
{
public:
    /** unique id of the sample.*/
    int unique_id;
    /** label (+1 or -1) of the sample.*/
    int label;
    /** Features of the sample. ==0 if sample is unsed.*/
    T* features;
   
    /**Standard constructor setting the sample to unused.*/
    labeled_sample(){features=0;unique_id=-1;};
    /**Clear the sample, deleting the features.
     */
    void clear()
    {
	if(features)
	{
	    delete [] features;
	}
	features=0;
    };
    
    /** Set the data of sample (using [][] operator).
     * @param features Complete sample array (in which at place source_index the desired sample is).
     * @param source_index The index in features we are interested in.
     * @param length Number of features.
     * @param label Label of sample.
     * @param unique_id Unique id of the sample.
     */
    void setData(const std::vector<std::vector<T> > & features,int source_index,int length,int label,int unique_id)
    {
	clear();
	this->features=new T[length];
	for(int i=0;i<length;++i)
	    this->features[i]=features[source_index][i];
	this->label=label;
	this->unique_id=unique_id;
    }

    /** Set the data of sample (using () operator).
     * @param features Complete sample array (in which at place source_index the desired sample is).
     * @param source_index The index in features we are interested in.
     * @param length Number of features.
     * @param label Label of sample.
     * @param unique_id Unique id of the sample.
     */
    template<class vigra_like_array>
    void setData(const vigra_like_array& features,int source_index,int length,int label,int unique_id)
    {
        clear();
        this->features=new T[length];
        for(int i=0;i<length;++i)
            this->features[i]=features(source_index,i);
        this->label=label;
        this->unique_id=unique_id;
    }
};

/**A combined sample representing many close samples.
 */
template<class T>
class combined_sample
{
public:
    /**IDs of the samples combined here.*/
    std::vector<int> data_ids;
    /**Lables of the combined samples.*/
    int label;
    /**Average features of all data.*/
    T* features;
    /**Constructor, setting it to unused.*/
    combined_sample()
    {
        features=0;
    }
    /**Rebuild.
     * Remake the average, should be called when sample ids change.
     * @param sample_array Array of all the samples.
     * @param VLength Number of features in every sample.
     */
    template<class sample_array>
    void rebuild(const sample_array& samples,int VLength)
    {
        if(features==0)
            features=new T[VLength];
        for(int f=0;f<VLength;++f)
        {
            features[f]=0.0;
            for(int i=0;i<data_ids.size();++i)
            {
                features[f]+=samples[data_ids[i]].features[f];
            }
            features[f]/=VLength;
        }
    }
    /** Clear all data and make the combined sample unused.*/
    void clear()
    {
        data_ids.clear();
        if(features)
            delete [] features;
        features=0;
    }

    /** Test if all samples should be in this combined sample.
     * @param kernel The kernel for computing the common kernel value.
     * @param samples Array of all the samples.
     * @param VLength Number of features in every sample.
     * @param res Array which will be filled with the index that should be removed.
     */
    template<class sample_array,class Kernel>
    void testCoherence(const Kernel& kernel,const sample_array& samples,int VLength,T threshold,std::vector<int>& res)
    {
        res.clear();
        for(int i=0;i<data_ids.size();++i)
        {
            T k=kernel.compute(samples[data_ids[i]].features,features,VLength);
            if(1-k*k>threshold)
                res.push_back(data_ids[i]);
        }
    }

    /** Remove the sample closest to a given sample.
     * Afterwards rebuilding is necessary.
     * @param kernel The kernel for computing the common kernel value.
     * @param samples Array of all the samples.
     * @param VLength Number of features in every sample.
     * @param id Index in samples for the sample, to which the closeness should be determined.
     * @return data_id of the closest sample.
     */
    template<class sample_array,class Kernel>
    int removeClosest(const Kernel& kernel,const sample_array& samples,int VLength,int id)
    {
        int closest=0;
        typename Kernel::float_type max_k=-FLT_MAX; 
        for(int i=0;i<this->data_ids.size();++i)
        {
            T k=kernel.compute(samples[data_ids[i]].features,samples[id].features,VLength);
            if(k>max_k)
            {
                closest=i;
                max_k=k;
            }
        }
        int ret=data_ids[closest];
        data_ids[closest]=data_ids.back();
        data_ids.pop_back();
        return ret;
    }
};

#endif
