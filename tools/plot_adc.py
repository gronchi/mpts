import MDSplus as mds
import matplotlib.pyplot as plt
import sys


def main(argv):
    if len(argv) < 3:
        sys.stderr.write("Usage: python plot_adc.py mode shotnumber")
        return 1
    try:
        mode = argv[1]
        shotnumber = int(argv[2])
    except:
        sys.stderr.write("Usage: python plot_adc.py mode shotnumber")
        return 1

    try:
        tree = mds.Tree(mode, shotnumber, mode='ReadOnly')
    except mds.TreeFOPENR:
        sys.stderr.write("There is no data  available for the shot %d." % shotnumber)
        return 1

    adc = tree.getNode("\\ADC")
    adc_time = adc.CH1.SIGNAL.dim_of().data() * 1e6
    adc_Edirect = adc.CH1.SIGNAL.data()
    adc_Ereturn = adc.CH2.SIGNAL.data()
    plt.figure()
    plt.plot(adc_time, adc_Edirect)
    plt.plot(adc_time, adc_Ereturn)
    plt.show()


if __name__ == "__main__":
    sys.exit(main(sys.argv))
