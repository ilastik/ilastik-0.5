def getIlastikVersion():
    version = "$Revision$"  #SVN keyword, get replaced
    version = version.split(" ")[1]   
    return version.strip() 