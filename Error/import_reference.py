import Metashape
import os
import csv

# Function to read the header of the CSV file and return the setup string based on the second column
def get_setup_string_for_csv(path):
    with open(path, newline='') as csvfile:
        reader = csv.reader(csvfile)
        header = next(reader)  # Read the first row to get the header

        # Check if the second column header starts with "latitude" or "longitude" and set the setup_string accordingly
        if header[1].lower().startswith("latitude"):
            setup_string = 'nyxzabc[XY]Z'
        elif header[1].lower().startswith("longitude"):
            setup_string = 'nxyzabc[XY]Z'
        else:
            setup_string = ''  # Default or error case, adapt as necessary

    return setup_string

# Metashape document and chunk
doc = Metashape.app.document
chunk = doc.chunk

# Paths to the CSV files
path = r"Z:\ATD\Metashape_Alignment_Tests\Only_Checking_Initial_Photos\Test\MM_102123 Flight 01.csv"
path1 = r"Z:\ATD\Metashape_Alignment_Tests\Only_Checking_Initial_Photos\Test\MM_102123 Flight 02.csv"

# Get the setup string for the first CSV file
setup_string = get_setup_string_for_csv(path)

# Import reference data using the setup string
if setup_string:  # Ensure setup_string is not empty
    chunk.importReference(path, format=Metashape.ReferenceFormatCSV, skip_rows=1, columns=setup_string, delimiter=',')

