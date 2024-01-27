import Metashape
import os
import re
from datetime import datetime
import argparse
import copy as cp
#import MS_PSX_Setup.py
#import MS_Build_Products.py
from MS_PSX_Setup_integrated import setup_psx
from MS_WIngtra_Workflow import activate_chunk

def copy_chunks_for_cloud(post_error_chunk, doc):
    activate_chunk(doc, post_error_chunk)
    chunk = doc.chunk
    copied_list = []
    #Create copies of the chunk for each camera group (different flight dates separated for building dense cloiud and rasters)
    print("Camera groups: " + str(chunk.camera_groups))
    chunk_label_list = [chunk.label for chunk in doc.chunks]
    #check if any chunks already contain "_PostError" suffix 
    #and return the chunks that do

    
    post_error_chunks = [chunk for chunk in doc.chunks if chunk.label.endswith('_PostError') or chunk.label.endswith('_PostError_PCFiltered')]
    if len(post_error_chunks) > 0:
        print(f"The following PostError chunks already exist, skipping: {post_error_chunks}")
        return [chunk.label for chunk in post_error_chunks]
    
    for group in chunk.camera_groups:
        print("Copying chunk " + chunk.label + " for camera group " + group.label)
        #create a new chunk
        chunk = activate_chunk(doc, post_error_chunk)

        if activate_chunk(doc, group.label + '_PostError') is not None:
            print("Chunk " + group.label + "_PostError already exists, skipping")
            copied_list.append(chunk.label + '_PostError')
            break
        new_chunk = chunk.copy()
        #label the new chunk with the group name
        new_chunk.label = group.label + '_PostError'
        activate_chunk(doc, new_chunk.label)
        copied_list.append(new_chunk.label)
        #remove all other camera groups from the new chunk
        for camera_group in new_chunk.camera_groups:
            if camera_group.label != group.label:
                new_chunk.remove(camera_group)
    print("Copied chunks: " + str(copied_list))
    return copied_list

    
def buildDenseCloud(input_chunk, doc):
    print("Building Dense Cloud and Filtering Point Cloud for " + input_chunk)
    activate_chunk(doc, input_chunk)
    chunk = doc.chunk
    print("Chunk: " + chunk.label)
    try:
        print("Building Dense Cloud for " + input_chunk)
        #if len(chunk.dense_clouds) > 0:
         #   print("Dense Cloud already exists for " + input_chunk + "ccontinuing to filter point cloud")
          #  return
        chunk.buildDepthMaps(downscale = 2, filter_mode = Metashape.MildFiltering)
        chunk.buildPointCloud(point_confidence = True, point_colors = True)
        doc.save()
    except RuntimeError as e:
        print("Error building dense cloud for " + input_chunk)
        print(e)
        doc.save()
        return

def filter_point_cloud(input_chunk, maxconf, doc):
    
    chunk = activate_chunk(doc, input_chunk)
    chunk_label_list = [chunk.label for chunk in doc.chunks]
    #check if any chunks already contain "_PostError" suffix 
    #and return the chunks that do
    chunk = activate_chunk(doc, input_chunk)
    filtered_chunks = [chunk for chunk_label in chunk_label_list if chunk_label.endswith(str(chunk.label+'_PCFiltered'))]

    if len(filtered_chunks) > 0:
        print("Point clouid already filtered, skipping....")
        filt_chunk = input_chunk + '_PCFiltered'
        return filt_chunk
    print("Filtering Point Cloud for " + input_chunk)
    filter_chunk = chunk.copy()
    filter_chunk.label = chunk.label + '_PCFiltered'
    print('Copied chunk ' + chunk.label + ' to chunk ' + filter_chunk.label + ' for filtering ')
    filter_chunk.point_cloud.setConfidenceFilter(0, maxconf)  # configuring point cloud filter so that only point with low-confidence currently active
    all_points_classes = list(range(128))
    filter_chunk.point_cloud.removePoints(all_points_classes)  # removes all active points of the point cloud, i.e. removing all low-confidence points
    filter_chunk.point_cloud.resetFilters()  # resetting filter, so that all other points (i.e. high-confidence points) are now active
    return filter_chunk.label

