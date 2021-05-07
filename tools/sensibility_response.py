import MDSplus as mds
import matplotlib.pyplot as plt
from scipy.ndimage import median_filter
import numpy as np
from scipy import stats


def fix_cam1(data):
    frames, h, w = data.shape
    mask_y = np.arange(195, h - 1, 4)
    data_fixed = data.copy()

    for frame in range(frames):
        data_fixed[frame, mask_y, :] = (data[frame, mask_y - 1, :] + data[frame, mask_y + 1, :]) / 2

    data_fixed[:, 342, 115] = (data[:, 341, 115] + data[:, 344, 115]) / 2
    data_fixed[:, 343, 115] = (data_fixed[:, 342, 115] + data_fixed[:, 344, 115]) / 2
    data_fixed[:, 342, 114] = (data[:, 341, 114] + data[:, 344, 114]) / 2
    data_fixed[:, 343, 114] = (data_fixed[:, 342, 114] + data_fixed[:, 344, 114]) / 2

    data_fixed[:, 331, 216] = (data[:, 330, 216] + data[:, 333, 216]) / 2
    data_fixed[:, 332, 216] = (data_fixed[:, 331, 216] + data_fixed[:, 333, 216]) / 2

    return data_fixed


def fix_cam2(data):
    frames, h, w = data.shape
    mask_y = np.arange(195, h, 4)
    mask_x = np.arange(3, w, 8)
    mask_xx, mask_yy = np.meshgrid(mask_x, mask_y)

    data_fixed = data.copy()
    for frame in range(frames):
        data_fixed[frame, mask_yy, mask_xx] = median_filter(data[frame, :, :], size=2)[mask_yy, mask_xx]

    return data_fixed


shotnumber = 1284
shotlist = np.arange(1284, 1290 + 1)
counts = np.array([])
counts_std = np.array([])

for shotnumber in shotlist:
    tree = mds.Tree("mpts_manual", shotnumber, mode='ReadOnly')

    camera2 = tree.getNode("\\Phantom2")
    data2 = camera2.SIGNAL.getData().data()
    data2fixed = fix_cam2(data2)
    data2fixed = data2fixed - np.mean(data2fixed[-15:, :, :], axis=0)
    camera1 = tree.getNode("\\Phantom1")
    data1 = camera1.SIGNAL.getData().data()
    data1fixed = fix_cam2(data1)
    data1fixed = data1fixed - np.mean(data1fixed[-15:, :, :], axis=0)

    total1 = data1fixed[:, 65:115, 230:280].sum(axis=(1, 2))
    total2 = data2fixed[:, 285:298, 250:266].sum(axis=(1, 2))

    # plt.figure()
    # im = plt.imshow(data1fixed[49, 75:105, 240:270])
    # plt.show()
    plt.figure()
    im = plt.imshow(data2fixed[49, 285:298, 250:266])
    plt.show()
    # plt.plot(total2)
    # plt.plot(data2fixed[:, 285:298, 250:266].sum(axis=(1, 2)))
    # plt.show()

    signal = data2fixed[:, 285:298, 250:266].sum(axis=(1, 2))
    counts = np.append(counts, np.average(signal[60:115]))
    counts_std = np.append(counts_std, np.std(signal[60:115]))


#####
mcp_voltage = np.array([1000, 1000, 950, 900, 850, 800, 950])
counts_per_photon = counts / 3658.53
counts_per_photon_std = counts_std / 3658.53


slope, intercept, r_value, p_value, std_err = stats.linregress(mcp_voltage, np.log2(counts_per_photon))

fig = plt.figure(figsize=(1.4 * 4.5, 1.4 * 3))
ax = fig.add_subplot(1, 1, 1)
ax.errorbar(mcp_voltage, counts_per_photon, yerr=counts_per_photon_std, fmt='o', label="Data")
ax.plot(np.linspace(750, 1050, 10), 2**(slope * np.linspace(750, 1050, 10) + intercept), label=r"$2^{%.0f + %.4f \times MCP[V]}$" % (intercept, slope))
ax.set_yscale('log')
ax.set_xlim(750, 1050)
ax.set_ylim(0.1, 100)
ax.set_xlabel(r"MCP voltage [V]")
ax.set_ylabel(r"Counts/Photon")
ax.grid(True, which="both")
ax.set_title('Counts per photon as function of the MCP voltage')
plt.legend()
plt.tight_layout()
plt.show()


#
shotnumber = 1284
tree = mds.Tree("mpts_manual", shotnumber, mode='ReadOnly')
camera2 = tree.getNode("\\Phantom2")
data2 = camera2.SIGNAL.getData().data()
data2fixed = fix_cam2(data2)
data2fixed = data2fixed - np.mean(data2fixed[-15:, :, :], axis=0)

fig, ax = plt.subplots(figsize=(1.4 * 4.5, 1.4 * 3))
pos = ax.imshow(data2fixed[145, :, :], vmin=0, vmax=4000, aspect='equal', interpolation='none', cmap='Blues')
fig.colorbar(pos, ax=ax)
ax.set_xlim(250, 266)
ax.set_ylim(285, 298)
ax.set_xlabel(r"columns [pixels]")
ax.set_ylabel(r"rows [pixels]")
ax.set_title('Shot 1284, frame 145')
plt.tight_layout()
plt.show()
