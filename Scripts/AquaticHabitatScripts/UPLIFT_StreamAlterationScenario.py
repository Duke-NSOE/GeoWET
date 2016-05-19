# UPLIFT_StreamAlterationScenario.py
#
# Description: Copies the master response variable table and modifies values 
#  so that stream velocity values (V0001E) are reduced 10%
#
# The revised table is then used as an input to the ModelUplift scripts.

# Import arcpy module
import sys, os, arcpy

#User variables
origRVTbl = arcpy.GetParameterAsText(0)
HUCFilter = arcpy.GetParameterAsText(1) #optional filter to select specific catchments
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
msg("Copying original data to output table")
if HUCFilter in ("","#"):
    whereClause = ""
else:
    msg("...subsetting features that match HUC {}".format(HUCFilter))
    whereClause = "REACHCODE LIKE '{}%'".format(HUCFilter)
upliftTbl = arcpy.TableSelect_analysis(origRVTbl,upliftTbl,whereClause)

#Reduce values of V0001E to 90% of current values. 
msg("Reducing stream velocity to 90% of existing values")
arcpy.CalculateField_management(upliftTbl,"V0001E","[V0001E] * 0.90")



