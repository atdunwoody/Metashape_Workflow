
import json
import csv

# Load the raw data from the file
jfile = r"Z:\ATD\Metashape_Alignment_Tests\Only_Checking_Initial_Photos\Test\MM_102123 Flight 01.geotaglog"
csv_fn = r"Z:\ATD\Metashape_Alignment_Tests\Only_Checking_Initial_Photos\Test\MM_102123 Flight 01.csv"
with open(jfile, 'r') as file:
    data = json.load(file)
    images = data['images']  # Access the list of images

# Open a new CSV file for writing the converted data
with open(csv_fn, 'w', newline='') as csvfile:
    fieldnames = ['image name', 'longitude [decimal degrees]', 'latitude [decimal degrees]', 'altitude [meter]',
                  'yaw [degrees]', 'pitch [degrees]', 'roll [degrees]', 'accuracy horizontal [meter]',
                  'accuracy vertical [meter]']
    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
    
    # Write the header row
    writer.writeheader()

    # Iterate over each image in the list
    for item in images:
        geo_ref = item['geotaggedImage']['geoRef']
        coordinate = geo_ref['coordinate']
        writer.writerow({
            'image name': item['imageName'],
            'longitude [decimal degrees]': coordinate[1],
            'latitude [decimal degrees]': coordinate[0],
            'altitude [meter]': coordinate[2],
            'yaw [degrees]': geo_ref['yaw'],
            'pitch [degrees]': geo_ref['pitch'],
            'roll [degrees]': geo_ref['roll'],
            'accuracy horizontal [meter]': geo_ref['hAccuracy'],
            'accuracy vertical [meter]': geo_ref['vAccuracy']
        })