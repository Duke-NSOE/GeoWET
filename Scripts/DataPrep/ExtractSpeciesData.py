#ExtractSpeciesData.py
#
# Summary: Extracts catchment data for HUC8s in which species occurs and
#  merges the data with species presence absences records.
#
# Usage: ExtractSpeciesData(Species Name,
#                           Species Occurrences,
#                           Stream Cat data folder,
#                           Output CSV filename)
#
# Workflow:
#  - Checks that the supplied species name occurs in the species CSV file.
#  - Creates a list of the HUC8s in which the species has been observed.
#  - Extracts catchment records from each of the Stream Cat CSV file occurring
#    within these HUC8s into a series of pandas data frames.
#  - Merges each individual Stream Cat CSV file into a single pandas dataframe.
#  - Prepends a column of species presence and absence (background) to the
#    merged data frame
#  - Writes the contents out to a CSV file.
#
# June 2016
# John.Fay@duke.edu

import sys, os
import pandas as pd
import numpy as np

#Species to process
spp = "Nocomis_leptocephalus"

#Workspaces
eoCSV = r'C:\workspace\GeoWET\Data\ToolData\SpeciesOccurrences.csv'
dataFldr = r'C:\workspace\GeoWET\Data\StreamCat\AllRegions'
outFN = r'C:\workspace\GeoWET\Data\SpeciesModels\{}.csv'.format(spp)

##--------Functions--------##
def checkSpeciesName(speciesName,eoCSV):
    '''Ensures that the supplied species name exists in the observation table'''
    import csv
    fileObj = open(eoCSV,'rt')
    csvReader = csv.reader(fileObj)
    fldNames = csvReader.next()
    fileObj.close()
    if not speciesName in fldNames:
        print "***{}*** does not occur in the \n   {} file".format(speciesName,eoCSV)
        print "   Check your species name and try again..."
        sys.exit(1)
    else:
        return      

def getHUC8s(eoCSV,speciesName):
    '''Returns a list of the HUC8s in which a species occurs'''
    #Create a data frame from the species data
    useCols = ["REACHCODE",speciesName]
    eoDF = pd.read_csv(eoCSV,usecols=useCols,dtype={'REACHCODE':str})
    #Pull just the records where the species occurs
    sppDF = eoDF[eoDF[speciesName] == 1]
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
    useCols = ["FEATUREID",speciesName]
    eoDF = pd.read_csv(eoCSV,usecols=useCols,dtype={'FEATUREID':str})
    
    #Join the presence absence data to the catchment data frame
    outDF = pd.merge(eoDF,dataDF,how='right',left_on="FEATUREID",right_on="FEATUREID")

    #Add the species field and set default to "background"
    outDF.insert(0,"Species","Background")

    #Change NaNs to "Background
    outDF[speciesName] = outDF[speciesName].fillna(0)

    #Change Species values in records where observed
    outDF.loc[outDF[speciesName] == 1, 'Species'] = speciesName

    #Drop the speciesName column
    outDF.drop(speciesName,axis=1,inplace=True)
    
    return outDF

##------Procedures--------
#Make sure the species name is valid
checkSpeciesName(spp,eoCSV)

#Create a list of HUC8s in which the species was observed
huc8s = getHUC8s(eoCSV, spp)
print "{} was found in {} HUC8s".format(spp, len(huc8s))

##Loop through StreamCat tables and create a dataframe of just the records
##in the HUC8s where the species was found...
allFiles = os.listdir(dataFldr)     # List if all files in the StreamCat folder
dataFrames = []                     # Initialize the list of dataFrames
firstFile = True                    # Initialize variable to see if it's the first variable

for f in allFiles:                  # Loop through the StreamCat files
    if f[-4:] == ".csv":            # Only process the CSV files
        #Get the full file name
        fullFN = os.path.join(dataFldr,f)
        print "Extracting records from {}".format(f)
        #Retrieve only the HUC8 records as a data frame using above function
        dataDF = spatialSelect(fullFN,huc8s)
        print "...{} catchment records extracted".format(len(dataDF))
        #If not the first file, then remove the 1st 5 columns (duplicates)
        if  firstFile:
            firstFile = False
            colNames = list(dataDF.columns)
        else:
            #Cross check the column names to skip duplicates
            newCols = []
            for col in list(dataDF.columns):
                if not (col in colNames):
                    newCols.append(col)
            dataDF = dataDF[newCols]
        #Convert columns to smaller datatypes to save memory
        for c in dataDF.columns:
            if dataDF[c].dtype.type == np.float64:
                dataDF[c]= dataDF[c].astype(np.float32)
        #Append to the list of data frames
        dataFrames.append(dataDF)

#Merge all file data frames into one
print "Merging data frames"
dataDF = pd.concat(dataFrames,axis=1)

#Remove single dfs to free memory
del dataFrames

#Add species presence absence data
print "Prepending presence absence to data frame"
outDF = mergePresAbs(eoCSV,spp,dataDF)

#Remove the OID column
outDF.drop("OID",axis=1,inplace=True)
print "Resulting table has {0} columns and {1} records".format(outDF.shape[1],outDF.shape[0])

#Write to a file for the spp
print "Saving to {}".format(outFN)
outDF.to_csv(outFN,index_label="OID")
