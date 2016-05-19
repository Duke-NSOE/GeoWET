# HABSTATS_EditResponseVariableList.py
#
# Description: A check box interface to allow users to remove variables from analysis
#
# John Fay
# Fall 2015

# Import modules
import sys, os, arcpy

# Set path variables
scriptsDir = os.path.dirname(sys.argv[0])
rootDir = os.path.dirname(scriptsDir)
dataDir = os.path.join(rootDir,"Data")

# Script Inputs
swdCSV = arcpy.GetParameterAsText(0)        #SWD data file
excludeFlds = arcpy.GetParameterAsText(1)   #List of variables to exclude

# Derived output
outCSV = os.path.join(os.path.dirname(swdCSV),"IncludedVariables.csv")
arcpy.SetParameterAsText(2,outCSV) 

##---FUNCTIONS-----
# Messaging function
def msg(txt,type="message"):
    print txt
    if type == "message":
        arcpy.AddMessage(txt)
    elif type == "warning":
        arcpy.AddWarning(txt)
    elif type == "error":
        arcpy.AddError(txt)
##       
##---PROCESSES----
#Make a list of response variables to include
msg("Extracting variables to include")
fldList = []
for f in arcpy.ListFields(swdCSV):
    #Exclude the label fields
    if f not in ("Species","X","Y"):
        fldList.append(f.name)

msg("Removing fields identified as redundant")
for xFld in excludeFlds.split(";"):
    if xFld in fldList:
        msg("...removing: {}".format(xFld))
        fldList.remove(xFld)


#open the CSV
msg("Initializing output file")
f = open(outCSV,'w')
#add the keeper fields
for fld in fldList:
    f.write("{}\n".format(fld))
    msg("...keeping: {}".format(fld))

f.close()