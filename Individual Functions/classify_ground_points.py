import Metashape


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

def classify_ground_points(chunk, params):
    # Set classification parameters
    max_angle = params.get('max_angle', 15)
    max_distance = params.get('max_distance', 1.0)
    max_terrain_slope = params.get('max_terrain_slope', 5)
    cell_size = params.get('cell_size', 10)
    erosion_radius = params.get('erosion_radius', 5)
    
    # Perform ground point classification
    chunk.point_cloud.classifyGroundPoints(max_angle=max_angle, 
                                           max_distance=max_distance,
                                           max_terrain_slope=max_terrain_slope,
                                           cell_size=cell_size, 
                                           erosion_radius=erosion_radius)

def duplicate_chunk(doc, chunk_index, params):
    chunk = doc.chunks[chunk_index]

    # Duplicate the chunk
    new_chunk = chunk.copy()

    # Create a name for the chunk based on the parameters
    chunk_name = (
        f"Chunk_{chunk_index}_Angle_{params['max_angle']}_Dist_{params['max_distance']}_"
        f"Slope_{params['max_terrain_slope']}_Cell_{params['cell_size']}_"
        f"Ero_{params['erosion_radius']}"
    )
    new_chunk.label = chunk_name

    return new_chunk

def main():
    # Specify the Metashape project file path
    project_path = r"Y:\ATD\Drone Data Processing\Metashape_Processing\Bennett\062023-062022\UE\UE_062023-062022_Ground_Classification.psx"

    # Specify the output log file path (optional)
    log_file_path = r"Y:\ATD\Drone Data Processing\Metashape_Processing\Bennett\062023-062022\UE\UE_062023-062022_Ground_Classification_log.txt"
    
    # Load the project
    doc = Metashape.app.document
    doc.save()
    doc.open(project_path)

    # Select the original chunk to work on
    original_chunk_list = [0,1]  # Change this index if you have multiple chunks
    for original_chunk_index in original_chunk_list:
        # Define parameter ranges
        max_angle_range = [10, 15, 20]
        max_distance_range = [1.0, 1.5, 2]
        max_terrain_slope_range = [10, 20, 30]
        cell_size_range = [5, 10, 15]
        erosion_radius_range = [0, 1, 3]
        
        # Iterate over parameter combinations
        for max_angle in max_angle_range:
            for max_distance in max_distance_range:
                for max_terrain_slope in max_terrain_slope_range:
                    for cell_size in cell_size_range:
                        for erosion_radius in erosion_radius_range:
                            params = {
                                'max_angle': max_angle,
                                'max_distance': max_distance,
                                'max_terrain_slope': max_terrain_slope,
                                'cell_size': cell_size,
                                'erosion_radius': erosion_radius
                            }

                            # Duplicate the original chunk and classify ground points
                            #check if chunk already exists
                            chunk_exists = False
                            chunk_label = f"Chunk_{original_chunk_index}_Angle_{params['max_angle']}_Dist_{params['max_distance']}_Slope_{params['max_terrain_slope']}_Cell_{params['cell_size']}_Ero_{params['erosion_radius']}"
                            for chunk in doc.chunks:
                                if chunk.label == chunk_label:
                                    chunk_exists = True
                            if chunk_exists == False:
                                new_chunk = duplicate_chunk(doc, original_chunk_index, params)
                            else:
                                new_chunk = activate_chunk(doc, chunk_label)
                            classify_ground_points(new_chunk, params)
                            new_chunk.removePoints([Metashape.PointClass.Unclassified])
                            # Log the parameters used (optional)
                            with open(log_file_path, 'a') as log_file:
                                log_file.write(f"Classified in {new_chunk.label} with params: {params}\n")

        # Save the project after classification
        doc.save()

if __name__ == "__main__":
    main()
