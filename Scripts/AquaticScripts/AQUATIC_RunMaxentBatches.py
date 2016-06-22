#AQUATIC_RunMaxentBatches.py
#
#Locates and runs all batch files in sequence
#
# June 2016
# John.Fay@duke.edu

import sys, os

#Inputs
modelFolder = r'C:\workspace\GeoWET\Data\SpeciesModels'
prjFilename = r'C:\workspace\GeoWET\Scratch\ExampleProject_SWD1.csv'

#Msg function
def msg(txt):
    print txt
    try:
        arcpy.AddMessage(msg)
    except:
        pass

def getCommand(fileName):
    with open(fileName,'rt') as fileObj:
        cmd = fileObj.readline()
    return cmd      

def setAutorun(cmd,bool=True):
    if bool:
        outCmd = cmd.replace("autorun=false","autorun=true")
    else:
        outCmd = cmd.replace("autorun=true","autorun=false")
    return outCmd      

def setProjectFN(cmd,projFN):
    #Get the project name
    origFN = cmd.split("=")[-1]
    outCmd = cmd.replace(origFN,projFN)
    return outCmd    

#Get a list of batch files
os.chdir(modelFolder)
allFiles = os.listdir(modelFolder)

#Loop through files; run if a batch file
for f in allFiles:
    if f[-4:] == ".bat":
        fullFN = os.path.join(modelFolder,f)
        runCmd = getCommand(fullFN)
        #Set autorun to true
        runCmd = setAutorun(runCmd)
        #Change the project filename
        if prjFilename not in ("#",""):
            runCmd = setProjectFN(runCmd,prjFilename)
        msg(runCmd)
        os.system(runCmd)