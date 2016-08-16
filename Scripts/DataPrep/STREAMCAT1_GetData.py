#GetStreamCatData.py
#
# Description: Downloads StreamCat data via FTP for processing with the GeoWET model
#
# Summer 2016
# John.Fay@duke.edu

import sys, os, ftplib

#Set variables
ftpURL="newftp.epa.gov"
ftpDir="/EPADataCommons/ORD/NHDPlusLandscapeAttributes/StreamCat/HydroRegions/"

#Regions to grab
regions = ["03N","05","06"]
     
##--FUNCTIONS--
def gettext(ftp, filename, outfile=None):
    # fetch a text file
    if outfile is None:
        outfileObj = sys.stdout
    else:
        outfileObj = open(outfile,'wt')
    # use a lambda to add newlines to the lines read from the server
    ftp.retrlines("RETR " + filename, lambda s, w=outfileObj.write: w(s+"\n"))
   
#Get paths; create folders if not present
scriptDir = os.path.dirname(sys.argv[0])
rootDir = os.path.dirname(os.path.dirname(scriptDir)) #up two folders
dataDir = os.path.join(rootDir,"Data")
streamCatDir = os.path.join(dataDir,"StreamCat")
if not os.path.exists(streamCatDir):
    print "Creating {}".format(streamCatDir)
    os.mkdir(streamCatDir)
regionDir = os.path.join(streamCatDir,"Regions")
if not os.path.exists(regionDir):
    print "Creating {}".format(regionDir)
    os.mkdir(regionDir)
for region in regions:
    theDir = os.path.join(regionDir,region)
    if not os.path.exists(theDir):
        print "Creating {}".format(theDir)
        os.mkdir(theDir)

##--PROCEDURE---
#Log into the site
ftp = ftplib.FTP(ftpURL)
ftp.login("anonymous","GetWetUser")

#Go to the current directory
ftp.cwd(ftpDir)

#Get a list of files
files = []
try:
    files = ftp.nlst()
except ftplib.error_perm, resp:
    if str(resp) == "550 No files found":
        print "No files in this directory"
    else:
        raise
    
#Loop through the files in the folder
for f in files:
    for region in regions:
        regionSearch = region + ".csv"
        if region in f:
            outFN = os.path.join(regionDir,region,f)
            if os.path.exists(outFN):
                print "{} exists; skipping".format(outFN)
            else:
                print "downloading {}".format(f)
                gettext(ftp,f,outFN)
            