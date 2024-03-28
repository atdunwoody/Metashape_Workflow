import Metashape
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

def setup_psx(user_tag, flight_folder_dict, psx):
    
    #Open the Metashape document
    
    doc = Metashape.app.document
    doc.open(psx)
    group_dict = {}
    chunk = doc.chunk
    if chunk.label == "Raw_Photos":
        chunk = doc.chunk
    else:
        chunk = chunk.copy()
        chunk.label = "Raw_Photos"
        
    for group_info, flight_folder in flight_folder_dict.items():
        group_name = group_info[0]
        if user_tag not in group_info[1]:
            continue
        folders = find_folders_with_tag(flight_folder, user_tag)
        photos_in_folder = find_jpgs_in_output_folders(folders)
        if group_name not in group_dict:
            if not group_dict:
                group_dict[group_name] = 0
            else:
                group_dict[group_name] = max(group_dict.values()) + 1
            current_group = chunk.addCameraGroup()
            current_group.label = group_name
            
        print(f"Adding photos from {flight_folder} with tag {user_tag} to group {group_name}")
        print(f"Current group: {group_dict[group_name]}")
        photos_in_chunk = [photo.label for photo in chunk.cameras]
        photos_to_load = [photo for photo in photos_in_folder if photo not in photos_in_chunk]
        chunk.addPhotos(photos_to_load, group=group_dict[group_name]) if photos_to_load else None
        doc.save()
    return chunk
                        
   

def main():

    psx_dict ={
    "LM2" : r"Z:\ATD\Drone Data Processing\Metashape Processing\East_Troublesome\LM2_10_2023\LM2_2023.psx",
    "MPM" : r"Z:\ATD\Drone Data Processing\Metashape Processing\East_Troublesome\MPM_10_2023\MPM_2023.psx",
    "UM1" : r"Z:\ATD\Drone Data Processing\Metashape Processing\East_Troublesome\UM1_10_2023\UM1_2023.psx",
    #"UM2" : r"Z:\ATD\Drone Data Processing\Metashape Processing\East_Troublesome\UM2_10_2023\UM2_2023.psx",
    }
    flight_folder_dict = {
            ('102123', ('LM2', 'LPM', 'MM', 'MPM', 'UM1', 'UM2')) : r"Z:\ATD\Drone Data Processing\Drone Images\East_Troublesome\Flights\102123", # LM2, LPM, MM, MPM, UM1, UM2
            ('070923', ('LM2', 'LPM', 'MM', 'MPM', 'UM1', 'UM2')) : r"Z:\JTM\Wingtra\WingtraPilotProjects\070923 Trip", # LM2, LPM, MM, MPM, UM1, UM2
            #r"Z:\JTM\Wingtra\WingtraPilotProjects\053123 Trip", # Don't Use 
            ('100622', ('LM2', 'LPM', 'MM', 'MPM')) : r"Z:\JTM\Wingtra\WingtraPilotProjects\100622 Trip", # LM2, LPM, MM, MPM
            ('090822', ('UM1', 'UM2')) : r"Z:\JTM\Wingtra\WingtraPilotProjects\090822 Trip", #  UM1, UM2
            ('090122', ('MM', 'MPM', 'LPM')) : r"Z:\JTM\Wingtra\WingtraPilotProjects\090122 Trip", # MM, MPM, LPM
            ('081222', ('LM2', 'LPM')) : r"Z:\JTM\Wingtra\WingtraPilotProjects\081222 Trip", # LM2, LPM
            ('071922', ('UM2')) : r"Z:\JTM\Wingtra\WingtraPilotProjects\071922 Trip", # UM1, UM2
    }
    
    for user_tag, psx in psx_dict.items():
        setup_psx(user_tag, flight_folder_dict, psx)
        
if __name__ == "__main__":
    main()



