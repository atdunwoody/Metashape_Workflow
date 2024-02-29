import Metashape, math

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

    estimated_geoc = chunk.transform.matrix.mulp(camera.center)
    error = chunk.crs.unproject(camera.reference.location) - estimated_geoc
    error = error.norm()
    sums += error**2
    num += 1
print(math.sqrt(sums / num))