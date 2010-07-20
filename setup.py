from distutils.core import setup

setup(name = 'ilastik',
      version = '0.5',
      description = 'Interactive Learning and Segmentation Tool Kit',
      author = 'Christoph Sommer, Christoph Straehle, Ullrich Koethe, Fred Hamprecht',
      author_email = 'ilastik@hci.iwr.uni-heidelberg.de',
      url = 'http://www.ilastik.org',
      download_url = 'http://www.ilastik.org',
      keywords = ['segmentation', 'numpy', 'ndarray', 'image', 'classification', 'PyQt4'],
      packages = ['ilastik.core', 'ilastik.gui', 'ilastik.core.features', 'ilastik.core.classifiers'],
      py_modules = ['ilastik/ilastikMain'],
      package_data ={'ilastik.gui':['ilastik/gui/icons/*']},
      long_description = ''' ''')