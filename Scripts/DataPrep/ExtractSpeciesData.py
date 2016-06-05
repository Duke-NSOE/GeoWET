#ExtractSpeciesData.py
#
# Summary: Extracts catchment data for HUC8s in which species occurs.
#
# Workflow: Pulls catchment records where the species occurs and creates
#  a list of the unique HUC8s from these records. Then extracts catchment
#  data for these HUC8s and writes them all to a table
#
# June 2016
# John.Fay@duke.edu

import sys, os
import pandas as pd
import numpy as np

#Species to process
spp = "Acantharchus_pomotis"

#Workspaces
eoCSV = r'C:\workspace\GeoWET\Data\ToolData\SpeciesOccurrences.csv'
dataFldr = r'C:\workspace\GeoWET\Data\StreamCat\AllRegions'
outFN = r'C:\workspace\GeoWET\Data\SpeciesModels\{}.csv'.format(spp)

##Functions##
def getHUC8s(eoCSV,speciesName):
    '''Returns a list of the HUC8s in which a species occurs'''
    #Create a data frame from the species data
    useCols = ["REACHCODE",spp]
    eoDF = pd.read_csv(eoCSV,usecols=useCols,dtype={'REACHCODE':str})
    #Pull just the records where the species occurs
    sppDF = eoDF[eoDF[spp] == 1]
    #Get a list of the huc8s in which the spp is found
    huc8s = sppDF['REACHCODE'].str[:8].unique()
    #Return the list
    return huc8s.tolist()

def spatialSelect(dataFN,huc8List):
    '''Returns a dataframe of the catchment attributes for the HUC8s in the list'''
    #Load the catchment attributes into a data frame
    dtypes = {"GRIDCODE":np.str,"FEATUREID":np.str,"REACHCODE":np.str,"HUC_12":np.str} 
    dataDF = pd.read_csv(dataFN,dtype=dtypes)

    #Filter the cachment attributes for the HUC8s
    selectDF = dataDF[dataDF["HUC_12"].str[:8].isin(huc8s)]
    return selectDF

def mergePresAbs(eoCSV,speciesName,dataDF):
    '''Adds a column of species presence/absence to the dataFN'''
    #Create a data frame from the species data
    useCols = ["FEATUREID",spp]
    eoDF = pd.read_csv(eoCSV,usecols=useCols,dtype={'FEATUREID':str})
    
    #Join the species data to the catchment data frame
    idxDF = dataDF.set_index("FEATUREID")
    outDF = pd.merge(eoDF,idxDF,left_on="FEATUREID",right_index=True)

    #Change NaNs to 0
    outDF[spp].fillna(0,inplace=True)
    return outDF

#Get the HUC8s
huc8s = getHUC8s(eoCSV, spp)
print "{} was found in {} HUC8s".format(spp, len(huc8s))

#Loop through StreamCat tables and create a dataframe of HUC8 records
allFiles = os.listdir(dataFldr)
dataFrames = []
firstFile = True
for f in allFiles:
    if f[-4:] == ".csv":
        fullFN = os.path.join(dataFldr,f)
        print "Extracting records from {}".format(f)
        dataDF = spatialSelect(fullFN,huc8s)
        print "...{} catchment records extracted".format(len(dataDF))
        #If not the first file, then remove the 1st 5 columns (duplicates)
        if  firstFile:
            #dataDF = dataDF[dataDF.columns[1:]]
            firstFile = False
        else:
            dataDF = dataDF[dataDF.columns[5:]]
        dataFrames.append(dataDF)

#Merge dfs into one
print "Merging data frames"
dataDF = pd.concat(dataFrames,axis=1)

#Prepend with spp presense/absence
print "Adding species presence/absence column"
outDF = mergePresAbs(eoCSV,spp,dataDF)

print "Resulting table has {0} columns and {1} records".format(dataDF.shape[1],dataDF.shape[0])

#Write to a file for the spp
print "Saving to {}".format(outFN)
outDF.to_csv(outFN,index_label="OID")


##NEXT STEPS
# Remove COLUMNS where spp is present but has -9999 in an attribute
# Remove RECORDS where spp is not presence but has -9999 in an attribute
# Identify and remove COLUMNS that don't have a correlation with presence/absence
# Identify cross correlated columns; remove lower ranking column
  ## Need to develope column ranking table
# End result is a table of records and attribues to model with Maxent
  ## Generate a table of modified conditions on which to project Maxent results