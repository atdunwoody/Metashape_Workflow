import Metashape

# Define the chunks
doc = Metashape.app.document
chunk = doc.chunk

main_chunk = doc.chunks[4]  # The main chunk
operand_chunk = doc.chunks[5]  # The chunk to subtract from

# Print out information on the chunk
print("Main chunk: ", main_chunk.label)
print("Operand chunk: ", operand_chunk.label)

# Check available methods and attributes for chunk and transformRaster
print("Methods in main_chunk: ", dir(main_chunk))  # Inspect all available methods and properties

# Check the available methods in the Metashape module
print("Methods in Metashape: ", dir(Metashape))

# Get detailed information about transformRaster method
print(help(main_chunk.transformRaster))  # This will show the docstring for transformRaster if available
