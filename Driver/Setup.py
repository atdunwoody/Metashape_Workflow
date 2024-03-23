
import Metashape
import os
import re


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


def align_images(chunk, alignment_params):
    """
    Align images in the specified Metashape chunk.

    Parameters:
        chunk (Metashape.Chunk): The chunk containing the images to be aligned.
    """

    # Perform image matching and alignment
    chunk.matchPhotos(**alignment_params)
    chunk.alignCameras()
    print(f"Images in chunk '{chunk.label}' have been aligned.")


def setup_psx(user_tags, flight_folder_list, doc, load_photos = True):

    # Initialize an empty dictionary
    tag_dict = {}
    group_dict = {}
    # Regular expression pattern to match the text before "Flight"
    pattern = re.compile(r'(.+?)\s*Flight\s*\d+')

    geo_ref_list =[]
    if load_photos:
        orig_chunk = doc.chunk
        chunk = orig_chunk.copy()
        chunk.label = "Raw_Photos"
    chunk = doc.chunk
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
    pass

if __name__ == "__main__":
    main()