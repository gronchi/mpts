import numpy as np
import pyqtgraph as pg
from pyqtgraph.Qt import QtCore, QtGui
from pyqtgraph.Point import Point
import MDSplus as mds

shot_number = 980
tree = mds.Tree("mpts_manual", shot_number, mode='ReadOnly')


camera = tree.getNode("\\Phantom1")
data1 = camera.SIGNAL.getData().data()
camera = tree.getNode("\\Phantom2")
data2 = camera.SIGNAL.getData().data()


p1 = pg.image(data2[:, ::-1, :])

## Start Qt event loop unless running in interactive mode.
if __name__ == '__main__':
    import sys
    if (sys.flags.interactive != 1) or not hasattr(QtCore, 'PYQT_VERSION'):
        QtGui.QApplication.instance().exec_()
