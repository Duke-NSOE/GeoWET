# HABMODEL_CreateMaxentUpliftBatchFile.py
#
# Creates a batch file (.bat) used to run MaxEnt with the supplied files. The way
#  this script is configured, the MaxEnt.jar file must live in the project's
#  scripts folder. This script also searches for all scenario output files (xx_Output)
#  and adds projection info for those runs.
#
# Inputs include the MaxEnt samples with data format (SWD) CSV file, 
#
#  Model outputs will be sent to the Outputs folder in the MaxEnt directory.They include
#   the "runmaxent.bat" batch file and a final list of variables included in the analysis. 
#
# Spring 2015
# John.Fay@duke.edu

import sys, os, arcpy

# Input variables
speciesName = arcpy.GetParameterAsText(0)       # MaxEnt SWD formatted CSV file
statsRootFolder = arcpy.GetParameterAsText(1)   # Root folder holding data for all species
autorun = arcpy.GetParameterAsText(2)           # Whether or not to set autorun

# Number of processors to run on
numProcessors = 16

## ---Functions---
def msg(txt,type="message"):
    print txt
    if type == "message":
        arcpy.AddMessage(txt)
    elif type == "warning":
        arcpy.AddWarning(txt)
    elif type == "error":
        arcpy.AddError(txt)
        
def checkFile(fileName):
    #Checks whether file exists. Sends error and exits if not. 
    if not os.path.exists(fileName):
        msg("File {} does not exist.\nExiting.".format(fileName),"error")
        sys.exit(1)
    else:
        return
## ---Get derived files--
# Check that the maxent.jar file exists in the scripts folder
msg("Locating Maxent.jar file")
maxentJarFile = os.path.dirname(sys.argv[0])+"\\maxent.jar"
checkFile(maxentJarFile)

msg("Getting input files for {}".format(speciesName))
msg("...Getting species sub-folder")
sppFolder = os.path.join(statsRootFolder,speciesName)
checkFile(sppFolder)

msg("...Getting SWD file")
swdFile = os.path.join(sppFolder,"{}_SWD.csv".format(speciesName))
checkFile(swdFile)

# Check that the output folder exists; create it if not
outDir = os.path.abspath(os.path.dirname(swdFile)+"\\Output")
if not(os.path.exists(outDir)):
    msg("Creating model output directory")
    os.mkdir(outDir)
else: msg("Setting model output to {}".format(outDir))

# Output Maxent batch file
msg("Initializing maxent batch file")
maxentFile = os.path.join(os.path.dirname(swdFile),"RunMaxentProjections.bat")
arcpy.SetParameterAsText(2,maxentFile)

## ---Processes---
# Search for projection folders and build a list of them
msg("Searching for projection folders")
projFldrs = ""
for f in os.walk(sppFolder).next()[1]:
    if "_Output" in f:
        msg("...adding {}".format(f))
        fullPath = os.path.join(sppFolder,f)
        projFldrs += ",{}".format(fullPath)

# Begin creating the batch run string with boilerplate stuff
msg("Initializing the Maxent batch command")
runString = "java -Xmx4G -jar {}".format(maxentJarFile)

# set samples file
msg("...Setting samples file to \n    {}".format(swdFile))
runString += " samplesfile={}".format(swdFile)

# set enviroment layers file
msg("...Setting enviroment layers file to \n    {}".format(swdFile))
runString += " environmentallayers={}".format(swdFile)
    
# set output directory
msg("...Setting output directory to {}\n    ".format(outDir))
runString += " outputdirectory={}".format(outDir)

# disable response curves
msg("...Disabling response curves")
runString += " responsecurves=false"

# disable pictures
msg("...Disabling drawing pictures")
runString += " pictures=false"

# disable plots
msg("...Disabling drawing plots")
runString += " plots=false"

# disable jackknifing
msg("...Disabling jackknifing")
runString += " jackknife=false"

### write background predictions
##msg("...writing background predictions")
##runString += " writebackgroundpredictions=false"

### write plot data
##msg("...enabling writing plot data")
##runString += " writeplotdata=true"

# Set nodata value 
msg("...Setting NoData value to -9999")
runString += " nodata=9999"

# enable 8 threads to speed processing
msg("...Running Maxent on {} processors".format(numProcessors))
runString += " threads={}".format(numProcessors)

# setting to autorun
if autorun == "true":
    msg("...Setting autorun ON")
    runString += " autorun=true"
else:
    msg("...Setting autorun OFF")
    runString += " autorun=false"

# turn off background spp
msg('...Toggling "Background" species')
runString += " togglespeciesselected=Background"
           
# Set stream order and FCODE to categorical fields (if not excluded)
flds = []
for fld in arcpy.ListFields(swdFile):
    flds.append(fld.name)

for catItem in ("StreamOrde","FCODE"):
    if catItem in flds:
        msg("...Setting <{}> to categorical".format(catItem))
        runString += " togglelayertype={}".format(catItem)

# Set projection folders
if projFldrs:
    msg("Adding projection folders to analysis")
    runString += " projectionlayers={}".format(projFldrs[1:]) #[1:] is to remove initial comma 

# Write commands to batch file
msg("Writing commands to batchfile {}".format(maxentFile))
outFile = open(maxentFile,'w')
outFile.write(runString)
outFile.close()


    
