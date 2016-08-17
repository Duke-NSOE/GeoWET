#AQUATIC_RunMaxentBatches.py
#
#Locates and runs all batch files in sequence.
#
# This script requires 64-bit Java installed on the machine.
#  Download at: https://java.com/en/download/manual.jsp
#  and then 
#
# NOTE: to allocate space for java to run, see:
#   http://stackoverflow.com/questions/18040361/java-could-not-reserve-enough-space-for-object-heap-error
#
# June 2016
# John.Fay@duke.edu

import sys, os

#Inputs
modelFolder = sys.argv[1]#r'C:\workspace\GeoWET\Data\SpeciesModels'
prjFilenames = sys.argv[2]#r'C:\workspace\GeoWET\Scratch\ExampleProject_SWD1.csv'
species = sys.argv[3].split(";")

#Derived inputs
prjFilename = prjFilenames.replace(";",",")

#Msg function
def msg(txt):
    print txt
    try:
        arcpy.AddMessage(txt)
    except:
        pass

def getCommand(fileName):
    '''Returns the entire batch command as a string'''
    with open(fileName,'rt') as fileObj:
        cmd = fileObj.readline()
    return cmd      

def setAutorun(cmd,bool=True):
    '''Sets the Maxent Autorun option to the value specified. True by default.'''
    if bool:
        outCmd = cmd.replace("autorun=false","autorun=true")
    else:
        outCmd = cmd.replace("autorun=true","autorun=false")
    return outCmd      

def setProjectFN(cmd,projFN):
    '''Adds the projection filename(s) in the MaxEnt command'''
    #Augment the root project name with its CUR counterpart. 
    #Get any existing project name
    origFN = cmd.split("=")[-1]
    if origFN == '':
        #If none, add the projFN
        outCmd = cmd + projFN
    else:
        #Else replace the proj FN
        outCmd = cmd.replace(origFN,projFN)
    return outCmd    

#Get a list of batch files
os.chdir(modelFolder)
allFiles = os.listdir(modelFolder)

#Loop through files; adjust and run if a batch file
for f in allFiles:
    if f[-4:] == ".bat" and f[:-4] in species:
        msg("Processing {}".format(f))
        #Process only if in selected species
        #Expand to its full path
        fullFN = os.path.join(modelFolder,f)
        #Get the unmodified Maxent batch file
        runCmd = getCommand(fullFN)
        #Set autorun to true
        runCmd = setAutorun(runCmd)
        #Change the project filename
        if prjFilename not in ("#",""):
            runCmd = setProjectFN(runCmd,prjFilename)
        msg(runCmd)
        os.system(runCmd)
        