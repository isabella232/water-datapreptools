import arcpy
import sys
import os
import re

def elevIndex(OutLoc, rcName, coordsysRaster, InputELEVDATAws, OutFC, version = None):
	"""
	Make a raster catalog and polygon index to NED tiles in a directory tree. 
	
	Usage: MakeNEDIndex_NHDPlusBuildRefreshTools <Output_Geodatabase> <Output_Raster_Catalog_Name> 
												 <Coordinate_System> <Input_NED_Workspace> <Output_Polygon_Feature_Class>
		   

	Description
	----------- 
  
	Makes a geodatabase raster catalog plus a polygon feature class containing the footprints of the 
	rasters in the raster catalog. All rasters to be loaded to the raster catalog should be on a common 
	projection and coordinate system. All rasters under the input workspace are loaded, so be sure only
	rasters of a particular type are included in the directory tree under that workspace. The primary 
	purpose of this tool is to create an index to National Elevation Dataset (NED) data, which meets the 
	above constraints. Use for other purposes has not been tested.

	Created on: Fri Nov 13 2009 04:25:02 PM
	  (generated by ArcGIS/ModelBuilder)
	Alan Rea, ahrea@usgs.gov, 20091113, original coding
	   updated  20091231, cleanup and commenting
	   updated  20100311, removed hard-coded toolbox reference
	Theodore Barnhart, tbarnhart@usgs.gov, 20190220, moved to code.usgs.gov for version control.
	  Updated for arcpy.
	"""
	if version:
		arcpy.AddMessage('StreamStats Data Preparation Tools version: %s'%(version))

	arcpy.env.overwriteOutput=True

	Output_Raster_Catalog = os.path.join(OutLoc,rcName) 
	Raster_Management_Type = "UNMANAGED"
	coordsysPolys = coordsysRaster     # Coordinate system for polygon footprints. Use same NED grid to specify. (type Spatial Reference)

	if arcpy.Exists(OutLoc): 
	  DSType = arcpy.Describe(arcpy.Describe(OutLoc).CatalogPath).WorkspaceType
	  arcpy.AddMessage("Dataset type =" + DSType)
	  if DSType == "FileSystem":
		arcpy.AddError("Output " + OutLoc + " is not a Geodatabase. Output location must be a Geodatabase.")
	else:
	  arcpy.AddError("Output " + OutLoc + "does not exist")
	
	# Now that we're sure the geodb exists, make it the active workspace
	arcpy.Workspace = OutLoc
	arcpy.ScratchWorkspace = OutLoc
	arcpy.AddMessage("Working geodatabase is " + OutLoc)

	OutFCpath = os.path.join(OutLoc,OutFC)
	if arcpy.Exists(OutFCpath): 
	  arcpy.AddError("Output feature class" + OutFCpath + "Already exists")
	  sys.exit(0) # end script

	if arcpy.Exists(Output_Raster_Catalog): 
	  arcpy.AddError("Output raster catalog" + Output_Raster_Catalog + "Already exists")
	  sys.exit(0) # end script

	# Process: Create Raster Catalog...
	arcpy.AddMessage("Creating output raster catalog " + Output_Raster_Catalog)
	arcpy.CreateRasterCatalog_management(OutLoc, rcName, coordsysRaster, coordsysPolys, "", "0", "0", "0", Raster_Management_Type, "")
	
	# Process: Workspace To Raster Catalog...
	arcpy.AddMessage("Loading all rasters under workspace " + InputELEVDATAws + " into raster catalog...")
	arcpy.WorkspaceToRasterCatalog_management(InputELEVDATAws, Output_Raster_Catalog, "INCLUDE_SUBDIRECTORIES", "NONE") 
	
	tabName = "tmp" # maybe strip off the .dbf since the table should be inside a geodatabase.
	tmpTablePath = os.path.join(OutLoc,tabName) # generate path to temp table

	if arcpy.Exists(tmpTablePath): # if the temp table exists, delete it.
	  arcpy.AddMessage("Temp table exits, deleting...")
	  arcpy.Delete_management(tmpTablePath)

	#arcpy.CreateTable_management(OutLoc,tabName) # create empty table
	# Process: Export Raster Catalog paths, then join paths to raster catalog
	arcpy.AddMessage("Getting full pathnames into raster catalog")
	#out_table = ScratchName("tmp","tbl","table") # create blank table
	arcpy.ExportRasterCatalogPaths_management(Output_Raster_Catalog, "ALL", tmpTablePath)
	arcpy.JoinField_management(Output_Raster_Catalog, "OBJECTID", tmpTablePath, "SourceOID", "Path")
	
	# Process: Use Copy Features to make a polygon feature class out of the raster catalog footprints 
	arcpy.AddMessage("Making polygon index of raster catalog...")
	arcpy.CopyFeatures_management(Output_Raster_Catalog, OutFCpath)
	
	# remove temporary table 
	arcpy.AddMessage("Removing temporary table ... ")
	arcpy.Delete_management(tmpTablePath)
   

	# handle errors and report using GPMsg function
	#except xmsg:
	#  arcpy.AddError(str(xmsg))
	#except arcgisscripting.ExecuteError:
	#  line, file, err = TraceInfo()
	#  arcpy.AddError("Geoprocessing error on %s of %s:" % (line,file))
	#  for imsg in range(0, arcpy.MessageCount):
	#    if arcpy.GetSeverity(imsg) == 2:     
	#      arcpy.AddError(imsg) # AddReturnMessage
	#except:  
	#  line, file, err = TraceInfo()
	#  arcpy.AddError("Python error on %s of %s" % (line,file))
	#  arcpy.AddError(err)
	#finally:
	  # Clean up here (delete cursors, temp files)
	#  arcpy.Delete_management(out_table)
	#  pass # you need *something* here 

