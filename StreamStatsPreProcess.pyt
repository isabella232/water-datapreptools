import arcpy
import ELEVDATA_tools as ET # import each toolset here...

class Toolbox(object):
    def __init__(self):
        """Toolbox for preprocessing data for creating or refreshing a StreamStats project."""
        self.label = "ELEVDATAtools"
        self.alias = "ELEVDATA processing tools"

        # List of tool classes associated with this toolbox
        self.tools = [
                        ET.makeELEVDATAIndex,
                        ET.ExtractPoly
                    ]

class Setup(object):
    def __init__(self):
        """Define the tool (tool name is the name of the class)."""
        self.label = "Setup"
        self.description = "Generate the file structure for Stream Stats Data Preprocessing."
        self.canRunInBackground = False

    def getParameterInfo(self):
        """Define parameter definitions"""
        params = None
        return params

    def isLicensed(self):
        """Set whether tool is licensed to execute."""
        return True

    def updateParameters(self, parameters):
        """Modify the values and properties of parameters before internal
        validation is performed.  This method is called whenever a parameter
        has been changed."""
        return

    def updateMessages(self, parameters):
        """Modify the messages created by internal validation for each tool
        parameter.  This method is called after internal validation."""
        return

    def execute(self, parameters, messages):
        """The source code of the tool."""
        return