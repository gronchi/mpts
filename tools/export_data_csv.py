import numpy as np
import MDSplus as mds

shot_list = range(37168, 37187 + 1)
data = np.empty((0, len(shot_list)), float)
for shot_number in shot_list:
    try:
        tree = mds.Tree("mpts", shot_number)
        Ed = tree.getNode("\\OPHIRENERGYDIRECT").data()
        Er = tree.getNode("\\OPHIRENERGYRETURN").data()
        Ed = 0 if Ed < 0 else Ed
        Er = 0 if Er < 0 else Er
        try:
            mcp = tree.getNode("\\IIMCPVOLTAGE").data()
        except:
            mcp = 0
        try:
            t = tree.getNode("\\IIPULSEDURATION").data() / 1000
        except:
            t = 0
        t_trigger = tree.getNode("\\A4_DELAY").data() / 1000000.

        print("%d\t%.2f\t%.2f\t%s\t%s" % (shot_number, Ed, Er, mcp, t))
        data = np.append(data, [[shot_number, Ed, Er, mcp, t, t_trigger]], axis=0)
    except:
        continue

np.savetxt("Energy_table.csv", data, fmt="%d, %.2f, %.2f, %d, %.1f, %.3f", header=u"Shot, E direct[J], E return[J], MCP [V], dur II [us], trigger time [s]")
