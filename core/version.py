def getIlastikVersion():
    version = "$Revision$"
    version = version.split(" ")[1]
    return version.strip()