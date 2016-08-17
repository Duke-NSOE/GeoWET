#AQUATIC_GenerateSpeciesList.py
#
# Generates a multivalue list of species for a given ecoregion, or all if specified
#
# REQUIRES the Fish Indicator Species file which lists the species' scientific name
#  along with a 1 in ecoregion columns in which the species is an indicator. Scientific
#  names MUST match the names in the SpeciesOccurrences CSV file
#
# June 2016
# John.Fay@duke.edu

import sys, os
import pandas as pd

sppXLSX = sys.argv[1]   #r'C:\workspace\GeoWET\Data\ToolData\Fish Indicator Species for EEP.xls'
ecoregion = sys.argv[2] #"PIEDMONT"

#Read in the table as a data frame
sppDF = pd.read_excel(sppXLSX,sheetname="IndicatorSppTable")

#Create the dataframe used to grab species
if ecoregion == "ALL":
    #If all ecoregions are specified, return all species
    outDF = sppDF.ScientificName
else:
    #Otherwise return selected records
    outDF = sppDF.ScientificName[sppDF[ecoregion] == 1]
    print "{} species selected".format(len(outDF))

#Generate multilist string from the selected species
outStr = ""
for spp in outDF.values:
    outStr += ";{}".format(spp)
outStr = outStr

#Set the output, if called from ArcMap
try:
    arcpy.AddMessage("Saving table")
    arcpy.SetParameterAsText(2,outStr)
except:
    pass
