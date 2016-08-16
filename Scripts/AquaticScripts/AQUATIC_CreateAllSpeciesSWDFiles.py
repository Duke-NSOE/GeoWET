#AQUATIC_CreateAllSpeciesSWDFiles.py
#
# SUMMARY: Loops through all species found in the SpeciesOccurrences.csv file, 
#  and extracts catchment data for HUC8s in which species occurs,
#  merges these records with species presence absences records, and then
#  culls data (rows and then columns) to eliminate Null values. 
#
# USAGE: ExtractSpeciesData(Species Occurrences CSV file,
#                           Stream Cat data folder, Output SWD filename)
#
# REQUIREMENTS: pandas, numpy, scipy
#
# WORKFLOW:
#  - Checks that the supplied species name occurs in the species CSV file.
#  - Creates a list of the HUC8s in which the species has been observed.
#  - Extracts catchment records from each of the Stream Cat CSV file occurring
#    within these HUC8s into a series of pandas data frames.
#  - Merges each individual Stream Cat CSV file into a single pandas dataframe.
#  - Prepends a column of species presence and absence (background) to the
#    merged data frame
#  - Remove RECORDS where spp is not present but has -9999 in an attribute
#  - Remove COLUMNS where spp is present but has -9999 in an attribute
#  - Identify and remove COLUMNS that don't have a correlation with presence/absence
#  - Identify cross correlated columns; remove lower ranking column
#  - Arranges columns for MaxEnt processing 
#  - Writes out the records as CSV file in MaxEnt SWD format
#
# June 2016
# John.Fay@duke.edu

import sys, os, datetime
import pandas as pd
import numpy as np
from scipy import stats
import arcpy

#Script inputs
rootFldr = os.path.dirname(os.path.dirname(os.path.dirname(sys.argv[0])))
eoCSV = os.path.join(rootFldr,"Data","ToolData","SpeciesOccurrences.csv")
streamCatFldr = os.path.join(rootFldr,"Data","StreamCat","AllRegions")
speciesFldr = os.path.join(rootFldr,"Data","SpeciesModels")
#sppName = sys.argv[1] #'Nocomis_leptocephalus'
#streamCatFldr = sys.argv[1] #r'C:\workspace\GeoWET\Data\StreamCat\AllRegions'
#eoCSV = sys.argv[2] #r'C:\workspace\GeoWET\Data\ToolData\SpeciesOccurrences.csv'
#outFN = sys.argv[3] #r'C:\workspace\GeoWET\Data\SpeciesModels\{}_swd.csv'.format(sppName)

##--------Functions--------##
def msg(txt,severity=""):
    '''Reports message to interactive windor or ArcPy, if loaded'''
    print txt
    try:
        if severity=="Warning":
            arcpy.AddWarning(txt)
        elif severity=="Error":
            arcpy.AddError(txt)
        else:
            arcpy.AddMessage(txt)
    except:
        pass
def checkSpeciesName(speciesName,sppFN):
    '''Ensures that the supplied species name exists in the observation table'''
    import csv
    fileObj = open(eoCSV,'rt')
    csvReader = csv.reader(fileObj)
    fldNames = csvReader.next()
    fileObj.close()
    if not speciesName in fldNames:
        msg("***{}*** does not occur in the \n   {} file".format(speciesName,sppFN),"Error")
        sys.exit(1)
    else:
        return      

def getHUC8s(sppFN,speciesName):
    '''Returns a list of the HUC8s in which a species occurs'''
    #Create a data frame from the species data
    useCols = ["REACHCODE",speciesName]
    eoDF = pd.read_csv(sppFN,usecols=useCols,dtype={'REACHCODE':str})
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
    dataDF = pd.read_csv(dataFN,dtype=dtypes)#,index_col="FEATUREID")

    #Filter the cachment attributes for the HUC8s
    selectDF = dataDF[dataDF["HUC_12"].str[:8].isin(huc8s)]
    return selectDF

def mergePresAbs(sppFN,speciesName,dataDF):
    '''Adds a column of species presence/absence to the dataFN'''
    #Create a data frame from the species data
    useCols = ["FEATUREID",speciesName]
    eoDF = pd.read_csv(sppFN,usecols=useCols,dtype={'FEATUREID':str})

    #Join the presence absence data to the catchment data frame
    outDF = pd.merge(eoDF,dataDF,how='right',on="FEATUREID")    
    
    #Set Nan to Zeros
    outDF[speciesName] = outDF[speciesName].fillna(0)

    return outDF

