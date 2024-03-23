import Metashape
import os
import re
from datetime import datetime
import argparse
import copy as cp
import math

def parse_command_line_args(parg, doc):
    """
    Parse command line arguments with argparse.
        args:
            parg: default Arg object with all defined defaults
        returns:
            parg: parsed Arg object with all args formatted.
    """


    # ===========================  BEGIN PARSER ==============================
    descriptionstr = ('  Script to run Metashape image alignment, and conduct gradual selection of sparse tiepoints. '
                      'Script begins on chunk designated by optional "'"-chunk"'" argument. If no chunk is designated, '
                      'the currently active chunk is used. Each operation creates a new chunk. The initial chunk is '
                      'copied to a new chunk and given a suffix of "'"_Align"'", "'"_RU"'", "'"_PA"'", or "'"_RE"'".')

    parser = argparse.ArgumentParser(description=descriptionstr, epilog='example: run Align_RuPaRe.py -chunk myChunk '
                                                                        '-align'
                                                                        '-ru -ru_level=11 '
                                                                        '-pa -pa_level=2 '
                                                                        '-re -re_level=0.3 '
                                                                        '-log my_output_logfile.txt')
    # =================== Chunk args ==========================================
    parser.add_argument('-chunk', '--initial_chunk', dest='initial_chunk', nargs='?', const=parg.initial_chunk,
                        type=str,
                        help='Initial chunk on which to perform process [default = currently active chunk]')
    #==================== Setup args ==========================================
    parser.add_argument('-setup', '--setup', dest='setup', default=False, action='store_true',
                        help='Setup project for processing [default=DISABLED].')
    #add output_dir argument that accepts filepath
    parser.add_argument('-export_dir', '--export_dir', dest='export_dir', nargs='?', const=parg.export_dir, type=str,
                        help='Output directory for DEM and Ortho products [default=project directory]')
    # =================== Alignment args ======================================
    parser.add_argument('-align', '--align_images', dest='align', default=False, action='store_true',
                        help='Align images [default=DISABLED].')

    # =================== RU args =============================================
    parser.add_argument('-ru', '--reconstruction_uncertainty', dest='ru', default=False, action='store_true',
                        help='Reconstruction Uncertainty [default=DISABLED]')

    parser.add_argument('-ru_level', '--reconstruction_uncertainty_level', dest='ru_level', nargs='?',
                        const=parg.ru_filt_level, type=float,
                        help='Reconstruction Uncertainty filter level, optimum value 10-15 [default=10]')

    # =================== PA args =============================================
    parser.add_argument('-pa', '--projection_accuracy', dest='pa', default=False, action='store_true',
                        help='Projection Accuracy [default=DISABLED]')

    parser.add_argument('-pa_level', '--projection_accuracy_level', dest='pa_level', nargs='?',
                        const=parg.pa_filt_level, type=float,
                        help='Projection Accuracy filter level, optimum value 2-4 [default=3]')

    # =================== RE args =============================================
    parser.add_argument('-re', '--reprojection_error', dest='re', default=False, action='store_true',
                        help='Reprojection Error, optimum value 0.3 [default=0.3]')

    parser.add_argument('-re_level', '--reprojection_error_level', dest='re_level', nargs='?',
                        const=parg.re_filt_level, type=float,
                        help='Projection Accuracy filter level, optimum value 2-4 [default=3]')

    parser.add_argument('-pcbuild', '--pcbuild', dest='pcbuild', default=False, action='store_true',
                    help='Build point cloud [default=DISABLED]')
    # =================== Export args =========================================
    parser.add_argument('-build', '--build', dest='build', default=False, action='store_true',
                        help='Build DEM and Ortho and Export results [default=DISABLED]')
    
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

    # align camera optimization parameters

    # -----------------RU arguments-----------------------
    if arglist.ru:
        # set ru to true
        parg.ru = True

    # RU filter level
    if arglist.ru_level is not None:
        parg.ru_filt_level = arglist.ru_level


    # -----------------PA arguments-----------------------
    if arglist.pa:
        # set pa to true
        parg.pa = True
    # Check if any -pa options called without -ru argument

    # PA filter level
    if arglist.pa_level is not None:
        parg.pa_filt_level = arglist.pa_level


    # -----------------RE arguments-----------------------
    if arglist.re:
        # set re to true
        parg.re = True
    # Check if any -re options called without -ru argument
    
    # RE filter level
    if arglist.re_level is not None:
        parg.re_filt_level = arglist.re_level

    if arglist.pcbuild:
        parg.pcbuild = True
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
        print('2. Alignment ENABLED with the following options:\n')
        #print every line in parg.alignment_params
        align_params = parg.alignment_params
        for key in align_params:
            print(f"    -{key}: {align_params[key]}")

    else:
        print('2. Alignment DISABLED.')

    # ru message
    if parg.ru:
        print('3. Reconstruction Uncertainty gradual selection ENABLED with the following options:\n'
              + '    -RU filter level = ' + str(parg.ru_filt_level) + '\n')
    else:
        print('3. Reconstruction Uncertainty gradual selection DISABLED.')

    # pa message
    if parg.pa:
        print('4. Projection Accuracy gradual selection ENABLED with the following options:\n'
              + '    -PA filter level = ' + str(parg.pa_filt_level) + '\n')
    else:
        print('4. Projection Accuracy gradual selection DISABLED.')

    # re message
    if parg.re:
        print('5. Reprojection Error gradual selection ENABLED with the following options:\n'
              + '    -RE filter level = ' + str(parg.re_filt_level) + '\n')
        
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
    
    if parg.pcbuild:
        print('8. Build Point Cloud ENABLED.')
    else:
        print('8. Build Point Cloud DISABLED.')
    
    if parg.build:
        print('9. Build ENABLED.')
    else:   
        print('9. Build DISABLED.')
        
    
    
    return parg

