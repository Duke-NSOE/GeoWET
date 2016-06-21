#AQUATIC_GenerateSpeciesList.py
#
# Generates a multivalue list of species for a given ecoregion

import sys, os
import pandas as pd

sppXLSX = sys.argv[1]#r'C:\workspace\GeoWET\Data\ToolData\Fish Indicator Species for EEP.xls'
ecoregion = sys.argv[2] #"PIEDMONT"

#Read in the table as a data frame
sppDF = pd.read_excel(sppXLSX,sheetname="IndicatorSppTable")

#Select records
outDF = sppDF.ScientificName[sppDF[ecoregion] == 1]
print "{} species selected".format(len(outDF))

#Generate multilist
outStr = ""
for spp in outDF.values:
    outStr += ";{}".format(spp)
outStr = outStr

try:
    arcpy.SetParameterAsText(2,outStr)
except:
    pass
