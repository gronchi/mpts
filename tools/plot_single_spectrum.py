import MDSplus as mds
import matplotlib.pyplot as plt
import numpy as np

shot = 176
tree = mds.Tree("mpts_manual", shot)

camera = tree.getNode("\\Phantom2")
data = camera.SIGNAL.getData().data()[:, 150:152, 95:115]
#data -= np.mean(data)

plt.plot((data[51, :, :]).sum(axis=0))
plt.show()

fig, ax = plt.subplots(1, 1)
plt.subplots_adjust(bottom=0.25)
ax.pcolormesh(data[51, :, :])
ax.set_aspect('auto')
plt.show()
#%%%

import MDSplus as mds
import matplotlib.pyplot as plt
import numpy as np

shot = 170
tree = mds.Tree("mpts_manual", shot)

camera = tree.getNode("\\Phantom2")
data = camera.SIGNAL.getData().data()[:, :, :]
#data -= np.mean(data)

plt.plot((data[51, :, :]).sum(axis=0))
plt.show()

fig, ax = plt.subplots(1, 1)
plt.subplots_adjust(bottom=0.25)
ax.pcolormesh(data[51, :, :])
ax.set_aspect('auto')
plt.show()
