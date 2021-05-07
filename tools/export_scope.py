import MDSplus as mds

shot_number = 28500

shots = range(35741, 35783)
for shot_number in shots:
    try:
        tree = mds.Tree("mpts", shot_number)

        Ed = tree.getNode("\\OPHIRENERGYDIRECT").data()
        Er = tree.getNode("\\OPHIRENERGYRETURN").data()

        try:
            mcp = tree.getNode("\\IIMCPVOLTAGE").data()
            t = tree.getNode("\\IIPULSEDURATION").data()
        except:
            mcp = ''
            t = ''
        print("%d\t%.2f\t%.2f\t%s\t%s" % (shot_number, Ed, Er, mcp, t))
    except:
        continue
