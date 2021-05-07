import MDSplus as mds
import matplotlib.pyplot as plt
import matplotlib.cm as cm

shot_number = 34773
tree = mds.Tree("mpts", shot_number)

camera = tree.getNode("\\Phantom2")
data = camera.SIGNAL.getData().data()

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(7, 4), sharey=True)
plt.subplots_adjust(bottom=0.25)
ax1.pcolormesh(data[45, :, :], cmap=cm.gray)
ax1.set_aspect('equal')
ax2.pcolormesh(data[46, :, :], cmap=cm.gray)
ax2.set_aspect('equal')
ax1.set_ylabel("wavelength [px]")
plt.tight_layout()
ax1.annotate(u'Without laser', xy=(200, 300), xytext=(200, 300), color='white')
ax1.annotate('$H_α$', xy=(270, 45), xytext=(250, 45), color='white')
ax2.annotate('$H_α$', xy=(270, 45), xytext=(250, 45), color='white')
ax2.annotate(u'stray light', xy=(200, 100), xytext=(200, 100), color='white')
ax2.annotate(u'With laser', xy=(200, 300), xytext=(200, 300), color='white')
fig.savefig("Camera_Tokamak_discharge.png")
plt.show()