def extractPoly(Input_Workspace, nedindx, clpfeat, OutGrd, version = None):
	"""
	This tool extracts a polygon area from NED tiles, and merges to a single grid.
	This tool requires as input a polygon feature class created from a raster catalog and containing the 
	full pathnames to each raster in the raster catalog (specifically NED, but probably other seamless tiled 
	rasters would work). This feature class can be created using the Make NED Index tool, also 
	bundled with this toolbox. The polygon attribute table must contain a field named "Path", containing
	full pathnames to all the NED tile grids. 
	
	Extract an area from NED tiles
	
	Usage: ExtractPolygonAreaFromNED_NHDPlusBuildRefreshTools <Output_Workspace> <NED_Index_Polygons> 
																 <Clip_Polygon> <Output_Grid>
	Alan Rea, ahrea@usgs.gov, 2009-12-31, original coding
	   """
	if version:
		arcpy.AddMessage('StreamStats Data Preparation Tools version: %s'%(version))

	arcpy.CheckOutExtension("Spatial") # checkout the spatial analyst extension

	# set working folder
	arcpy.env.workspace = Input_Workspace
	arcpy.env.scratchWorkspace = arcpy.env.workspace

	# select index tiles overlapping selected poly(s)
	intersectout = os.path.join(arcpy.env.workspace,"clipintersect.shp")
	if arcpy.Exists(intersectout):
	  arcpy.Delete_management(intersectout)
	
	arcpy.Clip_analysis(nedindx, clpfeat, intersectout) # clip the dataset

	MosaicList = []
	# Create search cursor 
	with arcpy.da.SearchCursor(intersectout,"Path") as cursor:
		ct = 0
		for row in cursor: # interate through each entry
			pth = row[0] # extract path

			if ct == 0:
				arcpy.AddMessage("Setting raster snap and coordinate system to match first input grid " + pth )
				try:
				  assert arcpy.Exists(pth) == True
				  arcpy.env.snapRaster = pth
				  arcpy.env.outputCoordinateSystem = pth
				except:
				  arcpy.AddError("First input grid does not exist: " + pth)
				  arcpy.AddMessage("Stopping... ")
				  sys.exit(0)

			arcpy.Extent = pth # set extent
	  		MosaicList.append(arcpy.sa.ExtractByMask(pth, clpfeat)) # extract the chunk of the DEM needed.
	  		ct += 1

	arcpy.Extent = clpfeat # reset extent to the whole layer
	
	arcpy.AddMessage("Merging grids to create " + OutGrd)
	arcpy.MosaicToNewRaster_management(MosaicList,arcpy.env.workspace,OutGrd,None,"32_BIT_SIGNED",None,1) # merge the grids together.

	if arcpy.Exists(intersectout):
		arcpy.Delete_management(intersectout)

def checkNoData(InGrid, tmpLoc, OutPolys_shp, version = None):
	"""
	Converted from model builder to arcpy, Theodore Barnhart, tbarnhart@usgs.gov, 20190222
	"""
	if version:
		arcpy.AddMessage('StreamStats Data Preparation Tools version: %s'%(version))

	arcpy.CheckOutExtension("Spatial") # checkout the spatial analyst extension

	from arcpy.sa import *

	arcpy.env.extent = InGrid
	arcpy.env.cellSize = InGrid

	InGrid = Raster(InGrid)

	tmpGrid = Con(IsNull(InGrid), 1)

	# Process: Raster to Polygon
	arcpy.RasterToPolygon_conversion(tmpGrid, os.path.join(tmpLoc,OutPolys_shp), "NO_SIMPLIFY", "Value", "SINGLE_OUTER_PART", "")

