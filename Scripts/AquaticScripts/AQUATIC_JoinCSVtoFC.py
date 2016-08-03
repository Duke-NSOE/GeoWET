#AQUATIC_JoinCSVtoFC.py
#
# Merges records in a CSV to a catchment FC
#
# June 2106
# John.Fay@duke.edu

import sys, os, arcpy
import pandas as pd
import numpy as np
from AQUATIC_utils import msg

#Inputs
csvFilename = r'C:\workspace\GeoWET\Data\Projects\ExampleProject_SWD_Uplift.csv'
catchmentFC = r'C:\workspace\GeoWET\Data\ToolData\NC_Results.gdb\CatchmentAttributes2'
linkFld = "GRIDCODE"
outFC = r'C:\workspace\GeoWET\Scratch\Scratch.gdb\foo'

#Generate a list of gridCodes from the csvFilename
df = pd.read_csv(csvFilename)

#Check that linkfield occurs in the file
if not linkFld in df.columns:
    print "ERROR"
    sys.exit

#Get a unique list of values
vals = pd.unique(df[linkFld])
valList = list(vals)            #Convert array to list
strList = str(valList)[1:-1]    #Convert list to string; strip '[' and ']'

#Create the where clause
whereClause = "{} IN ({})".format(linkFld,strList)

#Subset Catchment records
msg("Extracting {} records".format(len(valList)))
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
        msg("...adding {} as FLOAT".format(col))
        arcpy.AddField_management(outFC,col,"FLOAT",8,5)
    elif dtype == np.int64:
        msg("...adding {} as LONG".format(col))
        arcpy.AddField_management(outFC,col,"LONG",20)
    else:
        msg("...adding {} as TEXT".format(col))
        arcpy.AddField_management(outFC,col,"TEXT",30)

#Insert values
with arcpy.da.UpdateCursor(outFC,cols) as cursor:
    for row in cursor:
        gridCode = row[0]
        catchVals = df[df[linkFld] == gridCode].values.tolist()
        #Update all values
        for i in range(1,len(catchVals)):
            row[i] = catcVals[i]
        cursor.updateRow(row)
    
    
    