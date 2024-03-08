import Metashape
import math
doc = Metashape.app.document
chunk_list = doc.chunks

for chunk in chunk_list:
        metadata = chunk.meta
        SEUW = metadata['OptimizeCameras/sigma0']
        print(f"SEUW: {SEUW} for chunk {chunk.label}")

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
        #check if camera is selected
        if not camera.reference.enabled:
            continue
        camera_acc = camera.reference.accuracy[2] # Change index to 0 and 1 for lateral accuracy
        sums += camera_acc
        num += 1
    if num == 0:
        print("No cameras selected")
        return 0    
    return sums / num

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
        #check if camera is selected
        if not camera.reference.enabled:
            continue
        estimated_geoc = chunk.transform.matrix.mulp(camera.center)
        error = chunk.crs.unproject(camera.reference.location) - estimated_geoc
        error = error.norm()
        sums += error**2
        num += 1
    if num == 0:
        print("No cameras selected")
        return 0    
    return math.sqrt(sums / num)

print(f"Camera accuracy: {calc_camera_accuracy(chunk)}")
print(f"Camera error: {calc_camera_error(chunk)}")
