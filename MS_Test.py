psx_dict ={
    # 'LPM': r"Z:\JTM\Wingtra\WingtraPilotProjects\WingtraPilotProjects.psx", #for setup, {user tag: psx project filepath}
}

if len(psx_dict) == 0:
    psx_dict = {'_': 'Dummy'}
    print(len(psx_dict))
    print(psx_dict)

for key, value in psx_dict.items():
    print(key, value)