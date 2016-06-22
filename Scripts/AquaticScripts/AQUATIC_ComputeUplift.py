#AQUATIC_ComputeUplift.py
#
# Isolates all species within an ecoregion and uses them to compute
# uplift (change between current and alternate species likelihood)
# for each species and then an average of all of them. 
#
# Requires:
# - The AquaticSpeciesList.xlsx file (to extract species for
#   a given ecoregion).
# - The species folder, containing completed runs for all species
# - A project name, e.g. "ExampleProject2_SWD" that has been run as a
#   projection in all MaxEnt species models.
# - The AQUATICS_util script functions
#
# June 2016
# John.Fay@duke.edu

import sys, os
import pandas as pd
import numpy as np
from AQUATIC_utils import *

#Inputs
AqSppXLSX = r'C:\workspace\GeoWET\Data\ToolData\AquaticSpeciesList.xlsx'
sppModelFolder = r'C:\workspace\GeoWET\Data\SpeciesModels'
prjName = 'ExampleProject_SWD'

#Output
outputCSV = r'C:\workspace\GeoWET\scratch\{}.csv'.format(prjName)

##---PROCEDURES---
#Get the list of species
sppMultiString = getSpeciesList(AqSppXLSX,"PIEDMONT")
sppList = sppMultiString.split(";")

#running list of uplift flds
upliftFlds = []
sppDFs = []

#Loop through each species
for species in sppList:
    msg("Processing results for {}".format(species))

    #Get the species current projection results corresponding to the project
    msg("[{}] Locating project result files".format(species.upper()))
    currentFN = os.path.join(sppModelFolder,species,"{}_{}CUR.csv".format(species,prjName))
    projectFN = os.path.join(sppModelFolder,species,"{}_{}.csv".format(species,prjName))
     
    #Generate a brief species name for columns
    genus,spp = species.split("_")
    sppName = "{}_{}".format(genus[1],spp)
    curFld = "{}_C".format(sppName)
    prjFld = "{}_P".format(sppName)
    upliftFld = "{}_U".format(sppName)
    upliftFlds.append(upliftFld)

    #Read in the Maxent results as dataframes
    msg("[{}] Importing current likelihood".format(species.upper()))
    cDF = pd.read_csv(currentFN, dtype={'GRIDCODE':np.long})
    cDF.rename(columns={cDF.columns[2]:curFld},inplace=True)
    cDF.drop('FEATUREID',axis=1,inplace=True)

    msg("[{}] Importing project likelihood".format(species.upper()))
    pDF = pd.read_csv(projectFN, dtype={'GRIDCODE':np.long})
    pDF.rename(columns={pDF.columns[2]:prjFld},inplace=True)
    pDF.drop('FEATUREID',axis=1,inplace=True)

    #Join the cDF values to the pDF
    msg("[{}] Joining result tables".format(species.upper()))
    sppDF = pd.merge(cDF,pDF)

    #If not the first table, drop the GRIDCODE field
    if species <> sppList[0]:
        sppDF.drop("GRIDCODE",axis=1,inplace=True)

    #Ensure there's an intersection
    if len(sppDF) == 0:
        msg("ERROR: {} was not modeled for the projection area".format(species),"error")
        continue

    #Calculate uplift
    msg("...Computing uplift")
    sppDF[upliftFld] = sppDF[prjFld] - sppDF[curFld]
    
    #Add the df to the list of dfs
    sppDFs.append(sppDF)

#Merge all dfs
allDF = pd.concat(sppDFs,axis=1)

#Write to CSV file
allDF.to_csv(outputCSV,index=False)

sys.exit(0)
#Extract just the relevant catchments
msg("...Creating output file")
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