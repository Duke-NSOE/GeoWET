#GenerateAttributeList.py
#
# Creates a CSV file listing all the attributes included in the Stream Cat data
#
# June 2016
# John.Fay@duke.edu

import sys, os, pandas

# Get the files
dataFldr = r'C:\workspace\GeoWET\Data\StreamCat\AllRegions'
files = os.listdir(dataFldr)

# Set the outpuf file name
outFN = r'C:\workspace\GeoWET\Data\StreamCat\StreamCatInfo.csv'
outFObj = open(outFN,'wt')
outFObj.write("File, Attirbute\n")

# Set the filter (filenames not to report
filter = ("OID","GRIDCODE","FEATUREID","REACHCODE","HUC_12")

#Set the current working directory
os.chdir(dataFldr)

#Loop through all files
for fName in files:
    #Skip if not a csv file
    if fName[-4:] <> '.csv': continue
    #Get the header line
    with open(fName,'rt') as fObj:
        headerLine = fObj.readline()[:-1]
    #Split into parts
    headerItems = headerLine.split(",")
    #Write each to the output file
    for headerItem in headerItems:
        if headerItem not in filter:
            outFObj.write("{}, {}\n".format(fName,headerItem))

outFObj.close()
    