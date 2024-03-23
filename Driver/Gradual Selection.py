import Metashape 
import os
from datetime import datetime


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

    while len(chunk.tie_points.points) > init_pointcount * 0.6 and noptimized < 1:
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
        if nselected < 100:
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
                if ninc_reduced > 15:
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
                              fit_p4=cam_opt_parameters['cal_p4'],
                              adaptive_fitting = cam_opt_parameters['adaptive_fitting'],
                              tiepoint_covariance = cam_opt_parameters['tiepoint_covariance'],
                              fit_corrections = False
                              )
        noptimized = noptimized + 1
        print("completed optimization #", noptimized)


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
                f.write("=============Reconstruction Uncertainty optimization:=============\n")
                f.write("Chunk: " + chunk.label + "\n")
                f.write(str(ndeleted) + " of " + str(init_pointcount) + " removed in " + str(
                    noptimized) + " optimizations.\n")
                f.write("Final point count: " + str(end_pointcount) + "\n")
                f.write(f"Iterations: {noptimized}\n")
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

    while len(chunk.tie_points.points) > init_pointcount * 0.6 and noptimized < 1:
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
        if nselected < 100:
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
                if ninc_reduced > 15:
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
                              fit_p4=cam_opt_parameters['cal_p4'],
                              adaptive_fitting = cam_opt_parameters['adaptive_fitting'],
                              tiepoint_covariance = cam_opt_parameters['tiepoint_covariance'],
                              fit_corrections = False
                              )
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
                f.write("=============Projection Accuracy optimization:=============\n")
                f.write("Chunk: " + chunk.label + "\n")
                f.write(str(ndeleted) + " of " + str(init_pointcount) + " removed in " + str(
                    noptimized) + " optimizations.\n")
                f.write("Final point count: " + str(end_pointcount) + "\n")
                f.write(f"Iterations: {noptimized}\n")
                f.write("Final Projection Accuracy: " + str(threshold_pa) + ".\n")
                f.write('Final camera lens calibration parameters: ' + ', '.join(
                    [k for k in cam_opt_parameters if cam_opt_parameters[k]]) + '\n')
                f.write("Start time: " + str(starttime) + "\n")
                f.write("End time: " + str(endtime) + "\n")
                f.write("Processing duration: " + str(tdiff) + "\n")
                f.write("\n")


