import MDSplus as mds
import matplotlib.pyplot as plt
import matplotlib.cm as cm
from matplotlib.widgets import Slider, TextBox


def get_data(shot_number):
    tree = mds.Tree("mpts", shot_number, mode='ReadOnly')
    camera1 = tree.getNode("\\Phantom1")
    data1 = camera1.SIGNAL.getData().data()
    camera2 = tree.getNode("\\Phantom2")
    data2 = camera2.SIGNAL.getData().data()
    tree.close()
    return data1, data2


shot_number = 36091
data1, data2 = get_data(shot_number)
(frames, w, h) = data2.shape


fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 8))
plt.subplots_adjust(bottom=0.25)
plt1 = ax1.imshow(data1[49, :, :].T, cmap=cm.gray, interpolation=None, vmin=0, vmax=2**11, aspect='equal')
ax1.set_aspect('auto')
plt2 = ax2.imshow(data2[49, ::-1, :].T, cmap=cm.gray, interpolation=None, vmin=0, vmax=2**11, aspect='equal')
ax2.set_aspect('auto')
ax1.set_title("Cam 1 #%d" % shot_number)
ax2.set_title("Cam 2 #%d" % shot_number)

index = plt.axes([0.2, 0.1, 0.65, 0.03])
sindex = Slider(index, 'frame', 0, frames - 1, valinit=49, valstep=1, valfmt='%d')


class Index(object):
    ind = 0

    def __init__(self):
        self.data1 = data1
        self.data2 = data2
        self.frame = 49
        self.shot_number = 1083

    def frame_selection(self, event):
        self.frame = int(event)
        plt1.set_data(self.data1[self.frame, :, :].T)
        plt2.set_data(self.data2[self.frame, ::-1, :].T)
        fig.canvas.draw_idle()

    def update_shot(self, event):
        self.shot_number = int(event)
        self.data1, self.data2 = get_data(self.shot_number)
        (frames, w, h) = data2.shape
        sindex.valmax = frames - 1
        plt1.set_data(self.data1[self.frame, :, :].T)
        plt2.set_data(self.data2[self.frame, ::-1, :].T)
        ax1.set_title("Cam 1 #%d" % self.shot_number)
        ax2.set_title("Cam 2 #%d" % self.shot_number)


callback = Index()
axbox = plt.axes([0.1, 0.01, 0.8, 0.05])
text_box = TextBox(axbox, 'Shot', hovercolor='0.975', initial="1083")
text_box.on_submit(callback.update_shot)
sindex.on_changed(callback.frame_selection)

plt.show()
