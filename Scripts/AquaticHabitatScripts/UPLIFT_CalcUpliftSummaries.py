# UPLIFT_CalcUpliftMinMax.py
#
# Description:
#  Appends columns to the merged uplift table that lists:
#   (1) the most negative uplift across modeled species("minUplift")
#   (2) the most positive uplift across modeled species ("maxUplift")
#   (3) the range in uplift across modeled species ("minUplift")
#   (4) the count of species with uplift scores above a set threshold ("highCount")
#   (4) the count of species with uplift scores below a set threshold ("lowCount")
#  and most positive species uplift values.
#
#  The input tables must be in the format that the UPLIFT_MergeUpliftResults.py
#  generates, i.e., with all species uplift fields ending with "_up"
#
# Jan 2016
# John.Fay@duke.edu

import sys, os, arcpy, csv, tempfile
arcpy.env.overwriteOutput = 1

# Input variables
upliftTable = arcpy.GetParameterAsText(0)
highThreshold = float(arcpy.GetParameterAsText(1))
lowThreshold = float(arcpy.GetParameterAsText(2))

# Script variables
minUpliftFld = "minUplift"
maxUpliftFld = "maxUplift"
rngUpliftFld = "rngUplift"
hiCountFld = "pctAbove"
loCountFld = "pctBelow"

## ---Functions---
def msg(txt,type="message"):
    print txt
    if type == "message":
        arcpy.AddMessage(txt)
    elif type == "warning":
        arcpy.AddWarning(txt)
    elif type == "error":
        arcpy.AddError(txt)

    
#Create list of spp uplift fields. Also, check whether the fields already exist (set to add if not)
upliftFlds = []
makeFlds = [minUpliftFld,maxUpliftFld,rngUpliftFld,hiCountFld,loCountFld] #fields removed from this list if found
for fld in arcpy.ListFields(upliftTable):
    if fld.name in makeFlds:
        msg("...{} already exists for this table".format(fld.name))
        makeFlds.remove(fld.name)
    elif fld.name[-3:] == "_up": #If the field is an uplift field, add to list
        upliftFlds.append(fld.name)

#Check that uplift fields were found
fldCount = len(upliftFlds)
if fldCount == 0:
    msg("No uplift fields found.\nAre you using the correct table?","error")
    sys.exit(0)
else:
    msg("...{} uplift fields found".format(fldCount))

#Create any fields remaining in the makeFlds list (i.e., not already found) 
for fld in makeFlds:
    msg("...Adding {} field to table".format(fld))
    arcpy.AddField_management(upliftTable,fld,"DOUBLE",5,3)

#Create calc strings to calclate min, max, and range...
minCalcStr = "min("
maxCalcStr = "max("
for fld in upliftFlds:
    minCalcStr += "!{}!,".format(fld)
    maxCalcStr += "!{}!,".format(fld)
minCalcStr = minCalcStr[:-1] + ")"
maxCalcStr = maxCalcStr[:-1] + ")"
rangeCalcStr = "!{}! - !{}!".format(maxUpliftFld,minUpliftFld)

#Apply the calcStrings for min/max/range
msg("...calculating min uplift")
arcpy.CalculateField_management(upliftTable,minUpliftFld,minCalcStr,"PYTHON")
msg("...calculating max uplift")
arcpy.CalculateField_management(upliftTable,maxUpliftFld,maxCalcStr,"PYTHON")
msg("...calculating uplift range")
msg(rangeCalcStr)
arcpy.CalculateField_management(upliftTable,rngUpliftFld,rangeCalcStr,"PYTHON")

#Create the update cursor to calculate highCount and lowCount
msg("Computing counts above and below thresholds")
records = arcpy.UpdateCursor(upliftTable)
rec = records.next()
while rec:
    #Initialize the values
    hiCount = 0.0
    loCount = 0.0
    #Loop through uplift fields and count # spp above and below thresholds
    for fld in upliftFlds:
        if rec.getValue(fld) > highThreshold: hiCount += 1
        if rec.getValue(fld) < lowThreshold: loCount += 1
    #Update the values in the high and low columns
    rec.setValue(hiCountFld,hiCount / fldCount)
    rec.setValue(loCountFld,loCount / fldCount)
    #Committ updates
    records.updateRow(rec)
    #Move to the next record
    rec = records.next()
    
#Finished
msg("Completed")
