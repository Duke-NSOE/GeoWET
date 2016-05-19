# UPLIFT_DispayCurrentConditions.py
#
# Displays current conditions (species likelihood averaged across all indicator
#  species) in the current map. Classes are set as deciles with a user range of
#  values removed from the decile computation (to eliminate zeros).
#
# Jan 2016, John.Fay@duke.edu

import sys, os, arcpy
from arcpy import mapping as mp

#Paths
scriptDir = os.path.dirname(sys.argv[0])
rootDir = os.path.dirname(scriptDir)

#Inputs
mxd = mp.MapDocument(os.path.join(rootDir,"HabitatPrioritizationTool.mxd"))
ecoregion = "Piedmont"
scenario = "BF"
scenarioFC = os.path.join(rootDir,"Data\\{0}\\{1}_Uplift.gdb\\{1}_Uplift03050102".format(ecoregion,scenario))
baseLyrFile = os.path.join(scriptDir,"LyrFiles","CurrentConditionsBase.lyr")

# ---Functions---
def msg(txt,type="message"):
    print txt
    if type == "message":
        arcpy.AddMessage(txt)
    elif type == "warning":
        arcpy.AddWarning(txt)
    elif type == "error":
        arcpy.AddError(txt)

#Get the data fram
df = mp.ListDataFrames(mxd)[0]

#Create the layer
lyr = mp.Layer(scenarioFC)

#Create the symbology for the layer using the base
baseLyr = mp.Layer(baseLyrFile)
symb = 