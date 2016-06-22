#AQUATIC_MapProjections.py
#
# Merges projected habitat likelihood with current conditions to
# map uplift for each catchment.

import sys, os
import pandas as pd
import numpy as np
import arcpy

#Inputs
currentFN = sys.argv[1]
projectFN = sys.argv[2]
catchmentFN = sys.argv[3]

#Derived inputs
species = os.path.basename(currentFN[:-4])
sppFolder = os.path.dirname(currentFN)
allSppFolder = os.path.dirname(sppFolder)

#Output
outputFC = sys.argv[4]

##---FUNCTIONS---
def msg(txt,severity=""):
    print txt
    if severity=="warning":
        arcpy.AddWarning(txt)
    elif severity=="error":
        arcpy.AddError(txt)
    else:
        arcpy.AddMessage(txt)

##---PROCEDURES---
msg("Processing results for {}".format(species))
   
#Read in the Maxent results as dataframes
msg("Importing Maxent results")
cDF = pd.read_csv(currentFN, dtype={'X':np.long})#,index_col='X')
cDF.rename(columns={'X':'GRIDCODE',cDF.columns[2]:"current"},inplace=True)
cDF.drop('Y',axis=1,inplace=True)

msg("Importing projection results")
pDF = pd.read_csv(projectFN, dtype={'GRIDCODE':np.long})#,index_col='GRIDCODE')
pDF.rename(columns={'{} logistic values'.format(species):"project"},inplace=True)
pDF.drop('FEATUREID',axis=1,inplace=True)

#Join the cDF values to the pDF
msg("Joining result tables")
allDF = pd.merge(cDF,pDF)

#Ensure there's an intersection
if len(allDF) == 0:
    msg("{} was not modeled for the projection area".format(species),"error")
    sys.exit(0)

#Calculate uplift
msg("Computing uplift")
allDF["uplift"] = allDF.project - allDF.current

#Extract just the relevant catchments
msg("Creating output file")
msg("...Extracting {} catchment records".format(len(allDF)))
gridCodes1 = str(allDF.GRIDCODE.values.tolist())
gridCodes2 = gridCodes1.replace('L','')[1:-1]
whereClause = 'GRIDCODE IN ({})'.format(gridCodes2)
selCatch = arcpy.Select_analysis(catchmentFN,outputFC,whereClause)

#Add fields
msg("...appending attribute table")
arcpy.AddField_management(selCatch,"Current","FLOAT",6,4)
arcpy.AddField_management(selCatch,"Project","FLOAT",6,4)
arcpy.AddField_management(selCatch,"Uplift","FLOAT",6,4)

#Append values to selCatch
msg("...updating values")
with arcpy.da.UpdateCursor(selCatch,("GRIDCODE","Current","Project","Uplift")) as cur:
    for row in cur:
        gridCode = row[0]
        #Get the record from the dataframe
        vals = allDF.loc[allDF.GRIDCODE == gridCode].values[0].tolist()
        row[1] = vals[1]
        row[2] = vals[2]
        row[3] = vals[3]
        cur.updateRow(row)

msg("Finished!")