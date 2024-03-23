# -*- coding: utf-8 -*-
"""
------------------------------------------------------------------------------
Metashape Image Alignment and Error Reduction Script v1.20
for Agisoft Metashape 1.5

This script automates the Agisoft Metashape image alignment and error reduction
workflow based on techniques taught by Tom Noble (USDOI-BLM Ret.) of 
TN Photogrammetry LLC, and Neffra Matthews (USDOI-BLM). The error reduction 
technique and gradual selection values were developed with the goal to maintain
the accuracies of the traditional photogrammetric process with newer techniques
supported by structure from motion (SfM) based software. 

The script allows users to align imagery and apply different gradual selection
filters to sparse point clouds. Each filter is applied in an iterative fashion, 
such that only a fraction of the total sparse points are selected and deleted 
within an iteration.  A camera optimization is performed between each iteration
to improve the camera lens model using the newly filtered subset of higher 
quality sparse point matches.  These iterations continue until a user-defined
level is achieved.  

Default gradual selection levels are supplied, but can be changed by the user 
in the command line or in the defaults.object code block.  Your imagery may not
support the default levels, so exercise caution if accepting these defaults.

------------------------------------------------------------------------------
usage: 
Align_RuPaRe.py [-h] 
                    Display help message, list of args.
                [-chunk [str name of chunk]] 
                    Initial chunk to process. Optional. [Default=active chunk]
                [-align] 
                    Perform image alignment. 
                [-ru]
                    Perform reconstruction uncertainty (RU) gradual selection iterations. 
                        Optional RU sub-arguments:
                            [-ru_level [float]]
                                RU gradual selection filter level [Default=10]

                [-pa]
                    Perform projection accuracy (PA) gradual selection iterations. 
                        Optional PA sub-arguments:
                            [-pa_level [float]]
                                PA gradual selection filter level [Default=3]

                [-re]
                    Perform reprojection error (RE) gradual selection iterations. 
                        Optional RE sub-arguments:
                            [-re_level [float]]
                                RE gradual selection filter level [Default=0.3]

                [-log [str name optional, otherwise Metashape proj. name used]]
                    Create optional processing log file. [Default=no log file]
                        (if -log provided with no arg, log will be named using Metashape proj. name)
------------------------------------------------------------------------------
Script begins on chunk designated by optional '-chunk' argument.  If no chunk is 
designated, the currently active chunk is used. Initial chunk is copied to a new
chunk and given a suffix of '_Align', '_RUx', '_PAx', or '_REx' (where x is the 
gradual selection filter level). Each operation creates a new chunk.

defaults:
    -chunk     active chunk
    
    -align     keypointlimit=40000
               tiepointlimit=4000
               accuracy=high
               generic_preselection=True
               reference_preselection=False
               camera optimization lens param: f, cx, cy, k1, k2, k3, p1, p2
           
    -ru        Reconstruction Uncertainty level 10.0
               camera optimization lens param: f, cx, cy, k1, k2, k3, p1, p2
           
    -pa        Projection Accuracy level 3.0
               camera optimization lens param: f, cx, cy, k1, k2, k3, p1, p2
               
    -re        Reprojection Error level 0.3
               initial camera optimization lens param: f, cx, cy, k1, k2, k3, p1, p2
               camera optimization lens params adjusted when RE < 1 pixel
               adjusted camera optimization lens param: f, cx, cy, k1, k2, k3, k4, b1, b2, p1, p2, p3, p4
    
    -log       Output processing log file name: XXXXX_ProcessingLog.txt (XXXXX = Metashape project name)

@authors: 
This script was developed at the United States Geological Survey, 
Pacific Coastal and Marine Science Center, Santa Cruz, CA 
(https://walrus.wr.usgs.gov/).
        
    Joshua Logan (jlogan@usgs.gov)
    Andy Ritchie (aritchie@usgs.gov)
    
The error reduction workflow performed by this script was developed by
Tom Noble (USDOI-BLM Ret.) of TN Photogrammetry LLC, and Neffra Matthews (USDOI-BLM).  
For further information and professional training on this workflow and other 
photogrammetry topics, please contact:

    Tom Noble, TN Photogrammetry LLC, tnphotogrammetry@gmail.com
------------------------------------------------------------------------------
"""

import Metashape
import os
import re
from datetime import datetime
import argparse
import copy as cp
import math

    
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
