import Metashape

doc = Metashape.app.document
chunk = doc.chunk

cameras = chunk.cameras

#check for duplicate labels in the chunk
camera_labels = [camera.label for camera in cameras]
if len(camera_labels) != len(set(camera_labels)):
    print("There are duplicate camera labels in the chunk.")