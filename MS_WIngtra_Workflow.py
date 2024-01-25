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
                        Optional alignment sub-arguments:                  
                            [-al_acc [highest, high, medium, low, lowest]]
                                Alignment accuracy. [Default=high]
                            [-al_kplim [float]] 
                                Alignment keypoint limit. [Default=100,000]
                            [-al_tplim [float]]
                                Alignment tiepoint limit. [Default=0]
                            [-al_generic [bool]]
                                Alignment generic preselection. [Default=True]
                            [-al_reference [bool]]
                                Alignment reference preselection. [Default=False]
                            [-al_cam_param [space delim list of str (ex: f cx cy k1 k2)] 
                                Camera optimization lens params. 
                                        [Default= f, cx, cy, k1, k2, k3, p1, p2]
                [-ru]
                    Perform reconstruction uncertainty (RU) gradual selection iterations. 
                        Optional RU sub-arguments:
                            [-ru_level [float]]
                                RU gradual selection filter level [Default=10]
                            [-ru_cam_param [space delim list of str (ex: f cx cy k1 k2)] 
                                Camera optimization lens params. 
                                        [Default= f, cx, cy, k1, k2, k3, p1, p2]
                [-pa]
                    Perform projection accuracy (PA) gradual selection iterations. 
                        Optional PA sub-arguments:
                            [-pa_level [float]]
                                PA gradual selection filter level [Default=3]
                            [-pa_cam_param [space delim list of str (ex: f cx cy k1 k2)] 
                                Camera optimization lens params. 
                                        [Default= f, cx, cy, k1, k2, k3, p1, p2]
                [-re]
                    Perform reprojection error (RE) gradual selection iterations. 
                        Optional RE sub-arguments:
                            [-re_level [float]]
                                RE gradual selection filter level [Default=0.3]
                            [-re_cam_param [space delim list of str (ex: f cx cy k1 k2)]
                                Camera optimization lens params. 
                                        [Default= f, cx, cy, k1, k2, k3, p1, p2]
                            [-re_adapt_cam [bool]
                                Adjust camera opt. lens params based on RE level [Default=True]
                            [-re_adapt_level [float]]
                                RE level at which to add additional lens params. [Default=1]
                            [-re_adapt_cam_param [space delim list of str (ex: f cx cy k1 k2)]
                                Additional lens params to add
                                        [Default= k4, b1, b2, p3, p4]
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
#import MS_PSX_Setup.py
#import MS_Build_Products.py
from MS_PSX_Setup_integrated import setup_psx

class Args():
    """ Simple class to hold arguments """
    pass

# ==================== DEFAULT ARGUMENTS BELOW===========================================
defaults = Args()
# ========These can be changed here, or changed at execution using command line arguments=====================

# ------------Chunk defaults -------------------------------------------------------
defaults.initial_chunk = 'active'    # Name of first chunk to operate on ('active' = active chunk)
defaults.input_dir = None        # path to input directory where all psx folders will be processed
defaults.user_tags = ['MM']             # list of user tags to process
defaults.flight_folders = [
    r"Z:\ATD\Drone Data Processing\Drone Images\East_Troublesome\Flights\102123",
    r"Z:\JTM\Wingtra\WingtraPilotProjects\070923 Trip",
    r"Z:\JTM\Wingtra\WingtraPilotProjects\053123 Trip",
    r"Z:\JTM\Wingtra\WingtraPilotProjects\100622 Trip"
                           ]         # list of photo folders to process
defaults.geoid = r"Z:\JTM\Metashape\us_noaa_g2018u0.tif"              # path to geoid file
# ------------Alignment defaults -------------------------------------------------------
defaults.setup = False              # run MS_PSX_Setup.py
defaults.build = False             # run MS_Build_Products.py
defaults.align = False              # run image alignment
defaults.align_accuracy = 'high'    # image alignment accuracy (must be: 'highest', 'high', 'medium', 'low', 'lowest'
defaults.keypointlimit = 40000     # alignment keypointlimit (0 = unlimited)
defaults.tiepointlimit = 4000         # alignment tiepointlimit (0 = unlimited)
defaults.gen_preselect = True       # alignment generic preselection
defaults.ref_preselect = False      # alignment reference preselection
# alignment camera optimization parameters
defaults.al_cam_opt_param = ['f','cx','cy','k1','k2','k3','p1','p2']

# ------------Reconstruction Uncertainty (ru) defaults ---------------------------------
defaults.ru = False                 # run ru gradual selection iterations
defaults.ru_filt_level = 10         # ru gradual selection filter level (default=10, optimum value: [10 - 15])
# ru camera optimization parameters
defaults.ru_cam_opt_param = ['f','cx','cy','k1','k2','k3','p1','p2']

# ------------Projection Accuracy (pa) defaults ---------------------------------------
defaults.pa = False                 # run pa gradual selection iterations
defaults.pa_filt_level = 2          # pa gradual selection filter level (default=3, optimum value: [2-4])
# pa camera optimization parameters
defaults.pa_cam_opt_param = ['f','cx','cy','k1','k2','k3','p1','p2']

# ------------Reprojection Error (re) defaults -----------------------------------------
defaults.re = False                 # run re gradual selection iterations
defaults.re_filt_level = 0.25        # re gradual selection filter level (default=0.3, optimum value: [0.3])
# re camera optimization parameters
defaults.re_cam_opt_param = ['f','cx','cy','k1','k2','k3','p1','p2']
# adjust camera optimization parameters when RE level is below threshold
defaults.re_adapt = True            # enable adaptive camera opt params (default=True)
defaults.re_adapt_level = 1         # RE level at which to adjust camera opt params (default=1)
# re adjust camera optimization parameters. These are enabled and added to initial re_cam_opt_param
defaults.re_adapt_add_cam_param = ['k4','b1','b2','p3','p4']

# ------------Process logging defaults ------------------------------------------------
defaults.log = True
# logfile name. Set to 'default.txt' to have output file named X_ProcessingLog.txt, where X=name of Metashape project
defaults.proclogname = 'default.txt'

# ------------ru, pa, re iteration defaults -------------------------------------------
# Only change these if you know what you're doing.-------------------------------------
defaults.ru_cutoff = 0.25           # percentage of points removed in single RU iteration [0.25]
defaults.pa_cutoff = 0.50           # percentage of points removed in single PA iteration [0.50]
defaults.re_cutoff = 0.10           # percentage of points removed in single RE iteration [0.10]
# Changing these values may result in infinite loops
defaults.ru_increment = 1           # increment by which RU filter advanced when finding RU level to select ru_cutoff percentage [1]
defaults.pa_increment = 0.5         # increment by which PA filter advanced when finding PA level to select pa_cutoff percentage [0.5]
defaults.re_increment = 0.01        # increment by which RE filter advanced when finding RE level to select re_cutoff percentage [0.01]

#-------------------Build Products defaults--------------------------------------------
defaults.maxconf = 2               # max confidence level for dense cloud filtering [2]

parg = cp.deepcopy(defaults)

# ==================== FUNCTIONS BELOW===========================================
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


def align_images(chunk):
    """
    Align images in the specified Metashape chunk.

    Parameters:
        chunk (Metashape.Chunk): The chunk containing the images to be aligned.
    """
    
    # Define alignment parameters
    alignment_params = {
        #Set Accuracy to high
        "downscale": "High",
        "generic_preselection": True,
        "reference_preselection": True,
        "reference_preselection_mode": Metashape.ReferencePreselectionSource,
        "filter_mask": False,
        "mask_tiepoints": True,
        "filter_stationary_points": True,
        "keypoint_limit": 40000,
        "keypoint_limit_per_mpx": 1000,
        "tiepoint_limit": 4000,
        "keep_keypoints": False,
        "guided_matching": False,
        "reset_matches": False,
        "subdivide_task": True,
        "workitem_size_cameras": 20,
        "workitem_size_pairs": 80,
        "max_workgroup_size": 100
    }
    
    # Perform image matching and alignment
    chunk.matchPhotos(**alignment_params)
    chunk.alignCameras()

    print(f"Images in chunk '{chunk.label}' have been aligned.")

def reconstruction_uncertainty(chunk, ru_filt_level_param, ru_cutoff, ru_increment, cam_opt_parameters, **kwargs):
    """
    Perform gradual selection on sparse cloud using Reconstruction Uncertainty ("RU") filter.
    Filter and remove only a percentage (ru_cutoff) of overall points in each iteration.
    After deleting perform camera optimization using parameters defined in cam_opt_parameters dictionary.
    Iterate until desired level of reconstruction uncertainty is attained.
        args:
              chunk = chunk on which to perform function
              ru_filt_level_param = desired level of reconstruction uncertainty
              ru_cutoff = max percentage (0-1) of points to be deleted in one iteration
              ru_increment = value to increment grad selection filter in while loop
              cam_opt_parameters = dictionary of camera optimization parameters
        kwargs:
              log = boolean
              proclog = str name of proclog
    """
    # initialize counter variables
    noptimized = 0
    ndeleted = 0
    ninc_reduced = 0

    # get start time for processing log
    starttime = datetime.now()
    # get initial point count
    points = chunk.tie_points.points
    init_pointcount = len([True for point in points if point.valid is True])

    while True:
        # define threshold variables
        points = chunk.tie_points.points
        f = Metashape.TiePoints.Filter()
        threshold_ru = ru_filt_level_param
        print("initializing with RU =", threshold_ru)
        # initialize filter for RU
        f.init(chunk, criterion=Metashape.TiePoints.Filter.ReconstructionUncertainty)
        f.selectPoints(threshold_ru)
        # calculate number of selected points
        nselected = len([True for point in points if point.valid is True and point.selected is True])
        print(nselected, " points selected")
        if nselected == 0:
            break
        npoints = len(points)
        while nselected * (1 / ru_cutoff) > npoints:
            print("RU threshold ", threshold_ru, "selected ", nselected, "/", npoints, "(",
                  round(nselected / npoints * 100, 4), " %) of  points. Adjusting")
            threshold_ru = threshold_ru + ru_increment
            f.selectPoints(threshold_ru)
            nselected = len([True for point in points if point.valid is True and point.selected is True])
            # if increment is too large, 0 points will be selected. Adjust increment value downward by 25%. Only do this 10 times before stopping.
            if nselected == 0:
                ru_increment = ru_increment * 0.25
                ninc_reduced = ninc_reduced + 1
                if ninc_reduced > 10:
                    print('RU filter increment reduction called ten times, stopping execution.')
                    raise ValueError('RU filter increment reduction called ten times, stopping execution.')
                else:
                    print("RU increment too large, reducing to " + str(ru_increment) + ".")

        print("RU threshold ", threshold_ru, " is ", round(nselected / npoints * 100, 4),
              "% of total points. Ready to delete")
        ndeleted = ndeleted + nselected
        chunk.tie_points.removeSelectedPoints()
        print("RU", threshold_ru, "deleted", nselected, "points")
        chunk.optimizeCameras(fit_f=cam_opt_parameters['cal_f'],
                              fit_cx=cam_opt_parameters['cal_cx'],
                              fit_cy=cam_opt_parameters['cal_cy'],
                              fit_b1=cam_opt_parameters['cal_b1'],
                              fit_b2=cam_opt_parameters['cal_b2'],
                              fit_k1=cam_opt_parameters['cal_k1'],
                              fit_k2=cam_opt_parameters['cal_k2'],
                              fit_k3=cam_opt_parameters['cal_k3'],
                              fit_k4=cam_opt_parameters['cal_k4'],
                              fit_p1=cam_opt_parameters['cal_p1'],
                              fit_p2=cam_opt_parameters['cal_p2'],
                              fit_p3=cam_opt_parameters['cal_p3'],
                              fit_p4=cam_opt_parameters['cal_p4'])
        noptimized = noptimized + 1
        print("completed optimization #", noptimized)
    else:
        print("If this shows up I don't understand while True loops")

    # get end time for processing log
    endtime = datetime.now()
    tdiff = endtime - starttime
    # get end point count
    end_pointcount = len([True for point in points if point.valid is True])

    # print status
    print('Reconstruction Uncertainty optimization completed.\n' +
          str(ndeleted) + ' of ' + str(init_pointcount) + ' removed in ' + str(
        noptimized) + ' optimizations on chunk "' + chunk.label + '".\n')

    # Check if logging option enabled
    if 'log' in kwargs:
        # check that filename defined
        if 'proclog' in kwargs:
            # write results to processing log
            with open(kwargs['proclog'], 'a') as f:
                f.write("\n")
                f.write("============= AUTO GENERATED PROCESSING LOG TEXT BELOW =============\n")
                f.write("Reconstruction Uncertainty optimization:\n")
                f.write("Chunk: " + chunk.label + "\n")
                f.write(str(ndeleted) + " of " + str(init_pointcount) + " removed in " + str(
                    noptimized) + " optimizations.\n")
                f.write("Final point count: " + str(end_pointcount) + "\n")
                f.write("Final Reconstruction Uncertainty: " + str(threshold_ru) + ".\n")
                f.write('Final camera lens calibration parameters: ' + ', '.join(
                    [k for k in cam_opt_parameters if cam_opt_parameters[k]]) + '\n')
                f.write("Start time: " + str(starttime) + "\n")
                f.write("End time: " + str(endtime) + "\n")
                f.write("Processing duration: " + str(tdiff) + "\n")
                f.write("\n")


def projection_accuracy(chunk, pa_filt_level_param, pa_cutoff, pa_increment, cam_opt_parameters, **kwargs):
    """
    Perform gradual selection on sparse cloud using Projection Accuracy ("PA") filter.
    Filter and remove only a percentage (pa_cutoff) of overall points in each iteration.
    After deleting perform camera optimization using parameters defined in cam_opt_parameters dictionary.
    Iterate until desired level of projection accuracy is attained.
        args:
              chunk = chunk on which to perform function
              pa_filt_level_param = desired level of projection accuracy
              pa_cutoff = max percentage (0-1) of points to be deleted in one iteration
              pa_increment = value to increment grad selection filter in while loop
              cam_opt_parameters = dictionary of camera optimization parameters
        kwargs:
              log = boolean
              proclog = str name of proclog
    """
    # initialize counter variables
    noptimized = 0
    ndeleted = 0
    ninc_reduced = 0

    # get start time for processing log
    starttime = datetime.now()
    # get initial point count
    points = chunk.tie_points.points
    init_pointcount = len([True for point in points if point.valid is True])

    while True:
        # define threshold variables
        points = chunk.tie_points.points
        f = Metashape.TiePoints.Filter()
        threshold_pa = pa_filt_level_param
        print("initializing with PA =", threshold_pa)
        # initialize filter for PA
        f.init(chunk, criterion=Metashape.TiePoints.Filter.ProjectionAccuracy)
        f.selectPoints(threshold_pa)
        # calculate number of selected points
        nselected = len([True for point in points if point.valid is True and point.selected is True])
        print(nselected, " points selected")
        if nselected == 0:
            break
        npoints = len(points)

        while nselected * (1 / pa_cutoff) > npoints:
            print("PA threshold ", threshold_pa, "selected ", nselected, "/", npoints, "(",
                  round(nselected / npoints * 100, 4), " %) of  points. Adjusting")
            threshold_pa = threshold_pa + pa_increment
            f.selectPoints(threshold_pa)
            nselected = len([True for point in points if point.valid is True and point.selected is True])
            # if increment is too large, 0 points will be selected. Adjust increment value downward by 25%. Only do this 10 times before stopping.
            if nselected == 0:
                pa_increment = pa_increment * 0.25
                ninc_reduced = ninc_reduced + 1
                if ninc_reduced > 10:
                    print('PA filter increment reduction called ten times, stopping execution.')
                    raise ValueError('PA filter increment reduction called ten times, stopping execution.')
                else:
                    print("PA increment too large, reducing to " + str(pa_increment) + ".")

        print("PA threshold ", threshold_pa, " is ", round(nselected / npoints * 100, 4),
              "% of total points. Ready to delete")
        ndeleted = ndeleted + nselected
        chunk.tie_points.removeSelectedPoints()
        print("PA", threshold_pa, "deleted", nselected, "points")
        chunk.optimizeCameras(fit_f=cam_opt_parameters['cal_f'],
                              fit_cx=cam_opt_parameters['cal_cx'],
                              fit_cy=cam_opt_parameters['cal_cy'],
                              fit_b1=cam_opt_parameters['cal_b1'],
                              fit_b2=cam_opt_parameters['cal_b2'],
                              fit_k1=cam_opt_parameters['cal_k1'],
                              fit_k2=cam_opt_parameters['cal_k2'],
                              fit_k3=cam_opt_parameters['cal_k3'],
                              fit_k4=cam_opt_parameters['cal_k4'],
                              fit_p1=cam_opt_parameters['cal_p1'],
                              fit_p2=cam_opt_parameters['cal_p2'],
                              fit_p3=cam_opt_parameters['cal_p3'],
                              fit_p4=cam_opt_parameters['cal_p4'])
        noptimized = noptimized + 1
        print("completed optimization #", noptimized)
    else:
        print("If this shows up I don't understand while True loops")

    # get end time for processing log
    endtime = datetime.now()
    tdiff = endtime - starttime
    # get end point count
    end_pointcount = len([True for point in points if point.valid is True])

    # print status
    print('Projection Accuracy optimization completed.\n' +
          str(ndeleted) + ' of ' + str(init_pointcount) + ' removed in ' + str(
        noptimized) + ' optimizations on chunk "' + chunk.label + '".\n')

    # Check if logging option enabled
    if 'log' in kwargs:
        # check that filename defined
        if 'proclog' in kwargs:
            # write results to processing log
            with open(kwargs['proclog'], 'a') as f:
                f.write("\n")
                f.write("============= AUTO GENERATED PROCESSING LOG TEXT BELOW =============\n")
                f.write("Projection Accuracy optimization:\n")
                f.write("Chunk: " + chunk.label + "\n")
                f.write(str(ndeleted) + " of " + str(init_pointcount) + " removed in " + str(
                    noptimized) + " optimizations.\n")
                f.write("Final point count: " + str(end_pointcount) + "\n")
                f.write("Final Projection Accuracy: " + str(threshold_pa) + ".\n")
                f.write('Final camera lens calibration parameters: ' + ', '.join(
                    [k for k in cam_opt_parameters if cam_opt_parameters[k]]) + '\n')
                f.write("Start time: " + str(starttime) + "\n")
                f.write("End time: " + str(endtime) + "\n")
                f.write("Processing duration: " + str(tdiff) + "\n")
                f.write("\n")


def reprojection_error(chunk, re_filt_level_param, re_cutoff, re_increment, cam_opt_parameters, **kwargs):
    """"
    Perform gradual selection on sparse cloud using Reprojection Error ("RE") filter.
    Filter and remove only a percentage (re_cutoff) of overall points in each iteration.
    After deleting perform camera optimization using parameters defined in cam_opt_parameters dictionary.
    Iterate until desired level of reprojection error is attained.
        args:
              chunk = chunk on which to perform function
              re_filt_level_param = desired level of projection accuracy
              re_cutoff = max percentage (0-1) of points to be deleted in one iteration
              re_increment = value to increment grad selection filter in while loop
              cam_opt_parameters = dictionary of camera optimization parameters
        kwargs:
              adapt_cam_opt = Enable additional camera opt. parameters if re_filt_level_param falls below threshold (boolean)
              adapt_cam_level = re_filt_level_param below which to enable additional camera opt. params (float)
              adapt_cam_param = dictionary of additional camera optimization parameters to enable
              log = boolean
              proclog = str name of proclog
    """
    # initialize counter variables
    noptimized = 0
    ndeleted = 0
    ninc_reduced = 0

    # get start time for processing log
    starttime = datetime.now()
    # get initial point count
    points = chunk.tie_points.points
    init_pointcount = len([True for point in points if point.valid is True])

    while True:
        # define threshold variables
        points = chunk.tie_points.points
        f = Metashape.TiePoints.Filter()
        threshold_re = re_filt_level_param
        print("initializing with RE =", threshold_re)
        # initialize filter for RE
        f.init(chunk, criterion=Metashape.TiePoints.Filter.ReprojectionError)
        f.selectPoints(threshold_re)
        # calculate number of selected points
        nselected = len([True for point in points if point.valid is True and point.selected is True])
        print(nselected, " points selected")
        if nselected < 50:
            break
        npoints = len(points)
        while nselected * (1 / re_cutoff) > npoints:
            print("RE threshold ", threshold_re, "selected ", nselected, "/", npoints, "(",
                  round(nselected / npoints * 100, 4), " %) of  points. Adjusting")
            threshold_re = threshold_re + re_increment
            f.selectPoints(threshold_re)
            nselected = len([True for point in points if point.valid is True and point.selected is True])
            # if increment is too large, 0 points will be selected. Adjust increment value downward by 25%. Only do this 10 times before stopping.
            if nselected == 0:
                re_increment = re_increment 
                ninc_reduced = ninc_reduced + 1
                if ninc_reduced > 15:
                    print('RE filter increment reduction called ten times, stopping execution.')
                    break
                else:
                    print("RE increment too large, reducing to " + str(re_increment) + ".")

        print("RE threshold ", threshold_re, " is ", round(nselected / npoints * 100, 4),
              "% of total points. Ready to delete")
        ndeleted = ndeleted + nselected
        chunk.tie_points.removeSelectedPoints()
        print("RE", threshold_re, "deleted", nselected, "points")
        
        # check if adaptive camera optimization parameters called
        if 'adapt_cam_opt' in kwargs:
            # if true
            if kwargs['adapt_cam_opt']:
                # check if other required kwargs present
                if 'adapt_cam_level' not in kwargs or 'adapt_cam_param' not in kwargs:
                # print exception so it will be visible in console, then raise exception
                    print('ArgumentError: '"'adapt_cam_opt'"' keyword called, but '"'adapt_cam_level'"' and '"'adapt_cam_param'"' not present.')
                    raise Exception(
                            'ArgumentError: '"'adapt_cam_opt'"' keyword called, but '"'adapt_cam_level'"' and '"'adapt_cam_param'"' not present.')
                # get 'adapt_cam_level', should be float 
                adapt_cam_level = kwargs['adapt_cam_level']
                if not str(adapt_cam_level).replace('.','',1).isdigit():
                    # print exception so it will be visible in console, then raise exception
                    print('ArgumentError: '"'adapt_cam_level'"' keyword is not a number.')
                    raise Exception('ArgumentError: '"'adapt_cam_level'"' keyword is not a number.')
    
                # If threshold gets below adapt_cam_level, add additional camera params.
                if threshold_re < adapt_cam_level:
                    # then enable additional lens params
                    cam_opt_parameters = kwargs['adapt_cam_param']
                    cam_opt_parameters_str = str([k for (k, v) in cam_opt_parameters.items() if v])
                    cam_opt_parameters_str = cam_opt_parameters_str.replace('cal_','')
                    print('RE below ' +  str(adapt_cam_level) + ' pixel, enabling ' + cam_opt_parameters_str)

        chunk.optimizeCameras(fit_f=cam_opt_parameters['cal_f'],
                              fit_cx=cam_opt_parameters['cal_cx'],
                              fit_cy=cam_opt_parameters['cal_cy'],
                              fit_b1=cam_opt_parameters['cal_b1'],
                              fit_b2=cam_opt_parameters['cal_b2'],
                              fit_k1=cam_opt_parameters['cal_k1'],
                              fit_k2=cam_opt_parameters['cal_k2'],
                              fit_k3=cam_opt_parameters['cal_k3'],
                              fit_k4=cam_opt_parameters['cal_k4'],
                              fit_p1=cam_opt_parameters['cal_p1'],
                              fit_p2=cam_opt_parameters['cal_p2'],
                              fit_p3=cam_opt_parameters['cal_p3'],
                              fit_p4=cam_opt_parameters['cal_p4'])
        noptimized = noptimized + 1
        print("completed optimization #", noptimized)
    else:
        print("If this shows up I don't understand while True loops")

    # get end time for processing log
    endtime = datetime.now()
    tdiff = endtime - starttime
    # get end point count
    end_pointcount = len([True for point in points if point.valid is True])

    # print status
    print('Reprojection Error optimization completed.\n' +
          str(ndeleted) + ' of ' + str(init_pointcount) + ' removed in ' + str(
        noptimized) + ' optimizations on chunk "' + chunk.label + '".\n')

    # Check if logging option enabled
    if 'log' in kwargs:
        # check that filename defined
        if 'proclog' in kwargs:
            # write results to processing log
            with open(kwargs['proclog'], 'a') as f:
                f.write("\n")
                f.write("============= AUTO GENERATED PROCESSING LOG TEXT BELOW =============\n")
                f.write("Reprojection Error optimization:\n")
                f.write("Chunk: " + chunk.label + "\n")
                f.write(str(ndeleted) + " of " + str(init_pointcount) + " removed in " + str(
                    noptimized) + " optimizations.\n")
                f.write("Final point count: " + str(end_pointcount) + "\n")
                f.write("Final Reprojection Error: " + str(threshold_re) + ".\n")
                f.write('Final camera lens calibration parameters: ' + ', '.join(
                    [k for k in cam_opt_parameters if cam_opt_parameters[k]]) + '\n')
                f.write("Start time: " + str(starttime) + "\n")
                f.write("End time: " + str(endtime) + "\n")
                f.write("Processing duration: " + str(tdiff) + "\n")
                f.write("\n")


def parse_command_line_args(parg, doc):
    """
    Parse command line arguments with argparse.
        args:
            parg: default Arg object with all defined defaults
        returns:
            parg: parsed Arg object with all args formatted.
    """

    # ============== HELPER FUNCTIONS =========================================
    # function to convert str args to boolean args
    def str_to_bool(s):
        """
        Converts str ['t','true','f','false'] to boolean, not case sensitive.
        Raises exception if unexpected entry.
            args:
                s: str
            returns:
                out_boolean: output boolean [True or False]
        """
        # remove quotes, commas, and case from s
        sf = s.lower().replace('"', '').replace("'", '').replace(',', '')
        # True
        if sf in ['t', 'true']:
            out_boolean = True
        # False
        elif sf in ['f', 'false']:
            out_boolean = False
        # Unexpected arg
        else:
            # print exception so it will be visible in console, then raise exception
            print('ArgumentError: Argument invalid. Expected boolean '
                  + 'got ' + '"' + str(s) + '"' + ' instead')
            raise Exception('ArgumentError: Argument invalid. Expected boolean '
                            + 'got ' + '"' + str(s) + '"' + ' instead')
        return out_boolean

    # function to convert camera param args to formatted list
    def cam_arg_to_param_list(cam_arg):
        """
        Converts camera parameter argument t formatted list, checks that all args
        are in expected list not case sensitive.  Doesn't work with quotes.
        Raises exception if unexpected entry.
            args:
                cam_arg: cam_param argument
            returns:
                out_cam_list: formatted camera param list
        """
        # Create set of all allowed camera optimization parameters
        cam_allowed = {'f', 'cx', 'cy', 'k1', 'k2', 'k3', 'p1', 'p2', 'k4', 'b1', 'b2', 'p3', 'p4'}
        # remove trialing commas, quotes, brackets and lowercase all
        camlist = [x.lower().replace(',', '').replace('"', '').replace('"', '').replace('[', '').replace(']', '') for x
                   in cam_arg]
        # check that all values passed are allowed
        if not set(camlist).issubset(cam_allowed):
            # print exception so it will be visible in console, then raise exception
            print('ArgumentError: Camera parameter list argument invalid.\n'
                  + 'Expected args: [f, cx, cy, k1, k2, k3, k4, b1, b2, p1, p2, p3, p4]\n'
                  + 'Unexpected arg found instead: ['
                  + str(set(camlist).difference(cam_allowed)).replace("'", '').replace('{', '').replace('}', '')
                  + ']\nCheck that list is called without quotes (example: -al_cam_param f, k1, k2)')
            raise Exception('ArgumentError: Camera parameter list argument invalid.\n'
                            + 'Expected args: [f, cx, cy, k1, k2, k3, k4, b1, b2, p1, p2, p3, p4]\n'
                            + 'Unexpected arg found instead: ['
                            + str(set(camlist).difference(cam_allowed)).replace("'", '').replace('{', '').replace('}',
                                                                                                                  '')
                            + ']\nCheck that list is called without quotes (example: -al_cam_param f, k1, k2)')
        # if all arguments allowed, set out_cam_list
        out_cam_list = camlist
        return out_cam_list


    # ===========================  BEGIN PARSER ==============================
    descriptionstr = ('  Script to run Metashape image alignment, and conduct gradual selection of sparse tiepoints. '
                      'Script begins on chunk designated by optional "'"-chunk"'" argument. If no chunk is designated, '
                      'the currently active chunk is used. Each operation creates a new chunk. The initial chunk is '
                      'copied to a new chunk and given a suffix of "'"_Align"'", "'"_RU"'", "'"_PA"'", or "'"_RE"'".')

    parser = argparse.ArgumentParser(description=descriptionstr, epilog='example: run Align_RuPaRe.py -chunk myChunk '
                                                                        '-align -al_kplim=50000 '
                                                                        '-al_generic=False '
                                                                        '-al_reference=True '
                                                                        '-ru -ru_level=11 '
                                                                        '-ru_cam_param f, cx, cy, k1, k2, k3 '
                                                                        '-pa -pa_level=2 '
                                                                        '-re -re_level=0.3 '
                                                                        '-re_adapt_cam=False '
                                                                        '-log my_output_logfile.txt')
    # =================== Chunk args ==========================================
    parser.add_argument('-chunk', '--initial_chunk', dest='initial_chunk', nargs='?', const=parg.initial_chunk,
                        type=str,
                        help='Initial chunk on which to perform process [default = currently active chunk]')
    #==================== Setup args ==========================================
    parser.add_argument('-setup', '--setup', dest='setup', default=False, action='store_true',
                        help='Setup project for processing [default=DISABLED].')
    #add output_dir argument that accepts filepath
    parser.add_argument('-input_dir', '--input_dir', dest='input_dir', nargs='?', const=parg.input_dir, type=str,
                        help='Output directory for project [default=project directory]')
    # =================== Alignment args ======================================
    parser.add_argument('-align', '--align_images', dest='align', default=False, action='store_true',
                        help='Align images [default=DISABLED].')

    parser.add_argument('-al_acc', '--alignment_accuracy', dest='acc', nargs='?', const=parg.align_accuracy,
                        type=str,
                        help='Alignment accuracy (highest, high, medium, low, lowest) [default=high]')

    parser.add_argument('-al_kplim', '--align_keypointlimit', dest='kplim', nargs='?', const=parg.keypointlimit,
                        type=int,
                        help='Alignment keypointlimit, set to 0 for unlimited [default=100,000]')

    parser.add_argument('-al_tplim', '--align_tiepointlimit', dest='tplim', nargs='?', const=parg.tiepointlimit,
                        type=int,
                        help='Alignment tiepointlimit, set to 0 for unlimited [default=0]')

    # action="store_true" doesn't work for these because need to be able to set false, need to convert str to boolean
    parser.add_argument('-al_generic', '--align_generic_preselection', dest='gen_preselect', nargs='?',
                        const=parg.gen_preselect, type=str,
                        help='Alignment generic preselection [default=True]')
    # action="store_true" doesn't work for these because need to be able to set false, need to convert str to boolean
    parser.add_argument('-al_reference', '--align_reference_preselection', dest='ref_preselect', nargs='?',
                        const=parg.ref_preselect, type=str,
                        help='Alignment reference preselection [default=False]')

    parser.add_argument('-al_cam_param', '--align_camera_opt_param', dest='al_cam', nargs='*',
                        help='Camera optimization parameters used for optimization after aligment'
                             + '[default="'"f"'", "'"cx"'", "'"cy"'", "'"k1"'", "'"k2"'", "'"k3"'", "'"p1"'", "'"p2"'"]')

    # =================== RU args =============================================
    parser.add_argument('-ru', '--reconstruction_uncertainty', dest='ru', default=False, action='store_true',
                        help='Reconstruction Uncertainty [default=DISABLED]')

    parser.add_argument('-ru_level', '--reconstruction_uncertainty_level', dest='ru_level', nargs='?',
                        const=parg.ru_filt_level, type=float,
                        help='Reconstruction Uncertainty filter level, optimum value 10-15 [default=10]')

    parser.add_argument('-ru_cam_param', '--ru_camera_opt_param', dest='ru_cam', nargs='*',
                        help='Camera optimization parameters used for optimization during RU iterations'
                             + '[default="'"f"'", "'"cx"'", "'"cy"'", "'"k1"'", "'"k2"'", "'"k3"'", "'"p1"'", "'"p2"'"]')

    # =================== PA args =============================================
    parser.add_argument('-pa', '--projection_accuracy', dest='pa', default=False, action='store_true',
                        help='Projection Accuracy [default=DISABLED]')

    parser.add_argument('-pa_level', '--projection_accuracy_level', dest='pa_level', nargs='?',
                        const=parg.pa_filt_level, type=float,
                        help='Projection Accuracy filter level, optimum value 2-4 [default=3]')

    parser.add_argument('-pa_cam_param', '--pa_camera_opt_param', dest='pa_cam', nargs='*',
                        help='Camera optimization parameters used for optimization during PA iterations'
                             + '[default="'"f"'", "'"cx"'", "'"cy"'", "'"k1"'", "'"k2"'", "'"k3"'", "'"p1"'", "'"p2"'"]')

    # =================== RE args =============================================
    parser.add_argument('-re', '--reprojection_error', dest='re', default=False, action='store_true',
                        help='Reprojection Error, optimum value 0.3 [default=0.3]')

    parser.add_argument('-re_level', '--reprojection_error_level', dest='re_level', nargs='?',
                        const=parg.re_filt_level, type=float,
                        help='Projection Accuracy filter level, optimum value 2-4 [default=3]')

    parser.add_argument('-re_cam_param', '--re_camera_opt_param', dest='re_cam', nargs='*',
                        help='Camera optimization parameters used for optimization during RE iterations'
                             + '[default="'"f"'", "'"cx"'", "'"cy"'", "'"k1"'", "'"k2"'", "'"k3"'", "'"p1"'", "'"p2"'"]')

    parser.add_argument('-re_adapt_cam', '--re_adaptive_cam', dest='re_adapt', nargs='?',
                        const=parg.re_adapt, type=str,
                        help='Enable adaptive camera optimization parameters at RE pixel threshold [default=True]')

    parser.add_argument('-re_adapt_level', '--re_adaptive_cam_level', dest='re_adapt_level', nargs='?',
                        const=parg.re_adapt_level, type=float,
                        help='RE pixel threshold below which to enable adapted camera parameters [default=1]')

    parser.add_argument('-re_adapt_cam_param', '--re_adapt_camera_param', dest='re_adapt_add_cam_param', nargs='*',
                        help='Additional camera optimization parameters used when below RE pixel threshold'
                             + '[default="'"k4"'", "'"b1"'", "'"b2"'", "'"p3"'", "'"p4"'"]')

    # =================== Export args =========================================
    parser.add_argument('-build', '--build', dest='build', default=False, action='store_true',
                        help='Export results [default=DISABLED]')
    
    # =================== Logging args =============================================
    parser.add_argument('-log', '--logfile', dest='logfile', nargs='?', const='default.txt', type=str,
                        help='Create or append to log file. [default name = XXXXX_ProcessingLog.txt]')

    # Parse known and unknown args
    try:
        arglist, unknown_args = parser.parse_known_args()
    except: 
        # this will catch invalid argument types and prevent the default argparse behavior of showing usage 
        # (which crashes Metashape) when script invoked from 'Run Script' dialog box. 
        # print exception so it will be visible in console, then raise exception
        print('ArgumentError: Possible argument type error. Stopping execution.')
        raise Exception(
            'ArgumentError: Possible argument type error. Stopping execution.')
    
    # check if any unknown args, if so, warn user and stop execution.  This will prevent the default argparse 
    # behavior of showing usage (which crashes Metashape) when script invoked from 'Run Script' dialog box. 
    if unknown_args:
        # print exception so it will be visible in console, then raise exception
        print('ArgumentError: unrecognized arguments found: ' + str(unknown_args) + '. Stopping execution.')
        raise Exception(
            'ArgumentError: unrecognized arguments found: ' + str(unknown_args) + '. Stopping execution.')
        

    # =================== CONFIGURE ARGS ========================================
    # Chunk argument
    if arglist.initial_chunk is not None:
        #remove quotes, and trailing commas
        chstr = arglist.initial_chunk.replace("'",'').replace('"','').replace(',','')
        parg.initial_chunk = chstr

    # -----------------Align arguments-----------------------
    if arglist.align:
        parg.align = True
    # Check if any -align options called without -align argument
    alargs = [arglist.acc, arglist.gen_preselect, arglist.ref_preselect, arglist.kplim, arglist.tplim, arglist.al_cam]
    if any(alargs) and not arglist.align:
        # an -al argument was called without -align also being called, raise exception
        # print exception so it will be visible in console, then raise exception
        print('ArgumentError: an -alignment (-al) option was called without the --align_images(-al) also being called.')
        raise Exception(
            'ArgumentError: an -alignment (-al) option was called without the --align_images(-al) also being called.')

    # alignment accuracy
    if arglist.acc is not None:
        # remove possible quotes
        accopt = arglist.acc.replace('"', '').replace("'", '')
    else:
        # use default
        accopt = parg.align_accuracy

    # capitalize and check that keyword is valid
    if not accopt.capitalize() in ['Highest', 'High', 'Medium', 'Low', 'Lowest']:
        # print exception so it will be visible in console, then raise exception
        print('ArgumentError: --alignment_accuracy argument invalid. Expected'
              + '[''Highest'', ''High'', ''Medium'', ''Low'', ''Lowest''], got ' + str(accopt) + ' instead')
        raise Exception('ArgumentError: --alignment_accuracy argument invalid. Expected'
                        + '[''Highest'', ''High'', ''Medium'', ''Low'', ''Lowest''], got ' + str(accopt) + ' instead')

    # append 'Accuracy' for required Metashape argument formatting
    parg.align_accuracy = accopt.capitalize() + 'Accuracy'

    # keypoint limit
    if arglist.kplim is not None:
        parg.keypointlimit = arglist.kplim

    # tiepoint limit
    if arglist.tplim is not None:
        parg.tiepointlimit = arglist.tplim

    # generic preselection
    if arglist.gen_preselect is not None:
        # convert arg to boolean
        parg.gen_preselect = str_to_bool(arglist.gen_preselect)

    # reference preselection
    if arglist.ref_preselect is not None:
        # convert arg to boolean
        parg.ref_preselect = str_to_bool(arglist.ref_preselect)

    # align camera optimization parameters
    if arglist.al_cam is not None:
        parg.al_cam_opt_param = cam_arg_to_param_list(arglist.al_cam)

    # -----------------RU arguments-----------------------
    if arglist.ru:
        # set ru to true
        parg.ru = True
    # Check if any -ru options called without -ru argument
    ruargs = [arglist.ru_level, arglist.ru_cam]
    if any(ruargs) and not arglist.ru:
        # an -ru argument was called without -ru also being called, raise exception
        # print exception so it will be visible in console, then raise exception
        print(
            'ArgumentError: a -ru option was called without the --reconstruction_uncertainty argument(-ru) also being called.')
        raise Exception(
            'ArgumentError: a -ru option was called without the --reconstruction_uncertainty argument(-ru) also being called.')

    # RU filter level
    if arglist.ru_level is not None:
        parg.ru_filt_level = arglist.ru_level

    # RU camera optimization parameters
    if arglist.ru_cam is not None:
        parg.ru_cam_opt_param = cam_arg_to_param_list(arglist.ru_cam)

    # -----------------PA arguments-----------------------
    if arglist.pa:
        # set pa to true
        parg.pa = True
    # Check if any -pa options called without -ru argument
    paargs = [arglist.pa_level, arglist.pa_cam]
    if any(paargs) and not arglist.pa:
        # a -pa argument was called without -pa also being called, raise exception
        # print exception so it will be visible in console, then raise exception
        print(
            'ArgumentError: a -pa option was called without the --projection_accuracy argument(-pa)  also being called.')
        raise Exception(
            'ArgumentError: a -pa option was called without the --projection_accuracy argument(-pa) also being called.')

    # PA filter level
    if arglist.pa_level is not None:
        parg.pa_filt_level = arglist.pa_level

    # PA camera optimization parameters
    if arglist.pa_cam is not None:
        parg.pa_cam_opt_param = cam_arg_to_param_list(arglist.pa_cam)

    # -----------------RE arguments-----------------------
    if arglist.re:
        # set re to true
        parg.re = True
    # Check if any -re options called without -ru argument
    reargs = [arglist.re_level, arglist.re_cam, arglist.re_adapt, arglist.re_adapt_level,
              arglist.re_adapt_add_cam_param]
    if any(reargs) and not arglist.re:
        # a -re argument was called without -re also being called, raise exception
        # print exception so it will be visible in console, then raise exception
        print(
            'ArgumentError: a -re option was called without the --reprojection_error argument(-re) also being called.')
        raise Exception(
            'ArgumentError: a -re option was called without the --reprojection_error argument(-re) also being called.')

    # RE filter level
    if arglist.re_level is not None:
        parg.re_filt_level = arglist.re_level

    # RE camera optimization parameters
    if arglist.re_cam is not None:
        parg.re_cam_opt_param = cam_arg_to_param_list(arglist.re_cam)

    # RE adapt camera enable/disable
    if arglist.re_adapt is not None:
        parg.re_adapt = str_to_bool(arglist.re_adapt)

    # RE adapt camera level
    if arglist.re_adapt_level is not None:
        parg.re_adapt_level = arglist.re_adapt_level

    # RE adapt camera optimization parameters
    # initialize new cam_param list, then change if called in defaults/command line args
    parg.re_adapted_cam_param = parg.re_cam_opt_param + parg.re_adapt_add_cam_param
    if arglist.re_adapt_add_cam_param is not None:
        parg.re_adapt_add_cam_param = cam_arg_to_param_list(arglist.re_adapt_add_cam_param)
        parg.re_adapted_cam_param = parg.re_cam_opt_param + parg.re_adapt_add_cam_param

    if arglist.build:
        parg.build = True
    if arglist.setup:
        parg.setup = True
    
    # ======== PARSE -LOG ARGUMENT =============================================
    arglist.logfile = 'default.txt'
    if arglist.logfile is not None:
        parg.log = True
        logfilename = arglist.logfile
        if logfilename == 'default.txt':
            # Get name of document to set name of processing log.
            # Logfile will be named XXXXX_ProcessingLog.txt, where XXXXX is the name of the Metashape project.
            base = os.path.basename(doc.path)
            proclogdir = os.path.dirname(doc.path)
            proclogfile = os.path.splitext(base)[0] + "_ProcessingLog.txt"
            parg.proclogname = proclogdir + "/" + proclogfile
            print(f"Log file name not specified, using default name: {parg.proclogname}")
        else:
            # then user supplied name
            # remove quotes in string if supplied
            proclogfile = logfilename.replace('"', '').replace("'", '')
            parg.proclogname = proclogfile
    else:
        parg.log = False

    # ==========================================================================

    # chunk message
    print('1. Process will be performed on chunk ' + '"' + parg.initial_chunk + '"' + '.')
    # align message
    if parg.align:
        print('2. Alignment ENABLED with the following options:\n'
              + '    -accuracy = ' + parg.align_accuracy + '\n'
              + '    -keytiepoint limit = ' + str(parg.keypointlimit) + '\n'
              + '    -tiepoint limit = ' + str(parg.tiepointlimit) + '\n'
              + '    -generic preselection = ' + str(parg.gen_preselect) + '\n'
              + '    -reference preselection = ' + str(parg.ref_preselect) + '\n'
              + '    -camera optimization parameters: ' + str(parg.al_cam_opt_param))
    else:
        print('2. Alignment DISABLED.')

    # ru message
    if parg.ru:
        print('3. Reconstruction Uncertainty gradual selection ENABLED with the following options:\n'
              + '    -RU filter level = ' + str(parg.ru_filt_level) + '\n'
              + '    -camera optimization parameters: ' + str(parg.ru_cam_opt_param))
    else:
        print('3. Reconstruction Uncertainty gradual selection DISABLED.')

    # pa message
    if parg.pa:
        print('4. Projection Accuracy gradual selection ENABLED with the following options:\n'
              + '    -PA filter level = ' + str(parg.pa_filt_level) + '\n'
              + '    -camera optimization parameters: ' + str(parg.pa_cam_opt_param))
    else:
        print('4. Projection Accuracy gradual selection DISABLED.')

    # re message
    if parg.re:
        print('5. Reprojection Error gradual selection ENABLED with the following options:\n'
              + '    -RE filter level = ' + str(parg.re_filt_level) + '\n'
              + '    -camera optimization parameters: ' + str(parg.re_cam_opt_param))
        if parg.re_adapt:
            print('    -adaptive camera opt. params ENABLED, when Reprojection Error below '
                  + str(parg.re_adapt_level) + ' pixels\n'
                  + '    -adapted camera opt. parameters: '
                  + str(parg.re_cam_opt_param + parg.re_adapt_add_cam_param))
    else:
        print('5. Reprojection Error gradual selection DISABLED.')

    # log message
    if parg.log:
        print('6. Log file enabled, writing to: ' + parg.proclogname + '.')
    else:
        print('6. Log file DISABLED.')

    if parg.setup:
        print('7. Setup ENABLED.')
    else:
        print('7. Setup DISABLED.')
    
    if parg.build:
        print('8. Build ENABLED.')
    else:   
        print('8. Build DISABLED.')
        
    
    
    return parg

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


    

def main(parg, doc):
    """
    args:
          doc = active Metashape.app.document object
          parg = Arg object with formatted argument attributes
    """
    print(parg.setup==False and parg.align==False and parg.ru==False and parg.pa==False and parg.re==False and parg.build==False)
    print(parg.setup)
    print(parg.align)
    if parg.setup==False and parg.align==False and parg.ru==False and parg.pa==False and parg.re==False and parg.build==False:
        parg.setup = True
        parg.align = True
        parg.ru = True
        parg.pa = True
        parg.re = True
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
    # reference active chunk
    chunk = doc.chunk
    if chunk is not None:    
        active_chunk = chunk.label

    # Initialize camera optimization parameters with all params false. 
    # This will be copied and changed for use in each function
    blank_cam_opt_parameters = {'cal_f': False,
                                'cal_cx': False,
                                'cal_cy': False,
                                'cal_b1': False,
                                'cal_b2': False,
                                'cal_k1': False,
                                'cal_k2': False,
                                'cal_k3': False,
                                'cal_k4': False,
                                'cal_p1': False,
                                'cal_p2': False,
                                'cal_p3': False,
                                'cal_p4': False}

    
    user_tags = parg.user_tags
    flight_folders = parg.flight_folders
    psx_list = []
    if parg.input_dir is not None:
        for tag in user_tags:
            #Get last subdirectory in first entry of flight folders
            flight_folder = flight_folders[0]
            flight_folder = os.path.basename(os.path.normpath(flight_folder))
            doc_name = tag + "_" + flight_folder + ".psx"
            print("Saving PSX to: " + os.path.join(parg.input_dir, doc_name))
            doc_path = os.path.join(parg.input_dir, doc_name)
            doc.save(path = doc_path)
            psx_list.append(doc_path)
    else:
        doc = Metashape.app.document
        psx = doc.path
        psx_list.append(psx)
        
    # ====================MAIN CODE STARTS HERE====================
    if parg.setup:
        geo_ref_dict = {}
        for psx in psx_list:
            print(f"PSX: {psx}")
            print(f"Flight Folders: {flight_folders}")
            print(f"User Tags: {user_tags}")
            geo_ref_list, chunk = setup_psx(user_tags,flight_folders, psx)
            geo_ref_dict[psx] = geo_ref_list
    else:
        geo_ref_dict = {}
        for psx in psx_list:
            geo_ref_list, chunk = setup_psx(user_tags, flight_folders, psx, load_photos = False)
            geo_ref_dict[psx] = geo_ref_list
        
    print(f"PSX List: {psx_list}")
    for psx in psx_list:
        doc.open(path = psx)
        print(f"Geo Ref List: {geo_ref_dict[psx]}")
        # ALIGN IMAGES
        if parg.align:
            # reference active chunk
            if chunk is None:
                chunk_label_list = [chunk.label for chunk in doc.chunks]
                chunk = activate_chunk(doc, chunk_label_list[0])

            # copy active chunk, rename, make active
            align_chunk = chunk.copy()
            align_chunk.label = chunk.label + '_Align'
            print('Copied chunk ' + chunk.label + ' to chunk ' + align_chunk.label)

            # Set camera optimization parameters.
            # make a dictionary of camera opt params using arguments from parg
            al_cam_param = blank_cam_opt_parameters.copy()
            # loop through all cam parameters in parg list and set called params to True
            for elem in parg.al_cam_opt_param:
                al_cam_param['cal_{}'.format(elem)] = True

            # Run alignment using align_images function
            print('Aligning images')
            geo_ref_list = geo_ref_dict[psx] 
            if parg.log:
                # if logging enabled use kwargs
                print('Logging to file ' + parg.proclogname)
                # write input and output chunk to log file
                with open(parg.proclogname, 'a') as f:
                    f.write("\n")
                    f.write("============= AUTO GENERATED PROCESSING LOG TEXT BELOW =============\n")
                    f.write("Copied chunk " + chunk.label + " to chunk " + align_chunk.label + "\n")
                    f.write("Geo Ref List: " + str(geo_ref_list) + "\n")
                # execute function
                align_images(align_chunk)
            else:
                align_images(align_chunk)
             
              
            print(f"Geo Ref List: {geo_ref_list}")
            #for geo_ref in geo_ref_list:    
                #chunk.importReference(os.path.join(geo_ref), delimiter = ',', columns = 'nxyzabcXZ')
            doc.save()

        # RECONSTRUCTION UNCERTAINTY
        if parg.ru:
            # reference active chunk
            chunk = doc.chunk
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

            # Set camera optimization parameters.
            # make a dictionary of camera opt params using arguments from parg
            ru_cam_param = blank_cam_opt_parameters.copy()
            # loop through all cam parameters in parg list and set called params to True
            for elem in parg.ru_cam_opt_param:
                ru_cam_param['cal_{}'.format(elem)] = True

            # Run Reconstruction Uncertainty using reconstruction_uncertainty function
            print('Running Reconstruction Uncertainty optimization')
            if parg.log:
                # if logging enabled use kwargs
                print('Logging to file ' + parg.proclogname)
                # write input and output chunk to log file
                with open(parg.proclogname, 'a') as f:
                    f.write("\n")
                    f.write("============= AUTO GENERATED PROCESSING LOG TEXT BELOW =============\n")
                    f.write("Copied chunk " + chunk.label + " to chunk " + ru_chunk.label + "\n")
                # execute function
                reconstruction_uncertainty(ru_chunk, parg.ru_filt_level, parg.ru_cutoff, parg.ru_increment, ru_cam_param,
                                        log=True, proclog=parg.proclogname)
            else:
                reconstruction_uncertainty(ru_chunk, parg.ru_filt_level, parg.ru_cutoff, parg.ru_increment, ru_cam_param)
            doc.save()

        # PROJECTION ACCURACY
        if parg.pa:
            # reference active chunk
            chunk = doc.chunk

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

            # Set camera optimization parameters.
            # make a dictionary of camera opt params using arguments from parg
            pa_cam_param = blank_cam_opt_parameters.copy()
            # loop through all cam parameters in parg list and set called params to True
            for elem in parg.pa_cam_opt_param:
                pa_cam_param['cal_{}'.format(elem)] = True

            # Run Projection Accuracy using projection_accuracy function
            print('Running Projection Accuracy optimization')
            if parg.log:
                # if logging enabled use kwargs
                print('Logging to file ' + parg.proclogname)
                # write input and output chunk to log file
                with open(parg.proclogname, 'a') as f:
                    f.write("\n")
                    f.write("============= AUTO GENERATED PROCESSING LOG TEXT BELOW =============\n")
                    f.write("Copied chunk " + chunk.label + " to chunk " + pa_chunk.label + "\n")
                # execute function
                projection_accuracy(pa_chunk, parg.pa_filt_level, parg.pa_cutoff, parg.pa_increment, pa_cam_param, log=True,
                                    proclog=parg.proclogname)
            else:
                projection_accuracy(pa_chunk, parg.pa_filt_level, parg.pa_cutoff, parg.pa_increment, pa_cam_param)
            doc.save()

        # REPROJECTION ERROR
        if parg.re:
            # reference active chunk
            chunk = doc.chunk
            chunk.tiepoint_accuracy = 0.1
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
            re_chunk = chunk.copy()
            re_chunk.label = chunk.label + '_RE' + str(parg.re_filt_level)
            print('Copied chunk ' + chunk.label + ' to chunk ' + re_chunk.label)

            # Set INITIAL camera optimization parameters.
            # make a dictionary of camera opt params using arguments from parg
            re_cam_param = blank_cam_opt_parameters.copy()
            # loop through all cam parameters in parg list and set called params to True
            for elem in parg.re_cam_opt_param:
                re_cam_param['cal_{}'.format(elem)] = True

            # if re_adapt_camera, make cam_param for that also
            if parg.re_adapt:
                # make a dictionary of camera opt params using arguments from parg
                re_adapted_cam_param = blank_cam_opt_parameters.copy()
                # loop through all cam parameters in parg list and set called params to True
                for elem in parg.re_adapted_cam_param:
                    re_adapted_cam_param['cal_{}'.format(elem)] = True

            # Run Reprojection Error using reprojection_error function
            print('Running Reprojection Error optimization')
            if parg.log:
                # if logging enabled use kwargs
                print('Logging to file ' + parg.proclogname)
                # write input and output chunk to log file
                with open(parg.proclogname, 'a') as f:
                    f.write("\n")
                    f.write("============= AUTO GENERATED PROCESSING LOG TEXT BELOW =============\n")
                    f.write("Copied chunk " + chunk.label + " to chunk " + re_chunk.label + "\n")
                # execute function, give additional kwargs if re_adapt_cam_opt enabled
                if parg.re_adapt:
                    reprojection_error(re_chunk, parg.re_filt_level, parg.re_cutoff, parg.re_increment, re_cam_param, log=True,
                                proclog=parg.proclogname, adapt_cam_opt=parg.re_adapt, adapt_cam_level=parg.re_adapt_level,
                                adapt_cam_param=re_adapted_cam_param)
                else:
                    reprojection_error(re_chunk, parg.re_filt_level, parg.re_cutoff, parg.re_increment, re_cam_param, log=True,
                                proclog=parg.proclogname)
            else:
                if parg.re_adapt:
                    reprojection_error(re_chunk, parg.re_filt_level, parg.re_cutoff, parg.re_increment, re_cam_param, 
                                    adapt_cam_opt=parg.re_adapt, adapt_cam_level=parg.re_adapt_level,
                                    adapt_cam_param=re_adapted_cam_param)
                else:
                    reprojection_error(re_chunk, parg.re_filt_level, parg.re_cutoff, parg.re_increment, re_cam_param)
        
            doc.save()

    if parg.build:
        print("----------------------------------------------------------------------------------------")

        #make output folder called Exports in the same directory as psx file
        outputFolder = os.path.join(os.path.dirname(doc.path), "Metashape Exports")
        geoidPath = parg.geoid
        maxconf = parg.maxconf
        

        #psx_list = [os.path.join(inputFolder, file) for file in os.listdir(inputFolder) if file.endswith(".psx")]
        
        if len(psx_list) == 0:
            if parg.input_dir is not None:
                for tag in parg.user_tags:
                    doc_name = tag + "_" + str(datetime.date.today()) + ".psx"
                    doc_path = os.path.join(parg.input_dir, doc_name)
                    doc.save(path = doc_path)
                    psx_list.append(doc_path)
                doc = Metashape.app.document
            else:
                doc = Metashape.app.document
                psx = doc.path
                psx_list.append(psx)
        
            
        for psx in psx_list:
            #Open the .psx file
            doc = Metashape.app.document
            print("Opening " + psx)
            doc.open(psx)
            #Get file name of .psx file without .psx extension
            psx_name = os.path.splitext(os.path.basename(psx))[0]
            print("Processing " + psx_name)
            chunk_label_list = [chunk.label for chunk in doc.chunks]
            
            psx_folder = os.path.join(outputFolder, psx_name)
            print("Output folder: " + psx_folder)
            os.makedirs(os.path.dirname(psx_folder), exist_ok=True)
    
            post_error_chunk_list = [chunk for chunk in chunk_label_list if chunk.endswith("_RE0.25")]
            print("Chunks to process: " + str(post_error_chunk_list))

            #Get the chunk names and create a counter for progress updates
            for current_chunk, i in zip(post_error_chunk_list, range(len(post_error_chunk_list))):
                print("Processing " + current_chunk + " in " + psx_name) 
                print("Chunk " + str(i+1) + " of " + str(len(post_error_chunk_list)) + " in " + psx_name)
                #-------------Create File Paths-----------------#
                file_name = current_chunk.replace("\\", "_") #Account for backslashes when creating file path
                file_name = file_name.replace("/", "_") #Account for forward slashes when creating file path
                outputOrtho = os.path.join(psx_folder, os.path.basename(psx)[:-4] + "____" "Ortho_"+ file_name+ ".tif") #[:-4] removes .psx extension
                outputDEM = os.path.join(psx_folder, os.path.basename(psx)[:-4] + "____" +"DEM_"+ file_name + ".tif")
                if os.path.exists(outputDEM) or os.path.exists(outputOrtho):
                    print("File already exists, skipping " + outputDEM + " and " + outputOrtho + " of " + psx_name)
                    continue
            #------------Build Dense Cloud and Filter Point Cloud-----------------#
                try:
                    print("-------------------------------COPY CHUNKS FOR CLOUD---------------------------------------")
                    copied_list = copy_chunks_for_cloud(current_chunk, doc)
                    
                    for copied_chunk in copied_list:
                        chunk = activate_chunk(doc, copied_chunk)
                        if len(chunk.depth_maps_sets) == 0:
                            print("-------------------------------BUILD DENSE CLOUD---------------------------------------")
                            print("")
                            print(f"Filtering point cloud for {copied_chunk}")
                            buildDenseCloud(copied_chunk, doc)
                        print("-------------------------------FILTER DENSE CLOUD---------------------------------------")
                        filtered_chunk = filter_point_cloud(copied_chunk, maxconf, doc)
                        print("-------------------------------BUILD DEM/ORTHO---------------------------------------")
                        print("")
                        print(f"Building DEM and Orthomosaic for {filtered_chunk}")
                        chunk = activate_chunk(doc, filtered_chunk)
                        if chunk.elevation is None:    
                            buildDEMOrtho(filtered_chunk, doc)
                        print("-------------------------------EXPORT DEM/ORTHO---------------------------------------")
                        outputOrtho = os.path.join(psx_folder, os.path.basename(psx)[:-4] + "____" + filtered_chunk + "_Ortho.tif") #[:-4] removes .psx extension
                        outputDEM = os.path.join(psx_folder, os.path.basename(psx)[:-4] + "____" + filtered_chunk + "_DEM.tif")
                        if os.path.exists(outputDEM) or os.path.exists(outputOrtho):
                            print("File already exists, skipping " + outputDEM + " and " + outputOrtho + " of " + psx_name)
                            continue
                        #out_crs, in_crs = exportDEMOrtho(filtered_chunk, path_to_save_dem = outputDEM, path_to_save_ortho=outputOrtho, geoidPath=geoidPath)
                        
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
                                f.write('\nExported Chunks:')
                                f.write('\nDEM: {}'.format(outputDEM))
                                f.write('\nOrthomosaic: {}'.format(outputOrtho))
                                #f.write('\nChunk CRS: {}'.format(in_crs))
                                #f.write('\nOutput CRS: {}'.format(out_crs))

                except Exception as e:
                    print("Error processing " + current_chunk + " of " + psx_name)
                    print(e)
                    doc.save()
                    continue
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
