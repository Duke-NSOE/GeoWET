# MISC_aggregate_to_HUC12.py
#
# Description:
#  Upscales catchment data to the HUC12 using area weighted means. Inputs are the catchment feature
#  class containing the fields you want to upscale, the fields to upscale, a GRIDCODE-HUC12 lookup
#  table (located in the NC_Results.gdb).
#
# Overview:
#  - Copies the original feature class
#  - Joins the HUC_12 field to this copy
#  - Multiplies the join fields by the catchment area (for area weighting)
#  - Dissolved features on the HUC_12 attribute, computing the sum of the field*area values
#  - Renames the sum fields back to original field names and divides by the dissolved area
#    to revert values to original ones. 
#
# Fall 2015
# John.Fay@duke.edu

import sys, os, arcpy, csv, tempfile
arcpy.env.overwriteOutput = 1

# Input variables
inputFC = arcpy.GetParameterAsText(0)       #Feature class to upscale
upscaleFlds = arcpy.GetParameterAsText(1)   #Fields to upscale
HUC12Tbl = arcpy.GetParameterAsText(2)      #Catchment FC containing HUC12 values
outputFC = arcpy.GetParameterAsText(3)      #Output HUC12 feature class

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
#Copy the feature class to a temp copy
msg("Creating temp feature class")
tmpFC = arcpy.CopyFeatures_management(inputFC,"in_memory/tmpFC1")

#Join the HUC12 field to the tmpFC
arcpy.JoinField_management(tmpFC,"GRIDCODE",HUC12Tbl,"GRIDCODE","HUC_12")

#Initilize the Dissolve field list
fldList = []

#Loop through fields

for fldName in upscaleFlds.split(";"):
    msg("...calculating wtd value for {}".format(fldName))

    #Create the wtd field
    fldName12 = "{}12".format(fldName)
    arcpy.AddField_management(tmpFC,fldName12,"DOUBLE")
    arcpy.CalculateField_management(tmpFC,fldName12,"!shape.area! * !{}!".format(fldName),"PYTHON")

    #Build the stats field list for the Dissolve commmand
    fldList.append((fldName12,"SUM"))

#Dissolve on HUC12
msg("Dissolving data on HUC12")
tmpFC2 = arcpy.Dissolve_management(tmpFC,"in_memory/tmpFC2","HUC_12",fldList)

#Recalculate fields
for fldName in upscaleFlds.split(";"):
    #Rename the field
    arcpy.AlterField_management(tmpFC2,"SUM_{}12".format(fldName),fldName,fldName)
    #Revert area wtd values to just values
    arcpy.CalculateField_management(tmpFC2,fldName,"!{}! / !shape.area!".format(fldName),"PYTHON")

    #Save the output
    arcpy.CopyFeatures_management(tmpFC2,outputFC)
