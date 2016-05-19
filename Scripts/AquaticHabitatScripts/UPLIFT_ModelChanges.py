# UPLIFT_ModelChanges.py
#
# Description: Runs a second iteration of Maxent with a modified ResponseVars table

# Import arcpy module
import sys, os, arcpy

# Check out any necessary licenses
arcpy.CheckOutExtension("spatial")

#User variables
speciesName = arcpy.GetParameterAsText(0)
respvarsFC = arcpy.GetParameterAsText(1)    #Modified Response Vars Table
statsFolder = arcpy.GetParameterAsText(2)   #Stats root folder containing all species models
scenarioName = arcpy.GetParameterAsText(3)  #Prefix used to identify outputs
HUCFilter = arcpy.GetParameterAsText(4)

#Set environments
arcpy.env.overwriteOutput = True

# Get paths
rootWS = os.path.dirname(sys.path[0])
dataWS = os.path.join(rootWS,"Data")

# Local variables:
reuse = True

##---Functions---
def msg(txt,type="message"):
    print txt
    if type == "message":
        arcpy.AddMessage(txt)
    elif type == "warning":
        arcpy.AddWarning(txt)
    elif type == "error":
        arcpy.AddError(txt)

def checkFile(fileName):
    if not os.path.exists(fileName):
        msg("{} not found.\Exiting.".format(fileName),"error")
        sys.exit(1)
    else: return
##---DERIVED INPUTS---
msg("...Locating the species folder")
sppFolder = os.path.join(statsFolder,speciesName)
checkFile(sppFolder)

msg("...Locating the SWD file for the species")
swdFile = os.path.join(sppFolder,"{}_SWD.csv".format(speciesName))
checkFile(sppFolder)

msg("...Locating original maxent batch file")
origBatchFile = os.path.join(sppFolder,"RunMaxent.bat")
checkFile(origBatchFile)

msg("...Getting/creating scenario subfolder")
scenarioFolder = os.path.join(sppFolder,"{}_Output".format(scenarioName))
if os.path.exists(scenarioFolder):
    if reuse: 
        msg("Using existing scenario folder")
    else:
        msg("Removing old scenario folder and creating new one")
        os.rename(scenarioFolder,scenarioFolder + "_OLD")
        os.mkdir(scenarioFolder)
else:
    msg("Output folder does not exist. Creating it")
    os.mkdir(scenarioFolder)

#Set output parameters
arcpy.SetParameterAsText(5,scenarioFolder)
newBatchFN = os.path.join(sppFolder,"{}_RunMaxent.bat".format(scenarioName))
arcpy.SetParameterAsText(6,newBatchFN)

##---PROCESSES----
#Extract records for catchments in the selected HUC
msg("...Extracting records within HUC {}".format(HUCFilter))
whereClause = "REACHCODE LIKE '{}%'".format(HUCFilter)
tmpRVTable = arcpy.MakeTableView_management(respvarsFC,"tmpRVtable",whereClause)
#tmpRVTable = arcpy.TableSelect_analysis(respvarsFC,"in_memory/tmpTable",whereClause)
#Get the number of records extracted and tell the user
recordCount = arcpy.GetCount_management(tmpRVTable).getOutput(0)
msg("{} catchment records extracted".format(recordCount),'warning')

##Start creating the output ASCII files
#Create the ASCII header
msg("...Creating the header lines for the output pseudo ASCII files")
#  Create the header string, incorporating the number of rows determined above
asciiHeader = 'ncols\t1\nnrows\t{0}\nxllcorner\t0\nxyllcorner\t0\ncellsize\t1\nNODATA_value\t-9999\n'.format(recordCount)

#Generate a list of fields to include (from the SWD file)
msg("...Generating a list of fields to include")
file = open(swdFile,'r')
line = file.readline()[:-1] #Omit the last character (new line char)
file.close()
lineItems = line.split(",")[3:] #Omit the 1st item (Species,X,Y)
lineItems.append("GRIDCODE") #Add GRIDCODE (to match ASCII results back to CSV later

#Create a cursor to access data in the rv table
msg("Starting to extract data")
cursor = arcpy.da.SearchCursor(respvarsFC,lineItems,whereClause)
fldNames = cursor.fields
total = len(fldNames)
for fld in fldNames:
    fldIndex = cursor.fields.index(fld)
    #msg("   Converting {} [{} of {}]".format(fld,fldIndex+1,total))
    #Initialize output file
    outFile = open(os.path.join(scenarioFolder,"{}.asc".format(fld)),'w')
    outFile.write(asciiHeader)
    for rec in cursor:
        val  = rec[fldIndex]
        outFile.write("{}\n".format(val))
    outFile.close()
    #reset the cursor
    cursor.reset()
del cursor
        
#Create a new batch file to run MaxEnt
# Open the original for reading
origFile = open(origBatchFile,'r')
lineString = origFile.readline()
origFile.close()

#Make a dictioary of key/values from data in the line string
lineObjects = lineString.split()

#Create dictionary of modify values
changeDict = {}
changeDict['outputdirectory'] = scenarioFolder
changeDict['responsecurves'] = 'false'
changeDict['pictures'] = 'false'
changeDict['jackknife'] = 'false'

#Initialize the output file
outFile = open(newBatchFN,'w')

#Modify key objects and write to output
for lineObj in lineObjects:
    lineString = lineObj
    for key,val in changeDict.items():
        if key in lineString:
            lineString = "{}={} ".format(key,val)
            break
    outFile.write("{} ".format(lineString))
    
#Add pointer to projection folder
outFile.write('projectionlayers={}'.format(scenarioFolder))

outFile.close()

