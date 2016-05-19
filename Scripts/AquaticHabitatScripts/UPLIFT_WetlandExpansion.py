# UPLIFT_WetlandExpansion.py
#
# Description: Creates a modified NLCD raster where all non-urban, non-water pixels
#  that coincide with hydric soils are reclassified as wetland.
#
# Requires an NLCD data layer and a connection to the ESRI Hydric Soils layer (which
#  in turn, requires an organizational account on ArcGIS Online.
#
# Fall, 2015
# John.Fay@duke.edu
#
# Import arcpy module
import sys, os, arcpy

# Input variables
responseVarsFC = arcpy.GetParameterAsText(0) # Response variables feature class
HUCFilter = arcpy.GetParameterAsText(1)      # HUC filter to select catchments to process
outRaster = arcpy.GetParameterAsText(2)      # Out raster of modified NLCD
outRespVarsFC = arcpy.GetParameterAsText(3)  # Out feature class of response vars (to modify)

#Set environments
arcpy.env.overwriteOutput = True

# Check out any necessary licenses
arcpy.CheckOutExtension("spatial")

# ---Functions---
def msg(txt,type="message"):
    print txt
    if type == "message":
        arcpy.AddMessage(txt)
    elif type == "warning":
        arcpy.AddWarning(txt)
    elif type == "error":
        arcpy.AddError(txt)
        
##--PROCESSES--
# Filter the catchment FC
msg("Extracting catchments within HUC {}".format(HUCFilter))
whereClause = "REACHCODE LIKE '{}%'".format(HUCFilter)
catchFC = arcpy.Select_analysis(responseVarsFC,outRespVarsFC,whereClause)

# Set the extent variable
inputExtent = arcpy.Describe(catchFC).extent
arcpy.env.extent = inputExtent

# Check the extent
extentSize = inputExtent.width * inputExtent.height / 900.0
extentLimit = 24000 * 24000
if extentSize > extentLimit:
    msg("Extent is too big!","warning")


# Get the service layers
scriptDir = os.path.dirname(sys.argv[0])
nlcdSvc = os.path.join(scriptDir,"LYRFiles","ESRI Landscape 5","USA_NLCD_2011.ImageServer")
hydricSvc = os.path.join(scriptDir,"LYRFiles","ESRI Landscape 4","USA_Soils_Hydric_Classification.ImageServer")

try:
    msg("Getting NLCD service layer")
    NLCDLyr = arcpy.MakeImageServerLayer_management(nlcdSvc,"NLCD_lyr",inputExtent)
    msg("Getting Hydric Soils service layer")
    hydricLyr = arcpy.MakeImageServerLayer_management(hydricSvc,"Soils_lyr",inputExtent)

except:
    msg("Could not make image service layer.","error")
    msg(arcpy.GetMessages())
    sys.exit(1)

# Set hydric soils to wetland, otherwise keep NLCD values
msg("...converting all areas with hydric soils as wetlands")
hydricNLCD = arcpy.sa.Con(hydricLyr,90,NLCDLyr,"Value in (2)")

# Createsa raster where urban areas are zero, otherwise hydric values
msg("...reverting wetlands on developed areas back to developed")
#Keep urban, set all other areas to hydric
hydricRaster = arcpy.sa.Con(NLCDLyr,NLCDLyr,hydricNLCD,"VALUE IN (21, 22, 23, 24)")

# Save the output
msg("...saving output")
hydricRaster.save(outRaster)