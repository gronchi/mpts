import MDSplus as mds
from scipy.io import savemat

for shot_number in range(35812, 35991):
    try:
        print(shot_number)
        tree = mds.Tree("mpts", shot_number)
        camera = tree.getNode("\\Phantom1")
        data1 = camera.SIGNAL.getData().data()
        camera = tree.getNode("\\Phantom2")
        data2 = camera.SIGNAL.getData().data()
        savemat('%d.mat' % shot_number, {'cam1': data1, 'cam2': data2})
    except:
        continue


