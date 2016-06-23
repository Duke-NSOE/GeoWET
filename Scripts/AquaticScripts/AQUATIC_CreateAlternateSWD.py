#AQUATIC_CreateAlternateSWD.py
#
# Modifies the StreamCat tables within a selected area (e.g. HUC8) to
# reflect a conservation action. The inputs are a set of catchments and
# the modified land cover.
#
# WORKFLOW:
# - Identify the HUC8 and Catchments in which the project occurs
# - Extract catchment records for the HUC8s in which the project occurs
# - Write unmodified values to a SWD file
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
arcpy.CheckOutExtension("spatial")

#Inputs
projectFC = sys.argv[1]     #r'C:\workspace\GeoWET\Data\Templates\ExampleProject.shp'
projectType = sys.argv[2]   #'Wetland'
dataFolder = sys.argv[3]    #r'C:\workspace\GeoWET\Data\StreamCat\AllRegions'

#Static inputs
fieldMapXLS = sys.argv[4]   #r'C:\workspace\GeoWET\Data\StreamCat\StreamCatInfo.xlsx'
nlcdRaster = sys.argv[5]    #r'C:\workspace\GeoWET\Data\EEP_030501.gdb\nlcd_2011'
flowlineFC = sys.argv[6]    #r'C:\workspace\GeoWET\Data\EEP_030501.gdb\NHDFlowlines'
elevRaster = sys.argv[7]    #r'C:\workspace\GeoWET\Data\EEP_030501.gdb\elev_cm'
catchmentFC = sys.argv[8]   #r'C:\workspace\GeoWET\Data\EEP_030501.gdb\NHDCatchments'
flowNet = sys.argv[9]       #r'C:\workspace\GeoWET\Data\ToolData\NHD_H_03050102_GDB.gdb\Hydrography\HYDRO_NET'

#Derived inputs
flowNetFC = os.path.join(flowNet,'..',"NHDFlowline")

#Output
projectSWDFile = sys.argv[10]#r'C:\workspace\GeoWET\Scratch\ExampleProject_SWD.csv'
currentSWDFile = projectSWDFile.replace(".csv","CUR.csv")

##-----------FUNCTIONS----------
def msg(txt,severity=""):
    '''Feedback'''
    print msg
    #Send to ArcPy, if tool run from ArcMap
    try:
        if severity=="warning":
            arcpy.AddWarning(txt)
        elif severity=="error":
            arcpy.AddError(txt)
        else:
            arcpy.AddMessage(txt)
    except:
        pass
    return
            
def getGridcodes(prjFC,catchFC):
    '''Returns a list of NHD Reachcodes in which the project occurs (via clip)'''
    #Create a feature class of just the catchments intersecting the project
    clipFC = arcpy.Clip_analysis(catchmentFC,projectFC,"in_memory/clipFC")
    #Initialize the list of reach codes
    gridcodes = []
    #Loop through the feature classes and add them to a list
    with arcpy.da.SearchCursor(clipFC,"GRIDCODE") as cur:
        for rec in cur:
            gridcodes.append(rec[0])
    #Delete the feature class
    arcpy.Delete_management(clipFC)
    #Return the list of reachcodes
    return gridcodes

def getDownstreamGridCodes(gridcode,catchFC,flownet,flownetFC):
    '''Traces downstream from the project's catchment and lists all downstream catchment GRIDCODES'''
    #Get the catchment corresponding to the gridcode
    theCatchLyr = arcpy.MakeFeatureLayer_management(catchFC,"theCatch","GRIDCODE = {}".format(gridcode))
    #Clip the flowine within the catchment and get its lowest point
    theFlowline = arcpy.Clip_analysis(flownetFC,theCatchLyr,"in_memory/theFlowline")
    theFlowpoint = arcpy.FeatureVerticesToPoints_management(theFlowline,"in_memory/thePoint","END")
    #Trace from this point downstream to the end of the HUC8 geometric network
    theTraceLyr = arcpy.TraceGeometricNetwork_management(flownet,"DownStrmLyr",theFlowpoint,"TRACE_DOWNSTREAM")
    #Extract the line feature
    theTraceLine = arcpy.SelectData_management(theTraceLyr,"NHDFlowline")
    #Make a new feature layer of catchments and select those that intersect the downstream trace
    theCatchLyr = arcpy.MakeFeatureLayer_management(catchFC,"theCatch")
    theCatchments = arcpy.SelectLayerByLocation_management(theCatchLyr,"INTERSECT",theTraceLine)
    #Create a list of catchment GRIDCODEs in the selected catchments
    outGridcodes = []
    with arcpy.da.SearchCursor(theCatchments,"GRIDCODE") as cur:
        for rec in cur:
            outGridcodes.append(rec[0])
    return outGridcodes
   
