import Metashape
import math

ypr = [-1.6394716501235962,-0.072235397078270369, 0.027110883966088295]

print("Yaw (rad): ", ypr[0], "Pitch (rad): ", ypr[1], "Roll (rad): ", ypr[2])

yaw = ypr[0] * 180 / math.pi # Yaw in degrees
pitch = ypr[1] * 180 / math.pi # Pitch in degrees
roll = ypr[2] * 180 / math.pi # Roll in degrees

print("Yaw (deg): ", yaw, "Pitch (deg): ", pitch, "Roll (deg): ", roll)

vect = Metashape.Vector( (yaw, pitch, roll) )
mat = Metashape.Utils.ypr2mat(vect)

opk_vect = Metashape.Utils.mat2opk(mat) 
opk_vect = opk_vect

omega = opk_vect[0] 
phi = opk_vect[1]
kappa = opk_vect[2]

print("Omega (deg): ", omega, "Phi (deg): ", phi, "Kappa (deg): ", kappa)