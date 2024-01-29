
#script to test commands in Metashape
import Metashape

doc = Metashape.app.document
chunk = doc.chunk

print(chunk.elevations)