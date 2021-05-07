import MDSplus as mds
import matplotlib.pyplot as plt
import matplotlib.cm as cm


shot_number = 191
tree = mds.Tree("mpts_manual", shot_number)

camera = tree.getNode("\\Phantom1")
data1 = camera.SIGNAL.getData().data()
camera = tree.getNode("\\Phantom2")
data2 = camera.SIGNAL.getData().data()

fig, (ax1, ax2) = plt.subplots(1, 2)
plt.subplots_adjust(bottom=0.25)
ax1.imshow(data1[51, :, :], cmap=cm.gray, interpolation=None, vmin=0, vmax=400)
ax1.set_aspect('auto')
ax2.imshow(data2[51, :, :], cmap=cm.gray, interpolation=None, vmin=0, vmax=400)
ax2.set_aspect('auto')
(frames, numcols, numrows) = data1.shape


plt.show()
