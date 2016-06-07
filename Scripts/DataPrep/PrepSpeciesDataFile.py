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
sppName = 'Acantharchus_pomotis'
sppFN = r'C:\workspace\GeoWET\Data\SpeciesModels\{}.csv'.format(sppName)

#Read in file as pandas dataframe
if not ("initialDF" in dir()):
    print "Reading data for {}".format(sppName)
    initialDF = pd.read_csv(sppFN)
    
sppDF = initialDF #pd.read_csv(sppFN)

def removeAbsenceNullRows(theDF):
    '''Remove ROWS where spp is absence and attribute has -9999'''
    #Loop through each field
    for fld in list(theDF.columns):
        #Get the number of records before deletion
        dbSize = len(theDF)
        theDF = theDF[~((theDF[sppName] == 0) & (theDF[fld] == -9999))]
        #Calculate the number of records deleted
        dbDelta = dbSize - len(theDF)
        #LOGGING: Report how many records deleted for the current field
        if dbDelta > 0:
            print "...{} records removed via {} field".format(dbDelta,fld)
    return theDF

def removePresenceNullColumns(theDF):
    '''Remove COLUMNS with missing data in species presence rows'''
    for fld in list(theDF.columns):
        #Get the min value of the field
        if theDF[fld].min() == -9999:
            #Drop the fields
            print "...Removing: {}".format(fld)
            theDF.drop(fld,axis=1,inplace=True)
    return theDF

def removeUncorrelated(theDF):
    '''Remove attributes with no correlation with presence/absence'''
    theDF = sppDF3
    threshold = 0.7
    sppVector = theDF[sppName]
    for fld in list(theDF.columns)[7:]:
        envVector = theDF[fld]
        pearson = stats.pearsonr(sppVector, envVector)
        coeff = pearson[0]
        pValue = pearson[1]
        #Print output to the CSV file
        if abs(pValue) > 0.05:
            print "%s is not significant (p = %2.3f)" %(fld,pValue)
            theDF.drop(fld,axis=1,inplace=True)
    return theDF

#-------------------------------------------------------------            
print "Removing absence records with no catchment data"
print "...Starting with {} records".format(len(sppDF))
#sppDF2 = removeAbsenceNullRows(sppDF)
print "...{} records remain".format(len(sppDF2))

print "Removing attributes with null values"
print "...Starting with {} columns".format(sppDF2.shape[1])
#sppDF3 = removePresenceNullColumns(sppDF2)
print "...{} columns remain".format(sppDF3.shape[1])

print "Removing attributes not correlated with presence absence"
print "...Starting with {} columns".format(sppDF3.shape[1])
sppDF4 = removeUncorrelated(sppDF3)
print "...{} columns remain".format(sppDF3.shape[1])


   