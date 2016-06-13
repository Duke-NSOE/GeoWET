# MAXENT_SavePredictions.py
#
# Saves Maxent raw logistical and thresholded output to csv
#
# Spring 2015
# John.Fay@duke.edu

import sys, os, csv


# Input variables
maxentOutputFile = r'C:\workspace\GeoWET\Data\SpeciesModels\Output\Nocomis_leptocephalus.csv'
outCSV = r'C:\workspace\GeoWET\Data\SpeciesModels\Output\Nocomis_leptocephalus_GIS.csv'

# Derived variables
speciesName = os.path.basename(maxentOutputFile)[:-4]
maxentFolder = os.path.dirname(maxentOutputFile)
logFN = os.path.join(maxentFolder,"maxent.log")
resultsFN = os.path.join(maxentFolder,"maxentResults.csv")
logisticFN = os.path.join(maxentFolder,speciesName+".csv")

# ---Functions---
def msg(txt,type="message"):
    print txt

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

