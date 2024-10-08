import Metashape
import os
from datetime import datetime
import math


def calc_camera_error(chunk):
    chunk = Metashape.app.document.chunk #active chunk
    T = chunk.transform.matrix
    crs = chunk.crs
    sums = 0
    num = 0
    for camera in chunk.cameras:
        if not camera.transform:
            continue
        if not camera.reference.location:
            continue
        if not camera.reference.enabled:
            continue
        estimated_geoc = chunk.transform.matrix.mulp(camera.center)
        error = chunk.crs.unproject(camera.reference.location) - estimated_geoc
        error = error.norm()
        sums += error**2
        num += 1
    if num > 0: return math.sqrt(sums / num) 
    else: return 0

def calc_camera_accuracy(chunk):
    # Returns the average vertical accuracy of the camera reference locations in the chunk
    chunk = Metashape.app.document.chunk #active chunk
    sums = 0
    num = 0
    for camera in chunk.cameras:
        if not camera.transform:
            continue
        if not camera.reference.location:
            continue
        if not camera.reference.enabled:
            continue
        if not camera.reference.accuracy:
            continue
        camera_acc = camera.reference.accuracy[2] # Change index to 0 and 1 for lateral accuracy
        sums += camera_acc
        num += 1
    if num > 0: return sums / num
    else: return 0

def calc_RMS_error(chunk):
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
     if num > 0: return sigma
     else: return 0

def main():
    pass

if __name__ == "__main__":
    main()
    
