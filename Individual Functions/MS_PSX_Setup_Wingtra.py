
import os
import re
import Metashape


def setup_psx(user_tags, flight_folder_list, psx, load_photos = True):
    
    #Open the Metashape document
    
    doc = Metashape.app.document
    doc.open(psx)
    # Initialize an empty dictionary
    tag_dict = {}
    group_dict = {}
    # Regular expression pattern to match the text before "Flight"
    pattern = re.compile(r'(.+?)\s*Flight\s*\d+')

    geo_ref_list =[]
    
    orig_chunk = doc.chunk
    chunk = chunk.copy()
    chunk.label = "Raw_Photos"
    for flight_folder in flight_folder_list:
        # Walk through the subdirectories
        for subdir, dirs, _ in os.walk(flight_folder):
            if "OUTPUT" in dirs:
                # Extract group name using regular expression
                match = pattern.search(os.path.basename(subdir))
                temp_name =os.path.basename(subdir)
                if match:
                    group_name = match.group(1).strip()  # Get the matched group and strip whitespace
                    ref_name = temp_name + ' geotags.csv'    # Check if the group name starts with any of the user-specified tags
                    
                    if any(group_name.startswith(tag) for tag in user_tags):
                        if group_name not in tag_dict:
                            tag_dict[group_name] = []
                        tag_dict[group_name].append(subdir)

                        # Process further if needed, e.g., add photos
                        output_dir = os.path.join(subdir, "OUTPUT")
                        if load_photos:
                            photos = [os.path.join(output_dir, f) for f in os.listdir(output_dir) if f.lower().endswith(('.jpg', '.jpeg', '.png'))]
                            if group_name not in group_dict:
                                ##check if group_dict is empty
                                if not group_dict:
                                    group_dict[group_name] = 0
                                else:
                                    group_dict[group_name] = max(group_dict.values()) + 1
                                current_group = chunk.addCameraGroup()
                                current_group.label = group_name
                            # Here you might want to add photos to the Metashape chunk
                            print(f"Adding photos from {output_dir} to group {group_name}")
                            chunk.addPhotos(photos, group=group_dict[group_name])
                            
                        geo_ref_list.append(os.path.join(output_dir, ref_name))
                        chunk = doc.chunk
    return geo_ref_list, chunk
                        

def main():
    doc = Metashape.app.document
    chunk = doc.chunk
    user_tags = ['LM2']
    output_dir = r"Z:\ATD\Drone Data Processing\Drone Images\East_Troublesome"
    flight_folder_list = [r"Z:\ATD\Drone Data Processing\Drone Images\East_Troublesome", r"Z:\JTM\Wingtra\WingtraPilotProjects\100622 Trip"]
    
    
if __name__ == "__main__":
    main()