def buildDEMOrtho(input_chunk, doc):
    # Ensure Metashape is running and a document is open
    print("Building DEM and Orthomosaic for " + input_chunk)
    activate_chunk(doc, input_chunk)  # Assuming doc is defined globally or passed to the function.
    chunk = doc.chunk
    
    projection = Metashape.OrthoProjection()
    projection.crs = chunk.crs  # Set the CoordinateSystem
    projection.type = Metashape.OrthoProjection.Type.Planar  # Set the projection type
    print(f"chunk.crs type: {type(chunk.crs)}, value: {chunk.crs}")
    
    # 1. Building DEM
    chunk.buildDem(
            source_data=Metashape.DataSource.PointCloudData, 
            interpolation=Metashape.EnabledInterpolation,
            projection=projection  # Use the OrthoProjection
            resolution = 0.04
        )
    print("DEM built successfully!")

    # 2. Building Orthomosaic with default settings
    chunk.buildOrthomosaic(
        surface_data=Metashape.DataSource.ElevationData,
        blending_mode=Metashape.MosaicBlending,
        fill_holes=True,
        ghosting_filter=False,
        cull_faces=False,
        refine_seamlines=False,
        projection=projection  # Use the OrthoProjection
        resolution = 0.02
    )
    print("Orthomosaic built successfully!")
        
    doc.save()

def getResolution(chunk, doc):
    activate_chunk(doc, chunk)
    dem = chunk.elevation
    resolution = dem.resolution
    return resolution

def exportDEMOrtho(input_chunk, path_to_save_dem=None, path_to_save_ortho = None, geoidPath = None):
    """
    Export the DEM and Orthomosaic from the provided chunk to specified file paths.

    Parameters:
        chunk (Metashape.Chunk): The chunk containing the DEM and orthomosaic to export.
        path_to_save_dem (str): The file path to save the DEM.
        path_to_save_ortho (str): The file path to save the orthomosaic.
    """
    
    # Ensure Metashape is running and a document is open
    doc = Metashape.app.document
  
    #EPSG:6342
    # Activate the provided chunk
    activate_chunk(doc, input_chunk)
    
    
    # Specifying the coordinate system using Proj4 string
    #NAD83(2011)/UTM zone 13N + GEOID18 = "+proj=utm +zone=13 +ellps=GRS80 +units=m"
    chunk = doc.chunk
    cwd = os.getcwd()
    if geoidPath is None:
        geoidPath  = cwd + r"\us_noaa_g2018u0.tif"
    print('Setting Geoid path:' + geoidPath)
    Metashape.CoordinateSystem.addGeoid(geoidPath)
    #EPSG for NAD83(2011) / UTM zone 13N = 6342
    new_crs = Metashape.CoordinateSystem("EPSG::6342")
    #chunk.updateTransform()
    #chunk.crs = new_crs
    
    # Create a new OrthoProjection object with the desired output CRS
    output_projection = Metashape.OrthoProjection()
    # Well Known Text for NAD83(2011) / UTM zone 13N + GEOID 18
    coordWKT = '''COMPD_CS["NAD83(2011) / UTM zone 13N + GEOID 18",
                    PROJCS["NAD83(2011) / UTM zone 13N",
                    GEOGCS["NAD83(2011)",
                    DATUM["NAD83 (National Spatial Reference System 2011)",
                    SPHEROID["GRS 1980",6378137,298.257222101,AUTHORITY["EPSG","7019"]],
                    TOWGS84[0,0,0,0,0,0,0],
                    AUTHORITY["EPSG","1116"]],
                    PRIMEM["Greenwich",0,AUTHORITY["EPSG","8901"]],
                    UNIT["degree",0.01745329251994328,AUTHORITY["EPSG","9102"]],
                    AUTHORITY["EPSG","6318"]],
                    PROJECTION["Transverse_Mercator",AUTHORITY["EPSG","9807"]],
                    PARAMETER["latitude_of_origin",0],
                    PARAMETER["central_meridian",-105],
                    PARAMETER["scale_factor",0.9996],
                    PARAMETER["false_easting",500000],
                    PARAMETER["false_northing",0],
                    UNIT["metre",1,AUTHORITY["EPSG","9001"]],
                    AUTHORITY["EPSG","6342"]],
                    VERT_CS["GEOID18",
                    VERT_DATUM["North American Vertical Datum 1988",2005,AUTHORITY["EPSG","5103"]],
                    UNIT["metre",1,AUTHORITY["EPSG","9001"]]]]'''

    output_projection.crs = Metashape.CoordinateSystem(coordWKT) # or your desired output CRS
    if path_to_save_dem is not None:
        # Exporting the DEM with specified projection
        
        chunk.exportRaster(path=path_to_save_dem,
                        source_data=Metashape.DataSource.ElevationData,
                        projection=output_projection)  # Using the custom CRS
        print("DEM Exported Successfully!")
    
    if path_to_save_ortho is not None:
        # Exporting the Orthomosaic with specified projection
        compression = Metashape.ImageCompression()
        compression.tiff_big = True
        chunk.exportRaster(path=path_to_save_ortho,
                        source_data=Metashape.DataSource.OrthomosaicData,
                        projection=output_projection,
                        image_compression = compression)
        print("Orthomosaic Exported Successfully!")
    

    doc.save()
    return output_projection.crs, chunk.crs

doc = Metashape.app.document
chunk = doc.chunk

buildDEMOrtho