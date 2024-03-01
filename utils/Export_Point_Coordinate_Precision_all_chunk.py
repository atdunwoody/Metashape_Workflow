import Metashape
import csv
import math

# For use with Metashape Pro v.1.5
#
# Python script associated with James et al. - 
# Mitigating systematic error in topographic models for geomorphic change detection:
# Accuracy, precision and considerations beyond off-nadir imagery, Earth Surf. Proc. Landforms
# 
# This script uses Metashape's point coordinate variance estimates to provide oriented and scaled
# point coordinate precision estimates, exported as a text file. 
#
# The text file is saved in the same directory as the Metashape project, with the project file 
# name appended with '_pt_prec.txt'. The file is tab-separated, with one header row and columns:
# X(m) Y(m) Z(m) sX(mm) sY(mm) sZ(mm) covXX(m2) covXY(m2) covXZ(m2) covYY(m2) covYZ(m2) covZZ(m2)
# Where:	X, Y, Z are point coordinates
#			sX, sY, xZ are point coordinate precisions, and
#			cov... are point coordinate covariances.
# Note that units are assumed to be metric, and are as given above (and in the file header line).
#
# Running this script resets the project region to default values.
# 
# Tested and used in PhotoScan Pro v.1.5.0
# Thanks to Paul Pelletier (pap1956@gmail.com) for correcting errors in an early version of this script 
# and (in conjunction with Alexey Pasumansky) for providing the coordinate system transformation code.
# 
# Author: Mike James, Lancaster University, U.K.
# Contact: m.james at lancaster.ac.uk
# Updates: Check http://tinyurl.com/sfmgeoref


doc = Metashape.app.document
chunk = doc.chunk

#list of chunks
for chunk in doc.chunks[-6:]:		
	chunk_name = chunk.label[12:]
	#check if label starts with "Raw_Photos" or "Chunk 1
	if chunk_name != "Raw_Photos" and chunk_name != "Chunk 1":
		try:
			points = chunk.tie_points.points
		except:
			continue
		point_proj = chunk.tie_points.projections


		out_path = doc.path[0:(len(doc.path)-4)] + '_' + chunk_name + '_pt_prec.txt'

		# Get transforms to account for real-world coordinate system (CRS)
		# Note, this resets the region to the default
		M = chunk.transform.matrix
		region = chunk.region
		T = chunk.crs.localframe(M.mulp(chunk.region.center)) * M
		if chunk.transform.scale:
			R = chunk.transform.scale * T.rotation()
		else:
			R = T.rotation()
   
		print(f"Exporting precision estimates for {chunk_name} to {out_path}")
		# Open the output file and write the precision estimates to file
		with open(out_path, "w") as fid:
			# Open the output file
			fwriter = csv.writer(fid, delimiter='\t', lineterminator='\n')
			
			# Write the header line
			fwriter.writerow( [	'X(m)', 'Y(m)', 'Z(m)', 'sX(mm)', 'sY(mm)', 'sZ(mm)',
								'covXX(m2)', 'covXY(m2)', 'covXZ(m2)', 'covYY(m2)', 'covYZ(m2)', 'covZZ(m2)'] )					

			# Iterate through all valid points, writing a line to the file for each point
			for point in points:
				if not point.valid:
					continue
				
				# Transform the point coordinates into the output local coordinate system
				if chunk.crs:
					V = M * (point.coord)
					V.size = 3
					pt_coord = chunk.crs.project(V)
				else:
					V = M * (point.coord)
					V.size = 3
					pt_coord = V

				# Transform the point covariance matrix into the output local coordinate system
				pt_covars = R * point.cov * R.t()

				# Write the line of coordinates, precisions and covariances to the text file
				fwriter.writerow( [ 
					'{0:0.5f}'.format( pt_coord[0] ), '{0:0.5f}'.format( pt_coord[1] ), '{0:0.5f}'.format( pt_coord[2] ),
					'{0:0.7f}'.format( math.sqrt(pt_covars[0, 0])*1000 ), '{0:0.7f}'.format( math.sqrt(pt_covars[1,1])*1000 ), '{0:0.7f}'.format( math.sqrt(pt_covars[2, 2] )*1000),
					'{0:0.9f}'.format( pt_covars[0, 0] ), '{0:0.9f}'.format( pt_covars[0, 1] ), '{0:0.9f}'.format( pt_covars[0, 2] ),
					'{0:0.9f}'.format( pt_covars[1, 1] ), '{0:0.9f}'.format( pt_covars[1, 2] ), '{0:0.9f}'.format( pt_covars[2, 2] ) ] )

						
			# Close the text file
			fid.close()