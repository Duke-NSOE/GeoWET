#AQUATIC_ComputeUplift.py
#
# Runs Maxent projections for the supplied projections SWD file for all
#  species in the supplied ecoregion and then merges the uplift result into
#  a single table, along with averages, that is joined to the catchment features.
#
# The output must be a feature class in a geodatabase to preserve column names.
#
# June 2016
# John.Fay@duke.edu

import sys, os
import pandas as pd
import numpy as np
import AQUATIC_utils as aq

#Inputs
prjSWDFile = r'C:\workspace\GeoWET\Data\Projects\ExampleProject4_SWD.csv'
ecoregion = "PIEDMONT"
AqSppXLSX = r'C:\workspace\GeoWET\Data\ToolData\AquaticSpeciesList.xlsx'
sppModelFolder = r'C:\workspace\GeoWET\Data\SpeciesModels'
catchmentFC = r'C:\workspace\GeoWET\Data\ToolData\NC_Results.gdb\CatchmentAttributes2'

#Derived inputs
prjName = os.path.basename(prjSWDFile[:-4])
prjFolder = os.path.dirname(prjSWDFile)
curSWDFile = prjSWDFile[:-4] + 'CUR.csv'

#Output
outputCSV = os.path.join(prjFolder,'{}_Uplift.csv'.format(prjName))
tmpFile = os.path.join(prjFolder,'tmp_{}.csv'.format(prjName))
outputFC = r'C:\workspace\GeoWET\scratch\scratch.gdb\{}_Uplift'.format(prjName)

##---PROCEDURES---
#Get the list of species
sppMultiString = aq.getSpeciesList(AqSppXLSX,"PIEDMONT")
sppList = sppMultiString.split(";")

#Create a list of species dataframes to merge
sppDFs = []

#Create a list of uplift field columns, for computing averages
upliftFlds = []

#Loop through each species, compute uplift and current tables
for species in sppList:
    aq.msg("Analyzing {}".format(species))
    
    #Create a short name for the spp
    genus,spp = species.split("_")
    sppName = "{}{}".format(genus[0],spp[:5])

    #Create field names
    curFld ='C_{}'.format(sppName)
    prjFld ='P_{}'.format(sppName)
    upliftFld = 'U_{}'.format(sppName)
    upliftFlds.append(upliftFld)
    
    #Get the lamda file
    lamdaFile = os.path.join(sppModelFolder,species,"{}.lambdas".format(species))
                            
    #Compute current conditions for catchments; convert to dataframe
    aq.maxentProject(lamdaFile,curSWDFile,tmpFile,verbose=False)
    cDF = pd.read_csv(tmpFile,dtype={'GRIDCODE':np.long})
    cDF.drop('FEATUREID',axis=1,inplace=True)
    cDF.rename(columns={'{} logistic values'.format(species):curFld},inplace=True)
    
    #Compute the project uplift; convert to dataframe
    aq.maxentProject(lamdaFile,prjSWDFile,tmpFile,verbose=False)
    pDF = pd.read_csv(tmpFile,dtype={'GRIDCODE':np.long})
    pDF.drop('FEATUREID',axis=1,inplace=True)
    pDF.rename(columns={'{} logistic values'.format(species):prjFld},inplace=True)

    #Join the cDF values to the pDF
    sppDF = pd.merge(cDF,pDF)

    #If not the first table, drop the GRIDCODE field
    if species <> sppList[0]:
        sppDF.drop("GRIDCODE",axis=1,inplace=True)

    #Ensure there's an intersection
    if len(sppDF) == 0:
        aq.msg("ERROR: {} was not modeled for the projection area".format(species),"error")
        continue

    #Calculate uplift
    sppDF[upliftFld] = sppDF[prjFld] - sppDF[curFld]

    #Drop cur and uplift fields
    sppDF.drop(prjFld,axis=1,inplace=True)
    sppDF.drop(curFld,axis=1,inplace=True)
    
    #Add the df to the list of dfs
    sppDFs.append(sppDF)

#Merge all dfs
allDF = pd.concat(sppDFs,axis=1)

#Compute average uplift
allDF["AvgUplift"] = allDF[upliftFlds].mean(axis=1)

#Write to CSV file
allDF.to_csv(outputCSV,index=False)

#Delete tmpFile
os.remove(tmpFile)

#Merge with catchment features
aq.msg("Joining uplift table to {}".format(outputFC))
aq.JoinCSVtoCatchmentFC(outputCSV,catchmentFC,outputFC,verbose=True)