def removeAbsenceNullRows(theDF,speciesName):
    '''Remove ROWS where spp is absence and attribute has -9999'''
    #Loop through each field
    for fld in list(theDF.columns):
        theDF2 = theDF[~((theDF[speciesName] == 0) & (theDF[fld] == -9999))]
    return theDF2

def removePresenceNullColumns(theDF,log=""):
    '''Remove COLUMNS with missing data in species presence rows'''
    for fld in list(theDF.columns):
        #Get the min value of the field
        if theDF[fld].min() == -9999:
            #Drop the fields
            if log:
                log.write("   ...Removing: {}\n".format(fld))
            theDF.drop(fld,axis=1,inplace=True)
    return theDF

def removeUncorrelated(theDF,speciesName,log=""):
    '''Remove attributes with no correlation with presence/absence'''
    '''Returns: the culled data frame & a dict of fields and their correlations'''
    #Initialize the correlation dictionary
    corDict = {}
    sppVector = theDF[speciesName]
    #Compute correlation with presence/absence
    for fld in list(theDF.columns)[6:]:
        envVector = theDF[fld]
        pearson = stats.pearsonr(sppVector, envVector)
        coeff = pearson[0]
        pValue = pearson[1]
        #Print output to the CSV file
        if abs(pValue) > 0.05:
            log.write("   ...Removing %s [p=%2.3f]\n"%(fld,pValue))
            theDF.drop(fld,axis=1,inplace=True)
        else:
            #Add the field to the correlation dictionary
            corDict[fld] = coeff
    #Return column values
    sppVector.replace(0,"Background",inplace=True)
    sppVector.replace(1,sppName,inplace=True)
    return theDF, corDict

def removeXCorrelated(theDF, corrDict, log, threshold=0.75):
    #Initialize the list of fields to drop
    dropFlds = []
    #Create a list of fields from the corrDict keys, sorted on value
    flds = sorted(corrDict,key=corrDict.get)
    nCols = len(flds)
    #Compute cross correlation pairs; add field to drop list
    for i in range(0,nCols):
        #Get the ith field; skip already marked for deletion
        iFld = flds[i]
        if iFld in dropFlds:
            continue
        #Get the correlation
        for j in range(0,nCols):
            if j > i: #Only process half the matrix
                #Get the jth field
                jFld =flds[j]
                #Skip if one of the fields is already marked for deletion
                if jFld in dropFlds:
                    continue
                #Get the value vectors for each field
                v1 = theDF[iFld]
                v2 = theDF[jFld]
                # Calculate the correlation coefficient
                pearson = stats.pearsonr(v1, v2)[0]
                # If the coefficient is > the threshold consider them redundant and add to the CSV
                if abs(pearson) >= float(threshold):
                    log.write("     %s & %s xcorrelated @ %2.2f; "%(iFld,jFld,pearson))
                    #Because the fields are sorted, drop the 2nd field (lower correlation)
                    if not (jFld in dropFlds): dropFlds.append(jFld)
    #Drop cross correlated fields
    for dropFld in dropFlds:
        theDF.drop(dropFld,axis=1,inplace=True)
    #Return the data frame
    return theDF

##------Procedures--------
#Get a list of species names from the Speciesoccurrences.csv file
with open(eoCSV,'rt') as eoFile:
    lineText=eoFile.readline()
allHeaders = lineText.split(",")
sppNames = allHeaders[4:]

