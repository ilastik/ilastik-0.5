// -*-c++-*-
%Module draw 0

%Import QtCore/QtCoremod.sip
%Import QtGui/QtGuimod.sip

%ModuleCode
#include <Python.h>
#define PY_ARRAY_UNIQUE_SYMBOL labelarray_qimage_API
//#include <numpy/arrayobject.h>
#include <Python.h>
#include <boost/python.hpp>
#include <boost/python/numeric.hpp>
//#include <iostream>
using namespace boost::python;
%End

//%PostInitialisationCode
//import_array();
//%End

//void drawImage(QImage &image, SIP_PYDICT colDictp, SIP_PYOBJECT datap);
void drawImage(QImage &image, SIP_PYOBJECT colDictp, SIP_PYOBJECT datap);
%MethodCode
{
	numeric::array::set_module_and_type("numpy", "ndarray");
	//numeric::array::set_module_and_type("numpy", "ArrayType");
	dict colDict = extract<dict>(a1);
	numeric::array data = extract<numeric::array>( a2 );
	/*
	handle <> dataph(borrowed(a2));
	numeric::array & data = extract<numeric::array &>( object(dataph) );
	handle <> colDictph(borrowed(a1));
	dict& colDict = extract<dict&>( object(colDictph) );
	*/
	for (int xx=0; xx<a0->width(); xx++) for (int yy=0; yy<a0->height(); yy++) {
		//int label = extract<int>( data[xx][yy] );		// [WA] doesn't work on 64 bit machines...
		double dlabel = extract<double>( data[yy][xx] );	// [WA] hack...   [yy][xx]: numpy order
		long int label = (long int) dlabel;			// [WA] hack
		double rgb;
		if (label) {
			//std::string classstr = extract<std::string>( ((colDict.get( label )).attr("__class__")).attr("__name__") );
			//std::cout << "label: " << label << " > " << classstr << std::endl;
			// [WA] here a double is extracted, it is actually a long but extract only works with double
			rgb = extract<double>(colDict.get( label ));
		}
		else {
			rgb = 0;
		}
		a0->setPixel(xx,yy, rgb);
	}
}
%End
