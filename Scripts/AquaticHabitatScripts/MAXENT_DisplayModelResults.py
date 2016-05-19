# MAXENT_DisplayModelResults.py
#
# Converts Maxent result tables to the catchment feature class to display results.
#  Allow the user to supply a HUC to filter only specific catchments (e.g. HUC8)
#
# Fall 2015
# John.Fay@duke.edu

import arcpy, sys, os, csv
arcpy.env.overwriteOutput = 1

# Input variables
SpeciesFC = arcpy.GetParameterAsText(0)    # Feature class of Species in FCs NHD Catchments
speciesName = arcpy.GetParameterAsText(1)  # Species Name
HUCFilter = arcpy.GetParameterAsText(2)    #(Optional) HUC label used to select specific catchments
statsFolder = arcpy.GetParameterAsText(3)  # Folder containing all species output sub-folders
maxentName = arcpy.GetParameterAsText(4)   #(Optional) Name of folder containing maxent output; defaults to OUTPUT

# Output
outFC = os.path.join(statsFolder,speciesName,"ME_output.shp")
arcpy.SetParameterAsText(5,outFC) #Output feature class listing habitat likelihood for the species

## ---Functions---
#Message Function
def msg(txt,type="message"):
    print txt
    if type == "message":
        arcpy.AddMessage(txt)
    elif type == "warning":
        arcpy.AddWarning(txt)
    elif type == "error":
        arcpy.AddError(txt)
#Checkfile function        
def checkFile(fileName):
    #Checks whether file exists. Sends error and exits if not. 
    if not os.path.exists(fileName):
        msg("File {} does not exist.\nExiting.".format(fileName),"error")
        sys.exit(1)
    else:
        return 

## ---Derived inputs---
#Set the maxent scenario name to Output, if none given
if maxentName in ("", "#"): maxentName = "Output"

#Set the full path to the maxent scenario folder
msg("...Locating Maxent output folder")
maxentFolder = os.path.join(statsFolder,speciesName,maxentName)
checkFile(maxentFolder)

#Get the maxent results CSV file
msg("...Locating Maxent results file")
resultsFN = os.path.join(maxentFolder,"maxentResults.csv")
checkFile(resultsFN)

msg("...Locating Maxent prediction file")
#Get the maxent predictions file
logisticFN = os.path.join(maxentFolder,speciesName+".csv")
checkFile(logisticFN)

## ---Processes---
#Get the threshold 
msg("...Extracting the probability threshold")
f = open(resultsFN,'rt')
reader = csv.reader(f)
row1 = reader.next() #Header line
row2 = reader.next() #Values line
f.close()
idx = row1.index('Balance training omission, predicted area and threshold value logistic threshold')
threshold = row2[idx]
msg("   Maxent logistic threshold set to {}".format(threshold),"warning")

#Create a table of from the logistic CSV
msg("...Converting maxent prediction file to a table")
logTbl = arcpy.CopyRows_management(logisticFN,"in_memory/Logistic")

#Get the logistic field name (last field in the CSV table)
logFld = arcpy.ListFields(logTbl)[-1].name

#Make a feature layer of the catchment features (to trim fields)
msg("...Creating a feature layer of catchment features")
fldInfo = arcpy.FieldInfo()
for f in arcpy.ListFields(SpeciesFC):
    fName = f.name
    if fName in ("OBJECTID","Shape","GRIDCODE","REACHCODE",speciesName):
        fldInfo.addField(fName,fName,"VISIBLE","")
    else:
        fldInfo.addField(fName,fName,"HIDDEN","")
catchLyr = arcpy.MakeFeatureLayer_management(SpeciesFC,"catchLyr","","",fldInfo)

#Make a where clause if a HUC was given
if HUCFilter in ("","#"):
    whereClause = ""
else:
    whereClause = "REACHCODE LIKE '{}%'".format(HUCFilter)

#Make a copy of the feature layer
msg("Selecting catchment features")
tmpFC = arcpy.Select_analysis(catchLyr, "in_memory\Results", whereClause)

#Join the Maxent results to it
msg("...Joining maxent results to catchment features")
#arcpy.AddJoin_management(catchLyr,"GRIDCODE",logTbl,"X")
arcpy.JoinField_management(tmpFC,"GRIDCODE",logTbl,"X",logFld)

#Remove all but the first three and last four fields
msg("...Cleaning up fields")
#Get the observed and predicted fields
flds = arcpy.ListFields(tmpFC)
obsFld = flds[-2].name
probFld = flds[-1].name
#If Shape_Area and Shape_Length get appended, move back two fields
if obsFld == "Shape_Length":
    obsFld = flds[-4].name
    probFld = flds[-3].name
#Change their names
arcpy.AlterField_management(tmpFC,obsFld,"Observed")
arcpy.AlterField_management(tmpFC,probFld,"Likelihood")

#Create and update output fields
msg("...Adding habitat binary field...")
arcpy.AddField_management(tmpFC,"Predicted","Short")

msg("...Updating habitat binary values..")
arcpy.CalculateField_management(tmpFC,"Predicted","!Likelihood! > {}".format(threshold),"PYTHON")

msg("...Changing observed nulls to 0")
pyCode = "def checkVal(val):\n if val == 1:\n  return 1\n else:\n  return 0"
arcpy.CalculateField_management(tmpFC,"Observed","checkVal(!Observed!)","PYTHON",pyCode)

msg("Writing output")
arcpy.CopyFeatures_management(tmpFC,outFC)

