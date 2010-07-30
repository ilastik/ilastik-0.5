//Online prediction set for faster online prediction

#ifndef SVM_ONLINE_PREDICTION_SET
#define SVM_ONLINE_PREDICTION_SET

#include <vigra/multi_array.hxx>
#include <map>
#include <vector>

template<class T>
class SvmPredictionSet
{
public:
  std::vector<std::vector<T> > features;

  SvmPredictionSet(const std::vector<std::vector<T> >& f)
  {
    features=f;
  }
  SvmPredictionSet(const vigra::NumpyArray<2,T>& f)
  {
    //Copy the baby
    features.resize(f.shape(0));
    for(int i=0;i<features.size();++i)
    {
      features[i].resize(f.shape(1));
      for(int j=0;j<f.shape(1);++j)
	features[i][j]=f(i,j);
    }
  }
};

#endif
