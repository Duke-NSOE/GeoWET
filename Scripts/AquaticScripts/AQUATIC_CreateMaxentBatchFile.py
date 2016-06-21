# CreateMaxentBatchFile.py
#
# Creates a batch file (.bat) used to run MaxEnt with the supplied files. The way
#  this script is configured, the workspace must contain a MaxEnt folder (containing
#  the MaxEnt.jar file) in the project's root folder. 
#
# Inputs include the MaxEnt samples with data format (SWD) CSV file, 
#
#  Model outputs will be sent to the Outputs folder in the MaxEnt directory.They include
#   the "runmaxent.bat" batch file and a final list of variables included in the analysis.
#
# NOTE: to allocate space for java to run, see:
#   http://stackoverflow.com/questions/18040361/java-could-not-reserve-enough-space-for-object-heap-error
#
# Spring 2015
# John.Fay@duke.edu

import sys, os
import pandas as pd


# Inputs
swdFile = sys.argv[1]#r'C:\\workspace\\GeoWET\\Data\\SpeciesModels\\Nocomis_leptocephalus_swd.csv'
prjFile = sys.argv[2]
runMaxent = sys.argv[3]

# Derived inputs
speciesName = os.path.basename(swdFile)[:-8]
speciesFldr = os.path.dirname(swdFile)
maxentFile = os.path.join(speciesFldr,"{}.bat".format(speciesName))

# Number of processors
numProcessors = 16

# Set Autorun in batch file
autorun = "false"

## ---Functions---
def msg(txt,severity=""):
    print txt
    try:
        arcpy.AddMessage(txt)
    except:
        pass
        
## ---Processes---
# Check that the maxent.jar file exists in the scripts folder
maxentJarFile = os.path.dirname(sys.argv[0])+"\\maxent.jar"
if not os.path.exists(maxentJarFile):
    msg("Maxent.jar file cannot be found in Scripts folder.\nExiting.","error")
    sys.exit(0)
else:
    msg("Maxent.jar found in Scripts folder".format(maxentJarFile))

# Check that the output folder exists; create it if not
outDir = os.path.join(speciesFldr,speciesName)
if not(os.path.exists(outDir)):
    msg("Creating output directory")
    os.mkdir(outDir)
else: msg("Setting output to {}".format(outDir))

# Add folder as model output (if run from ArcMap)
try:
    arcpy.SetParameter(3,outDir)
    msg("Output folder set to {}".format(outDir))
except:
    pass

# Begin creating the batch run string with boilerplate stuff
msg("Initializing the Maxent batch command")
runString = "java -mx4096m -d64 -jar {}".format(maxentJarFile)

# set samples file
msg("...Setting samples file to \n    {}".format(swdFile))
runString += " samplesfile={}".format(swdFile)

# set enviroment layers file
msg("...Setting enviroment layers file to \n    {}".format(swdFile))
runString += " environmentallayers={}".format(swdFile)
    
# set output directory
msg("...Setting output directory to {}    ".format(outDir))
runString += " outputdirectory={}".format(outDir)

# enable response curves
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

# enable overwrite
msg("...Allowing overwriting existing output")
runString += " askoverwrite=false"

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
'''           
# Set stream order and FCODE to categorical fields (if not excluded)
flds = []
for fld in arcpy.ListFields(swdFile):
    flds.append(fld.name)

for catItem in ("StreamOrde","FCODE"):
    if catItem in flds:
        msg("...Setting <{}> to categorical".format(catItem))
        runString += " togglelayertype={}".format(catItem)
'''

#Add Projection file, if supplied
if prjFile <> "#":
    msg("Setting projection file to {}".format(prjFile))
    runString += " projectionlayers={}".format(prjFile)

# Write commands to batch file
msg("Writing commands to batchfile {}".format(maxentFile))
outFile = open(maxentFile,'w')
outFile.write(runString)
outFile.close()

# Run MaxEnt, if set
if runMaxent == 1:
    msg("Running Maxent")
    os.system(maxentFile)
    
