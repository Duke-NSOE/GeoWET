#MergeStreamCatCSVFiles.py
#
# Description: Merges regional stream cat data files into a single file. The regional
#  files need to be downloaded to the StreamCat/Regional/XX folders, where XX is the
#  region name (.e.g., "03N").
#
#  ALSO, the HUC12Lookup.csv file must reside in the Data/Tooldata folder. The HUC12Lookup
#  file is used to attach HUC lookup values to each combined table.
#
#  This script must be run AFTER having downloaded all the stream cat data and BEFORE
#  any scripts creating a project. 
#
# June 2016
# John.Fay@duke.edu

import sys, os, pandas
import numpy as np

#Workspaces
rootFldr = os.path.dirname(os.path.dirname(os.path.dirname(sys.argv[0])))
baseFldr = os.path.join(rootFldr,"Data","StreamCat")
regionFldr = os.path.join(baseFldr,"Regions")
rgn03N = os.path.join(regionFldr,"03N")
rgn05 =  os.path.join(regionFldr,"05")
rgn05 =  os.path.join(regionFldr,"06")

#Get list of files
csvFiles = os.listdir(rgn03N)

#Get the catchment lookup table (to add HUC12, GRIDCODE columns)
nhdTableFN = os.path.join(rootFldr,"Data","Tooldata","HUC12Lookup.csv")

#Create a dataframe from the HUC12 Lookup
cols = ("GRIDCODE","FEATUREID","REACHCODE","HUC_12")
dtypes = {"GRIDCODE":np.str,"FEATUREID":np.str,"REACHCODE":np.str,"HUC_12":np.str}
dfNHD = pandas.read_csv(nhdTableFN,usecols=cols,dtype=dtypes)

#Loop through each file and merge records into a single file
for csvFile in csvFiles:
    if csvFile[-3:] <> "csv": continue
    print "Merging {}".format(csvFile.replace("03N",""))

    #Data Files to be read
    file03n = os.path.join(rgn03N,csvFile)
    file05 = file03n.replace("03N","05")
    file06 = file03n.replace("03N","06")

    #Output file -- in StreamCat folder
    outFN = os.path.join(baseFldr,"AllRegions",csvFile.replace("03N",""))
    if os.path.exists(outFN): continue

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
