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
spp = "Etheostoma_olmstedi"
#spp = "Acantharchus_pomotis"

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

def getFeatureIDs(eoCSV,speciesNames):
    '''Returns a list of the FEATUREIDS in which a species occurs'''
    #Create a data frame from the species data
    useCols = ["FEATUREID",spp]
    eoDF = pd.read_csv(eoCSV,usecols=useCols,dtype={'FEATUREID':str})
    #Pull just the records where the species occurs
    sppDF = eoDF[eoDF[spp] == 1]
    #Get a list of the huc8s in which the spp is found
    FeatureIDs = sppDF['FEATUREID']
    #Return the list
    return FeatureIDs.tolist()

def makeSpeciesDF(eoCSV,dataDF,speciesNames):
    '''Returns a dataframe of feature IDs where the species is present'''
    #Create a data frame from the species data
    useCols = ["FEATUREID",spp]
    eoDF = pd.read_csv(eoCSV,usecols=useCols,dtype={'FEATUREID':str})
    #Pull just the records where the species occurs
    sppDF = pd.merge(dataDF,eoDF,how='inner',left_on="FEATUREID",right_on="FEATUREID")
    #sppDF = eoDF[eoDF[spp] == 1]
    
    #Change NaNs to 0
    sppDF[spp].fillna(0,inplace=True)
    
    return sppDF#[spp]
    #THen concat this with the others

def assignPresence(df,spp,FeatureIDs):
    '''Adds a column and assigns 1 to presence values'''
    #Insert column, assign zero as default
    df.insert(0,spp,0)
    #Select records with matching FeatureIDs
    for FeatureID in FeatureIDs:
        df.ix[df.FEATUREID == FeatureID,spp] = 1

def mergePresAbs(eoCSV,speciesName,dataDF):
    '''Adds a column of species presence/absence to the dataFN'''
    #Create a data frame from the species data
    useCols = ["FEATUREID",spp]
    eoDF = pd.read_csv(eoCSV,usecols=useCols,dtype={'FEATUREID':str})
    
    #Join the presence absence data to the catchment data frame
    idxDF = dataDF.set_index("FEATUREID")
    #outDF = pd.merge(eoDF,idxDF,left_on="FEATUREID",right_index=True)
    outDF = pd.merge(df,eoDF,how='inner',left_on="FEATUREID",right_on="FEATUREID")

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
    #Only process the CSV files
    if f[-4:] == ".csv":
        #Get the full file name
        fullFN = os.path.join(dataFldr,f)
        print "Extracting records from {}".format(f)
        #Retrieve only the HUC8 records as a data frame
        dataDF = spatialSelect(fullFN,huc8s)
        print "...{} catchment records extracted".format(len(dataDF))
        #If not the first file, then remove the 1st 5 columns (duplicates)
        if  firstFile:
            #Prepend species presence absence to table
            firstFile = False
        else:
            dataDF = dataDF[dataDF.columns[5:]]

        #Convert to smaller datatypes to save memory
        for c in dataDF.columns:
            if dataDF[c].dtype.type == np.float64:
                dataDF[c]= dataDF[c].astype(np.float32)
        #Append to the list of data frames
        dataFrames.append(dataDF)

#Create the species presence/absence data frame
print "Creating presence absence data frame"
#sppDF = makeSpeciesDF(eoCSV,dataFrames[1],spp)
#dataFrames.insert(0,sppDF)

#Merge dfs into one
print "Merging data frames"
dataDF = pd.concat(dataFrames,axis=1)

#Add species presence absence data
outDF = mergePresAbs(eoCSV,spp,dataDF)

#Remove single dfs to free memory
del dataFrames
print "Resulting table has {0} columns and {1} records".format(outDF.shape[1],outDF.shape[0])

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