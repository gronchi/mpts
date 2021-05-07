import MDSplus as mds
import matplotlib.pyplot as plt
import sys
import numpy as np


def main(argv):
    try:
        tree = mds.Tree("mpts_manual", 1382, mode='ReadOnly')
    except mds.TreeFOPENR:
        sys.stderr.write("There is no data  available for the shot %d." % 1382)
        return 1

    trigger_val = 3

    adc = tree.getNode("\\ADC")
    adc_time = adc.CH1.SIGNAL.dim_of().data() * 1e6
    if 1382 >= 1358:
        # adc_time -= 100
        adc_time -= 20000
    adc_Edirect = adc.CH1.SIGNAL.data()
    adc_Ereturn = adc.CH2.SIGNAL.data()


    tree = mds.Tree("mpts_manual", 1381, mode='ReadOnly')

    adc = tree.getNode("\\ADC")
    ch3 = adc.CH1.SIGNAL.data()

    index_ch1 = np.flatnonzero((adc_Edirect[:-1] < trigger_val) & (adc_Edirect[1:] > trigger_val))-1
    index_ch2 = np.flatnonzero((adc_Ereturn[:-1] > trigger_val) & (adc_Ereturn[1:] < trigger_val))-1
    index_ch3 = np.flatnonzero((ch3[:-1] > trigger_val) & (ch3[1:] < trigger_val))-1
    fig, ax1 = plt.subplots(figsize=(9, 7))
    ax1.plot(adc_time, adc_Edirect, label="II")
    ax1.plot(adc_time, adc_Ereturn, label="CMOS")
    ax1.plot(adc_time, ch3, label="PC")
    for i in range(len(index_ch1)):
        ax1.text(adc_time[index_ch1[i]], 2.25 + (0.05 if i%2 else -0.05), "%d" % (i+1), fontsize=6)
    for i in range(len(index_ch2)):
        ax1.text(adc_time[index_ch2[i]], 2.75+ (0.05 if i%2 else -0.05), "%d" % (i+1), fontsize=6)
    for i in range(len(index_ch3)):
        ax1.text(adc_time[index_ch3[i]], 3.25+ (0.05 if i%2 else -0.05), "%d" % (i+1), fontsize=6)
    plt.show()


if __name__ == "__main__":
    sys.exit(main(sys.argv))
