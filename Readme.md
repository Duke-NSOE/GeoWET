# GeoWET
GEOspatial Wetland Evaluation Tool

This tool computes the uplift to aquatic habitat associated with conversion of land to wetland. Uplift is calculated as the increase in estimated habitat likelihood of key indicator species under the modified conditions relative to likelihoods modeled under existing conditions. 

## Required data
### Known species occurrence data
Mark Endries (USFWS) has compiled a list of 226 aquatic speices tagged with the NHD+ flowline segments in which they occur ([link](https://www.fws.gov/asheville/htmls/maxent/maxent.html)). These species locations data are used to train the initial habitat likelihood models. 
### Selection of key indicator species
The suite of key indicator species are ecoregion specific (Mid-Atlantic Coastal Plain, South Eastern Plains, Piedmont, Blue Ridge) and were identified by Bryn Tracy of the NC DEQ ([link](http://deq.nc.gov/about/divisions/water-resources/water-resources-data/water-sciences-home-page/biological-assessment-branch/fish-stream-assessment-program)). 
### Stream and catchment data
The National Hydrographic Dataset (version 2) and its associated [StreamCat](ftp://newftp.epa.gov/EPADataCommons/ORD/NHDPlusLandscapeAttributes/StreamCat/Documentation/ReadMe.html) data include ~260 stream and catchment attrubutes which provide the basis for modeling habtiat likelihood.
### Base data
NHD+ catchment features
NLCD Land Cover

## Data prep
### Species occurrence data
### Indicator species
### StreamCat data
* The StreamCat data area downloaded for the three hydrographic regions covering North Carolina (03N, 05, and 06). This is done using the STREAMCAT1_GetData.py script (Scripts/DataPrep folder), with files stored in the Data/StreamCat/Regional folder. A total of 29 CSV files are downloaded for each region. 
* The StreamCat CSV files for the three separate regions are then merged together so that each of the 29 files cover
