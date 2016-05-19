# UPLIFT_UpdateCatchmentAttributes.py
#
# Description: Updates the fields in the Catchment Attributes feature class with
#  the values in associated fields in a separate table. Does so by joining the
#  two tables and calculating values in the original table equal to those in the
#  joined tables. Both tables must have a common attribute for joining.
#
# Fall 2015
# John.Fay@duke.edu

# Import arcpy module
import sys, os, arcpy

#Script variables
catchmentsFC = arcpy.GetParameterAsText(0)  # Catchment feature class
fromJoinFld = arcpy.GetParameterAsText(1)   # Join field in Catchment FC, typically GRIDCODE
updateTbl = arcpy.GetParameterAsText(2)     # Table with values used to update the catchment attributes
toJoinFld = arcpy.GetParameterAsText(3)     # Join field in updateTbl
updateFlds = arcpy.GetParameterAsText(4)    # Fields to update (multi-value string)

#Set environments
arcpy.env.overwriteOutput = True

# Local variables:
rvLyr = "RespVarsLyr"

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
# Make a feature layer of the catchmentsFC
msg("...creating table view of response variables")
rvLyr = arcpy.MakeTableView_management(catchmentsFC,rvLyr)

# Join updateTbl to layer
msg("...joining tables")
rvJoin = arcpy.AddJoin_management(rvLyr,fromJoinFld,updateTbl,toJoinFld)

# Loop through the update fields
for fld in updateFlds.split(";"):
    msg("...updating {}".format(fld))
    
    # Get the update and calc field names
    updateFld = os.path.basename(catchmentsFC) + "." + fld
    valueFld = os.path.basename(updateTbl) + "." + fld

    # Check that the update field actually exists
    if arcpy.ListFields(rvLyr,updateFld) == []:
        msg("{} field does not exist; skipping","warning")
        continue

    # Update the values
    arcpy.CalculateField_management(rvLyr,updateFld,"[{}]".format(valueFld))

#Return the merged table
arcpy.SetParameterAsText(5,catchmentsFC)
