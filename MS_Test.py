import Metashape
import time, math

def calc_reprojection(chunk):
     tie_points= chunk.tie_points
     points = tie_points.points
     npoints = len(points)
     projections = chunk.tie_points.projections
     err_sum = 0
     num = 0
     maxe = 0

     point_ids = [-1] * len(tie_points.tracks)
     point_errors = dict()
     for point_id in range(0, npoints):
          point_ids[points[point_id].track_id] = point_id

     for camera in chunk.cameras:
          if not camera.transform:
               continue
          for proj in projections[camera]:
               track_id = proj.track_id
               point_id = point_ids[track_id]
               if point_id < 0:
                    continue
               point = points[point_id]
               if not point.valid:
                    continue
               error = camera.error(point.coord, proj.coord).norm() ** 2
               err_sum += error
               num += 1
               if point_id not in point_errors.keys():
                    point_errors[point_id] = [error]
               else:
                    point_errors[point_id].append(error)
               if error > maxe: maxe = error
				
     sigma = math.sqrt(err_sum / num)
     return (sigma, point_errors, maxe)

chunk = Metashape.app.document.chunk
t0 = time.time()
result = calc_reprojection(chunk)
print('RMS reprojection error (pix): ' + str(result[0]))
print("Max reprojection error (pix): " + str(math.sqrt(result[2])))
t0 = time.time() - t0
print("Script finished in " + "{:.2f}".format(float(t0)) + " seconds")