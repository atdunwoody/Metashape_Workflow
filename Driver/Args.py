import Metashape
import os
import re
from datetime import datetime
import argparse
import copy as cp
import math

class Args():
    """ Simple class to hold arguments """
    pass

# ==================== DEFAULT ARGUMENTS BELOW===========================================
defaults = Args()
# ========These can be changed here, or changed at execution using command line arguments=====================

# ------------Chunk defaults -------------------------------------------------------
defaults.initial_chunk = 'active'    # Name of first chunk to operate on ('active' = active chunk)
defaults.export_dir = None        # path to input directory where all psx folders will be processed
defaults.user_tag = 'MM'             # list of user tags to process
defaults.flight_folders = [
    r"Z:\ATD\Drone Data Processing\Drone Images\East_Troublesome\Flights\102123", # LM2, LPM, MM, MPM, UM1, UM2
    r"Z:\JTM\Wingtra\WingtraPilotProjects\070923 Trip", # LM2, LPM, MM, MPM, UM1, UM2
    #r"Z:\JTM\Wingtra\WingtraPilotProjects\053123 Trip", # Don't Use 
    #r"Z:\ATD\Drone Data Processing\Drone Images\East_Troublesome\Flights\10__22" # Re-PPK processed 
    #r"Z:\JTM\Wingtra\WingtraPilotProjects\100622 Trip", # LM2, LPM, MM, MPM
    #r"Z:\JTM\Wingtra\WingtraPilotProjects\090822 Trip" #  UM1, UM2
    r"Z:\JTM\Wingtra\WingtraPilotProjects\090122 Trip", # MM, MPM, LPM
    #r"Z:\JTM\Wingtra\WingtraPilotProjects\081222 Trip" # LM2, LPM
    #r"Z:\JTM\Wingtra\WingtraPilotProjects\071922 Trip" # UM1, UM2
                           ]         # list of photo folders to process
defaults.psx_dict ={
    #"MM": r"Z:\ATD\Drone Data Processing\Metashape Processing\East_Troublesome\LPM_10_2023\LPM_2022_Surveys_One_Checked.psx" #for setup, {user tag: psx project filepath}
}

defaults.geoid = r"Z:\JTM\Metashape\us_noaa_g2018u0.tif"              # path to geoid file
defaults.dem_resolution = 0
defaults.ortho_resolution = 0
# ------------Alignment defaults -------------------------------------------------------
defaults.setup = False              # run MS_PSX_Setup.py
defaults.pcbuild = False            # run MS_Build_PointCloud.py
defaults.build = False             # run MS_Build_Products.py
defaults.align = False              # run image alignment

defaults.alignment_params = {
        "downscale": 1, # 0 = Highest, 1 = High, 2 = Medium, 3 = Low, 4 = Lowest
        "generic_preselection": True, # Default is True, speeds up alignment
        "reference_preselection": True, #Default is True, reference preselection enabled
        #Commented out below because it is already set to default parameter and Python can't pickle the Metashape.ReferencePreselectionSource object
        #"reference_preselection_mode": Metashape.ReferencePreselectionSource, # Source uses reference coordinates
        "filter_mask": False,
        "mask_tiepoints": True,
        "filter_stationary_points": True,
        "keypoint_limit": 60000, #Default = 40000, 60000 for high quality images 
        "keypoint_limit_per_mpx": 1000,
        "tiepoint_limit": 10000, #Default = 4000, 10000 for high quality images
        "keep_keypoints": False,
        "guided_matching": True,
        "reset_matches": True,
        "subdivide_task": True,
        "workitem_size_cameras": 20,
        "workitem_size_pairs": 80,
        "max_workgroup_size": 100
    }

defaults.cam_opt_param = {
        "cal_f": True,
        "cal_cx": True,
        "cal_cy": True,
        "cal_b1": False,
        "cal_b2": False,
        "cal_k1": True,
        "cal_k2": True,
        "cal_k3": True,
        "cal_k4": False,
        "cal_p1": True,
        "cal_p2": True,
        "cal_p3": False,
        "cal_p4": False,
        "adaptive_fitting": False,
        "tiepoint_covariance": True,
        "fit_corrections": True
    }


# ------------Reconstruction Uncertainty (ru) defaults ---------------------------------
defaults.ru = False                 # run ru gradual selection iterations
defaults.ru_filt_level = 10         # ru gradual selection filter level (default=10, optimum value: [10 - 15])


# ------------Projection Accuracy (pa) defaults ---------------------------------------
defaults.pa = False                 # run pa gradual selection iterations
defaults.pa_filt_level = 3          # pa gradual selection filter level (default=3, optimum value: [2-4])

# ------------Reprojection Error (re) defaults -----------------------------------------
defaults.re = False                 # run re gradual selection iterations
defaults.re_filt_level = 0.3        # re gradual selection filter level (default=0.3, optimum value: [0.3])
defaults.re_round1_opt = 30          # max number of camera optimization iterations in round 1 (default=5)
defaults.re_round2_opt = 12          # max number of camera optimization iterations in round 2 (default=5)
defaults.re_round2_TPA = 0.1
defaults.re_RMSE_goal = 0.18

# adjust camera optimization parameters when RE level is below threshold
defaults.re_adapt = False            # enable adaptive camera opt params (default=True)


# ------------Process logging defaults ------------------------------------------------
defaults.log = True
# logfile name. Set to 'default.txt' to have output file named X_ProcessingLog.txt, where X=name of Metashape project
defaults.proclogname = 'default.txt'

# ------------ru, pa, re iteration defaults -------------------------------------------
# Only change these if you know what you're doing.-------------------------------------
defaults.ru_cutoff = 0.50           # percentage of points removed in single RU iteration [0.50]
defaults.pa_cutoff = 0.50           # percentage of points removed in single PA iteration [0.50]
defaults.re_cutoff = 0.10           # percentage of points removed in single RE iteration [0.10]
# Changing these values may result in infinite loops
defaults.ru_increment = 1           # increment by which RU filter advanced when finding RU level to select ru_cutoff percentage [1]
defaults.pa_increment = 0.2         # increment by which PA filter advanced when finding PA level to select pa_cutoff percentage [0.2]
defaults.re_increment = 0.01        # increment by which RE filter advanced when finding RE level to select re_cutoff percentage [0.01]

#-------------------Build Products defaults--------------------------------------------
defaults.maxconf = 2               # max confidence level for dense cloud filtering [2]

parg = cp.deepcopy(defaults)