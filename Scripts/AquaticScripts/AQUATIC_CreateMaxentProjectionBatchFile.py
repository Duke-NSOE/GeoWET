# CreateMaxentProjectionBatchFile.py
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

# Inputs
speciesName = 'Acantharchus_pomotis'
sppModelFolder= r'C:\workspace\GeoWET\Data\SpeciesModels'
prjSWDFile = r'C:\workspace\GeoWET\Data\Projects\ExampleProject3_SWD.csv'

# Derived inputs
projectName = os.path.basename(prjSWDFile)[:-4]
lamdasFile = os.path.join(sppModelFolder,speciesName,"{}.lambdas".format(speciesName))                  
outputResultFile = os.path.join(sppModelFolder,"01{}_{}.csv".format(speciesName,projectName))
outputBatchFile = "Foo"

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


# Begin creating the batch run string with boilerplate stuff
msg("Initializing the Maxent batch command")
#runString = "java -mx4096m -d64 -jar {} density.Project ".format(maxentJarFile)
runString = "java -cp {} density.Project ".format(maxentJarFile)

# set lamdas file
msg("...Setting lambdas file to \n    {}".format(lamdasFile))
runString += " {}".format(lamdasFile)

# set projection SWD file
msg("...Setting enviroment layers file to \n    {}".format(prjSWDFile))
runString += " {}".format(prjSWDFile)
    
# set output file
msg("...Setting output file to {}    ".format(outputResultFile))
runString += " {}".format(outputResultFile)

# Write commands to batch file
msg("Writing commands to batchfile {}".format(outputBatchFile))
print runString
os.system(runString)
os.system("notepad {}".format(outputResultFile))



    
