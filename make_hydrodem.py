'''
Code to replicate the hydroDEM_work_mod.aml and agree.aml scripts

Theodore Barnhart, tbarnhart@usgs.gov, 20190225

Reference: agree.aml
    
'''

import numpy as np
import arcpy
import sys
import os

arcpy.CheckOutExtension("Spatial")

def hydrodem(outdir, huc8cov, origdem, dendrite, snap_grid, bowl_polys, bowl_lines, inwall, drainplug, start_path, buffdist, inwallbuffdist, inwallht, outwallht, agreebuf, agreesmooth, agreesharp, bowldepth, copylayers, cellsz, bowling, in_wall, drain_plugs):
    '''Hydro-enforce a DEM

    Parameters
    ----------
    outdir : DEWorkspace
        Working directory
    huc8cov : DEFeatureClass
        Local division feature class, often HUC8
    origdem
    dendrite
    snap_grid
    bowl_polys
    bowl_lines
    inwall
    drainplug
    start_path
    buffdist
    inwallbuffdist
    inwallht
    outwallht
    agreebuf
    agreesmooth
    agreesharp
    bowldepth
    copylayers
    cellsz
    bowling
    in_wall
    drain_plugs

    Returns
    -------
    '''

    arcpy.AddMessage("HydroDEM is running")

    # set working directory and environment
    arcpy.env.Workspace = outdir
    arcpy.env.cellSize = cellsz

    # buffer the huc8cov
    hucbuff = ' some temp location'
    arcpy.AddMessage('Buffering Local Divisons')
    arcpy.Buffer_analysis(huc8cov,hucbuff) # do we need to buffer if this is done in the setup tool, maybe just pass hucbuff to the next step from the parameters...

    arcpy.env.Extent = hucbuff # set the extent to the buffered HUC

    # rasterize the buffered local division
    arcpy.AddMessage('Rasterizing %s'%hucbuff)
    outGrid = 'some temp location'
    # may need to add a field to hucbuff to rasterize it... 
    arcpy.FeaturetoRaster_conversion(hucbuff,None,outGrid,cellsz)

    arcpy.env.Mask = outGrid # set mask (L169 in hydroDEM_work_mod.aml)

    elevgrid = agree(origdem,dendrite,agreebuf, agreesmooth, agreesharp) # run agree function

    # rasterize the dendrite
    arcpy.AddMessage('Rasterizing %s'%dendrite)
    dendriteGrid = 'some temp location'
    # may need to add a field to dendrite to rasterize it...
    arcpy.FeaturetoRaster_conversion(dendrite,None,dendriteGrid,cellsz)

    # burning streams and adding walls
    arcpy.AddMessage('Starting Walling') # (L182 in hydroDEM_work_mod.aml)

    ridgeNL = 'some temp location'
    # may need to add a field to huc8cov to rasterize it...
    arcpy.FeaturetoRaster_conversion(huc8cov,None,ridgeNL,cellsz) # rasterize the local divisions feature
    ridgeEXP = 'some temp location'
    outRidgeEXP = arcpy.Expand(ridgeNL,2,[1]) # the last parameter is the zone to be expanded, this might need to be added to the dummy field above... 
    outRidgeEXP.save(ridgeEXP) # save temperary file, maybe not needed

    arcpy.gp.SingleOutputMapAlgebra_sa()


def fill(dem_enforced, filldem, sink, zlimit, fdirg):
    ''' fill function from fill.aml
    Purpose
    -------
        This AML command fills sinks or peaks in a specified surface
        grid and outputs a filled surface grid and, optionally, its
        flow direction grid.  If output filled grid already exists,
        it will be removed first

    Authors
    -------
        Gao, Peng        Dec 20, 1991  Original coding
        Laguna, Juan     Nov  1, 2000  Fix to prevent failure on large FP grids
        Ajit M. George   Jul 31, 2001  Use force option for iterative flowdirection.
                                      calculation, and normal option for direction output.
        Theodore Barnhart, tbarnhart@usgs.gov, 20190225, recoded to arcpy/python
        
    Parameters
    ----------
    dem_enforced
    filldem
    sink
    zlimit
    fdirg

    Returns
    -------
    filldem?
    '''

    return filldem


