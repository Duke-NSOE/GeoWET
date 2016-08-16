#GenerateAttributeList.py
#
# Creates a CSV file listing all the attributes included in the Stream Cat data alongside the file
#  in which they occur. This is used in later scripts to extract specific attributes from the proper
#  file. 
#
# June 2016
# John.Fay@duke.edu

import sys, os, pandas

# Get the files
rootFldr = os.path.dirname(os.path.dirname(os.path.dirname(sys.argv[0])))
streamCatFldr = os.path.join(rootFldr,'Data','StreamCat')
files = os.listdir(streamCatFldr)

# Set the outpuf file name
outFN = os.path.join(streamCatFldr,'StreamCatInfo.csv')
outFObj = open(outFN,'wt')
outFObj.write("File, Attirbute\n")

# Set the filter (filenames not to report
filter = ("OID","GRIDCODE","FEATUREID","REACHCODE","HUC_12")

#Set the current working directory
os.chdir(streamCatFldr)

#Loop through all files
for fName in files:
    #Skip if not a csv file
    if fName[-4:] <> '.csv': continue
    #Skip if name is the output file
    if fName == outFN: continue
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
    