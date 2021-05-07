import MDSplus as mds
import matplotlib.pyplot as plt
from matplotlib.widgets import Slider, Button
import sys

if len(sys.argv) < 1:
    shot_number = 67
else:
    shot_number = int(sys.argv[1])


tree = mds.Tree("mpts_manual", shot_number)

camera = tree.getNode("\\Phantom2")
data = camera.SIGNAL.getData().data()[:, 50:-50, :]

fig, ax = plt.subplots(1, 1)
plt.subplots_adjust(bottom=0.25)
l, = ax.plot(data[51, :, 227] - data[51, :, 227].mean())
ax.set_aspect('auto')
ax.set_ylim(0, 200)
plt.grid()
(frames, numcols, numrows) = data.shape

# ax.set_ylim(0, 15)
# ax.set_xlim(shot.X['K'].min(), shot.X['K'].max())
# ax.set_ylabel("beating freq. (MHz)")
# ax.set_xlabel("freq (GHz)")
plt.title = fig.suptitle("# %s - Frame: %d" % (shot_number, 1))

ax_frame = plt.axes([0.10, 0.09, 0.75, 0.03])
ax_row = plt.axes([0.10, 0.15, 0.75, 0.03])

frame = Slider(ax_frame, 'Frame', 0, frames - 1, valinit=51, valfmt='%d')
row = Slider(ax_row, 'Column', 0, numrows - 1, valinit=227, valfmt='%d')


def update(val):
    j = int(row.val)
    i = int(frame.val)
    l.set_ydata(data[i, :, j] - data[i, :, j].mean())
    plt.title = fig.suptitle("# %s - Frame: %d" % (shot_number, i))
    fig.canvas.draw_idle()


frame.on_changed(update)
row.on_changed(update)

resetax = plt.axes([0.8, 0.025, 0.1, 0.04])
button = Button(resetax, 'Reset', hovercolor='0.975')


def reset(event):
    frame.reset()
    row.reset()


button.on_clicked(reset)

plt.show()
