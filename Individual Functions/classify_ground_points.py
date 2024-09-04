import Metashape
import os 

def activate_chunk(doc, chunk_name):
    """
    Activate chunk based on name
        args:
            doc = current Metashape.app.doc
            chunk_name = str name
        returns:
            chunk = activated chunk
    """
    # Get list of chunk labels
    chunk_label_list = [chunk.label for chunk in doc.chunks]
    # find all indices of chunks labeled chunk_name in document
    chunk_idx = [idx for idx, label in enumerate(chunk_label_list) if label == chunk_name]
    if len(chunk_idx) == 0:
        # no chunks with that label
        # print exception so it will be visible in console
        print('Exception: No chunk named ' + '"' + chunk_name + '"' + ' in project, stopping execution.')
        #raise Exception('No chunk named ' + '"' + chunk_name + '"' + ' in project.')
        return None
    if len(chunk_idx) > 1:
        # more than one chunk with that label
        # print exception so it will be visible in console
        print('Exception: More than one chunk named ' + '"' + chunk_name + '"' + ' in project, stopping execution.')
        raise Exception('More than one chunk named ' + '"' + chunk_name + '"' + ' in project.')
    # if only one chunk with that name, then activate chunk
    doc.chunk = doc.chunks[chunk_idx[0]]
    chunk = doc.chunk
    return chunk

def classify_ground_points(chunk, params):
    # Set classification parameters
    max_angle = params.get('max_angle', 15)
    max_distance = params.get('max_distance', 1.0)
    max_terrain_slope = params.get('max_terrain_slope', 5)
    cell_size = params.get('cell_size', 10)
    erosion_radius = params.get('erosion_radius', 5)
    
    # Perform ground point classification
    chunk.point_cloud.classifyGroundPoints(max_angle=max_angle, 
                                           max_distance=max_distance,
                                           max_terrain_slope=max_terrain_slope,
                                           cell_size=cell_size, 
                                           erosion_radius=erosion_radius)

def duplicate_chunk(doc, chunk_index, params):
    chunk = doc.chunks[chunk_index]

    # Duplicate the chunk
    new_chunk = chunk.copy()

    # Create a name for the chunk based on the parameters
    chunk_name = (
        f"Chunk_{chunk_index}_Angle_{params['max_angle']}_Dist_{params['max_distance']}_"
        f"Slope_{params['max_terrain_slope']}_Cell_{params['cell_size']}_"
        f"Ero_{params['erosion_radius']}"
    )
    new_chunk.label = chunk_name

    return new_chunk
def buildDEMOrtho(input_chunk, doc, ortho_res = None, dem_res = None, interpolation = False, buildOrtho = True):
    # Ensure Metashape is running and a document is open
    # print("Building DEM and Orthomosaic for " + input_chunk)
    activate_chunk(doc, input_chunk)  # Assuming doc is defined globally or passed to the function.
    chunk = doc.chunk
    
    projection = Metashape.OrthoProjection()
    projection.crs = chunk.crs  # Set the CoordinateSystem
    projection.type = Metashape.OrthoProjection.Type.Planar  # Set the projection type
    print(f"chunk.crs type: {type(chunk.crs)}, value: {chunk.crs}")
    
    if dem_res is None and interpolation is False:
        chunk.buildDem(
                source_data=Metashape.DataSource.PointCloudData, 
                interpolation=Metashape.DisabledInterpolation,
                projection=projection  # Use the OrthoProjection
            )
    elif dem_res is not None and interpolation is False:
        chunk.buildDem(
                source_data=Metashape.DataSource.PointCloudData, 
                interpolation=Metashape.DisabledInterpolation,
                projection=projection,  # Use the OrthoProjection
                resolution=dem_res
            )
    else:
        chunk.buildDem(
                source_data=Metashape.DataSource.PointCloudData, 
                interpolation=Metashape.EnabledInterpolation,
                projection=projection,  # Use the OrthoProjection
            )
    print("DEM built successfully!")

    # 2. Building Orthomosaic with default settings
    if ortho_res is None:
        chunk.buildOrthomosaic(
            surface_data=Metashape.DataSource.ElevationData,
            blending_mode=Metashape.MosaicBlending,
            fill_holes= True,
            ghosting_filter=False,
            cull_faces=False,
            refine_seamlines=False,
            projection=projection  # Use the OrthoProjection
        )
    elif buildOrtho:
        chunk.buildOrthomosaic(
            surface_data=Metashape.DataSource.ElevationData,
            blending_mode=Metashape.MosaicBlending,
            fill_holes=True,
            ghosting_filter=False,
            cull_faces=False,
            refine_seamlines=False,
            projection=projection,  # Use the OrthoProjection
            resolution=ortho_res
        )
        print("Orthomosaic built successfully!")
    doc.save()

