


import pandas as pd
from pyproj import Transformer

def convert_wgs84_to_nad83_utm13n(file_path, output_file):
    """
    Converts X(m), Y(m) points from WGS84 to NAD83 UTM Zone 13N.

    Parameters:
        file_path (str): The path to the input text file.

    Returns:
        pd.DataFrame: DataFrame with original data and converted coordinates.
    """
    # Read the data from the text file
    df = pd.read_csv(file_path, sep='\t')

    # Initialize the transformer from WGS84 to NAD83 UTM Zone 13N
    transformer = Transformer.from_crs("EPSG:4326", "EPSG:26913", always_xy=True)

    # Extract longitude and latitude from the DataFrame
    longitudes = df['X(m)'].values
    latitudes = df['Y(m)'].values

    # Perform the coordinate transformation
    eastings, northings = transformer.transform(longitudes, latitudes)

    # Add the converted coordinates to the DataFrame
    df['Easting(m)'] = eastings
    df['Northing(m)'] = northings

    # Write the DataFrame to a new text file
    df.to_csv(output_file, sep='\t', index=False)
    
    
    return df


def progress_callback(progress):
    if progress == -1:
        print("An error occurred during processing.")
    else:
        print(f"Progress: {progress}%")


if __name__ == '__main__':
    filename = r"Y:\ATD\Drone Data Processing\Metashape_Processing\East_Troublesome\072023 - 092022\LM2_072023_pt_prec.txt"  # Replace with your actual file path
    output_file = r"Y:\ATD\Drone Data Processing\Metashape_Processing\East_Troublesome\072023 - 092022\LM2_072023_pt_prec_nad83_utm13n.txt"
    #convert_wgs84_to_nad83_utm13n(filename, output_file)
    
    
    