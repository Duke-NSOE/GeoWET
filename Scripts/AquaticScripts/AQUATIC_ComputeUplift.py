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
prjName = 'ExampleProject4_SWD'
catchmentFC = r'C:\workspace\GeoWET\Data\ToolData\NC_Results.gdb\CatchmentAttributes2'

#Output
outputCSV = r'C:\workspace\GeoWET\scratch\{}_Uplift.csv'.format(prjName)
outputFC = r'C:\workspace\GeoWET\scratch\scratch.gdb\{}_Uplift'.format(prjName)

##---PROCEDURES---
#Get the list of species
sppMultiString = getSpeciesList(AqSppXLSX,"PIEDMONT")
sppList = sppMultiString.split(";")

#running list of uplift flds
upliftFlds = []
sppDFs = []

#Loop through each species
for species in sppList:
    msg("Processing {}".format(species))

    #Get the species current projection results corresponding to the project
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
    cDF = pd.read_csv(currentFN, dtype={'GRIDCODE':np.long})
    cDF.rename(columns={cDF.columns[2]:curFld},inplace=True)
    cDF.drop('FEATUREID',axis=1,inplace=True)

    pDF = pd.read_csv(projectFN, dtype={'GRIDCODE':np.long})
    pDF.rename(columns={pDF.columns[2]:prjFld},inplace=True)
    pDF.drop('FEATUREID',axis=1,inplace=True)

    #Join the cDF values to the pDF
    sppDF = pd.merge(cDF,pDF)

    #If not the first table, drop the GRIDCODE field
    if species <> sppList[0]:
        sppDF.drop("GRIDCODE",axis=1,inplace=True)

    #Ensure there's an intersection
    if len(sppDF) == 0:
        msg("ERROR: {} was not modeled for the projection area".format(species),"error")
        continue

    #Calculate uplift
    sppDF[upliftFld] = sppDF[prjFld] - sppDF[curFld]
    
    #Add the df to the list of dfs
    sppDFs.append(sppDF)

#Merge all dfs
allDF = pd.concat(sppDFs,axis=1)

#Write to CSV file
allDF.to_csv(outputCSV,index=False)

#Merge with catchment features
JoinCSVtoCatchmentFC(outputCSV,catchmentFC,outputFC,verbose=True)