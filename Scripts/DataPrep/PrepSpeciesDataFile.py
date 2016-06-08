#PrepSpeciesData.py
#
# Remove RECORDS where spp is not presence but has -9999 in an attribute
# Remove COLUMNS where spp is present but has -9999 in an attribute
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
from scipy import stats

#Get the species file
sppName = 'Nocomis_leptocephalus'
sppFN = r'C:\workspace\GeoWET\Data\SpeciesModels\{}.csv'.format(sppName)
outFN = r'C:\workspace\GeoWET\Data\SpeciesModels\{}_swd.csv'.format(sppName)

#Read in file as pandas dataframe
print "Reading data for {}".format(sppName)
sppDF = pd.read_csv(sppFN)

def removeAbsenceNullRows(theDF):
    '''Remove ROWS where spp is absence and attribute has -9999'''
    #Loop through each field
    for fld in list(theDF.columns):
        #Get the number of records before deletion
        dbSize = len(theDF)
        theDF = theDF[~((theDF.Species == 'Background') & (theDF[fld] == -9999))]
        #Calculate the number of records deleted
        dbDelta = dbSize - len(theDF)
        #LOGGING: Report how many records deleted for the current field
        #if dbDelta > 0:
            #print "...{} records removed via {} field".format(dbDelta,fld)
    return theDF

def removePresenceNullColumns(theDF):
    '''Remove COLUMNS with missing data in species presence rows'''
    for fld in list(theDF.columns):
        #Get the min value of the field
        if theDF[fld].min() == -9999:
            #Drop the fields
            #print "...Removing: {}".format(fld)
            theDF.drop(fld,axis=1,inplace=True)
    return theDF

def removeUncorrelated(theDF):
    '''Remove attributes with no correlation with presence/absence'''
    sppVector = theDF.Species
    #Convert species/background to binary 1/0
    sppVector.replace("Background",0,inplace=True)
    sppName = pd.unique(sppVector).tolist()[1]
    sppVector.replace(sppName,1,inplace=True)
    #Compute correlation with presence/absence
    for fld in list(theDF.columns)[6:]:
        envVector = theDF[fld]
        pearson = stats.pearsonr(sppVector, envVector)
        coeff = pearson[0]
        pValue = pearson[1]
        #Print output to the CSV file
        if abs(pValue) > 0.05:
            #print "%s is not significant (p = %2.3f)" %(fld,pValue)
            theDF.drop(fld,axis=1,inplace=True)
    #Return column values
    sppVector.replace(0,"Background",inplace=True)
    sppVector.replace(1,sppName,inplace=True)
    return theDF

def removeXCorrelated(theDF,threshold=0.75):
    #Initialize the list of fields to drop
    dropFlds = []
    #Include only StreamCat attributes
    flds = list(theDF.columns)[6:]
    nCols = len(flds)
    #Compute cross correlation pairs; add 2nd field to drop list
    for i in range(0,nCols):
        for j in range(0,nCols):
            if j > i:
                iFld = flds[i]; jFld =flds[j]
                v1 = theDF[iFld]
                v2 = theDF[jFld]
                # Calculate the correlation coefficient
                pearson = stats.pearsonr(v1, v2)[0]
                # If the coefficient is > the threshold consider them redundant and add to the CSV
                if abs(pearson) >= float(threshold):
                    #print "{}, {}, {}".format(iFld,jFld,pearson)
                    #Need ranking to decide which field to drop
                    #For now, just drop the 2nd field
                    if not (jFld in dropFlds): dropFlds.append(jFld)
    #Drop cross correlated fields
    for dropFld in dropFlds:
        theDF.drop(dropFld,axis=1,inplace=True)
    #Return the data frame
    return theDF

#-------------------------------------------------------------            
print "Removing absence records with no catchment data"
print "...Starting with {} records".format(len(sppDF))
sppDF = removeAbsenceNullRows(sppDF)
print "...{} records remain".format(len(sppDF))

print "Removing attributes with null values"
print "...Starting with {} columns".format(sppDF.shape[1])
sppDF = removePresenceNullColumns(sppDF)
print "...{} columns remain".format(sppDF.shape[1])

print "Removing attributes not correlated with presence absence"
print "...Starting with {} columns".format(sppDF.shape[1])
sppDF = removeUncorrelated(sppDF)
print "...{} columns remain".format(sppDF.shape[1])

print "Removing cross correlated attributes"
print "...Starting with {} columns".format(sppDF.shape[1])
sppDF = removeXCorrelated(sppDF)
print "...{} columns remain".format(sppDF.shape[1])

print "Adjusting column names to work with MaxEnt" #SPP,X,Y
sppDF.rename(columns = {'GRIDCODE':'X','REACHCODE':'Y'}, inplace=True)
sppDF.drop('OID',axis=1,inplace=True)
sppDF.drop('FEATUREID',axis=1,inplace=True)
sppDF.drop('HUC_12',axis=1,inplace=True)

#write file to csv
sppDF.to_csv(outFN,index_label="OID",index=False)