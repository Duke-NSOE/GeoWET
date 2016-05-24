#EPA_WebServices.py
#
# Intervace for retrieving data from EPA's Web Services: 
#  https://www.epa.gov/waterdata/watershed-characterization-service
#
# Tips for coding:
#  http://www.pythonforbeginners.com/python-on-the-web/how-to-access-various-web-services-in-python
#
# May 2016
# John.Fay@duke.edu

import sys, os, urllib2 , json, pprint

#User inputs
HUC8 = "03050102" #South Fork Catawba
COMID = "9745152"

#Construct the URL for the API
URL = "http://ofmpub.epa.gov/waters10/Watershed_Characterization.Control?" + \
      "pComID={}".format(COMID) + \
      "&optOutFormat=JSON" + \
      "&optOutPrettyPrint=0"