def reprojection_error(chunk, re_filt_level_param, re_cutoff, re_increment, cam_opt_parameters, RMSE_goal,
                       round1_max_optimizations, round2_max_optimizations, RE_round2_tie_point_acc, **kwargs):
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
    noptimized = 1
    ndeleted = 0
    ninc_reduced = 0
    
    # get start time for processing log
    starttime = datetime.now()
    # get initial point count
    points = chunk.tie_points.points
    init_pointcount = len([True for point in points if point.valid is True])
    if 'log' in kwargs:
        # check that filename defined
        if 'proclog' in kwargs:
            # write results to processing log
            with open(kwargs['proclog'], 'a') as f:
                f.write("\n")
                f.write("Chunk: " + chunk.label + "\n")
                f.write(f"Performing 1st round of reprojection error using a threshold of {re_filt_level_param}.\n")
                f.write(f"Each iteration, RE value will be lowered until {re_cutoff*100}% of points are removed or RE threshold is reached.\n")
                f.write(f"Max {round1_max_optimizations} iterations will be performed in the first round to prevent overfitting.\n")
                f.write(f"Tie Point Accuracy: {chunk.tiepoint_accuracy:.2f}\n")

    while len(chunk.tie_points.points) > init_pointcount * 0.25:

        metadata = chunk.meta
        SEUW = float(metadata['OptimizeCameras/sigma0'])

        # SEUW should be getting closer to 1 every iteration, if it's not, break
        #if math.fabs(1 - SEUW) > math.fabs(1 - SEUWlast): 
         #   break  
        
        # define threshold variables
        points = chunk.tie_points.points
        refilt = Metashape.TiePoints.Filter()
        threshold_re = re_filt_level_param
        print("initializing with RE =", threshold_re)
        # initialize filter for RE
        refilt.init(chunk, criterion=Metashape.TiePoints.Filter.ReprojectionError)
        refilt.selectPoints(threshold_re)
        # calculate number of selected points
        nselected = len([True for point in points if point.valid is True and point.selected is True])
        print(nselected, " points selected")
        if nselected < 100:
            break
        if noptimized > round1_max_optimizations: # Don't overfit, break after 6 iterations
            break
        npoints = len(points)
        while nselected * (1 / re_cutoff) > npoints:
            print("RE threshold ", threshold_re, "selected ", nselected, "/", npoints, "(",
                  round(nselected / npoints * 100, 4), " %) of  points. Adjusting")
            threshold_re = threshold_re + re_increment
            refilt.selectPoints(threshold_re)
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
        if 'log' in kwargs:
            # check that filename defined
            if 'proclog' in kwargs:
                # write results to processing log
                with open(kwargs['proclog'], 'a') as f:
                    f.write(f"Iteration #{noptimized}\n")
                    f.write(f"     -RE threshold: {threshold_re:.2f} deleted {nselected} points, {round(nselected / npoints * 100, 4)} of total points\n")
                    f.write(f"     -SEUW: {SEUW:.2f}\n")
                    f.write(f"     -RMSE: {calc_RMS_error(chunk):.2f}\n")
                    f.write(f"     -Camera Vertical Accuracy: {calc_camera_accuracy(chunk):.2f}\n")
                    f.write(f"     -Camera Vertical Error: {calc_camera_error(chunk):.2f}\n")
        # check if adaptive camera optimization parameters called
       
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
                              fit_p4=cam_opt_parameters['cal_p4'],
                              adaptive_fitting = cam_opt_parameters['adaptive_fitting'],
                              tiepoint_covariance = cam_opt_parameters['tiepoint_covariance'],
                              fit_corrections = False
                              )
        noptimized = noptimized + 1

        print("Completed optimization #", noptimized)
        
    
    if 'log' in kwargs:
            # check that filename defined
            if 'proclog' in kwargs:
                # write results to processing log
                with open(kwargs['proclog'], 'a') as f:
                    f.write(f"First round completed with {noptimized} optimizations.\n")
                    f.write(f"\nCamera optimizations for SEUW optimization will begin.\n")
                    f.write(f"Camera optimization will be performed until SEUW approaches 1\n and camera error is reduced relative to accuracy.\n")
    
    #======================================USGS Step 9==============================================================
    RMSE = calc_RMS_error(chunk)
    if RMSE < RMSE_goal:
        return SEUW, RMSE
    
    #======================================USGS Step 10 - 12==============================================================

    chunk.tiepoint_accuracy = RE_round2_tie_point_acc #step 10 in USGS document, lower from 0.1 for WIngtra flights on Peter's suggestion

    metadata = chunk.meta
    SEUW = float(metadata['OptimizeCameras/sigma0'])
    RMSE = calc_RMS_error(chunk)

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
                            fit_p4=cam_opt_parameters['cal_p4'],
                            adaptive_fitting = cam_opt_parameters['adaptive_fitting'],
                            tiepoint_covariance = cam_opt_parameters['tiepoint_covariance'],
                            fit_corrections = False
                            )

    #======================================USGS Step 14 - 18==============================================================
    threshold_re_R2 = 0.05
    if 'log' in kwargs:
        # check that filename defined
        if 'proclog' in kwargs:
            # write results to processing log
            with open(kwargs['proclog'], 'a') as f:
                f.write(f"\nSecond round of optimizations will begin with a tie point accuracy of {RE_round2_tie_point_acc}, which will be lowered dynamically if SEUW deviates from 1.\n")
                f.write("Optimal SEUW value is 1, and it should be approaching closer to 1 after every iteration.\n")
                f.write(f"the RE value will be lowered to {threshold_re_R2:.2f} and {re_cutoff * 100:.2f}% of tie points will be removed each iteration.\n")
                f.write(f"A max of {round2_max_optimizations} iterations will be performed in the second round.\n")
    noptimized_round2 = 1
    ninc_reduced = 0
    points = chunk.tie_points.points
    R2_pointcount = len([True for point in points if point.valid is True])
    while (RMSE > RMSE_goal) and (R2_pointcount > (init_pointcount * 0.25)):
        threshold_re = re_filt_level_param - 0.25 # set low threshold so 10% of points are removed  every iteration
        metadata = chunk.meta
        SEUW = float(metadata['OptimizeCameras/sigma0'])
        RMSE = calc_RMS_error(chunk)

        if 'log' in kwargs:
            # check that filename defined
            if 'proclog' in kwargs:
                # write results to processing log
                with open(kwargs['proclog'], 'a') as f:
                    f.write(f"Iteration Number: {noptimized + noptimized_round2}\n")
                    f.write(f"     -SEUW/Sigma0 value: {SEUW:.4f}\n")
                    f.write(f"     -Camera Error: {calc_camera_error(chunk)}\n")
                    f.write(f"     -Camera Accuracy: {calc_camera_accuracy(chunk)}\n")
                    f.write(f"     -RMSE: {RMSE:.4f}\n")
        # define threshold variables
        points = chunk.tie_points.points
        R2_pointcount = len([True for point in points if point.valid is True])
        refilt = Metashape.TiePoints.Filter()
       
        print("initializing with RE =", threshold_re)
        # initialize filter for RE
        refilt.init(chunk, criterion=Metashape.TiePoints.Filter.ReprojectionError)
        refilt.selectPoints(threshold_re)
        # calculate number of selected points
        nselected = len([True for point in points if point.valid is True and point.selected is True])
        print(nselected, " points selected")

        if noptimized_round2 > round2_max_optimizations:
            break
        npoints = len(points)
        
        while nselected * (1 / re_cutoff) > npoints:
            print("RE threshold ", threshold_re, "selected ", nselected, "/", npoints, "(",
                  round(nselected / npoints * 100, 4), " %) of  points. Adjusting")
            threshold_re = threshold_re + re_increment
            refilt.selectPoints(threshold_re)
            nselected = len([True for point in points if point.valid is True and point.selected is True])

        print("RE threshold ", threshold_re, " is ", round(nselected / npoints * 100, 4),
              "% of total points. Ready to delete")
        ndeleted = ndeleted + nselected
        chunk.tie_points.removeSelectedPoints()
        
        if 'log' in kwargs:
            # check that filename defined
            if 'proclog' in kwargs:
                # write results to processing log
                with open(kwargs['proclog'], 'a') as f:
                    f.write(f"RE {threshold_re:.2f} deleted {nselected} points {round(nselected / npoints * 100, 4)}% of total points\n")
    

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
                              fit_p4=cam_opt_parameters['cal_p4'],
                              adaptive_fitting = cam_opt_parameters['adaptive_fitting'],
                              tiepoint_covariance = cam_opt_parameters['tiepoint_covariance'],
                              fit_corrections = cam_opt_parameters['fit_corrections']
                              )
        noptimized_round2 = noptimized_round2 + 1
        SEUWlast = SEUW
        print("Completed optimization #", noptimized)
    # get end time for processing log
    endtime = datetime.now()
    tdiff = endtime - starttime
    # get end point count
    end_pointcount = len([True for point in points if point.valid is True])

    # print status
    print('Reprojection Error optimization completed.\n' +
          str(ndeleted) + ' of ' + str(init_pointcount) + ' removed in ' + str(
        noptimized) + ' optimizations on chunk "' + chunk.label + '".\n')
    refilt.init(chunk, criterion=Metashape.TiePoints.Filter.ReprojectionError)
    refilt.selectPoints(threshold_re)
    refilt.resetSelection()
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
                            fit_p4=cam_opt_parameters['cal_p4'],
                            adaptive_fitting = cam_opt_parameters['adaptive_fitting'],
                            tiepoint_covariance = cam_opt_parameters['tiepoint_covariance'],
                            fit_corrections = cam_opt_parameters['fit_corrections']
                            )
    # Check if logging option enabled
    if 'log' in kwargs:
        # check that filename defined
        if 'proclog' in kwargs:
            # write results to processing log
            with open(kwargs['proclog'], 'a') as f:
               
                f.write(str(ndeleted) + " of " + str(init_pointcount) + " removed in " + str(
                    noptimized + noptimized_round2 + 1) + " optimizations.\n")
                f.write(f"Round 2 Tie Point Accuracy: {chunk.tiepoint_accuracy:.2f}\n")
                f.write(f"Tie Point Accuracy kept constant in round 2") 
                f.write(f"Round 1: {noptimized} optimizations, Round 2: {noptimized_round2} optimizations.\n")
                f.write(f"Final Camera Error: {calc_camera_error(chunk):.2f}\n")
                f.write(f"Final SEUW: {SEUW:.3f}\n")
                f.write(f"Final RMSE: {calc_RMS_error(chunk):.2f}\n")  
                f.write("Final point count: " + str(end_pointcount) + "\n")
                f.write('Final camera lens calibration parameters: ' + ', '.join(
                    [k for k in cam_opt_parameters if cam_opt_parameters[k]]) + '\n')
                f.write("Start time: " + str(starttime) + "\n")
                f.write("End time: " + str(endtime) + "\n")
                f.write("Processing duration: " + str(tdiff) + "\n")
                f.write("\n")
    return SEUW, RMSE

def main():
    pass
if __name__ == "__main__":
    main()