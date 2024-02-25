import Metashape
import math
import csv

ypr = [72.66743443,	-1.81625184,	-3.60504727]

print("Yaw (rad): ", ypr[0], "Pitch (rad): ", ypr[1], "Roll (rad): ", ypr[2])

vect = Metashape.Vector( ypr)
mat = Metashape.Utils.ypr2mat(vect)

opk_vect = Metashape.Utils.mat2opk(mat) 
opk_vect = opk_vect

omega = opk_vect[0] 
phi = opk_vect[1]
kappa = opk_vect[2]

print("Omega (deg): ", omega, "Phi (deg): ", phi, "Kappa (deg): ", kappa)

mat = Metashape.Utils.opk2mat(opk_vect)
ypr_vect = Metashape.Utils.mat2ypr(mat)

print("Yaw (rad): ", ypr_vect[0], "Pitch (rad): ", ypr_vect[1], "Roll (rad): ", ypr_vect[2])