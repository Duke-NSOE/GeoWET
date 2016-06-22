#Aquatic_utils.py
#
# A set of functions frequently used by AQUATIC scripts
#
# June 2016
# John.Fay@duke.edu

def msg(txt,severity=""):
    '''Provides messaging to interactive window or to ArcMap if run as script tool'''
    #Print the message to the interactive window
    print txt
    #Try to print to ArcMap. Will pass harmlessly as error if ArcPy is not loaded
    try:
        if severity=="warning":
            arcpy.AddWarning(txt)
        elif severity=="error":
            arcpy.AddError(txt)
        else:
            arcpy.AddMessage(txt)
    except:
        pass

def getSpeciesList(sppFile,ecoregion):
    '''Returns a list of species in the ecoregion'''
    ##TO ADD: Error if sppFile incorrect; Error if ecoregion not in list
    #Import pandas
    import pandas as pd
    
    #Read in the table as a data frame
    sppDF = pd.read_excel(sppFile,sheetname="IndicatorSppTable")

    #Create the dataframe used to grab species
    if ecoregion == "ALL":
        #If all ecoregions are specified, return all species
        outDF = sppDF.ScientificName
    else:
        #Otherwise return selected records
        outDF = sppDF.ScientificName[sppDF[ecoregion] == 1]
        print "{} species selected".format(len(outDF))

    #Generate multilist string from the selected species
    outStr = ""
    for spp in outDF.values:
        #Add the species to the list
        outStr += "{};".format(spp)
        #Strip off the last semi-colon
    outStr = outStr[:-1]
        
    return outStr

    