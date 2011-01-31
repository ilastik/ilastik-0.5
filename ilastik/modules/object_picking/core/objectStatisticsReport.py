import os.path
import objectOperators

class ObjectStatisticsReport():
    def __init__(self, outputfile, objects, objectsOverlay, objectsInputOverlay, raw_data):
        self.outputfile = outputfile
        #sort by size
        self.objlist = sorted(objects.values(), key = lambda x: len(x[0]), reverse=True)
        self.objects = objects
        self.objectsOverlay = objectsOverlay
        self.objectsInputOverlay = objectsInputOverlay
        self.raw_data = raw_data
        self.functions = []
        self.initContents()
        
    def initContents(self):
        #specify, which operators have to be called
        outdir = os.path.dirname(self.outputfile)
        outdir3d = os.path.join(outdir, "outputpictures_3d")
        if not os.path.exists(outdir3d):
            os.mkdir(outdir3d)
        f3 = objectOperators.pc_projection_3d(self.objects, self.objectsOverlay, self.objectsInputOverlay, outdir3d)
        self.functions.append(f3)
        outdir2d = os.path.join(outdir, "outputpictures_2d")
        if not os.path.exists(outdir2d):
            os.mkdir(outdir2d)
        f2 = objectOperators.slice_view(self.objects, self.raw_data, outdir2d)
        self.functions.append(f2)
        fc = objectOperators.coords()
        self.functions.append(fc)     
        f1 = objectOperators.size_in_pixels()
        self.functions.append(f1)   
    
    def generate(self):
        f = open(self.outputfile, "w")
        lines = []
        lines.extend(self.generateTitle())
        lines.append("<body>") 
        lines.append("<table border=\"2\" cellpadding=\"10\">")
        for fun in self.functions:
            lines.append("<th>" + fun.getName() + "</th>")
        #for key, value in self.objects.iteritems():
        for value in self.objlist:
            lines.append("<tr>")
            for fun in self.functions:
                lines.append("<td align=\"center\">" + fun.generateOutput(value) + "</td>")
            lines.append("</tr>")
        lines.append("</body>")    
        lines.append("</html>")
        for line in lines:
            f.write("%s\n" % line)
        f.close()
        for fun in self.functions:
            fun.cleanUp()
        
    def generateTitle(self):
        titlelines = []
        titlelines.append("<html>")
        titlelines.append("<head>")
        titlelines.append("<title>")
        titlelines.append("Test Report")
        titlelines.append("</title>")
        titlelines.append("</head>")
        return titlelines