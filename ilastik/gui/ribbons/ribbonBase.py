
class IlastikTabBase(object):
    name = "Ribbon Base Class for Tab Pages" 
    description = "Virtual base class" 
    author = "HCI, University of Heidelberg"
    homepage = "http://hci.iwr.uni-heidelberg.de"

    def __init__(self, name='', desc='', icon='', parent=None):
        self.name = name
        self.desc = desc
        self.icon = icon
        self.parent = parent

