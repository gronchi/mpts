import MDSplus as mds
import matplotlib.pyplot as plt
import matplotlib.cm as cm
from matplotlib.widgets import Slider
from scipy.ndimage import median_filter
import sys
import numpy as np

mask_y = np.arange(195, 384, 4)
mask_x = np.arange(3, 512, 8)


def main(argv):
    if len(argv) < 3:
        sys.stderr.write("Usagage: python export2matfile.py mode [shotnumber]")
        return 1
    try:
        mode = argv[1]
        shot_number = int(argv[2])
    except:
        sys.stderr.write("Usagage: python export2matfile.py shotnumber")
        return 1

    tree = mds.Tree(mode, shot_number, mode='ReadOnly')

    camera1 = tree.getNode("\\Phantom1")
    data1 = camera1.SIGNAL.getData().data()
    camera2 = tree.getNode("\\Phantom2")
    data2 = camera2.SIGNAL.getData().data()

    (frames, w, h) = data2.shape

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 8))
    plt.subplots_adjust(bottom=0.25)
    img1 = ax1.imshow(data1[49, :, :].T, cmap=cm.gray, interpolation=None, vmin=120, vmax=2**12, aspect='equal')
    ax1.set_aspect('auto')
    img2 = ax2.imshow(data2[49, ::-1, :].T, cmap=cm.gray, interpolation=None, vmin=120, vmax=2**12, aspect='equal')
    ax2.set_aspect('auto')

    index = plt.axes([0.2, 0.1, 0.65, 0.03])
    sindex = Slider(index, 'frame', 1, frames, valinit=50, valstep=1, valfmt='%d')

    def update(val):
        frame = int(val) - 1
        img1.set_array(data1[frame - 1, :, :].T)
        #img2_median = median_filter(data2[frame, ::-1, :].T, size=2)
        #img_new = data2[frame, ::-1, :].T
        #img_new[mask_x, mask_y] = img2_median[mask_x, mask_y]  
        img2.set_array(data2[frame - 1, ::-1, :].T)
        fig.canvas.draw_idle()

    sindex.on_changed(update)

    plt.show()


if __name__ == "__main__":
    sys.exit(main(sys.argv))
