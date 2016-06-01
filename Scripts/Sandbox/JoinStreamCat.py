#JoinStreamCat.py
#
#Joins regional stream cat to the NHD Catchments Feature Class
#
# June 2016
# John.Fay@duke.edu

import sys, os, arcpy, csv
arcpy.env.overwriteOutput = True

#Get the catchment feature class
catchFC = r'C:\workspace\GeoWET\Data\ToolData\NC_Results.gdb\CatchmentAttributes2'

#Get the StreamCat data folder
streamCatFolder = r'C:\workspace\GeoWET\Data\StreamCat\Regional'

#Get header columns function
def getHeaders(fn):
    fileObj = open(fn,'rt')
    reader = csv.reader(fileObj)
    row = reader.next()
    fileObj.close()
    return row

#Create a list of columns already in the catchFC
flds = arcpy.ListFields(catchFC)
fldNames = []
for fld in flds:
    fldNames.append(fld.name)

#Loop through the regional folders
regions = ['03N']
for region in regions:
    print "Processing Region {}".format(region)
    #Get the region folder
    regionFldr = os.path.join(streamCatFolder,"Region{}".format(region))
    #List CSV files in the region folder
    files = os.listdir(regionFldr)
    for fileName in files:
        #Skip if not a data file
        if not "Region{}.csv".format(region) in fileName:
            print "...Skipping {}".format(fileName)
            continue
        #Process the CSV file
        print "...Processing {}".format(fileName)
        #get the full filename
        fullFN = os.path.join(regionFldr,fileName)
        #Get a list of attributes"
        attributesToJoin = getHeaders(fullFN)
        #Remove the COMID from the list
        if "COMID" in attributesToJoin: attributesToJoin.remove("COMID")
        #Remove fields already in the catchFC
        for attrib in attributesToJoin:
            if attrib in fldNames: attributesToJoin.remove(attrib)
        #See if any fields remain
        if len(attrib) == 0:
            print "...No attributes to join."
            continue
        #Join the fields to the catchment FC
        print "...Joining to catchment feature class"
        #Convert CSV to table
        print "......converting csv to ArcGIS table"
        joinTbl = arcpy.TableToTable_conversion(fullFN,"in_memory","tmp")
        print "......Joining fields"
        arcpy.JoinField_management(catchFC,"FEATUREID",joinTbl,"COMID",attributesToJoin)
        
        
    
    