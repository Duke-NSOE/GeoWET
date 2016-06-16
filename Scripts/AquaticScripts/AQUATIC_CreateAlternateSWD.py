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
#   - Create dataframe of current conditions for catchment
#   - Modify appropriate values 
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
fieldMapXLS = r'C:\workspace\GeoWET\Data\StreamCat\StreamCatInfo.xlsx'
nlcdRaster = r'C:\workspace\GeoWET\Data\EEP_030501.gdb\nlcd_2011'
flowlineFC = r'C:\workspace\GeoWET\Data\EEP_030501.gdb\NHDFlowlines'
elevRaster = r'C:\workspace\GeoWET\Data\EEP_030501.gdb\elev_cm'
catchmentFC = r'C:\workspace\GeoWET\Data\EEP_030501.gdb\NHDCatchments'
huc12FC = r'C:\workspace\GeoWET\Data\EEP_030501.gdb\HUC12'

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

def getHUC8(prjFC,hucFC):
    '''Returns the HUC8s in which the project occurs (via clip)'''
    #Create a feature class of just the catchments intersecting the project
    clipFC = arcpy.Clip_analysis(hucFC,projectFC,"in_memory/clipFC")
    #Loop through the feature classes and add them to a list
    with arcpy.da.SearchCursor(clipFC,"HUC_8") as cur:
        rec = cur.next()
        huc8 = str(rec[0])
    #Delete the feature class
    arcpy.Delete_management(clipFC)
    #Return the list of reachcodes
    return huc8

def getHUC8Data(csvFile,huc8):
    '''Creates a dataframe of the HUC8 Records from a catchment attribute file'''
    #Convert CSV to pandas data frame
    dtypes = {"GRIDCODE":np.str,"FEATUREID":np.str,"REACHCODE":np.str,"HUC_12":np.str} 
    fullDF = pd.read_csv(csvFile,dtype=dtypes)
    #Subset records
    selectDF = fullDF[fullDF["REACHCODE"].str[:8] == huc8]
    return selectDF

def getRasterCounts(rstr):
    '''Returns a dictionary of nlcd codes (keys) and area (values)'''
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
            nlcdCode = rec[1] #Value = NLCD Code
            areaKM2 = rec[2] * 0.0009 #Count * (0.0009 cells/sq km)
            #Add the land cover as key and count as value
            theDict[nlcdCode] = areaKM2
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

def updateRasterCounts(datadict,prjType="Wetland"):
    '''Updates the dataDict to show gain in wetland/forest'''
    #Assign the gainCode to the NLCD cover type
    if prjType == 'Wetland':
        gainCode = 90 #NLCD woody wetland
    else:
        gainCode = 43 #NLCD mixed forest
        
    #Get total existing areas of project not in project mode
    prjAreas = [0,0,0,0]
    for k,v in datadict.items():
        if k <> gainCode:
            #Loop through scenarios
            for i in range(4):
                prjAreas[i] -= v[i]
                
    #Change wetland/forest change to prjArea
    datadict[gainCode] = prjAreas

    #Return the revised dictionary
    return datadict

##---PROCEDURES----
#Create a dictionary of NLCD changes in the catchment
dataDict = getNLCDValues(flowlineFC,nlcdRaster,elevRaster,projectFC)

#Update the dataDict to show gain in wetland/forest
dataDict = updateRasterCounts(dataDict,projectType)
   
#Get the list of NHD gridcodes within the project
###>>>NEED TO ADAPT TO IF A PROJECT SPANS CATCHMENTS<<<<
gridCodes = getGridcodes(projectFC,catchmentFC)
gridCode = gridCodes[0]

#Get the HUC8 in which the project occurs
huc8 = getHUC8(projectFC,huc12FC)
print "Project is in HUC8: {}".format(huc8)

#Import the Excel file listing the fields to change...
fldmapDF = pd.read_excel(fieldMapXLS,'StreamCatInfo')

#Filter for fields changed in wetland project
fldsDF = fldmapDF[fldmapDF["WetlandProject"] <> 'Unchanged']
csvFiles = pd.unique(fldsDF.File).tolist()

##---REPLACE WITH LOOP---##
for csvFile in [csvFiles[-1]]:
    print "Processing {}".format(csvFile)

    #Get the relevant attributes
    attribDF = fldsDF[fldsDF["File"] == str(csvFile)]
    
    #Get the full file name (with path)
    csvFN = os.path.join(dataFolder,csvFile)
      
    #Create a dataframe of the HUC8 data from the CSV file
    dataDF = getHUC8Data(csvFN,huc8)
    print "...{} records returned".format(dataDF.shape[0])

    #Get the data for the gridcodes the project covers
    gridDF = dataDF[dataDF.GRIDCODE.isin(gridCodes)]
    areaColumn = gridDF.columns[5]
    catArea = gridDF[areaColumn].sum()
    
    #Get the lookup table fromthe XLSX file
    lutDict = attribDF.set_index('NLCDMap')['Attribute'].to_dict()

    #Update NLCD fields for the selected catchment
    for nlcdCode,areaChanges in dataDict.items():
        
        #Get the StreamCat code corresponding to the NLCD code
        #scCode = str(lutDict[nlcdCode])
        #nlcdFld = "Pct{}2011Cat".format(scCode)
        nlcdFld = str(lutDict[nlcdCode]).strip()
        
        #Extract the CURRENT pct area of the catchment
        curPct = gridDF[nlcdFld].values[0]
        
        #Convert to total area (sq km)
        nlcdArea = curPct * catArea / 100
        
        #Determine which project area value to get
        if "Rp100" in nlcdFld: idx = 1
        elif "Slp10" in nlcdFld: idx = 2
        elif "Slp20" in nlcdFld: idx = 3
        else: idx = 0
        #Get lost area from dictionary
        lostNlcdArea = areaChanges[idx]
        
        #Deduct the lost area
        newNlcdArea = nlcdArea - lostNlcdArea
        #Convert back to pct
        newPct = newNlcdArea / catArea * 100
        print "Changing NLCD %s from %2.1f to %2.1f pct" %(nlcdCode,curPct,newPct)
        #Update the output dataframe
        dataDF.loc[dataDF['GRIDCODE'] == gridCode, nlcdFld] = newPct

    #Save the DF
    dataDF.to_csv(outputSWDFile,index_label="OID",index=False)
 
