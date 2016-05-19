# HABMODEL_SHCorrelate.py
#
# Description:
#  This script identifies response variables that can be eliminated from the
#  analysis from lacking a significant correlation with whether a species occurs
#  in a catchment or not. It computes the Pearson product moment correlation
#  between a given response variable and the binary presence/absence variable.
#  If the correlation is not significant (p < 0.05), the response variable is
#  considered more noise than signal and is tagged for eliminated from the
#  habitat modeling.
#
#  *****************************************************************************
#  ** This module requires the SciPy module to be installed. When installing, **
#  ** be sure to get version 0.12.0 as that is the one that works with the    **
#  ** version of NumPy that is installed with ArcGIS 10.2                     ** 
#  *****************************************************************************
#
# Spring 2015
# John.Fay@duke.edu

import sys, os, arcpy, numpy, datetime
arcpy.env.overwriteOutput = 1

# Input variables
speciesCSV = arcpy.GetParameterAsText(0) #Catchment table of species p/a with all other response variables

# Output variables
statsFolder = os.path.dirname(speciesCSV)
correlationCSV = os.path.join(statsFolder,"SH_Correlations.csv")
logFilename = correlationCSV[:-4] + "_metadata.txt"
arcpy.SetParameterAsText(1,correlationCSV) #Table of only significant response variables and their coefficients

## ---Functions---
def msg(txt,type="message"):
    print txt
    if type == "message":
        arcpy.AddMessage(txt)
    elif type == "warning":
        arcpy.AddWarning(txt)
    elif type == "error":
        arcpy.AddError(txt)

## ---Processes---
#Check to see whether a SciPy exists
try:
    import scipy
    from scipy import stats
except:
    msg("The SciPy module is not installed.\nExiting.","error")
    sys.exit()

#Initialize the log file
now = datetime.datetime.now()
logFile = open(logFilename,'w')
logFile.write("INFO ON SPECIES-HABITAT CORRELATIONS\n")
logFile.write("File created at {}:{} on {}/{}/{}\n".format(now.hour,now.minute,now.month,now.day,now.year))

#Read in the column headers
f = open(speciesCSV,'rt')
headerText = f.readline()
headerText = headerText[:-1] #Strip the newline char
headerItems = headerText.split(",")
f.close()

#Read in the csv file as a numpy vector
msg("...Reading in data")
arrData = numpy.genfromtxt(speciesCSV,delimiter=",")

#Create variables from data array
nCols = arrData.shape[1]

#Create vectors
msg("...Extracting occurrence records")
sppVector = arrData[1:,0]

#Intialize output file
msg("...Creating output file")
f = open(correlationCSV,'wt')
f.write("variable, coef, abs_coef, p_value\n")

#Loop through columns and calculate the variables correlation with presence/absence
msg("Calculating correlation coefficients")
for i in range(2,nCols):
    # Get the variable name (from the list created above)
    envName = headerItems[i]
    # Skip if name is GRIDCODE or FeatureID
    if envName in ("GRIDCODE","FeatureID","REACHCODE"): continue
    # Get the env var column, as a vector
    envVector = arrData[1:,i]
    #Calculate correlation --THIS REQUIRES SCIPY--
    pearson = stats.pearsonr(sppVector, envVector)
    coeff = pearson[0]
    pValue = pearson[1]
    #Print output to the CSV file
    if abs(pValue) <= 0.05:
        f.write("%s, %2.4f, %2.4f, %2.3f\n"%(envName,coeff,abs(coeff),pValue))
    else:
        msg("--> [%s] was dropped (p=%2.2f)"%(envName,pValue),"warning")
        logFile.write("--> [%s] was dropped (p=%2.2f)\n"%(envName,pValue))

#Wrap up
logFile.close()
f.close()          