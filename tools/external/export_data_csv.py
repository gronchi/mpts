import numpy as np
import MDSplus as mds


def main(argv):
    if len(argv) < 2:
        sys.stderr.write("Usagage: python export_data_csv.py [mode] [shotnumber]")
        return 1
    try:
        mode = argv[1]
        first_shotnumber = int(argv[2])
    except:
        sys.stderr.write("Usagage: python export_data_csv.py [mode] [shotnumber]")
        return 1

    if len(argv) == 4:
        last_shotnumber = int(argv[3])
    else:
        last_shotnumber = first_shotnumber

    csv_data = np.empty((0, 6), float)
    conn = mds.Connection('mptspc.aug.ipp.mpg.de:8000')     # connect to the MDSplus server
    for shotnumber in range(first_shotnumber, last_shotnumber + 1):
        try:
            conn.openTree(mode, shotnumber)
            print("Getting data for shot #%d on the experiment %s." % (shotnumber, mode))
            timestamp = conn.get("\\timestamp").data()[0:10]
        except:
            continue

        try:
            Ed = conn.get("\\OPHIRENERGYDIRECT").data()
            Er = conn.get("\\OPHIRENERGYRETURN").data()
            Ed = Ed if Ed > 0 else 0
            Er = Er if Er > 0 else 0
        except:
            Ed = 0
            Er = 0

        try:
            mcp = conn.get("\\IIMCPVOLTAGE").data()
            t = conn.get("\\IIPULSEDURATION").data()
        except:
            mcp = 0
            t = 0


        t_trigger = np.round(tree.getNode("\\B5_DELAY").data() / 10000000., 1)
        print("%d\t%.2f\t%.2f\t%s\t%s\t%s" % (shotnumber, Ed, Er, mcp, t, t_trigger))
        csv_data = np.append(csv_data, [[shotnumber, Ed, Er, mcp, t, t_trigger]], axis=0)

    np.savetxt("../%s/%s_Energy_table.csv" % (timestamp, timestamp), data, fmt="%d, %.2f, %.2f, %d, %.1f, %.3f", header=u"Shot, E direct[J], E return[J], MCP [V], dur II [us], trigger time [s]")

if __name__ == "__main__":
    sys.exit(main(sys.argv))
