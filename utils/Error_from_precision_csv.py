import csv
import math
import os

def calc_precision_error(input_file_path):
    # Initialize sums for calculating RMS
    sum_sq_x, sum_sq_y, sum_sq_z = 0, 0, 0
    count = 0

    # Open the input file for reading and the output file for writing
    with open(input_file_path, 'r', newline='') as infile:
        # Create a CSV reader and writer with tab delimiter
        reader = csv.DictReader(infile, delimiter='\t')
        fieldnames = reader.fieldnames  # No need to add new fields for RMS in the output file
        
        # Iterate through each row in the input file
        for row in reader:
            # Convert standard deviations from mm to meters for consistency with squared terms
            sX = float(row['sX(mm)']) / 1000
            sY = float(row['sY(mm)']) / 1000
            sZ = float(row['sZ(mm)']) / 1000
            
            count += 1  # Increment count for each point
            # Add the squared standard deviations to the running sums
            sum_sq_x += sX
            sum_sq_y += sY
            sum_sq_z += sZ
            # Write the original row to the output file

    #Average of the squared standard deviations
    avg_sq_x = sum_sq_x / count
    avg_sq_y = sum_sq_y / count
    avg_sq_z = sum_sq_z / count

    print(f"File: {input_file_path}")
    print(f"Average precision in X: {avg_sq_x}")
    print(f"Average precision in Y: {avg_sq_y}")
    print(f"Average precision in Z: {avg_sq_z}")
    result = [avg_sq_x, avg_sq_y, avg_sq_z]
    return result

input_folder = r"Z:\JTM\Metashape"
results_dict = {}

for file in os.listdir(input_folder):
    if file.endswith("_pt_prec.txt"):
        file_path = os.path.join(input_folder, file)
        results_dict[file] = calc_precision_error(file_path)
        
#Rank the results from smallest to largest z precision
sorted_results = sorted(results_dict.items(), key=lambda x: x[1][2])
print("\nSorted results")
print(sorted_results)

#Write the results to a CSV file
output_file = os.path.join(input_folder, "precision_results.csv")
with open(output_file, "w") as fid:
    fwriter = csv.writer(fid, delimiter=',', lineterminator='\n')
    fwriter.writerow(["File", "X Precision", "Y Precision", "Z Precision"])
    for key, value in sorted_results:
        fwriter.writerow([key] + value)