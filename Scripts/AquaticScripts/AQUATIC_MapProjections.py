#AQUATIC_MapProjections.py
#
# Merges projected habitat likelihood with current conditions to
# map uplift for each catchment.

import sys, os
import pandas as pd
import numpy as np
import arcpy

#Inputs
species = "Percina_nevisense"
sppFolder = r'C:\workspace\GeoWET\Data\SpeciesModels'
currentFN = sppFolder+'\{0}\{0}.csv'.format(species)
projectFN = sppFolder+'\{0}\{0}_ExampleProject_SWD.csv'.format(species)
catchmentFN = r'C:\workspace\GeoWET\Data\ToolData\NC_Results.gdb\CatchmentAttributes'

#Output
outputFC = r'C:\workspace\GeoWET\scratch\{}_Uplift.shp'.format(species)

#Read in the Maxent results as dataframes
cDF = pd.read_csv(currentFN, dtype={'X':np.long})
pDF = pd.read_csv(projectFN, dtype={'GRIDCODE':np.long})

#Join the cDF values to the pDF
allDF = pd.merge(pDF,cDF,how='outer',left_on='GRIDCODE',right_on="X")



