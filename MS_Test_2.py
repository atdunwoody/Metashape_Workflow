import os
import glob

def find_folders_with_tag(basepath, user_tag):
    matched_folders = []
    
    # Walk through the directory structure starting at basepath
    for root, dirs, files in os.walk(basepath):
        # Filter directories that contain the user_tag
        for dir in dirs:
            if user_tag in dir:
                # Construct the full path to the directory
                full_path = os.path.join(root, dir)
                # Add the full path to the list if it's not already included
                if full_path not in matched_folders:
                    matched_folders.append(full_path)

    return matched_folders


def find_jpgs_in_output_folders(folders):
    jpg_files = []
    
    # Iterate through the list of folders
    for folder in folders:
        # Construct the path to the "Output" subfolder
        output_folder = os.path.join(folder, "Output")
        
        # Use glob to find all jpg files in this "Output" folder
        for jpg_file in glob.glob(os.path.join(output_folder, "*.jpg")):
            # Add the jpg file to the list if it's not already included
            if jpg_file not in jpg_files:
                jpg_files.append(jpg_file)

    return jpg_files

basepath = r'Z:\ATD\Drone Data Processing\Drone Images\Bennett\Spring2023_Wingtra\Wingtra Photos'
user_tag = 'ME'
folders = find_folders_with_tag(basepath, user_tag)
jpg_files = find_jpgs_in_output_folders(folders)
