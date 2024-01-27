import Metashape
from MS_WIngtra_Workflow import activate_chunk

doc = Metashape.app.document
psx = doc.path
doc.open(psx)
chunk_label_list = [chunk.label for chunk in doc.chunks]
# Get last chunk in list
chunk = activate_chunk(doc, chunk_label_list[-1])
chunk = doc.chunk
print(chunk.label)