def getCatchmentData(csvFile,downstreamCodes):
    '''Creates a dataframe of the HUC8 Records from a catchment attribute file'''
    #Convert CSV to pandas data frame
    dtypes = {"GRIDCODE":np.long,"FEATUREID":np.str,"REACHCODE":np.str,"HUC_12":np.str} 
    fullDF = pd.read_csv(csvFile,dtype=dtypes)
    #Subset records
    selectDF = fullDF[fullDF["GRIDCODE"].isin(downstreamCodes)]
    return selectDF

def makeDataFramefromCSVs(dataFldr,gridcodes):
    '''Returns a dataframe of stream cat attributes for selected gridcodes'''
    #Initialize the list of dataframes to merge
    dataFrames = []
    #Get a listing of all the files in the folder
    dataFiles = os.listdir(dataFldr)
    #Loop through each file
    for dataFile in dataFiles:
        #Skip if not a CSV file
        if dataFile[-4:].upper() <> ".CSV": continue
        msg("Processing streamcat file: {}".format(dataFile))
        #Get the full file path
        csvFN = os.path.join(dataFolder,dataFile)
        #Convert catchment records to a data frame
        csvDF = getCatchmentData(csvFN,gridcodes)
        #Remove duplicate column names (unless its the first file)
        if len(dataFrames) == 0:
            colNames = list(csvDF.columns)
        else:
            newCols = []
            for col in list(csvDF.columns):
                if not (col in colNames):
                    newCols.append(col)
                    colNames.append(col)
            csvDF = csvDF[newCols]
        #Append to dataDFs
        dataFrames.append(csvDF)

    #Merge dataframes
    msg("...merging dataframes")
    dataDF = pd.concat(dataFrames,axis=1)
    #Return the data frame
    return dataDF

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
    
    #Get the current extent (to reset later) and set to project
    initExtent = arcpy.env.extent
    arcpy.env.extent = selectNLCD
    
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
        
    #Reset the extent
    arcpy.env.extent = initExtent

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
msg("---------Initializing analysis-----------")
##[1]Create a dataframe of NLCD areas lost or gained
#Create a dictionary of NLCD changes in the catchment
dataDict = getNLCDValues(flowlineFC,nlcdRaster,elevRaster,projectFC)
#Update the dataDict to show gain in wetland/forest
dataDict = updateRasterCounts(dataDict,projectType)

##[2]Get the GRIDCODEs of the catchment(s) in which the project occurs
gridCodes = getGridcodes(projectFC,catchmentFC)
gridCode = gridCodes[0]
msg("Project occurs in catchment {}".format(gridCode))

##[3]Trace downstream to get the downstream catchments
dsGridCodes = getDownstreamGridCodes(gridCode,catchmentFC,flowNet,flowNetFC)
msg("{} catchments downstream".format(len(dsGridCodes)))

##[4]Create dataframes of selected catchments and merge into one...
#Append the project catchment to downstream ones
gridCodes = dsGridCodes
gridCodes.append(gridCode)
dataDF = makeDataFramefromCSVs(dataFolder,gridCodes)
msg("{} catchment attributes extracted".format(dataDF.shape[1]))

#Write out unmodified dataframe as current conditions
dataDF.to_csv(currentSWDFile,index_label="OID",index=False)

##[5]Adjust NLCD related attributes **in the project catchment**
#Read in the StreamCatInfo table
msg("Reading in field mappings")
lutDF = pd.read_excel(fieldMapXLS,'StreamCatInfo')

#Process changes record for the catchment itself
catchDF = dataDF[dataDF.GRIDCODE == gridCode]
#Get the catchment area values
catchArea = catchDF.CatAreaSqKm.values[0]
riparianArea = catchDF.CatAreaSqKmRp100.values[0]
midslopeArea = catchDF.PctAg2006Slp10Ws.values[0]
highslopeArea = catchDF.PctAg2006Slp20Ws.values[0]
#Put area values into a list
baseAreas = (catchArea,riparianArea,midslopeArea,highslopeArea)

