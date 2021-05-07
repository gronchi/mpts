import struct
import numpy as np
import matplotlib.pyplot as plt

import sys
from PyQt5.QtWidgets import QDialog, QApplication, QPushButton, QVBoxLayout
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure
import MDSplus as mds


class ScopeSignal(object):
    """Reads scope inal data frm ISF files."""

    def __init__(self, filename=None, mode="manual", shot_number=393):
        self.x = None
        self.y = None
        conn = mds.Connection('130.183.56.68:8000')     # connect to the MDSplus server
        conn.openTree('mpts_%s' % mode, shot_number)
        if filename:
            self.y = conn.get('\\%s.signal' % filename).data()            # get the plasma current signal
            self.x = conn.get('DIM_OF(\\%s.signal)' % filename).data()    # get the plasma current time axis
        conn.closeAllTrees()


def LaserOscTex(PC_signal=None, Dir_signal=None, Ret_signal=None, EnDir=None, EnRet=None, Plot=False):
    # Laser pulse power and energy from Textronic scope
    # PC - channel with Pockels cell pulses, [time, Volt]
    # ChDir,ChRet  - Laser signals from direct and return laser beams,[time, Volt]
    # EnDir, EnRet - Ophir measures of the direct and return energies
    # CorrectOn - correct zero lines of laser signals so that to exlude
    #             free oscillation energy
    # PC, ChDir, ChRet are readout from ifs files:
    # ChDir = isfread ('*.isf');

    PassN = 14        # number of passes in MPS

    PC = ScopeSignal(PC_signal)
    ChDir = ScopeSignal(Dir_signal)
    if Ret_signal is None:
        ChRet = ScopeSignal(Dir_signal)
        ChRet.y = 0 * ChRet.y

    # Indexing On and Off intervals of PC pulses:
    Mean = np.mean(PC.y)
    Std = np.std(PC.y)
    LevelPC = PC.y[np.abs(PC.y - Mean) < Std].mean()
    StdLevelPC = PC.y[np.abs(PC.y - Mean) < Std].std()
    PC.z = (PC.y - LevelPC) / np.max(PC.y - LevelPC)
    PC.x = PC.x * 1000
    Tact = np.mean(np.diff(PC.x))        # ms
    PCOnInd = np.nonzero(PC.z > 3 * StdLevelPC)[0]
    PCOnInd = np.insert(PCOnInd, 0, 0)

    DiffPCOnInd = np.diff(PCOnInd)
    DiffPCOnInd = np.append(DiffPCOnInd, 0)
    PCEndInd = PCOnInd[DiffPCOnInd > 1][1:]
    PCEndInd = np.append(PCEndInd, np.nonzero(PC.z > 3 * StdLevelPC)[0][-1])
    PCOnInd = np.delete(PCOnInd, 0)
    DiffPCOnInd = np.delete(DiffPCOnInd, -1)
    PCStartInd = PCOnInd[DiffPCOnInd > 1]
    PCStartN = len(PCStartInd)
    PCEndN = len(PCEndInd)
    if PCEndN == PCStartN:
        PCN = PCEndN

    LevelDir = np.mean(ChDir.y[:PCStartInd[0]])
    ChDir.x = ChDir.x * 1000

    ChDir.Power = EnDir * (LevelDir - ChDir.y) / np.sum(LevelDir - ChDir.y) / Tact / 1000            # MW
    StdPowerDir = np.std(ChDir.Power[:PCStartInd[0]])
    LevelRet = np.mean(ChRet.y[:PCStartInd[0]])
    ChRet.x = ChRet.x * 1000

    if Ret_signal is None:
        ChRet.Power = ChRet.y            # MW
        StdPowerRet = 0
    else:
        ChRet.Power = EnRet * (LevelRet - ChRet.y) / np.sum(LevelRet - ChRet.y) / Tact / 1000            # MW
        StdPowerRet = np.std(ChRet.Power[:PCStartInd[0]])

    PulseEn = np.zeros((PCN, 7))
    BkgPower = np.zeros((PCN, 2))
    for i in np.arange(PCN):
        Max = np.max(ChDir.Power[PCStartInd[i]:PCEndInd[i]])
        maxInd = np.argmax(ChDir.Power[PCStartInd[i]:PCEndInd[i]])
        maxInd = maxInd + PCStartInd[i]
        PulseEn[i, 0] = PC.x[maxInd]

        Ind1 = PCStartInd[i] + np.nonzero(ChDir.Power[PCStartInd[i]:maxInd] > 2 * StdPowerDir)[0][0]
        Ind2 = maxInd + np.nonzero(ChDir.Power[maxInd:PCEndInd[i]] < 2 * StdPowerDir)[0][0]
        if Ind2 is None:
            Ind2 = PCEndInd[i]

        IndN = Ind2 - Ind1 + 1
        PulseEn[i, 1] = np.sum(ChDir.Power[Ind1:Ind2]) * Tact * 1000
        BkgPower[i, 0] = np.mean(ChDir.Power[np.concatenate((np.arange(PCStartInd[i], Ind1 - 1), np.arange(Ind2, PCEndInd[i])))])
        PulseEn[i, 1] = PulseEn[i, 1] - BkgPower[i, 0] * IndN * Tact * 1000
        # Pulse width, us:
        PulseEn[i, 4] = PulseEn[i, 1] / Max

        if Ret_signal is None:
            Ind1 = PCStartInd[i]
            Ind2 = maxInd
        else:
            Ind1 = PCStartInd[i] + np.nonzero(ChRet.Power[PCStartInd[i]:maxInd] >= 2 * StdPowerRet)[0][0]
            Ind2 = maxInd + np.nonzero(ChRet.Power[maxInd:PCEndInd[i]] < 2 * StdPowerRet)[0][0]
            if Ind2 is None:
                Ind2 = PCEndInd[i]

        IndN = Ind2 - Ind1 + 1
        PulseEn[i, 2] = np.sum(ChRet.Power[Ind1:Ind2]) * Tact * 1000
        BkgPower[i, 1] = np.mean(ChRet.Power[np.concatenate((np.arange(PCStartInd[i], Ind1 - 1), np.arange(Ind2, PCEndInd[i])))])
        PulseEn[i, 2] = PulseEn[i, 2] - BkgPower[i, 1] * IndN * Tact * 1000
        # Delay of the pulse peak from PC start, us:
        PulseEn[i, 3] = (maxInd - PCStartInd[i]) * Tact * 1000

    FreeEn = np.zeros((PCN - 1, 3))
    for i in np.arange(PCN - 1):
        FreeEn[i, 0] = np.mean(PC.x[PCEndInd[i]:PCStartInd[i + 1]])
        FreeEn[i, 1] = np.sum(ChDir.Power[PCEndInd[i]:PCStartInd[i + 1]]) * Tact * 1000
        FreeEn[i, 2] = np.sum(ChRet.Power[PCEndInd[i]:PCStartInd[i + 1]]) * Tact * 1000

    # Portions of return energy:
    PulseEn[:, 5] = PulseEn[:, 2] / PulseEn[:, 1]
    q = PulseEn[:, 5] ** (1 / PassN)
    K = (1 - q ** PassN) / (1 - q)
    K[q >= 1] = PassN
    # Total probing energy in MPS:
    PulseEn[:, 6] = PulseEn[:, 1] * K

    if Plot:
        plt.figure()
        plt.subplot(2, 1, 1)

        plt.plot(PC.x, PC.z, 'k')                                # PC pulses
        plt.plot(ChDir.x, ChDir.Power, 'r', lw=2)                # Pulse power, direct
        plt.plot(ChRet.x, ChRet.Power, 'b', lw=2)                # Pulse power, return
        plt.plot(PulseEn[:, 0], PulseEn[:, 1], 'ro', lw=2)       # Pulse energy, direct
        plt.plot(PulseEn[:, 0], PulseEn[:, 2], 'b*', lw=2)       # Pulse energy, return
        plt.plot(PulseEn[:, 0], PulseEn[:, 6], 'g*', lw=2)       # Total probing energy in MPS
        plt.plot(FreeEn[:, 0], FreeEn[:, 1], 'mo', lw=2)         # Free energy, direct
        plt.plot(FreeEn[:, 0], FreeEn[:, 2], 'c*', lw=2)         # Free energy, return
        plt.plot(PulseEn[:, 0], PulseEn[:, 4], 'g^', lw=2)       # Pulse width
        plt.grid(True)
        plt.xlabel('t,ms')
        plt.ylabel('MW, J')

        plt.subplot(2, 1, 2)

        plt.plot(PulseEn[:, 0], 10 * PulseEn[:, 5], 'k^', lw=2)                                # return fraction
        plt.plot(PulseEn[:, 0], PulseEn[:, 3], 'ro', lw=2)                                # Delay of the pulse peak
        # plot(PulseEn(:,1),PulseEn(:,5),'b*','Linewidth',2);    % Pulse width
        plt.grid(True)
        plt.xlabel('t, ms')
        plt.ylabel(u'%/10, $\\mu s$')
        plt.show()

    return PulseEn, PC, ChDir, ChRet, FreeEn