def agree(origdem,dendrite,agreebuf, agreesmooth, agreesharp):
    '''Agree function from AGREE.aml

    Original function by Ferdi Hellweger, http://www.ce.utexas.edu/prof/maidment/gishydro/ferdi/research/agree/agree.html

    recoded by Theodore Barnhart, tbarnhart@usgs.gov, 20190225

    -------------
    --- AGREE ---
    -------------
    
    --- Creation Information ---
    
    Name: agree.aml
    Version: 1.1
    Date: 10/13/96
    Author: Ferdi Hellweger
            Center for Research in Water Resources
            The University of Texas at Austin
            ferdi@crwr.utexas.edu
    
    --- Purpose/Description ---
    
    AGREE is a surface reconditioning system for Digital Elevation Models (DEMs).
    The system adjusts the surface elevation of the DEM to be consistent with a
    vector coverage.  The vecor coverage can be a stream or ridge line coverage. 

    Parameters
    ----------
    origdem : arcpy.sa Raster
        Original DEM with the desired cell size, oelevgrid in original script
    dendrite : Feature Class
        Dendrite feature layer to adjust the DEM, vectcov in the original script
    agreebuf : float 
        Buffer smoothing distance (same units as the horizontal), buffer in original script
    agreesmooth : float
        Smoothing distance (same units as the vertical), smoothdist in the original script
    agreesharp : float
        Distance for sharp feature (same units as the vertical), sharpdist in the original script

    Returns
    -------
    elevgrid : arcpy.sa Raster
        conditioned elevation grid returned as a arcpy.sa Raster object
    '''
    from arcpy.sa import *

    arcpy.AddMessage('Starting AGREE')

    # code to check that all inputs exist

    cellsize = (float(arcpy.GetRasterProperties_management(origdem, "CELLSIZEX")) + float(arcpy.GetRasterProperties_management(origdem, "CELLSIZEY")))/2. # compute the raster cell size

    arcpy.AddMessage('Setting Environment Variables')
    arcpy.env.Extent = origdem # (L130 AGREE.aml)
    arcpy.env.cellSize = cellSize # (L131 AGREE.aml)

    arcpy.AddMessage('Rasterizing the Dendrite.')
    dendriteGridPth = 'some temp location' # might need to add a field for rasterization
    arcpy.FeaturetoRaster_conversion(dendrite,dendriteGridPth)

    arcpy.AddMessage('Computing smooth drop/raise grid...')
    # expression = 'int ( setnull ( isnull ( vectgrid ), ( \"origdem\" + \"greesmooth\" ) ) )'

    dendriteGrid = Raster(dendriteGridPth)
    origdem = Raster(origdem)
    
    smogrid = Int(SetNull(IsNull(dendriteGrid, origdem + agreesmooth))) # compute the smooth drop/raise grid (L154 in AGREE.aml)

    arcpy.AddMessage('Computing vector distance grids...')
    vectdist = EucDistance(smogrid)
    # Need to produce vectallo (stores the elevation of the closest vector cell), is this the same as the smogrid?
    vectallo = EucAllocation(smogrid) # Roland Viger thinks the original vectallo is an allocation grid, that can be made with EucAllocation.

    arcpy.AddMessage('Computing buffer grids...')
    bufgrid1 = Con((vectdist > (agreebuf - (cellsize / 2.))), 1, 0) 
    bufgrid2 = Int(SetNull(bufgrid1 == 0, oelevgrid)) # (L183 in AGREE.aml)

    arcpy.AddMessage('Computing buffer distance grids...')
    # compute euclidean distance and allocation grids
    bufdist = EucDistance(bufgrid2)
    bufallo = EucAllocation(bufgrid2)

    arcpy.AddMessage('Computing smooth modified elevation grid...')
    smoelev =  vectallo + ((bufallo - vectallo) / (bufdist + vectdist)) * vectdist

    arcpy.AddMessage('Computing sharp drop/raise grid...')
    #shagrid = int ( setnull ( isnull ( vectgrid ), ( smoelev + %sharpdist% ) ) )
    shagrid = Int(SetNull(IsNull(vectgrid), (smoelev + agreesharp)))

    arcpy.AddMessage('Computing modified elevation grid...')
    elevgrid = Con(IsNull(vectgrid), smoelev, shagrid)

    arcpy.AddMessage('AGREE Complete')
    
    return elevgrid 







    