#Loop through all species
for sppName in sppNames:
    #Set the output filename
    outFN = os.path.join(speciesFldr,'{}_swd.csv'.format(sppName))
    if os.path.exists(outFN):
        print "{} exists; skipping".format(sppName)
        continue

    #Aux files
    logFilename = outFN[:-4] + "_metadata.txt"

    #Initialize the log file
    now = datetime.datetime.now()
    logFile = open(logFilename,'w')
    logFile.write("SWD FILE CREATION FOR {}\n".format(sppName.upper()))
    logFile.write("File created at {}:{} on {}/{}/{}\n".format(now.hour,now.minute,now.month,now.day,now.year))
                  
    #Create a list of HUC8s in which the species was observed
    huc8s = getHUC8s(eoCSV, sppName)
    msg("{} was found in {} HUC8s".format(sppName, len(huc8s)))
    logFile.write("{} was found in {} HUC8s\n".format(sppName, len(huc8s)))

    #Loop through StreamCat file & create dataframes of just the HUC8 records in each
    allFiles = os.listdir(streamCatFldr)     # List if all files in the StreamCat folder
    dataFrames = []                     # Initialize the list of dataFrames
    firstFile = True                    # Initialize variable to see if it's the first variable

    for f in allFiles:                  # Loop through the StreamCat files
        if f[-4:] == ".csv":            # Only process the CSV files
            #Get the full file name
            fullFN = os.path.join(streamCatFldr,f)
            print ".",
            #msg("   Extracting records from {}".format(f))
            logFile.write("   Extracting records from {}\n".format(f))
            #Retrieve only the HUC8 records as a data frame using above function
            dataDF = spatialSelect(fullFN,huc8s)
            #If not the first file, then remove the 1st 5 columns (duplicates)
            if  firstFile:
                firstFile = False
                colNames = list(dataDF.columns)
            else:
                #Cross check the column names to skip duplicates
                newCols = []
                for col in list(dataDF.columns):
                    if not (col in colNames):
                        newCols.append(col)  #Add to list of cols to add
                        colNames.append(col) #Add to full column list
                dataDF = dataDF[newCols]
            #Convert columns to smaller datatypes to save memory
            for c in dataDF.columns:
                if dataDF[c].dtype.type == np.float64:
                    dataDF[c]= dataDF[c].astype(np.float32)
                if dataDF[c].dtype.type == np.int64:
                    dataDF[c]= dataDF[c].astype(np.int32)
            #Append to the list of data frames
            dataFrames.append(dataDF)

    #Merge all file data frames into one
    msg("Merging data frames")
    dataDF = pd.concat(dataFrames,axis=1)

    #Remove single dfs to free memory
    del dataFrames

    #Add species presence absence data
    msg("Prepending presence absence to data frame")
    sppDF = mergePresAbs(eoCSV,sppName,dataDF)

    #Remove the OID column
    sppDF.drop("OID",axis=1,inplace=True)
    msg("Resulting table has {0} columns and {1} records".format(sppDF.shape[1],sppDF.shape[0]))

    #Cull absence rows where columns have no data         
    msg("Removing absence records with no catchment data")
    logFile.write("Checking for absence records with missing catchment data\n")
    startRowCount = len(sppDF)
    sppDF = removeAbsenceNullRows(sppDF,sppName)
    endRowCount = len(sppDF)
    droppedRowCount = startRowCount - endRowCount
    msg("...{} records dropped".format(droppedRowCount))
    logFile.write("...{} absence records deleted for missing data\n".format(droppedRowCount))

    #Cull catchment attributes with no data
    msg("Removing catchment attributes with null values")
    logFile.write("Checking for catchment attributes with null values\n")
    startColCount = sppDF.shape[1]
    sppDF = removePresenceNullColumns(sppDF,logFile)
    endColCount = sppDF.shape[1]
    droppedColCount = startColCount - endColCount
    if droppedColCount > 0:
        msg("...{} columns dropped".format(droppedColCount))
        logFile.write("   ...{} columns removed for missing data\n".format(droppedColCount))

    #Cull catchment attributes not correlated with presence absence
    msg("Removing attributes not correlated with presence absence")
    logFile.write("Removing attributes not correlated with presence absence\n")
    startColCount = sppDF.shape[1]
    sppDF,correlationDict = removeUncorrelated(sppDF,sppName,logFile)
    endColCount = sppDF.shape[1]
    droppedColCount = startColCount - endColCount
    if droppedColCount > 0:
        msg("...{} columns dropped".format(droppedColCount))
        logFile.write("   ...{} columns removed: no sign. corr.\n".format(droppedColCount))

    msg("Removing cross correlated attributes")
    logFile.write("Checking for cross correlated columns\n")
    startColCount = sppDF.shape[1]
    sppDF = removeXCorrelated(sppDF,correlationDict,logFile)
    endColCount = sppDF.shape[1]
    droppedColCount = startColCount - endColCount
    if droppedColCount > 0:
        msg("...{} X correlated cols dropped".format(droppedColCount))
        logFile.write("   ...{} X correlated cols dropped\n".format(droppedColCount))

    msg("Adjusting column names to work with MaxEnt")
    logFile.write("Adjusting column names to work with MaxEnt\n")
    sppDF.rename(columns = {sppName:'Species','GRIDCODE':'X','REACHCODE':'Y'}, inplace=True)
    sppDF.loc[sppDF['Species']==1,'Species'] = sppName
    sppDF.loc[sppDF['Species']==0,'Species'] = "Background"

    sppDF.drop('FEATUREID',axis=1,inplace=True)
    sppDF.drop('HUC_12',axis=1,inplace=True)


    #write file to csv
    msg("Writing file to {}".format(outFN))
    logFile.write("File written to {}\n".format(outFN))
    sppDF.to_csv(outFN,index_label="OID",index=False)

    #close the log file
    logFile.close()