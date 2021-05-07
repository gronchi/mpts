import MDSplus as mds
import matplotlib.pyplot as plt
import matplotlib.cm as cm
import numpy as np


def getLastShot(mode):
    if mode == "tokamak":
        tree = mds.Tree("mpts", 1)
        return int(tree.getNode("\\lastshot").getData())
    else:
        tree = mds.Tree("mpts_manual", 1)
        return int(tree.getNode("\\lastshot").getData())


tree = mds.Tree("mpts", 34773, mode="READONLY")

camera = tree.getNode("\\Phantom2")
data = camera.SIGNAL.getData().data()


i = np.arange(41, 60, 2)
fig, ax = plt.subplots(1, 2)
plt.subplots_adjust(bottom=0.25)
ax[0].pcolormesh(data[i, :, :].sum(axis=0))
ax[0].set_aspect('auto')
ax[1].pcolormesh(data[i+1, :, :].sum(axis=0)-data[i, :, :].sum(axis=0))
ax[1].set_aspect('auto')


plt.show()
