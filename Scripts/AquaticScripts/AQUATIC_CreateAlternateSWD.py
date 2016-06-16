#AQUATIC_CreateAlternateSWD.py
#
# Modifies the StreamCat tables within a selected area (e.g. HUC8) to
# reflect a conservation action. The inputs are a set of catchments and
# the modified land cover.
#
# WORKFLOW:
# - Identify the HUC8 and Catchments in which the project occurs
# - Extract catchment records for the HUC8s in which the project occurs
# - List the area of NLCD types that will be converted in each catchment
# - List the area of NLCD types within 100m of stream...
# - List the area of NLCD types in slope categories...
# - Update the catchment attributes to reflect the land cover changes
#   - Current catchment
#   - All downstream catchments
# - Write out the projection file in SWD format.
#
# June 2016
# John.Fay@duke.edu

import sys, os, arcpy
import pandas as pd
import numpy as np

arcpy.env.overwriteOutput = True
arcpy.env.workspace = r'C:\workspace\GeoWET\scratch'
arcpy.env.scratchWorkspace =  r'C:\workspace\GeoWET\scratch'
arcpy.CheckOutExtension("spatial")

#Inputs
projectFC = r'C:\workspace\GeoWET\Data\Templates\ExampleProject.shp'
projectType = 'Wetland'
dataFolder = r'C:\workspace\GeoWET\Data\StreamCat\AllRegions'
outputSWDFile = r'C:\workspace\GeoWET\Scratch\ExampleProject_SWD.csv'

#Static inputs
nlcdRaster = r'C:\workspace\GeoWET\Data\EEP_030501.gdb\nlcd_2011'
flowlineFC = r'C:\workspace\GeoWET\Data\EEP_030501.gdb\NHDFlowlines'
elevRaster = r'C:\workspace\GeoWET\Data\EEP_030501.gdb\elev_cm'
catchmentFC = r'C:\workspace\GeoWET\Data\EEP_030501.gdb\NHDCatchments'

##-----------FUNCTIONS----------
def getGridcodes(prjFC,catchFC):
    '''Returns a list of NHD Reachcodes in which the project occurs (via clip)'''
    #Create a feature class of just the catchments intersecting the project
    clipFC = arcpy.Clip_analysis(catchmentFC,projectFC,"in_memory/clipFC")
    #Initialize the list of reach codes
    gridcodes = []
    #Loop through the feature classes and add them to a list
    with arcpy.da.SearchCursor(clipFC,"GRIDCODE") as cur:
        for rec in cur:
            gridcodes.append(str(rec[0]))
    #Delete the feature class
    arcpy.Delete_management(clipFC)
    #Return the list of reachcodes
    return gridcodes

def getHUC8s(reachcodes):
    '''Returns a list of HUCs in which the reachodes occur'''
    huc8s = []
    for r in reachcodes:
        huc8 = r[:8]
        if not huc8 in huc8s:
            huc8s.append(huc8)
    return huc8s

def getCatchmentData(csvFile,gridCodes):
    '''Extract the HUC8 Records from a catchment attribute file'''
    #Convert CSV to pandas data frame
    dtypes = {"GRIDCODE":np.str,"FEATUREID":np.str,"REACHCODE":np.str,"HUC_12":np.str} 
    fullDF = pd.read_csv(csvFile,dtype=dtypes)
    #Subset records
    selectDF = fullDF[fullDF["GRIDCODE"].isin(gridCodes)]

def getCurrentNLCD(nlcdRstr,prjFC):
    '''Return a dictionary of the land cover underneath the project'''
    #Get the NLCD raster
    selectNLCD = arcpy.sa.ExtractByMask(nlcdRstr,prjFC)
    #Get its attribute table
    nlcdTbl = arcpy.CopyRows_management(selectNLCD,"in_memory/nlcdTbl")
    #Initialize the dictionary
    nlcdDict = {}
    #Loop through each record
    with arcpy.da.SearchCursor(nlcdTbl,'*') as cur:
        for rec in cur:
            #Add the land cover as key and count as value
            nlcdDict[rec[1]] = rec[2]
    #Delete objects
    arcpy.Delete_management(selectNLCD)
    arcpy.Delete_management(nlcdTbl)
    #Return the dictionary
    return nlcdDict

def getRasterCounts(rstr):
    '''Returns a dataframe of raster values (keys) and counts (values)'''
    #Check that raster is not just NoData values
    if arcpy.GetRasterProperties_management(rstr,'ALLNODATA').getOutput(0) == '1':
        return {}
    #Get its attribute table
    theTbl = arcpy.CopyRows_management(rstr,"in_memory/nlcdTbl")
    #Initialize the dictionary
    theDict = {}
    #Loop through each record
    with arcpy.da.SearchCursor(theTbl,'*') as cur:
        for rec in cur:
            #Add the land cover as key and count as value
            theDict[rec[1]] = rec[2]
    #Delete the table
    arcpy.Delete_management(theTbl)
    #Return the dictionary
    return theDict

def getNLCDValues(flwlineFC,nlcdRstr,elevRstr,prjFC):
    '''Return a dictionary of the land cover underneath the project'''
    #Get the NLCD raster
    selectNLCD = arcpy.sa.ExtractByMask(nlcdRstr,prjFC)
    nlcdDict = getRasterCounts(selectNLCD)
    arcpy.env.extent =selectNLCD
    
    #Create a riparian buffer mask and NLCD raster
    bufMask = arcpy.sa.EucDistance(flwlineFC,100)
    buffNLCD = arcpy.sa.ExtractByMask(selectNLCD,bufMask)
    buffDict = getRasterCounts(buffNLCD)
    
    #Create slope masks and NLCD rasters
    slpRstr = arcpy.sa.Slope(elevRstr,"PERCENT_RISE")
    midSlope = arcpy.sa.SetNull(elevRstr,1,"VALUE >= 10")
    midNLCD = arcpy.sa.ExtractByMask(selectNLCD,midSlope)
    midDict = getRasterCounts(midNLCD)
    
    highSlope = arcpy.sa.SetNull(slpRstr,1,"VALUE >= 20")
    highNLCD = arcpy.sa.ExtractByMask(selectNLCD,highSlope)
    highDict = getRasterCounts(highNLCD)

    #Merge the dictionaries
    outDict = {}
    for k in nlcdDict.keys():
        valList = []
        valList.append(nlcdDict[k])
        for theDict in [buffDict,midDict,highDict]:
            if k in theDict.keys():
                valList.append(theDict[k])
            else:
                valList.append(0)
        outDict[k] = valList

    #Return the series
    return outDict

##---PROCEDURES----

#Get the changed NLCD
#nlcdDict = getCurrentNLCD(nlcdRaster,projectFC)
dataDict = getNLCDValues(flowlineFC,nlcdRaster,elevRaster,projectFC)

#Get the list of gridcodes
#gridCodes = getGridcodes(projectFC,catchmentFC)

#Get the CSV full path (replace with loop)
#csvFile = os.path.join(dataFolder,'NLCD2011_Region.csv')


