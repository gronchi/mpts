import MDSplus as mds
import matplotlib.pyplot as plt
import matplotlib.cm as cm
from matplotlib.widgets import Slider, Button
import sys


def getLastShot(mode):
    if mode == "tokamak":
        tree = mds.Tree("mpts", 1)
        return int(tree.getNode("\\lastshot").getData())
    else:
        tree = mds.Tree("mpts_manual", 1)
        return int(tree.getNode("\\lastshot").getData())


if len(sys.argv) < 2:
    mode = "tokamak"
    shot_number = getLastShot(mode)
else:
    mode = sys.argv[1]
    shot_number = int(sys.argv[2])

if mode == "tokamak":
    tree = mds.Tree("mpts", shot_number)
else:
    tree = mds.Tree("mpts_manual", shot_number)

camera = tree.getNode("\\Phantom2")
data = camera.SIGNAL.getData().data()

fig, ax = plt.subplots(1, 1)
plt.subplots_adjust(bottom=0.25)
ax.pcolormesh(data[0, :, :], cmap=cm.gray)
ax.set_aspect('auto')
(frames, numcols, numrows) = data.shape

# ax.set_ylim(0, 15)
# ax.set_xlim(shot.X['K'].min(), shot.X['K'].max())
# ax.set_ylabel("beating freq. (MHz)")
# ax.set_xlabel("freq (GHz)")
plt.title = fig.suptitle("# %s - Frame: %d" % (shot_number, 1))

axfreq = plt.axes([0.25, 0.1, 0.5, 0.03])

sweep = Slider(axfreq, 'Sweep', 0, frames - 1, valinit=1, valfmt='%d')


def update(val):
    i = int(sweep.val)
    ax.pcolormesh(data[i, :, :], cmap=cm.gray)
    plt.title = fig.suptitle("# %s - Frame: %d" % (shot_number, i))
    fig.canvas.draw_idle()


sweep.on_changed(update)

resetax = plt.axes([0.8, 0.025, 0.1, 0.04])
button = Button(resetax, 'Reset', hovercolor='0.975')


def reset(event):
    sweep.reset()


button.on_clicked(reset)

plt.show()