class Window(QDialog):
    def __init__(self, parent=None):
        super(Window, self).__init__(parent)

        # a figure instance to plot on
        self.figure, (self.ax1, self.ax2) = plt.subplots(2, figsize=(20, 10), sharex=True)

        # this is the Canvas Widget that displays the `figure`
        # it takes the `figure` instance as a parameter to __init__
        self.canvas = FigureCanvas(self.figure)

        # this is the Navigation widget
        # it takes the Canvas widget and a parent
        self.toolbar = NavigationToolbar(self.canvas, self)

        # Just some button connected to `plot` method
        self.button = QPushButton('Plot')
        self.button.clicked.connect(self.plot)

        # set the layout
        layout = QVBoxLayout()
        layout.addWidget(self.toolbar)
        layout.addWidget(self.canvas)
        layout.addWidget(self.button)
        self.setLayout(layout)

        # self.canvas.draw_idle()

    def plot(self):
        ''' plot some random stuff '''
        PulseEn, PC, ChDir, ChRet, FreeEn = LaserOscTex('ScopeCH2', 'ScopeCH4', None, 0.202, 0)

        # instead of ax.hold(False)
        # self.figure.clear()
        self.ax1.cla()
        self.ax2.cla()

        self.ax1.plot(PC.x, PC.z, 'k', label="Pocket cell")                                  # PC pulses
        self.ax1.plot(ChDir.x, ChDir.Power, 'r', lw=2, label="Power, direct")                # Pulse power, direct
        self.ax1.plot(ChRet.x, ChRet.Power, 'b', lw=2, label="Power, return")                # Pulse power, return
        self.ax1.plot(PulseEn[:, 0], PulseEn[:, 1], 'ro', lw=2, label="Energy, direct")      # Pulse energy, direct
        self.ax1.plot(PulseEn[:, 0], PulseEn[:, 2], 'b*', lw=2, label="Energy, return")      # Pulse energy, return
        self.ax1.plot(PulseEn[:, 0], PulseEn[:, 6], 'g*', lw=2, label="Probing energy")      # Total probing energy in MPS
        self.ax1.plot(FreeEn[:, 0], FreeEn[:, 1], 'mo', lw=2, label="Free energy, direct")   # Free energy, direct
        self.ax1.plot(FreeEn[:, 0], FreeEn[:, 2], 'c*', lw=2, label="Free energy, return")   # Free energy, return
        self.ax1.plot(PulseEn[:, 0], PulseEn[:, 4], 'g^', lw=2, label="Pulse width")         # Pulse width
        self.ax1.grid(True)
        self.ax1.legend(bbox_to_anchor=(1, 1), loc=2, borderaxespad=0)
        self.ax1.set_xlabel('t,ms')
        self.ax1.set_ylabel('MW, J')

        self.ax2.plot(PulseEn[:, 0], 10 * PulseEn[:, 5], 'k^', lw=2)                           # return fraction
        self.ax2.plot(PulseEn[:, 0], PulseEn[:, 3], 'ro', lw=2)                                # Delay of the pulse peak
        # plot(PulseEn(:,1),PulseEn(:,5),'b*','Linewidth',2);    % Pulse width
        self.ax2.grid(True)
        self.ax2.set_xlabel('t, ms')
        self.ax2.set_ylabel(u'%/10, $\\mu s$')

        # create an axis

        # discards the old graph
        # ax.hold(False) # deprecated, see above

        # plot data
        # ax.plot(data, '*-')

        # refresh canvas
        # self.canvas.draw()
        self.canvas.draw_idle()


if __name__ == '__main__':
    app = QApplication(sys.argv)

    main = Window()
    main.show()

    sys.exit(app.exec_())
