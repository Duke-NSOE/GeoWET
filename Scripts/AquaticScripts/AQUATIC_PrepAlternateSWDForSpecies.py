#AQUATIC_PrepAlternateSWDForSpecies.py
#
# Prepares a generic projection SWD for use in a species model.
#  Essentially, it just removes the columns not in the species
#  SWD file.
#
# June 2016
# John.Fay@Duke.edu

import sys, os
import pandas as pd

#Get the files
speciesSWDFile = r'C:\workspace\GeoWET\Scratch\SppModels\Nocomis_leptocephalus_SWD.CSV'
projectSWDFile = r'C:\workspace\GeoWET\Scratch\SppModels\ExampleProject_SWD.csv'
saveSWDFile = r'C:\workspace\GeoWET\Scratch\SppModels\Nocomis_leptocephalus_ALT.CSV'

#Convert to dataframes
sppDF = pd.read_csv(speciesSWDFile)
prjDF = pd.read_csv(projectSWDFile)

#Get list of columns
sppCols = sppDF.columns

for prjCol in prjDF.columns:
    if prjCol not in sppCols:
        print "Drop {}".format(prjCol)
        prjDF.drop(prjCol,axis=1,inplace=True)

#Write out to csv file
prjDF.to_csv(saveSWDFile,index_label="OID",index=False)
