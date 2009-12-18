#include "iostream"

#ifndef LABELD_SAMPLE_INCLUDED
#define LABELD_SAMPLE_INCLUDED

using namespace std;

template<class T>
class labeled_sample
{
public:
    //ID we got from outside
    int unique_id;
    //Out label
    int label;
    //Our features
    T* features;
    
    labeled_sample(){features=0;unique_id=-1;};
    void clear()
    {
	if(features)
	{
	    delete [] features;
	}
	features=0;
    };
    
    //Copy/set data
    void setData(const vector<vector<T> > & features,int source_index,int length,int label,int unique_id)
    {
	clear();
	this->features=new T[length];
	for(int i=0;i<length;++i)
	    this->features[i]=features[source_index][i];
	this->label=label;
	this->unique_id=unique_id;
    }
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
#endif
