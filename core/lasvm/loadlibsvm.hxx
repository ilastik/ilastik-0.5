#include <fstream>
#include <string>
#include <vector>
#include <stdexcept>
#include <iostream>

void tokenize(std::string str,std::vector<std::string>& res,const std::string delim=",")
{
    if(str.size() < delim.size() || str.rfind(delim) != str.size() - delim.size())
	str = str+delim;
    while(str.size()!=0)
    {
        if(str.find(delim)!=std::string::npos)
	{
	    res.push_back(str.substr(0,str.find(delim)));
	    str = str.substr(str.find(delim)+delim.size(), str.size());
	}
    }
}

//Write out a libsvm from a vector
template<class label_T,class T>
void write_libsvm_dataset(const std::string filename,std::vector<label_T>& labels,std::vector<std::vector<T> >& features)
{
    std::ofstream file(filename.c_str());
    if(!file.is_open())
        throw std::runtime_error("could not open file");
    for(int i=0;i<labels.size();++i)
    {
        file<<labels[i]<<" ";
        for(int j=0;j<features[0].size();++j)
            file<<j+1<<":"<<features[i][j]<<" ";
        file<<std::endl;
    }
}

//Load a libsvm file into a vector of vectord
template<class label_T,class T>
void load_libsvm_dataset(const std::string filename,std::vector<label_T>& labels,std::vector<std::vector<T> >& features,bool load_model=false,double* gamma=0)
{
    labels.clear();
    features.clear();
    std::ifstream file(filename.c_str()); 
    if(!file.is_open())
        throw std::runtime_error("could not open file");
    std::string line;
    //Process the dataset once to get #features
    if(load_model)
    {
        do
        {
            if(std::getline(file,line).eof())
                throw std::runtime_error("opening none svm model file as svm model file");
	    if(line[0]=='g' && line[1]=='a' && line[2]=='m' &&line[3]=='m' &&line[4]=='a')
	    {
                std::vector<std::string> inner_tokens;
		tokenize(line,inner_tokens," ");
		*gamma=atof(inner_tokens[1].c_str());
	    }
	}while(line[0]!='S' || line[1]!='V');
    }
    int dims=0;
    int num_samples=0;
    while(!std::getline(file,line).eof())
    {
	++num_samples;
        std::vector<std::string> tokens;
	tokenize(line,tokens," ");
	for(int i=1;i<tokens.size();++i)
	{
            std::vector<std::string> inner_tokens;
	    tokenize(tokens[i],inner_tokens,":");
	    int dim=atoi(inner_tokens[0].c_str());
	    if(dim>dims)
                dims=dim;
	}
    }
    file.clear();
    file.seekg(0,std::ios::beg);
    if(load_model)
    {
        do
        {
            if(std::getline(file,line).eof())
                throw std::runtime_error("opening none svm model file as svm model file");
	}while(line[0]!='S' || line[1]!='V');
    }
    //OK, load the oh so cool dataset
    features.resize(num_samples,std::vector<T>(dims,0.0));
    labels.resize(num_samples,0);
    int sample=0;

    while(!std::getline(file,line).eof())
    {
        std::vector<std::string> tokens;
        tokenize(line,tokens," ");
	labels[sample]=atof(tokens[0].c_str());
	for(int i=1;i<tokens.size();++i)
	{
            std::vector<std::string> inner_tokens;
	    tokenize(tokens[i],inner_tokens,":");
	    features[sample][atoi(inner_tokens[0].c_str())-1]=atof(inner_tokens[1].c_str());
	}
	++sample;
    }
}