def fillNoData(workspace, InGrid, OutGrid, version = None):
	"""
	2D_Fill_NoData_Cells.py
	Created on: 2019-02-21 16:28:59.00000
	  (generated by ArcGIS/ModelBuilder)
	Usage: 2D_Fill_NoData_Cells <InGrid> <OutGrid> 
	Description: 
	Replaces NODATA values in a grid with mean values within 3x3 window. May be run repeatedly to fill in areas wider than 2 cells. Note the output is floating point, even if the input is integer. Note this will expand the data area of the grid around the outer edges of data, in addition to filling in NODATA gaps in the interior of the grid.
	
	Converted from model builder to arcpy, Theodore Barnhart, tbarnhart@usgs.gov, 20190222
	"""
	if version:
		arcpy.AddMessage('StreamStats Data Preparation Tools version: %s'%(version))

	arcpy.CheckOutExtension("Spatial") # checkout the spatial analyst extension

	from arcpy.sa import *

	OutGridPth = os.path.join(workspace, OutGrid)

	if arcpy.Exists(InGrid) == False:
		arcpy.AddError("Input grid does not exist.")
		sys.exit(0)

	if arcpy.Exists(OutGridPth):
		arcpy.AddError("Output grid exists.")
		sys.exit(0)

	arcpy.env.extent = InGrid
	arcpy.env.cellSize = InGrid
	
	InGrid = Raster(InGrid)
	
	tmpRast = Con(IsNull(InGrid), FocalStatistics(InGrid), InGrid)
	
	tmpRast.save(OutGridPth)

def projScale(Input_Workspace, InGrd, OutGrd, OutCoordsys, OutCellSize, RegistrationPoint, version = None):
	"""
	Projects a NED grid to a user-specified coordinate system, handling cell registration. Converts
	 output grid to centimeters (multiplies by 100 and rounds). 
	
	Usage: ProjectNED_NHDPlusBuildRefreshTools <Input_Workspace> <Input_Grid> <Output_Grid> 
												 <Output_Coordinate_System> <Output_Cell_Size> <Registration_Point>
	
	#
	Alan Rea, ahrea@usgs.gov, 20091216, original coding
	   ahrea, 20091231 updated comments
	Theodore Barnhart, tbarnhart@usgs.gov, 20190222
		  Converted original code to arcpy
	"""
	if version:
		arcpy.AddMessage('StreamStats Data Preparation Tools version: %s'%(version))

	arcpy.CheckOutExtension("Spatial")
	from arcpy.sa import *

	try: 
		# set working folder
		arcpy.env.workspace = Input_Workspace
		arcpy.env.scratchWorkspace = arcpy.env.workspace
		tmpDEM = os.path.join(arcpy.env.workspace, "tmpdemprj")
		OutGrd = os.path.join(arcpy.env.workspace, OutGrd)

		if arcpy.Exists(OutGrd):
			arcpy.Delete_management(OutGrd)

		# clear the processing extent
		arcpy.Extent = ""
		arcpy.OutputCoordinateSystem = ""
		arcpy.SnapRaster = ""
		arcpy.AddMessage("Projecting " + InGrd + " to create " + tmpDEM)
		arcpy.ProjectRaster_management(InGrd, tmpDEM, OutCoordsys, "BILINEAR", OutCellSize, None, RegistrationPoint)

		arcpy.Extent = tmpDEM
		arcpy.OutputCoordinateSystem = OutCoordsys
		arcpy.SnapRaster = tmpDEM
		arcpy.CellSize = tmpDEM

		tmpDEMRAST = Raster(tmpDEM) # load projected raster
		
		arcpy.AddMessage("Converting to integer centimeter elevations and producing final output grid " + OutGrd)

		tmp = Int((tmpDEMRAST * 100) +0.5) # convert from m to cm integers

		tmp.save(OutGrd) # save output grid

		arcpy.AddMessage("Removing temporary grid tmpdemprj... ")
		arcpy.Delete_management(tmpDEM)

		#If process completed successfully, open prj.adf file and assign z units
		if arcpy.Exists(OutGrd):
			o = open(os.path.join(OutGrd,"prj_new.adf"),"w")
			data = open(os.path.join(OutGrd,"prj.adf")).read()
			o.write(re.sub("Zunits        NO","Zunits        100",data))
			o.close()
			os.rename(os.path.join(OutGrd,"prj.adf"),os.path.join(OutGrd,"prj_backup.adf"))
			os.rename(os.path.join(OutGrd,"prj_new.adf"), os.path.join(OutGrd,"prj.adf"))
	except:
		raise