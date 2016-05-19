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
layerName = arcpy.GetParameterAsText(0)
fldName = arcpy.GetParameterAsText(1)
outLayerFile = arcpy.GetParameterAsText(2)

mxd = mp.MapDocument("CURRENT") #os.path.join(rootDir,"HabitatPrioritizationTool.mxd"))
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

#Get the data frame
df = mxd.activeDataFrame
msg("Getting layer {}".format(layerName))
lyr = mp.ListLayers(mxd,layerName)[0]

msg("Getting existing symbology")
sym = lyr.symbology


