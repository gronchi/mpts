import MDSplus as mds
import matplotlib.pyplot as plt
import matplotlib.cm as cm


shot_number = 207
tree = mds.Tree("mpts_manual", shot_number)

camera = tree.getNode("\\Phantom2")
data2 = camera.SIGNAL.getData().data()

fig, ax2 = plt.subplots(1, 1)
plt.subplots_adjust(bottom=0.25)
ax2.imshow(data2[17, :, :], cmap=cm.gray, interpolation=None, vmin=0, vmax=1024)
ax2.set_aspect('auto')

plt.show()