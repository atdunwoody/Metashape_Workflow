import Metashape

def point_inside(point, poly):

	x, y = point.x, point.y
	inside = False

	p1x, p1y = poly[0]
	for i in range(len(poly) + 1):
		p2x, p2y = poly[i % len(poly)]
		if y >= min(p1y, p2y):
			if y <= max(p1y, p2y):
				if x <= max(p1x, p2x):
					if p1y != p2y:
						xinters = (y - p1y) * (p2x - p1x) / (p2y - p1y) + p1x
					if p1x == p2x or x <= xinters:
						inside = not inside
		p1x, p1y = p2x, p2y
	return inside

doc = Metashape.app.document
chunk = doc.chunk
shapes = chunk.shapes
crs = shapes.crs
T = chunk.transform.matrix
polygons = dict()

for shape in shapes:
	if not shape.selected: #skipping not selected shapes
		continue
	if shape.type == Metashape.Shape.Polygon:
		polygons[shape] = [[v.x, v.y] for v in shape.vertices]
		
for camera in chunk.cameras:
	camera.selected = True
	if not camera.transform:
		if camera.reference.location:
			camera_coord = crs.project(chunk.crs.unproject(camera.reference.location))
		else:
			continue
	else:
		camera_coord = crs.project(T.mulp(camera.center))
	for shape in polygons.keys():
		if point_inside(Metashape.Vector([camera_coord.x, camera_coord.y]), polygons[shape]):
			camera.selected = False

#Delete all selected cameras
chunk.remove(camera for camera in chunk.cameras if camera.selected)
			
print("Script finished")