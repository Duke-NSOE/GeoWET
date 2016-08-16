DataPrep Contents

Scripts are listed in the order they should be run.

- STREAMCAT1_GetData.py
	Retrieves, via FTP, the stream cat data files for the 3 regions: 03N, 05, and 06. Files are places in the proper directory structure for subsequent data manipulations.
	
- STREAMCAT2_MergeCSVFiles.py
	Combines the regional StreamCat data files into single files to faciliate analysis.
	
- STREAMCAT3_GenerateAttributeList.py
	Creates a CSV file listing all the attributes included in the Stream Cat data alongside the file in which they occur. This is used in later scripts to extract specific attributes from the proper file. 
	
- ExtractSpeciesData.py	
	Extracts catchment data for HUC8s in which species occurs and merges the data with species presence absences records.