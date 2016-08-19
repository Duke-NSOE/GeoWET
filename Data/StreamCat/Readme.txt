This folder contains StreamCat attribute tables merged from the 3 hydro regions covering North Carolina (03N, 05, and 06) as well as two files listing the attributes contained in the StreamCat files.

The *AllRegions* folder
 This folder contains the raw, merged regional StreamCat files. The scripts "STREAMCAT1_GetData.py" and "STREAMCAT2_MergeCSVFiles.py" are used to download and merge the regional StreamCat files, respectively. 

*StreamCatInfo.csv*
 This file lists all the StreamCat attributes and the files containing them. This table, which is the basis for the StreamCatInfo.xlsx file, is created by running the STREAMCAT3_GenerateAttributeList.py script. 
 
*StreamCatInfo.xlsx* 
 This file is created manually from the StreamCatInfo.csv file by filtering out duplicate attribues (e.g. CatAreaSqKm) and adding the following additional fields:
   *CatWS*: Indicates whether the StreamCat attribute pertains to the catchment itself (CAT) or all upstream area (WS)
   *NLCDMap*: Indicates the NLCD class to which the feature may be linked (or -9999 if none)
   *WetlandProject*: Indicates the likelihood and direction of change in the attribute associated with installation of a conversion of land to wetland. 
   *ForestProject*: Indicates the likelihood and direction of change in the attribute associated with installation of a conversion of land to forest.