#Reduce field map dataframe to only catchment (not watershed) records
catOnlyDF = lutDF.loc[lutDF.CatWs == 'CAT']

#Loop through the land cover types that have changed for the current catchment
for nlcdType, changeValues in dataDict.items():
    ##Process catchment wide values
    #Extract fields mapped to the current land cover type
    nlcdDF = catOnlyDF.loc[(catOnlyDF.NLCDMap==nlcdType)]
    #Loop through retrieved attributes 
    for nlcdAttrib in nlcdDF.Attribute.values:
        #Determine whether it's full catchment, riparian, or mid/high slope; set the index
        if "Rp" in nlcdAttrib: idx = 1        # Riparian
        elif "Slp10" in nlcdAttrib: idx = 2   # Mid-slope
        elif "Slp20" in nlcdAttrib: idx = 3   # High-slope
        else: idx = 0                         # Catchment wide
        #Get the appropriate change area
        changeArea = changeValues[idx]
        #Skip if no change has occurred
        if changeArea == 0: continue
        #Get the appropriate baseline area
        baseArea = baseAreas[idx]
        #Get the value of that attribute in the catchment dataframe
        currentPct = catchDF[nlcdAttrib].values[0]
        #Convert to sq km (multiply by area, computed above)
        currentArea = currentPct * baseArea / 100.0        
        #Calculate new area
        newArea = currentArea - changeArea
        #Calculate new percentage
        newPct = newArea / baseArea * 100.0
        if newArea > 0:
            msg("   ...%s has decreased %2.2f pct (%s km2)" %(nlcdAttrib,(currentPct - newPct),changeArea))
        #Update the data frame
        dataDF.loc[dataDF['GRIDCODE'] == gridCode, nlcdAttrib] = newPct
        
##[6] Adjust **downstream** values
#Extract only watershed values from the remap table
wsOnlyDF = lutDF.loc[lutDF.CatWs == 'WS']
#Loop through each downstream catchment record
for gridcode in gridCodes:
    msg("Processing catchment# {}".format(gridcode))
    #Retrieve the record for the current gridCode
    catchDF = dataDF[dataDF.GRIDCODE == gridcode]

    #Get the watershed area values
    wsArea = catchDF.WsAreaSqKm.values[0]
    wsRiparianArea = catchDF.WsAreaSqKmRp100.values[0]
    wsMidslopeArea = catchDF.PctAg2006Slp10Ws.values[0]
    wsHighslopeArea = catchDF.PctAg2006Slp20Ws.values[0]
    #Add to a list
    baseAreas = (wsArea,wsRiparianArea,wsMidslopeArea,wsHighslopeArea)
    
    #Loop through the land cover types that have changed for the current catchment
    for nlcdType, changeValues in dataDict.items():
        ##Process catchment wide values
        #Extract fields mapped to the current land cover type
        nlcdDF = wsOnlyDF.loc[(wsOnlyDF.NLCDMap==nlcdType)]
        #Loop through retrieved attributes 
        for nlcdAttrib in nlcdDF.Attribute.values:
            #Determine whether it's full catchment, riparian, or mid/high slope; set the index
            if "Rp" in nlcdAttrib: idx = 1        # Riparian
            elif "Slp10" in nlcdAttrib: idx = 2   # Mid-slope
            elif "Slp20" in nlcdAttrib: idx = 3   # High-slope
            else: idx = 0                         # Catchment wide
            #Get the appropriate change area
            changeArea = changeValues[idx]
            #Skip if no change has occurred
            if changeArea == 0: continue
            #Get the appropriate baseline area
            baseArea = baseAreas[idx]
            #Get the value of that attribute in the catchment dataframe
            currentPct = catchDF[nlcdAttrib].values[0]
            #Convert to sq km (multiply by area, computed above)
            currentArea = currentPct * baseArea / 100.0        
            #Calculate new area
            newArea = currentArea - changeArea
            #Calculate new percentage
            newPct = newArea / baseArea * 100.0
            #Update the data frame
            dataDF.loc[dataDF['GRIDCODE'] == gridcode, nlcdAttrib] = newPct

#Write out data
dataDF.to_csv(projectSWDFile,index_label="OID",index=False)