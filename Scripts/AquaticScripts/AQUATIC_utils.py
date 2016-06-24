#Aquatic_utils.py
#
# A set of functions frequently used by AQUATIC scripts
#
# June 2016
# John.Fay@duke.edu

import sys, os

#Import pandas
try:
    import pandas as pd
except:
    "Pandas is required for this module"
    sys.exit()

#Import numpy
try:
    import numpy as np
except:
    "Numpy is required for this module"
    sys.exit()

def msg(txt,severity=""):
    '''Provides messaging to interactive window or to ArcMap if run as script tool'''
    #Print the message to the interactive window
    print txt
    #Try to print to ArcMap. Will pass harmlessly as error if ArcPy is not loaded
    try:
        if severity=="warning":
            arcpy.AddWarning(txt)
        elif severity=="error":
            arcpy.AddError(txt)
        else:
            arcpy.AddMessage(txt)
    except:
        pass

def getSpeciesList(sppFile,ecoregion):
    '''Returns a list of species in the ecoregion'''
    ##TO ADD: Error if sppFile incorrect; Error if ecoregion not in list
    #Import pandas
    import pandas as pd
    
    #Read in the table as a data frame
    sppDF = pd.read_excel(sppFile,sheetname="IndicatorSppTable")

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
        #Add the species to the list
        outStr += "{};".format(spp)
        #Strip off the last semi-colon
    outStr = outStr[:-1]
        
    return outStr

def JoinCSVtoCatchmentFC(csvFilename,catchmentFC,outFC,linkFld="GRIDCODE",verbose=False):
    '''Selects catchment records and joins values in the CSV to them'''
    #Import modules
    import arcpy
    
    #Generate a list of gridCodes from the csvFilename
    df = pd.read_csv(csvFilename)

    #Check that linkfield occurs in the file
    if not linkFld in df.columns:
        msg("ERROR:{} not found in CSV file","error")
        sys.exit(1)

    #Get a unique list of link values
    vals = pd.unique(df[linkFld])
    valList = list(vals)            #Convert array to list
    strList = str(valList)[1:-1]    #Convert list to string; strip '[' and ']'

    #Create the where clause
    whereClause = "{} IN ({})".format(linkFld,strList)

    #Subset Catchment records
    if verbose: msg("Extracting {} records".format(len(valList)))
    arcpy.Select_analysis(catchmentFC,outFC,whereClause)

    #Make a list of columns; ensure that the link field is first
    cols = list(df.columns)
    cols.remove(linkFld)    #Remove the link field
    cols.insert(0,linkFld)  #Re-insert it as position 0

    #Append CSV columns, except the link fld
    for col in cols[1:]:
        #Determine the column type
        dtype = df[col].dtype
        if dtype == np.float64:
            if verbose: msg("...adding {} as FLOAT".format(col))
            arcpy.AddField_management(outFC,col,"FLOAT",8,5)
        elif dtype == np.int64:
            if verbose: msg("...adding {} as LONG".format(col))
            arcpy.AddField_management(outFC,col,"LONG",20)
        else:
            if verbose: msg("...adding {} as TEXT".format(col))
            arcpy.AddField_management(outFC,col,"TEXT",30)

    #Insert values
    with arcpy.da.UpdateCursor(outFC,cols) as cursor:
        for row in cursor:
            gridCode = row[0]
            catchVals = df[df[linkFld] == gridCode].values[0].tolist()
            #Update all values
            for i in range(1,len(catchVals)):
                row[i] = catchVals[i]
            cursor.updateRow(row)
            
    #Return the feature class
    return outFC
    
def maxentProject(lamdaFile,prjSWDFile,outFile,verbose=False):
    '''Runs a Maxent projection against the supplied lamdaFile)'''
    # Check that the maxent.jar file exists in the scripts folder
    maxentJarFile = os.path.dirname(sys.argv[0])+"\\maxent.jar"
    if not os.path.exists(maxentJarFile):
        msg("Maxent.jar file cannot be found in Scripts folder.\nExiting.","error")
        sys.exit(0)
    else:
        if verbose: msg("Maxent.jar found in Scripts folder".format(maxentJarFile))
    #Check that the other files exist
    if not os.path.exists(lamdaFile):
        msg("Lambda file not fount: {}".format(lamdaFile),"error")
        sys.exit(1)
    if not os.path.exists(prjSWDFile):
        msg("Lambda file not fount: {}".format(prjSWDFile),"error")
        sys.exit(1)
    # Begin creating the command with boilerplate stuff
    if verbose: msg("Initializing the Maxent batch command")
    runString = "java -cp {} density.Project ".format(maxentJarFile)
    # set lamdas file
    if verbose: msg("...Setting lambdas file to{}".format(lamdaFile))
    runString += " {}".format(lamdaFile)
    # set projection SWD file
    if verbose: msg("...Setting enviroment layers file to{}".format(prjSWDFile))
    runString += " {}".format(prjSWDFile)
    # set output file
    if verbose: msg("...Setting output file to {}".format(outFile))
    runString += " {}".format(outFile)
    # execute the command
    if verbose: msg("Executing Maxent command")
    import subprocess
    subprocess.call(runString,shell=True)

    # return the output file
    return outFile