import csv
import math

# Define the input and output file paths
input_file_path = r"Z:\ATD\Drone Data Processing\Metashape Processing\East_Troublesome\MM_all_102023_pt_prec.txt"
output_file_path = 'output_file_with_rms.tsv'

# Initialize sums for calculating RMS
sum_sq_x, sum_sq_y, sum_sq_z = 0, 0, 0
count = 0

# Open the input file for reading and the output file for writing
with open(input_file_path, 'r', newline='') as infile, open(output_file_path, 'w', newline='') as outfile:
    # Create a CSV reader and writer with tab delimiter
    reader = csv.DictReader(infile, delimiter='\t')
    fieldnames = reader.fieldnames  # No need to add new fields for RMS in the output file
    writer = csv.DictWriter(outfile, fieldnames=fieldnames, delimiter='\t')
    
    # Write the header to the output file
    writer.writeheader()
    
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
        writer.writerow(row)

#Average of the squared standard deviations
avg_sq_x = sum_sq_x / count
avg_sq_y = sum_sq_y / count
avg_sq_z = sum_sq_z / count

print(f"Average of the squared standard deviations:")
print(f"X: {avg_sq_x}")
print(f"Y: {avg_sq_y}")
print(f"Z: {avg_sq_z}")