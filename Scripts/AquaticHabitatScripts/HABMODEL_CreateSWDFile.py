# HABMODEL_CreateSWDFile.py
#
# Description: Creates a MaxEnt input CSV file in SWD (species with data) format. Includes a
#  column listing the species/background along with columns for all the env vars. Records produced
#  are limited to only catchments with recorded presences from any species in Endries' data.
#
# This tool requires the following files in the species sub folder before it can be run:
#  - The ALLHUC8Records.csv
#  - 
#
# Spring 2015
# John.Fay@duke.edu

import sys, os, arcpy, csv
arcpy.env.overwriteOutput = True

# Input variables
speciesName = arcpy.GetParameterAsText(0)  # Name of species to process
stats_folder = arcpy.GetParameterAsText(1) # Stats root folder name;

## ---Functions---
def msg(txt,type="message"):
    print txt
    if type == "message":
        arcpy.AddMessage(txt)
    elif type == "warning":
        arcpy.AddWarning(txt)
    elif type == "error":
        arcpy.AddError(txt)
               
def checkFile(fileName):
    #Checks whether file exists. Sends error and exits if not. 
    if not os.path.exists(fileName):
        msg("File {} does not exist.\nExiting.".format(fileName),"error")
        sys.exit(1)
    else:
        return 

## ---SET SCRIPT VARIABLES---
# Set the species folder 
msg("Locating species stats folder in root folder")
sppFolder = os.path.join(stats_folder,speciesName)
checkFile(sppFolder)
    
# Set the ALLHUC8Records.csv file
msg("Locating HUC8 records file in species folder")
huc8RecordsCSV = os.path.join(sppFolder,"ALLHUC8Records.csv")
checkFile(huc8RecordsCSV)

# Set the SHCorrelations.csv file
msg("Locating species-habitat correlations file in species folder")
varFilterCSV = os.path.join(sppFolder,"SH_Correlations.csv")
checkFile(varFilterCSV)
    
# Set the RedundantVariables html file
msg("Locating redundant variables file in species folder")
varFilterHTML = os.path.join(sppFolder,"{}_RedundantVars.html".format(speciesName))
checkFile(varFilterHTML)

# Output variable (derived)
swdCSV = os.path.join(sppFolder,"{}_SWD.csv".format(speciesName))
arcpy.SetParameterAsText(2,swdCSV) #Output SWD format CSV file to create

## ------------------------Processes-----------------------
#Create the list of fields to convey to the SWD CSV file
msg("Building field list")
inFldList = ["SPECIES","GRIDCODE","REACHCODE"]

#Get the list of significant variables from the SH_Correlations table and add them to the list
msg("...Adding fields identified as significantly correlated with species presence")
f = open(varFilterCSV,'rt')
for row in csv.reader(f):
    inFldList.append(row[0])
f.close()
inFldList.remove('variable') #Remove the column header from the list
msg("...{} fields added".format(len(inFldList) - 3))

#Remove redundant fields
msg("Removing fields identified as redundant")
f = open(varFilterHTML, 'rt')               #open the file
lineString = f.readline()                   #get the info
f.close()                                   #close the file
lineItems = lineString.split("<br>")[1:-1]  #Get the fields from the line
fldList = list(inFldList)                #Make a clone of the outField list to loop through (so we can remove
                                            # values from the outFieldList in the loop
for fld in fldList:                         #Loop through fields; if it's in the lineItems list, it should be removed
    if fld in lineItems:
        msg("   Removing <{}> (redundant)".format(fld))
        inFldList.remove(fld)

#Clone the inFldList to the outFldList and replace GRIDCODE and REACHCODE with "X" and "Y"
outFldList = list(inFldList)
outFldList.pop(1)
outFldList.insert(1,"X")
outFldList.pop(2)
outFldList.insert(2,"Y")

## WRITE THE SPECIES RECORDS TO THE FILE ##
# Initialize the species output csv file & create the writer object
msg("Initializing the output CSV files")
csvFile = open(swdCSV,'wb')
writer = csv.writer(csvFile)

# Write header row to CSV file
msg("...Writing headers to CSV file")
writer.writerow(outFldList) 

# Create a search cursor for the huc8 CSV
msg("...Writing catchment records")
# Create a cursor including all but the first and last fields (species names)
cursor = arcpy.da.SearchCursor(huc8RecordsCSV,inFldList)
# Initialize the counters
presenceCounter = 0
absenceCounter = 0
for row in cursor:
    rowData = list(row)
    #If the species is present, set first column to the species name, otherwise background
    if rowData[0] == 1:
        rowData[0] = speciesName
        presenceCounter += 1
    else:
        rowData[0] = "Background"
        absenceCounter += 1
    #write the species name + all the row data
    writer.writerow(rowData)

msg("{} species records written to file".format(presenceCounter))
msg("{} background records written to file".format(absenceCounter))

# Close file and clean up
csvFile.close()

msg("Finished")