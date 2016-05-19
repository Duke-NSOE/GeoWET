# UPLIFT_RiparianBufferScenario.py
#
# Description: Copies the master response variable table and modifies values
#  so that all FlowLineNLCD values that arent' water/developed/forest become
#  forest. This involved setting FLNLCD_X (X=3,5,7,8) to zero and taking the
#  sum of their original values and adding them to existing values. 
#
# The revised table is then used as an input to the ModelUplift script.

# Import arcpy module
import sys, os, arcpy

#User variables
origRVTbl = arcpy.GetParameterAsText(0)
HUCFilter = arcpy.GetParameterAsText(1)
upliftTbl = arcpy.GetParameterAsText(2)

#Set environments
arcpy.env.overwriteOutput = True

# ---Functions---
def msg(txt,type="message"):
    print txt
    if type == "message":
        arcpy.AddMessage(txt)
    elif type == "warning":
        arcpy.AddWarning(txt)
    elif type == "error":
        arcpy.AddError(txt)

## PROCESSES 
#Make a copy of the responseVariableTable
msg("Copying original data to {}".format(upliftTbl))
whereClause = "REACHCODE LIKE '{}%'".format(HUCFilter)
arcpy.Select_analysis(origRVTbl,upliftTbl,whereClause)

#Select all records with animal ops >= 1
msg("Selecting records with >= 1 animal operations")
selRecs = arcpy.MakeFeatureLayer_management(upliftTbl,"selRecs","AnimalOps > 0")

#Subtract 1 from these values
msg("Reducing animal operations by 1")
arcpy.CalculateField_management(selRecs,"AnimalOps","[AnimalOps] - 1")