def exportDEMOrtho(input_chunk, path_to_save_dem=None, path_to_save_ortho = None, geoidPath = None, ortho_res = None, dem_res = None):
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
        geoidPath  = r"Z:\JTM\Metashape\us_noaa_g2018u0.tif"
    print('Setting Geoid path:' + geoidPath)
    Metashape.CoordinateSystem.addGeoid(geoidPath)
    #EPSG for NAD83(2011) / UTM zone 13N = 6342
    new_crs = Metashape.CoordinateSystem("EPSG::6342")
    #chunk.updateTransform()
    #chunk.crs = new_crs
    if ortho_res is None:
        ortho_res = 0
    if dem_res is None:
        dem_res = 0
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
                        projection=output_projection,
                        resolution = dem_res)  # Using the custom CRS
        print("DEM Exported Successfully!")
    
    if path_to_save_ortho is not None:
        # Exporting the Orthomosaic with specified projection
        compression = Metashape.ImageCompression()
        compression.tiff_big = True
        chunk.exportRaster(path=path_to_save_ortho,
                        source_data=Metashape.DataSource.OrthomosaicData,
                        projection=output_projection,
                        image_compression = compression,
                        resolution = ortho_res)  # Using the custom CRS
        print("Orthomosaic Exported Successfully!")
    

    doc.save()
    return output_projection.crs, chunk.crs

def main():
    # Specify the Metashape project file path
    project_path = r"Y:\ATD\GIS\Veg Classification MS vs RF\UE_062023-062022_clip.psx"

    # Specify the output log file path by changing project path ext to .txt
    log_file_path = os.path.splitext(project_path)[0] + ".txt"
    export_dir = os.path.join(os.path.dirname(project_path), "MS Exports")
    # Load the project
    doc = Metashape.app.document
    doc.save()
    doc.open(project_path)

    # Select the original chunk to work on
    original_chunk_list = [0,1]  # Change this index if you have multiple chunks
    for original_chunk_index in original_chunk_list:
        chunk = doc.chunks[original_chunk_index]
        print(f"Compacting points in {chunk.label}")
        chunk.point_cloud.compactPoints()
        buildDEMOrtho(chunk.label, doc, buildOrtho = True)
        exportDEMOrtho(chunk.label, path_to_save_dem=os.path.join(export_dir, f"DEM_{original_chunk_index}_{chunk.label}.tif"), 
                       path_to_save_ortho = os.path.join(export_dir, f"Ortho_{original_chunk_index}_{chunk.label}.tif"))
    for original_chunk_index in original_chunk_list:
        # Define parameter ranges
        max_angle_range = [15, 35]
        max_distance_range = [1]
        max_terrain_slope_range = [10, 40]
        cell_size_range = [1]
        erosion_radius_range = [2]
        
        # Iterate over parameter combinations
        for max_angle in max_angle_range:
            for max_distance in max_distance_range:
                for max_terrain_slope in max_terrain_slope_range:
                    for cell_size in cell_size_range:
                        for erosion_radius in erosion_radius_range:
                            params = {
                                'max_angle': max_angle,
                                'max_distance': max_distance,
                                'max_terrain_slope': max_terrain_slope,
                                'cell_size': cell_size,
                                'erosion_radius': erosion_radius
                            }

                            # Duplicate the original chunk and classify ground points
                            #check if chunk already exists
                            chunk_exists = False
                            chunk_label = f"Chunk_{original_chunk_index}_Angle_{params['max_angle']}_Dist_{params['max_distance']}_Slope_{params['max_terrain_slope']}_Cell_{params['cell_size']}_Ero_{params['erosion_radius']}"
                            for chunk in doc.chunks:
                                if chunk.label == chunk_label:
                                    chunk_exists = True
                            if chunk_exists == False:
                                new_chunk = duplicate_chunk(doc, original_chunk_index, params)
                                classify_ground_points(new_chunk, params)
                            else:
                                new_chunk = activate_chunk(doc, chunk_label)
                            
                            new_chunk.point_cloud.removePoints([Metashape.PointClass.Unclassified])
                            new_chunk.point_cloud.compactPoints()
                            # Log the parameters used (optional)
                            with open(log_file_path, 'a') as log_file:
                                log_file.write(f"Classified in {new_chunk.label} with params: {params}\n")

                            export_dem_path = os.path.join(export_dir, f"DEM_{new_chunk.label}.tif")
                            buildDEMOrtho(new_chunk.label, doc, buildOrtho = False)
                            exportDEMOrtho(new_chunk.label, path_to_save_dem=export_dem_path)
                            # Save the project after classification
        doc.save()

if __name__ == "__main__":
    main()
