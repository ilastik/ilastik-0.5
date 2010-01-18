from distutils.core import setup, Extension

import sys, os.path, numpy
import sipdistutils

import PyQt4.pyqtconfig
config = PyQt4.pyqtconfig.Configuration()

# --------------------------------------------------------------------

# Replace the following with
#  qt_inc_dir = "C:/path/to/Qt/include"
#  qt_lib_dir = "C:/path/to/Qt/lib"
# when automatically extracted paths don't fit your installation.
# (Note that you should use a compatible compiler and Qt version
#  as was used for building PyQt.)
qt_inc_dir = config.qt_inc_dir
qt_lib_dir = config.qt_lib_dir

# --------------------------------------------------------------------

qt_lib_dirs = [qt_lib_dir]
qt_libraries = ["QtCore", "QtGui"]
boost_python_libraries = ["boost_python"]

if "mingw32" in sys.argv:
	# FIXME: better criterion - this should only apply to mingw32
	qt_lib_dirs.append(qt_lib_dir.replace(r"\lib", r"\bin"),
					   # fall back to default Qt DLL location:
					   os.path.dirname(PyQt4.__file__))
	qt_libraries = [lib + "4" for lib in qt_libraries]



libs = qt_libraries
libs.extend(boost_python_libraries)

# FIXME: is there a better way than to explicitly list the Qt4 include
# dirs and libraries here?  (before distutils, I used
# PyQt4.pyqtconfig.QtGuiModuleMakefile to build extensions)
draw = Extension('labelArrayDrawQImage.draw',
					   sources = ['draw.sip'],
					   include_dirs = [numpy.get_include(),
								   qt_inc_dir,
									   os.path.join(qt_inc_dir, "QtCore"),
									   os.path.join(qt_inc_dir, "QtGui")],
					   library_dirs = qt_lib_dirs,
					   libraries = libs )

class build_ext(sipdistutils.build_ext):
	def _sip_compile(self, sip_bin, source, sbf):
		import PyQt4.pyqtconfig
		config = PyQt4.pyqtconfig.Configuration()
		self.spawn([sip_bin,
					"-c", self.build_temp,
					"-b", sbf] +
				   config.pyqt_sip_flags.split() +
				   ["-I", config.pyqt_sip_dir,
					source])

setup(name = 'labelArrayDrawQImage',
	  version = '0.0',
	  description = 'Draws ndarray into a QImage using a colormap.',
	  author = "Stephan Kassemeyer",
	  author_email = "stephan.kassemeyer@iwr.uni-heidelberg.de",
	  url = "http://hci.iwr.uni-heidelberg.de/",
#	  download_url = "....tgz",
	  keywords = ["QImage", "numpy", "ndarray", "image", "draw", "PyQt4"],
	  packages = ['labelArrayDrawQImage'],
	  ext_modules = [draw],
	  cmdclass = {'build_ext': build_ext},
	  long_description = """\
Draws ndarray into a QImage using a colormap.
""",
	  classifiers = [
	"Programming Language :: Python",
	"Development Status :: 5 - Production/Stable",
	"Intended Audience :: Developers",
	"Intended Audience :: Science/Research",
	"License :: OSI Approved :: BSD License",
	"Operating System :: OS Independent",
	"Topic :: Multimedia :: Graphics",
	"Topic :: Software Development :: Libraries :: Python Modules",
	"Topic :: Software Development :: User Interfaces",
	]
)
