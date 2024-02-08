import Metashape




yaw = -1.3782637119293213 # Yaw in degrees
pitch = -0.027668341078037673 # Pitch in degrees
roll = -0.069545872509479523# Roll in degrees
vect = Metashape.Vector( (yaw, pitch, roll) )
mat = Metashape.Utils.ypr2mat(vect)

opk_vect = Metashape.Utils.mat2opk(mat) 
print(opk_vect)