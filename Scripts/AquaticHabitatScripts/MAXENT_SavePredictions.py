# MAXENT_SavePredictions.py
#
# Saves Maxent raw logistical and thresholded output to csv
#
# Spring 2015
# John.Fay@duke.edu

import arcpy, sys, os, csv
arcpy.env.overwriteOutput = 1

# Input variables
speciesName = arcpy.GetParameterAsText(0)
statsRootFolder = arcpy.GetParameterAsText(1)
maxentScenario = arcpy.GetParameterAsText(2)

# ---Functions---
def msg(txt,type="message"):
    print txt
    if type == "message":
        arcpy.AddMessage(txt)
    elif type == "warning":
        arcpy.AddWarning(txt)
    elif type == "error":
        arcpy.AddError(txt)

##--Derived Variables
msg("Locating species stats folder")
sppFolder = os.path.join(statsRootFolder,speciesName)
if not os.path.exists(sppFolder):
    msg("{} not found.\nExiting.".format(sppFolder))
    sys.exit(1)
    
msg("Locating Maxent output folder")
maxentFolder = os.path.join(sppFolder,maxentScenario)
if not os.path.exists(maxentFolder):
    msg("{} not found.\nExiting.".format(maxentFolder))
    sys.exit(1)

msg("Locating Maxent log file")
logFN = os.path.join(maxentFolder,"maxent.log")
if not os.path.exists(logFN):
    msg("File {} does not exist.\nExiting.".format(logFN),"error")
    sys.exit()

msg("Locating Maxent results file")
resultsFN = os.path.join(maxentFolder,"maxentResults.csv")
if not os.path.exists(logFN):
    msg("File {} does not exist.\nExiting.".format(logFN),"error")
    sys.exit()
    
msg("Locating Maxent predictions file")
logisticFN = os.path.join(maxentFolder,speciesName+".csv")
if not os.path.exists(logFN):
    msg("File {} does not exist.\nExiting.".format(logFN),"error")
    sys.exit()

# Output
outCSV = os.path.join(sppFolder,"ME_Results.csv")
msg("Setting output to {}".format(outCSV))
arcpy.SetParameterAsText(3,outCSV) 


## ---Processes---
msg("Reading result values")
f = open(logFN,"r")
lines = f.readlines()
f.close()

#Get the threshold (column 255 in the maxentResults.csv)
f = open(resultsFN,'rt')
reader = csv.reader(f)
row1 = reader.next()
row2 = reader.next()
f.close()
idx = row1.index('Balance training omission, predicted area and threshold value logistic threshold')
threshold = row2[idx]
msg("Maxent logistic threshold set to {}".format(threshold),"warning")

# Read in the predictions; make a list of values
msg("reading in logistic values")
predList = []
f = open(logisticFN,'rt')
row1 = f.readline()
row2 = f.readline()
while row2:
    predList.append(row2.split(","))
    row2 = f.readline()
f.close()
    
# Write the output to a file
msg("Creating Maxent Output File")
f = open(outCSV,'w')
f.write("GRIDCODE,PROB,HABITAT\n")
for rec in predList:
    gridcode = rec[0]
    prob = float(rec[2])
    if prob >= float(threshold): hab = 1
    else: hab = 0
    f.write("{},{},{}\n".format(gridcode,prob,hab))
f.close()

