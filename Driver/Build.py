

def copy_chunks_for_cloud(post_error_chunk, doc):
    activate_chunk(doc, post_error_chunk)
    chunk = doc.chunk
    #Re-enable all cameras in the chunk (e.g. select or "check" cameras in reference pane) 
    #This is in case some cameras were disabled before alignment 
    for camera in chunk.cameras:
        if camera.reference.location:
            camera.reference.location_enabled = True
        if camera.reference.rotation:
            camera.reference.rotation_enabled = True
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
        #Point Cloud Quality:Ultra = 1, High = 2, Medium = 4, Low = 8, Lowest = 16
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

def buildDEMOrtho(input_chunk, doc, ortho_res = None, dem_res = None, interpolation = False):
    # Ensure Metashape is running and a document is open
    print("Building DEM and Orthomosaic for " + input_chunk)
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
            fill_holes=False,
            ghosting_filter=False,
            cull_faces=False,
            refine_seamlines=False,
            projection=projection  # Use the OrthoProjection
        )
    else:
        chunk.buildOrthomosaic(
            surface_data=Metashape.DataSource.ElevationData,
            blending_mode=Metashape.MosaicBlending,
            fill_holes=False,
            ghosting_filter=False,
            cull_faces=False,
            refine_seamlines=False,
            projection=projection,  # Use the OrthoProjection
            resolution=ortho_res
        )
    print("Orthomosaic built successfully!")
    if parg.log:
        with open(parg.proclogname, 'a') as f:
            f.write("\n")
            f.write("DEM and Orthomosaic built for chunk " + chunk.label + ".\n")
            f.write("CRS: " + str(chunk.crs) + "\n")
            f.write("Projection type: " + str(projection.type) + "\n")  
            f.write("DEM Resolution: " + str(chunk.elevation.resolution) + "\n")
            f.write(f"Interpolation Enabled: {interpolation}\n")
            f.write("Orthomosaic Resolution: " + str(chunk.orthomosaic.resolution) + "\n")
            f.write("Orthomosaic Hole Filling Enabled: True\n")
        
        
        
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
        geoidPath  = cwd + r"\us_noaa_g2018u0.tif"
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

    
def main(parg, doc):
    """
    args:
          doc = active Metashape.app.document object
          parg = Arg object with formatted argument attributes
    """
    if len(parg.psx_dict) == 0:
        parg.psx_dict = {parg.user_tag: doc.path}
        print(len(parg.psx_dict))
        print(parg.psx_dict)
    for user_tag, psx_file in parg.psx_dict.items():
        # Open the project file
        processing_start = datetime.now()
        if parg.log:
            with open(parg.proclogname, 'a') as f:
                f.write("\n")
                f.write("============= PROCESSING START =============\n")
                f.write("Processing started at: " + str(processing_start) + "\n")
                f.write("Processing PSX: " + psx_file + "\n")
        try:
            doc.save()
            doc.open(psx_file)
        except:
            doc.open(psx_file)
        # Get the active chunk
        doc = Metashape.app.document
        if parg.setup==False and parg.align==False and parg.ru==False and parg.pa==False and parg.re==False and parg.pcbuild==False and parg.build==False:
            parg.setup = True
            parg.align = True
            parg.ru = True
            parg.pa = True
            parg.re = True
            parg.pcbuild = True
            parg.build = True
            parg.log = True
        # first verify that project has been saved/named, stop execution if not
        if not doc.path and parg.setup == False:
            # project has not been saved. stop execution and request that user save project
            # print exception before raising exception so it will be visible in console
            print('Exception: This project has not been saved/named. Please save it before running this '
                    'script. Stopping execution.')
            raise Exception('This project has not been saved/named. Please save it before running this '
                                                                'script. Stopping execution.')


        flight_folders = parg.flight_folders
        psx = doc.path
        psx_name = os.path.splitext(os.path.basename(psx))[0]
            
        # ====================MAIN CODE STARTS HERE====================
        if parg.setup:
            geo_ref_dict = {}
            print(f"Flight Folders: {flight_folders}")
            print(f"User Tags: {user_tag}")
            if parg.log:
                print('Logging to file ' + parg.proclogname)
                with open(parg.proclogname, 'a') as f:
                    f.write("============= SETUP =============\n")
                    f.write("PSX: " + psx + "\n")
                    f.write("Flight Folders: " + str(flight_folders) + "\n")
                    f.write("User Tags: " + str(user_tag) + "\n")
                    

            geo_ref_list, chunk = setup_psx(user_tag,flight_folders, doc)
            geo_ref_dict[psx] = geo_ref_list
        else:
            geo_ref_dict = {}
            geo_ref_list, chunk = setup_psx(user_tag, flight_folders, doc, load_photos = False)
            geo_ref_dict[psx] = geo_ref_list
            
        doc.save(psx)
        # ALIGN IMAGES
        if parg.align:
            align_start = datetime.now()
            #Aactivate last chunk in the list
            chunk_label_list = [chunk.label for chunk in doc.chunks]
            #chunk = activate_chunk(doc, chunk_label_list[-1])
            chunk = activate_chunk(doc, 'Raw_Photos')
            # copy active chunk, rename, make active
            align_chunk = chunk.copy()
            align_chunk.label = chunk.label + '_Align'
            print('Copied chunk ' + chunk.label + ' to chunk ' + align_chunk.label)

            geo_ref_list = geo_ref_dict[psx] 

            align_images(align_chunk, parg.alignment_params)

            if parg.log:    
                with open(parg.proclogname, 'a') as f:
                    f.write("\n")
                    f.write("============= ALIGNMENT =============\n")
                    f.write("Copied chunk " + chunk.label + " to chunk " + align_chunk.label + "\n")
                    f.write("Geo Ref List: " + str(geo_ref_list) + "\n")
                    align_params = parg.alignment_params
                    for key in align_params:
                        f.write(f"    -{key}: {align_params[key]}\n")
                    f.write(f"Alignment processing time: {datetime.now() - align_start}\n")
            print(f"Geo Ref List: {geo_ref_list}")
            #for geo_ref in geo_ref_list:    
                #chunk.importReference(os.path.join(geo_ref), delimiter = ',', columns = 'nxyzabcXZ')
            doc.save()

        # RECONSTRUCTION UNCERTAINTY
        if parg.ru:
            chunk_label_list = [chunk.label for chunk in doc.chunks]
            #chunk = activate_chunk(doc, chunk_label_list[-1])
            chunk = activate_chunk(doc, 'Raw_Photos_Align')
            # check that chunk has a point cloud
            try:
                len(chunk.tie_points.points)
            except AttributeError:
                # print exception so it will be visible in console
                print('AttributeError: Chunk "' + chunk.label + '" has no point cloud. Ensure that image '
                                                                'alignment was performed. Stopping execution.')
                raise AttributeError('Chunk "' + chunk.label + '" has no point cloud. Ensure that image alignment '
                                                            'was performed. Stopping execution.')

            # copy active chunk, rename, make active
            ru_chunk = chunk.copy()
            ru_chunk.label = chunk.label + '_RU' + str(parg.ru_filt_level)
            print('Copied chunk ' + chunk.label + ' to chunk ' + ru_chunk.label)
            doc.save()

            # Run Reconstruction Uncertainty using reconstruction_uncertainty function
            print('Running Reconstruction Uncertainty optimization')
            if parg.log:
                # if logging enabled use kwargs
                print('Logging to file ' + parg.proclogname)
                # write input and output chunk to log file
                with open(parg.proclogname, 'a') as f:
                    f.write("\n")
                    f.write("============= RECONSTRUCTION UNCERTAINTY =============\n")
                    f.write("Copied chunk " + chunk.label + " to chunk " + ru_chunk.label + "\n")
                # execute function
                reconstruction_uncertainty(ru_chunk, parg.ru_filt_level, parg.ru_cutoff, parg.ru_increment, parg.cam_opt_param, 
                                        log=True, proclog=parg.proclogname)
            else:
                reconstruction_uncertainty(ru_chunk, parg.ru_filt_level, parg.ru_cutoff, parg.ru_increment, parg.cam_opt_param)
            doc.save()

        # PROJECTION ACCURACY
        if parg.pa:
            chunk_label_list = [chunk.label for chunk in doc.chunks]
            #chunk = activate_chunk(doc, chunk_label_list[-1])
            chunk = activate_chunk(doc, "Raw_Photos_Align_RU10")
            # check that chunk has a point cloud
            try:
                len(chunk.tie_points.points)
            except AttributeError:
                # print exception so it will be visible in console
                print('AttributeError: Chunk "' + chunk.label + '" has no point cloud. Ensure that image '
                                                                'alignment was performed. Stopping execution.')
                raise AttributeError('Chunk "' + chunk.label + '" has no point cloud. Ensure that image alignment '
                                                            'was performed. Stopping execution.')

            # copy active chunk, rename, make active
            pa_chunk = chunk.copy()
            pa_chunk.label = chunk.label + '_PA' + str(parg.pa_filt_level)
            print('Copied chunk ' + chunk.label + ' to chunk ' + pa_chunk.label)


            # Run Projection Accuracy using projection_accuracy function
            print('Running Projection Accuracy optimization')
            if parg.log:
                # if logging enabled use kwargs
                print('Logging to file ' + parg.proclogname)
                # write input and output chunk to log file
                with open(parg.proclogname, 'a') as f:
                    f.write("\n============= PROJECTION ACCURACY=============\n")
                    f.write("Copied chunk " + chunk.label + " to chunk " + pa_chunk.label + "\n")
                # execute function
                projection_accuracy(pa_chunk, parg.pa_filt_level, parg.pa_cutoff, parg.pa_increment, parg.cam_opt_param, log=True,
                                    proclog=parg.proclogname)
            else:
                projection_accuracy(pa_chunk, parg.pa_filt_level, parg.pa_cutoff, parg.pa_increment, parg.cam_opt_param)
            doc.save()

        # REPROJECTION ERROR
        if parg.re:
            chunk_label_list = [chunk.label for chunk in doc.chunks]
            #chunk = activate_chunk(doc, chunk_label_list[-1])
            chunk = activate_chunk(doc, f"Raw_Photos_Align_RU{parg.ru_filt_level}_PA{parg.pa_filt_level}")
            R1_opt = parg.re_round1_opt # number of optimizations for round 1
            R2_opt = parg.re_round2_opt # number of optimizations for round 2
            R2_TPA = parg.re_round2_TPA # TPA for round 2
            RMSE_goal = parg.re_RMSE_goal
            SEUW_dict = {}
            RMSE_dict = {}
            # check that chunk has a point cloud
            try:
                len(chunk.tie_points.points)
            except AttributeError:
                # print exception so it will be visible in console
                print('AttributeError: Chunk "' + chunk.label + '" has no point cloud. Ensure that image '
                                                                'alignment was performed. Stopping execution.')
                raise AttributeError('Chunk "' + chunk.label + '" has no point cloud. Ensure that image alignment '
                                                            'was performed. Stopping execution.')
            # copy active chunk, rename, make active
            label = chunk.label
            re_chunk = chunk.copy()
            re_chunk.label = f"{label}_RE{parg.re_filt_level}_TPA{R2_TPA}"
            print('Copied chunk ' + chunk.label + ' to chunk ' + re_chunk.label)

            # Run Reprojection Error using reprojection_error function
            print('Running Reprojection Error optimization')
            if parg.log:
                # if logging enabled use kwargs
                print('Logging to file ' + parg.proclogname)
                # write input and output chunk to log file
                with open(parg.proclogname, 'a') as f:
                    f.write("\n")
                    f.write("============= REPROJECTION ERROR =============\n")
                    f.write("Copied chunk " + chunk.label + " to chunk " + re_chunk.label + "\n")

                reprojection_error(re_chunk, parg.re_filt_level, parg.re_cutoff, parg.re_increment, parg.cam_opt_param, RMSE_goal, R1_opt, R2_opt, R2_TPA, log=True,
                                proclog=parg.proclogname)
            else:
                reprojection_error(re_chunk, parg.re_filt_level, parg.re_cutoff, parg.re_increment, parg.cam_opt_param, RMSE_goal, R1_opt, R2_opt, R2_TPA)
        
            doc.save()

        if parg.pcbuild:
            print("----------------------------------------------------------------------------------------")
            pcbuild_start = datetime.now()
            chunk = doc.chunk
            maxconf = parg.maxconf
            print("Building Point Clouds")
            chunk_label_list = [chunk.label for chunk in doc.chunks]
            post_error_chunk = f"Raw_Photos_Align_RU{parg.ru_filt_level}_PA{parg.pa_filt_level}_RE{parg.re_filt_level}_TPA{parg.re_round2_TPA}"
            pc_chunk = f"{post_error_chunk}_PCFiltered"
            post_error_chunk_list = [chunk for chunk in chunk_label_list if chunk.endswith(post_error_chunk)]
            print("Chunks to process: " + str(post_error_chunk_list))
            if len(post_error_chunk_list) == 0:
                post_error_chunk_list = [chunk.label]
            #Get the chunk names and create a counter for progress updates
            for current_chunk, i in zip(post_error_chunk_list, range(len(post_error_chunk_list))):
                print("Processing " + current_chunk)

            #------------Build Dense Cloud and Filter Point Cloud-----------------#
                try:
                    print("-------------------------------COPY CHUNKS FOR CLOUD---------------------------------------\n")
                    copied_list = copy_chunks_for_cloud(current_chunk, doc)
                    for copied_chunk in copied_list:
                        chunk = activate_chunk(doc, copied_chunk)
                        if len(chunk.depth_maps_sets) == 0: #Check that a point cloud doesnt already exist
                            print("-------------------------------BUILD DENSE CLOUD---------------------------------------\n")

                            cloud_start = datetime.now()
                            buildDenseCloud(copied_chunk, doc)
                            if parg.log:
                                with open(parg.proclogname, 'a') as f:
                                    f.write("\n==================POINT CLOUD=============================== \n")
                                    f.write("Built Dense Cloud and Filtered Point Cloud for chunk " + copied_chunk + ".\n")
                                    f.write("Point Cloud Quality: High \n")
                                    f.write("Point Cloud Filter: Mild \n")
                                    f.write("Fltered by Confidence Level: " + str(maxconf) + "\n")
                                    f.write("Processing time: " + str(datetime.now() - cloud_start) + "\n")
                        print("-------------------------------FILTER DENSE CLOUD---------------------------------------")
                        filtered_chunk = filter_point_cloud(copied_chunk, maxconf, doc)
                except Exception as e:
                    print("Error processing " + current_chunk)
                    print(e)
                    doc.save()
                    continue
            if parg.log:
                with open(parg.proclogname, 'a') as f:
                    f.write(f"\n{len(copied_list)} Point Clouds built and filtered in {datetime.now() - pcbuild_start}\n")

        if parg.build:    
            print("----------------------------------------------------------------------------------------")
            chunk = doc.chunk
            geoidPath = parg.geoid
            
            if parg.export_dir is not None:
                psx_folder = parg.export_dir
            else:
                #Get file name of .psx file without .psx extension
                psx_folder = os.path.join(os.path.dirname(psx), psx_name + " Exports")
            
            print("Processing " + psx_name) 
            print("Output folder: " + psx_folder)
            os.makedirs(os.path.dirname(psx_folder), exist_ok=True)
            
            chunk_label_list = [chunk.label for chunk in doc.chunks]
            pc_chunk_list = [chunk for chunk in chunk_label_list if chunk.endswith("_PCFiltered")]
            
            #Get the chunk names and create a counter for progress updates
            for current_chunk, i in zip(pc_chunk_list, range(len(pc_chunk_list))):
                print("Processing " + current_chunk + " in " + psx_name) 
                print("Chunk " + str(i+1) + " of " + str(len(pc_chunk_list)) + " in " + psx_name)
                #-------------Create File Paths-----------------#
                
                print("-------------------------------BUILD DEM/ORTHO---------------------------------------")
                print("")
                print(f"Building DEM and Orthomosaic for {current_chunk}")
                
                chunk = activate_chunk(doc, current_chunk)
                if chunk.elevation is None:    
                    buildDEMOrtho(current_chunk, doc, ortho_res = parg.ortho_resolution, dem_res = parg.dem_resolution)
                print("-------------------------------EXPORT DEM/ORTHO---------------------------------------")
                outputOrtho = os.path.join(psx_folder, os.path.basename(psx)[:-4] + "____" + current_chunk + "_Ortho.tif") #[:-4] removes .psx extension
                outputDEM = os.path.join(psx_folder, os.path.basename(psx)[:-4] + "____" + current_chunk + "_DEM.tif")
                if os.path.exists(outputDEM) or os.path.exists(outputOrtho):
                    print("File already exists, skipping " + outputDEM + " and " + outputOrtho + " of " + psx_name)
                    continue
                out_crs, in_crs = exportDEMOrtho(current_chunk, path_to_save_dem = outputDEM, path_to_save_ortho=outputOrtho, geoidPath=geoidPath, ortho_res = parg.ortho_resolution, dem_res = parg.dem_resolution)
                if parg.log:
                    # if logging enabled use kwargs
                    print('Logging to file ' + parg.proclogname)
                    # write input and output chunk to log file
                    with open(parg.proclogname, 'a') as f:
                        f.write("\n")
                        f.write("Exported DEM and Orthomosaic for chunk: " + current_chunk + ".\n")
                        f.write("Chunk Metadata: \n")
                        metadata = chunk.meta
                        for key, value in metadata.items():
                            f.write(f"{key}: {value}\n")
            doc.save()
            
            if parg.log:
                # if logging enabled use kwargs
                print('Logging to file ' + parg.proclogname)
                # write input and output chunk to log file
                with open(parg.proclogname, 'a') as f:
                    f.write("\n")
                    f.write('--------------------------------------------------\n')
                    f.write('PSX File: {}'.format(psx))
                    f.write('\nExported on: {}'.format(datetime.now()))
                    f.write('\nExported Chunks:'.format(pc_chunk_list))
                    f.write('\nExported to: {}'.format(psx_folder))

                    
                    #f.write('\nChunk CRS: {}'.format(in_crs))
                    #f.write('\nOutput CRS: {}'.format(out_crs))
        processing_end = datetime.now()
        if parg.log:
            with open(parg.proclogname, 'a') as f:
                f.write("\n")
                f.write("============= PROCESSING END =============\n")
                f.write("Processing ended at: " + str(processing_end) + "\n")
                f.write("Processing time: " + str(processing_end - processing_start) + "\n")
                f.write("============= END OF PROCESSING =============\n")

# execute main() if script call
if __name__ == '__main__':
    # reference active document
    doc_obj = Metashape.app.document
    # get command line arguments

    
    parg_obj = parse_command_line_args(parg, doc_obj)
    # run main
    main(parg_obj, doc_obj)
    
## use this block for debugging (comment main() above)    
#    # Get confirmation from user to continue
#    conf = True
#    msg = '\n\nDo you want to continue with the options printed above?'
#    conf = input("%s (y/N) " % msg).lower() == 'y'
##    conf = Metashape.app.getBool(label='Do you want to continue?')
#
#    if conf:
#        # run main
#        main(parg_obj, doc_obj)
#    else:
#        print('\nStopping execution.')
