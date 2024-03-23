import Metashape
import os

doc = Metashape.app.document
chunk = doc.chunk
group_name = "Group 2"


    
def setup_psx(flight_folder_dict):
    # Open the Metashape document

    doc = Metashape.app.document
    # Initialize an empty dictionary
    chunk = doc.chunk
    if chunk.label == "Raw_Photos":
        chunk = chunk
    else:
        chunk = chunk.copy()
        chunk.label = "Raw_Photos"
    # Iterate through each flight folder
    group_dict ={}

    for group_name, flight_folder in flight_folder_dict.items():
        if any([camera_group.label == group_name for camera_group in chunk.camera_groups]):
            pass
        else:
            current_group = chunk.addCameraGroup()
            current_group.label = group_name
        if group_name not in group_dict:
            if not group_dict:
                group_dict[group_name] = 0
            else:
                group_dict[group_name] = max(group_dict.values()) + 1
        # Walk through the subdirectories and files in the flight_folder
        for root, dirs, files in os.walk(flight_folder):
            # Identify subdirectories that contain "100" in their name
            photo_dirs = [d for d in dirs if "100" in d]
            for photo_dir in photo_dirs:
                # Construct the full path to the photo directory
                full_photo_dir_path = os.path.join(root, photo_dir)
                # List all photos in the directory
                photos = [os.path.join(full_photo_dir_path, f) for f in os.listdir(full_photo_dir_path) if f.lower().endswith(('.jpg', '.jpeg', '.png'))]
                cameras = chunk.cameras
                #check if the photo is already in the chunk
                if len(photos) > 0:
                    for photo in photos:
                        photoname = os.path.basename(photo).split(".")[0]
                        for camera in cameras:
                            if camera.label == photoname:
                                print(f"Photo {photoname} is already in the chunk.")
                                photos.remove(photo)
                if len(photos) > 0:
                    chunk.addPhotos(photos, group=group_dict[group_name])
                    print(f"Loading photos from {full_photo_dir_path} into {group_name} group.")
    return chunk

def main():

    flight_folder_dict = {
        "060422" : r"Z:\LAH\Drone Projects\Bennett\ME\ME 6422",
    }

    setup_psx(flight_folder_dict)

    
if __name__ == "__main__":
    main()




