import numpy as np

def compute_rotation_matrix(yaw, pitch, roll):
    # Convert angles from degrees to radians
    psi = np.radians(yaw)
    theta = np.radians(pitch)
    phi = np.radians(roll)

    # Rotation matrices for yaw (psi), pitch (theta), and roll (phi)
    Rz = np.array([[np.cos(psi), -np.sin(psi), 0],
                   [np.sin(psi),  np.cos(psi), 0],
                   [0, 0, 1]])

    Ry = np.array([[np.cos(theta), 0, np.sin(theta)],
                   [0, 1, 0],
                   [-np.sin(theta), 0, np.cos(theta)]])

    Rx = np.array([[1, 0, 0],
                   [0, np.cos(phi), -np.sin(phi)],
                   [0, np.sin(phi),  np.cos(phi)]])

    # Combined rotation matrix C_n_b
    C_n_b = Rz.dot(Ry).dot(Rx)
    return C_n_b

def ypr_to_opk(yaw, pitch, roll):
    # Compute the YPR rotation matrix
    C_n_b = compute_rotation_matrix(yaw, pitch, roll)

    # Assuming C_E_B = C_n_b for this transformation (simplification)
    # Extract OPK angles from the rotation matrix
    omega = np.arcsin(C_n_b[0, 2])
    phi = np.arctan2(-C_n_b[1, 2], C_n_b[2, 2])
    kappa = np.arctan2(C_n_b[0, 1], C_n_b[0, 0])

    # Convert OPK angles from radians to degrees
    omega_deg = np.degrees(omega)
    phi_deg = np.degrees(phi)
    kappa_deg = np.degrees(kappa)

    return omega_deg, phi_deg, kappa_deg

ypr =[1.853051662440684,-0.14336860460805362, 0.02338354103267193]

print(f"Yaw: {ypr[0]} rad, Pitch: {ypr[1]} rad, Roll: {ypr[2]} rad")

yaw = np.degrees(ypr[0]) # Yaw in degrees
pitch = np.degrees(ypr[1]) # Pitch in degrees
roll = np.degrees(ypr[2]) # Roll in degrees

omega, phi, kappa = ypr_to_opk(yaw, pitch, roll)

#print with formatted degree symbol
print(f"Omega: {omega}°, Phi: {phi}°, Kappa: {kappa}°")

