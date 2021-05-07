import MDSplus as mds
import matplotlib.pyplot as plt
import matplotlib.cm as cm

shot_number = 710
tree = mds.Tree("mpts_manual", shot_number, mode='ReadOnly')


camera = tree.getNode("\\Phantom1")
data1 = camera.SIGNAL.getData().data()
camera = tree.getNode("\\Phantom2")
data2 = camera.SIGNAL.getData().data()

fig, ax1 = plt.subplots(1, 2)
ax1.plot(data[:, 100])

plt.show()
