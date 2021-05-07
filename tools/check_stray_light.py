import MDSplus as mds
import matplotlib.pyplot as plt
import numpy as np

data = np.array([])
energy = np.array([])
angle = np.array([0, 1, 0.5, 3 / 4., 1 / 4., 1 / 4., 0, 7 / 8., 7 / 8., 1 / 8., 0])
for shot_number in [1092, 1093, 1094, 1095, 1096, 1100, 1102, 1103, 1104, 1105, 1107]:
    tree = mds.Tree("mpts_manual", shot_number, mode='ReadOnly')
    camera2 = tree.getNode("\\Phantom2")
    Ed = tree.getNode("\\OPHIRENERGYDIRECT").data()
    cam = camera2.SIGNAL.getData().data()
    total = cam[20:, 220:255, :].sum(axis=(1, 2))
    total = total - np.median(total)
    Ed = tree.getNode("\\OPHIRENERGYDIRECT").data()
    data = np.append(data, total[20:].sum())
    energy = np.append(energy, Ed)

energy[6] = 15

fig = plt.figure()
ax = fig.add_subplot(1, 1, 1)
ax.plot(angle, data / (energy * 35 * 512), 'o')
# ax.plot(total[total > 5e5], 'o')
ax.set_title(r'Stray light notch filter angle')
# ax.set_ylabel(r'Counts / (pixel * energy)')
# ax.set_xlabel(r'Trigger time [$\mu$s]')
# ax.set_ylim(0, 100)
# ax.set_xlim(-0.25, 4.25)
ax.grid(True)
plt.tight_layout()
plt.savefig("Stray light vs notch filter angle.png")
plt.show()
