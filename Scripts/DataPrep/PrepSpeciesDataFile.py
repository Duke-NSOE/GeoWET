#PrepSpeciesData.py
#
# Remove COLUMNS where spp is present but has -9999 in an attribute
# Remove RECORDS where spp is not presence but has -9999 in an attribute
# Identify and remove COLUMNS that don't have a correlation with presence/absence
# Identify cross correlated columns; remove lower ranking column
  ## Need to develope column ranking table
# End result is a table of records and attribues to model with Maxent
  ## Generate a table of modified conditions on which to project Maxent results
#
# June 2016
# John.Fay@duke.edu

import sys, os
import pandas as pd

#Get the species file
sppName = 'Acantharchus_pomotis'
sppFN = r'C:\workspace\GeoWET\Data\SpeciesModels\{}.csv'.format(sppName)

#Read in file as pandas dataframe
#sppDF = pd.read_csv(sppFN)

#Remove rows where spp is absence and attribute has -9999
absencesDF = sppDF[sppDF[sppName] == 0]

flds = list(absencesDF.columns)

