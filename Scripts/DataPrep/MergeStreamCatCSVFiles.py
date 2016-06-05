#MergeStreamCatCSVFiles.py
#
# Description: Merges regional stream cat data files into a single file
#
# June 2016
# John.Fay@duke.edu

import sys, os, pandas
import numpy as np

#Workspaces
rootFldr = r'C:\workspace\GeoWET\Data\StreamCat\Regional'
rgn03N = os.path.join(rootFldr,"Region03N")
rgn05 =  os.path.join(rootFldr,"Region05")
rgn05 =  os.path.join(rootFldr,"Region06")

#Get list of files
csvFiles = os.listdir(rgn03N)

#Get the catchment lookup table (to add HUC12, GRIDCODE columns)
nhdTableFN = r'C:\workspace\GeoWET\Data\Tooldata\HUC12Lookup.csv'

#Create a dataframe from the HUC12 Lookup
cols = ("GRIDCODE","FEATUREID","REACHCODE","HUC_12")
dtypes = {"GRIDCODE":np.str,"FEATUREID":np.str,"REACHCODE":np.str,"HUC_12":np.str}
dfNHD = pandas.read_csv(nhdTableFN,usecols=cols,dtype=dtypes)

#Loop through each file and merge records into a single file
for csvFile in csvFiles:
    if csvFile[-3:] <> "csv": continue
    print "Merging {}".format(csvFile.replace("03N",""))

    #Data Files
    file03n = os.path.join(rgn03N,csvFile)
    file05 = file03n.replace("03N","05")
    file06 = file03n.replace("03N","06")
    outFN = os.path.join(rootFldr,csvFile.replace("03N",""))

    #Data frames
    df03n = pandas.read_csv(file03n,dtype={"COMID":np.str})
    df05 = pandas.read_csv(file05,dtype={"COMID":np.str})
    df06 = pandas.read_csv(file06,dtype={"COMID":np.str})

    #Merge data frames
    dfAll = [df03n, df05, df06]
    result = pandas.concat(dfAll)

    #Join HUC12 lookup columns
    indexed_df = result.set_index("COMID")
    outDF = pandas.merge(dfNHD,indexed_df,left_on="FEATUREID",right_index=True)

    #Write to new file
    shp = outDF.shape
    print "...writing {} records and {} columns to {}".format(shp[0],shp[1],outFN)
    outDF.to_csv(outFN,index_label="OID",na_rep="-9999")
