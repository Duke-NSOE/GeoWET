# UPLIFT_MergeUpliftResults.py
#
# Description:
#  Merges uplift FCs for multiple species into a single FC with average values.
#
# Overview:
#  Loops through each [species] folder in the stats root folder, and then locates
#  the Scenario folder (e.g. "BU_Output") within. In this folder should be the uplift
#  feature class for the species listing the observed, current likelihood, scenario
#  likelihood, scenario prediction, and computed uplift.
#
#  Uplift scores across all species are conveyed to the output feature class and a
#  mean score across all scpecies is calculated.
#
# Fall 2015
# John.Fay@duke.edu

import sys, os, arcpy, csv, tempfile
arcpy.env.overwriteOutput = 1

# Input variables
scenarioName = arcpy.GetParameterAsText(0)  #Prefix used to represent scenarion (e.g. BU for buffer)
statsRootFldr = arcpy.GetParameterAsText(1) #Folder containing all species stats results
catchmentFC = arcpy.GetParameterAsText(2)   #Catchment features, used to add uplift values to
HUCFilter = arcpy.GetParameterAsText(3)     #HUC Filter used to find tables and select appropriate catchment from the FC

## ---Functions---
def msg(txt,type="message"):
    print txt
    if type == "message":
        arcpy.AddMessage(txt)
    elif type == "warning":
        arcpy.AddWarning(txt)
    elif type == "error":
        arcpy.AddError(txt)
        
def checkFile(fileName):
    if not os.path.exists(fileName):
        msg("{} not found.\nExiting.".format(fileName),"error")
        sys.exit(1)
    else: return
    
## ---Set derived variables---
msg("Locating scenario geodatabase")
upliftGDB = os.path.join(statsRootFldr,"{}_Uplift.gdb".format(scenarioName))
checkFile(upliftGDB)

#Set the output table
outFC = os.path.join(upliftGDB,"{}_Uplift{}".format(scenarioName,HUCFilter))
arcpy.SetParameterAsText(4,outFC)

## ---Processes---
#Get a list of species uplift tables in the uplift GDB corresponding to the uplift filter
msg("Getting list of species tables")
arcpy.env.workspace = upliftGDB
sppTbls = arcpy.ListTables("*{}".format(HUCFilter))   #Get all the species tables (they have two underscores in them...)
#Exit if no tables were found. 
if len(sppTbls) == 0:
    msg("No results for HUC {}.\nExiting".format(HUCFilter),"error")
    sys.exit(1)

#Select catchments into the output feature class
msg("Initializing output feature class")
msg("...Selecting features in HUC {}".format(HUCFilter))
whereClause = "REACHCODE LIKE '{}%'".format(HUCFilter)
arcpy.Select_analysis(catchmentFC,outFC,whereClause)

#Remove fields (the last three in the sppTbl)
msg("...removing extra fields")
killFlds = []
for fld in arcpy.ListFields(outFC):
    if not fld.name.upper() in ("OBJECTID","SHAPE","GRIDCODE","REACHCODE","SHAPE_AREA","SHAPE_LENGTH"):
        killFlds.append(fld.name)
arcpy.DeleteField_management(outFC,killFlds)

#Add average current likelihood, current rank, averge uplift field, and uplift rank fields
msg("...adding mean current likelihood field")          
curFldName = "MeanLikelihood"
arcpy.AddField_management(outFC,curFldName,"DOUBLE")
msg("...adding current likelihood rank field")
curRankFld = "CurrentRank"
arcpy.AddField_management(outFC,curRankFld,"SHORT")
msg("...adding average uplift fld")
avgFldName = "MeanUplift"
arcpy.AddField_management(outFC,avgFldName,"DOUBLE")
msg("...adding decile rank fld")
rankFldName = "UpliftRank"
arcpy.AddField_management(outFC,rankFldName,"SHORT")

#Initialize a list of current and uplift fields so we can average them later
curFlds = []
upliftFlds = []

#Loop through the species folders and append the uplift columns to a master FC
msg("Merging species tables")
for sppTbl in sppTbls:
    #Get the current condition field (the 3rd field) and add it to the curFlds list
    curFld = arcpy.ListFields(sppTbl,"*cur*")[0].name
    curFlds.append(curFld)
    #Get the uplift field (the last field in the table) and add it to the list
    upliftFld = arcpy.ListFields(sppTbl)[-1].name
    upliftFlds.append(upliftFld)

    #Join the fields to the outFC
    arcpy.JoinField_management(outFC,"GRIDCODE",sppTbl,"GRIDCODE",(curFld,upliftFld))

##Compute average habitat likelihood across species
#Make a calculate string from the habitat fields
msg("Calculating average current likelihood")
msg("...constructing the equation")
calcString = "("
for curFld in curFlds:
    calcString += "[{}] + ".format(curFld)

#Modify the string to calculate averages
calcString = calcString[:-3] + ") / {}".format(len(curFlds))

#Apply the calcString
msg("...calculating average likelihood")
arcpy.CalculateField_management(outFC,curFldName,calcString)

##Compute averge uplift across species
#Make a calculate string from the upliftFlds
msg("Calculating average uplift")
msg("...constructing the equation")
calcString = "("
for upliftFld in upliftFlds:
    calcString += "[{}] + ".format(upliftFld)

#Modify the string to calculate averages
calcString = calcString[:-3] + ") / {}".format(len(upliftFlds))

#Apply the calcString
msg("...calculating average uplift")
arcpy.CalculateField_management(outFC,avgFldName,calcString)

##Compute deciles on current condition values
msg("Computing current condition deciles")
#Get the number of records and determine the quantile size
numRecs = int(arcpy.GetCount_management(outFC).getOutput(0))
decileSize = numRecs / 10.0
#Set the counter variables
decile = 1              #Index of decile's upper limit
ceiling = decileSize    #Initial decile value
counter = 1             #Counter that increases with each record

#Create the update cursor, sorted on average uplift
records = arcpy.UpdateCursor(outFC,"","","{}; {}".format(curFldName,curRankFld),"{} A".format(curFldName))
rec = records.next()
while rec:
    #Check to see if we've entered a new decile, if so, increase the index
    if counter > ceiling:       #If the current rec passes the ceiling
        ceiling += decileSize   #...raise the ceiling
        decile += 1           #...up the decile value
    #Assign the quantile to the rank field
    rec.setValue(curRankFld,decile)
    records.updateRow(rec)
    #Move to the next record
    counter += 1
    rec = records.next()
        
##Compute deciles on uplift values
msg("Computing uplift deciles")
#Get the number of records and determine the quantile size
numRecs = int(arcpy.GetCount_management(outFC).getOutput(0))
decileSize = numRecs / 10.0
#Set the counter variables
decile = 1              #Index of decile's upper limit
ceiling = decileSize    #Initial decile value
counter = 1             #Counter that increases with each record

#Create the update cursor, sorted on average uplift
records = arcpy.UpdateCursor(outFC,whereClause,"","{}; {}".format(avgFldName,rankFldName),"{} A".format(avgFldName))
rec = records.next()
while rec:
    #Check to see if we've entered a new decile, if so, increase the index
    if counter > ceiling:       #If the current rec passes the ceiling
        ceiling += decileSize   #...raise the ceiling
        decile += 1           #...up the decile value
    #Assign the quantile to the rank field
    rec.setValue(rankFldName,decile)
    records.updateRow(rec)
    #Move to the next record
    counter += 1
    rec = records.next()
        