import Metashape

doc = Metashape.app.document
chunk_list = doc.chunks

for chunk in chunk_list:
        metadata = chunk.meta
        SEUW = metadata['OptimizeCameras/sigma0']
        print(f"SEUW: {SEUW} for chunk {chunk.label}")