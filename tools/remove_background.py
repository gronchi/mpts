import MDSplus as mds
import matplotlib.pyplot as plt
import matplotlib.cm as cm
from scipy.ndimage import median_filter
import numpy as np


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




shot_number = 1285
tree = mds.Tree("mpts_manual", shot_number, mode='ReadOnly')


camera2 = tree.getNode("\\Phantom2")
data2 = fix_cam2(camera2.SIGNAL.getData().data())
camera1 = tree.getNode("\\Phantom1")
data1 = fix_cam1(camera1.SIGNAL.getData().data())

total = np.abs((data2[0::2, :, :] - data2[1::2, :, :]).sum(axis=(1, 2)))
signal = np.abs(data2[0::2, :, :] - data2[1::2, :, :])


# im = plt.imshow(signal[-11, ::-1, :].T, cmap=cm.gray, interpolation=None, vmin=0, vmax=500)
# plt.colorbar(im)
# plt.show()


im = plt.imshow(signal[25, ::-1, :].T, interpolation=None, vmin=0, vmax=2**11)
plt.colorbar(im)
plt.show()

im = plt.imshow(signal[24, ::-1, :].T, interpolation=None, vmin=0, vmax=2**11)
plt.colorbar(im)
plt.show()

plt.plot(data1.sum(axis=(1, 2)))
plt.plot(data2.sum(axis=(1, 2)))
plt.show()
#img2_median = median_filter(data2[frame, ::-1, :].T, size=2)
#img_new = data2[frame, ::-1, :].T
#img_new[mask_x, mask_y] = img2_median[mask_x, mask_y]

plt.figure()
plt.imshow(median_filter(data2[49, :, :], size=2), cmap=cm.gray, interpolation=None, vmin=0, vmax=2**10, aspect='equal')

plt.figure()
plt.imshow(median_filter(data2[49, :, :], size=2), cmap=cm.gray, interpolation=None, vmin=0, vmax=2**10, aspect='equal')
plt.show()

frames, h, w = data2.shape

mask_y = np.arange(195, h, 4)
mask_x = np.arange(3, w, 8)
mask_xx, mask_yy = np.meshgrid(mask_x, mask_y)

new_image = data2[49, :, :].copy()
#new_image[mask_y][:, mask_x] = median_filter(data2[49, :, :], size=2)[mask_y][:, mask_x]
new_image[mask_yy, mask_xx] = median_filter(data2[49, :, :], size=2)[mask_yy, mask_xx]

plt.figure()
plt.imshow(data2[49, :, :], cmap=cm.gray, interpolation=None, vmin=0, vmax=2**10, aspect='equal')

plt.figure()
plt.imshow(new_image, cmap=cm.gray, interpolation=None, vmin=0, vmax=2**10, aspect='equal')
plt.show()


mask_y = np.arange(195, h - 1, 4)


new_image = data1[49, :, :].copy()
new_image[np.arange(195, h - 1, 4), :] = (data1[49, mask_y - 1, :] + data1[49, mask_y + 1, :]) / 2

###

data1_new = fix_cam1(data1)

plt.figure()
plt.imshow(data1[53, :, :], cmap=cm.gray, interpolation=None, vmin=0, vmax=2**10, aspect='equal')

plt.figure()
plt.imshow(data1[54, :, :], cmap=cm.gray, interpolation=None, vmin=0, vmax=2**10, aspect='equal')
plt.show()
