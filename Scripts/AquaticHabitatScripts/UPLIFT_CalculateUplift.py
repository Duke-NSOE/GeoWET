# UPLIFT_CalculateUplift.py
#
# Description: Computes the difference between habitat likelihood under current and uplift
#  scenarios and stored the output as a table for the species.
#
#  Prior to running this script,Maxent needs to be run for the current conditions with the output
#   saved in the XX_Output sub-folder within the species stats folder. The current conditions run
#   must use the same HUCFilter as the scenario run. 
#
# Pseudo-code:
#  - Locates Maxent output files
#  - Pulls GRIDCODE values from the GRIDCODE.asc file
#  - Pulls the likelihood values from the current conditions projected ASC file
#  - Pulls the likelihood values from the scenario conditions projected ASC file
#  - Creates a CSV file of GRIDCODE, current likelihood, future likelihood, and uplift
#
# Sept 2015, John.Fay@duke.edu

# Import arcpy module
import sys, os, arcpy

# Check out any necessary licenses
arcpy.CheckOutExtension("spatial")

#User variables
speciesName = arcpy.GetParameterAsText(0)
scenarioName = arcpy.GetParameterAsText(1)   # Prefix used to identify outputs
statsFolder = arcpy.GetParameterAsText(2)    # Stats root folder containing all species models
speciesFC = arcpy.GetParameterAsText(3)      # Input catchment feature class; used to display output values 
HUCFilter = arcpy.GetParameterAsText(4)      # HUC filter

#Set environments
arcpy.env.overwriteOutput = True

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
        msg("{} not found.\nExiting.".format(fileName),"error")
        sys.exit(1)
    else: return
    
##---DERIVED INPUTS---
#Get the species stats folder in the stats root folder
msg("...Locating the species folder")
sppFolder = os.path.join(statsFolder,speciesName)
checkFile(sppFolder)

#Get the output folder
msg("...Locating the uplift output folder ({}_Uplift.gdb".format(scenarioName))
outGDB = os.path.join(statsFolder,"{}_Uplift.gdb".format(scenarioName))
checkFile(outGDB)

#Get the scenario folder holding all the Maxent run results
msg("...Locating the scenario folder")
scenarioFolder = os.path.join(sppFolder,"{}_Output".format(scenarioName))
checkFile(scenarioFolder)

#Get the GRIDCODE.asc file (scenario folder); this is an ordered listing of gridcodes use to match output to catchments
msg("...Locating GRIDCODE.asc file")
gridcodeASC = os.path.join(scenarioFolder,"GRIDCODE.asc")
checkFile(gridcodeASC)

#Get the current conditions (scenario folder); this is the baseline from which uplift is calculated
msg("...Locating the current conditions output for HUC {}".format(HUCFilter))
currentASC = os.path.join(sppFolder,"XX_Output","{}_XX_Output.asc".format(speciesName))
#If it's not there, check the main output folder
if not os.path.exists(currentASC):
    msg("Projected output not found in {}_XX_Output.asc. Searching the main folder.".format(speciesName))
    currentASC = os.path.join(sppFolder,"Output","{}_XX_Output.asc".format(speciesName))
    checkFile(currentASC)
    msg("...Found it!")

#Get the ASCII file containing the projected likelihood
msg("...Locating the projected conditions output for HUC {}".format(HUCFilter))
projectedASC = os.path.join(scenarioFolder,"{}_{}_Output.asc".format(speciesName,scenarioName))
if not os.path.exists(projectedASC):
    msg("Projected output not found in {}_XX_Output.asc. Searching the main folder.".format(speciesName))
    projectedASC = os.path.join(sppFolder,"Output","{}_{}_Output.asc".format(speciesName,scenarioName))
    checkFile(projectedASC)
    msg("...Found it!")

#Set output parameters
outTbl = os.path.join(outGDB,"{}_{}".format(speciesName,HUCFilter))
arcpy.SetParameterAsText(5,outTbl)

##---PROCESSES----
# Read in GRIDCODE values from the gridcode ASCII file
file = open(gridcodeASC,'r')
gridcodes = file.readlines()[6:] #skip the first 6 lines (header info)
file.close()

# Read in the current condition projections
file = open(currentASC,'r')
currentPredictions = file.readlines()[6:] #skip the first 6 lines (header info)
file.close()

# Read in the modified condition projections
file = open(projectedASC,'r')
upliftPredictions = file.readlines()[6:] #skip the first 6 lines (header info)
file.close()

# Abbreviate the species name to GSpecie
genus,species = speciesName.split("_")
sppName = genus[0].upper() + species[:6].capitalize()

# Set the projected likelihood field name
curFldName = sppName + "_cur"                   #Likelihood under current conditions
altFldName = sppName + "_" + scenarioName       #Likelihood under alternate conditions
upliftFldName = sppName + "_up"               #Uplift (alternate - current)

# Create the output table
arcpy.CreateTable_management(outGDB,"{}_{}".format(speciesName,HUCFilter))
arcpy.AddField_management(outTbl,"GRIDCODE","LONG")
arcpy.AddField_management(outTbl,curFldName,"DOUBLE")
arcpy.AddField_management(outTbl,altFldName,"DOUBLE")
arcpy.AddField_management(outTbl,upliftFldName,"DOUBLE")

# Create an insert cursor and add records
cursor = arcpy.da.InsertCursor(outTbl,"*")
for i in range(len(gridcodes)):
    gridcode = int(gridcodes[i])
    currentLikelihood = float(currentPredictions[i])
    alternateLikelihood = float(upliftPredictions[i])
    uplift = alternateLikelihood - currentLikelihood
    cursor.insertRow((i,gridcode,currentLikelihood,alternateLikelihood,uplift))
del cursor

tblCount  = int(arcpy.GetCount_management(outTbl).getOutput(0))
if not(tblCount == len(gridcodes)):
    msg("counts don't match: {},{}".format(tblCount,len(gridcodes)),"error")

## Clean up ASC files
fileNames = os.listdir(scenarioFolder)
for fName in fileNames:
    fNameParts = fName.split(".")
    name = fNameParts[0]
    ext = fNameParts[-1]
    if ext == 'asc':
        if speciesName not in name and name not in ("GRIDCODE"):
            os.remove(os.path.join(scenarioFolder,fName))