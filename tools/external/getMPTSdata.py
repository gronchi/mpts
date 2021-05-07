import sys
import os
import MDSplus as mds
from scipy.io import savemat


def main(argv):
    if len(argv) < 2:
        sys.stderr.write("Usagage: python export2matfile.py [mode] [shotnumber]")
        return 1
    try:
        mode = argv[1]
        first_shotnumber = int(argv[2])
    except:
        sys.stderr.write("Usagage: python export2matfile.py [mode] [shotnumber]")
        return 1

    if len(argv) == 4:
        last_shotnumber = int(argv[3])
    else:
        last_shotnumber = first_shotnumber

    conn = mds.Connection('mptspc.aug.ipp.mpg.de:8000')     # connect to the MDSplus server
    for shotnumber in range(first_shotnumber, last_shotnumber + 1):
        print("Processing %s" % shotnumber)
        try:
            conn.openTree(mode, shotnumber)
        except:
            continue

        print("Converting data for shot #%d on the experiment %s." % (shotnumber, mode))
        timestamp = conn.get("\\timestamp").data()[0:10]
        data1 = conn.get("\\Phantom1.signal").data()
        data2 = conn.get("\\Phantom2.signal").data()
        try:
            Ed = conn.get("\\OPHIRENERGYDIRECT").data()
            Er = conn.get("\\OPHIRENERGYRETURN").data()
            Ed = Ed if Ed > 0 else 0
            Er = Er if Er > 0 else 0
        except:
            Ed = 0
            Er = 0
        try:
            scope_time = conn.get("dim_of(\\scope.CH1.signal)").data()
            scope_pockels = conn.get("\\scope.CH1.signal").data()
            scope_Edirect = conn.get("\\scope.CH2.signal").data()
            scope_Ereturn = conn.get("\\scope.CH3.signal").data()
            scope_MCPTrigger = conn.get("\\scope.CH4.signal").data()
        except:
            scope_time = 0
            scope_pockels = 0
            scope_Edirect = 0
            scope_Ereturn = 0
            scope_MCPTrigger = 0
        try:
            adc_time = conn.get("dim_of(\\adc.CH1.SIGNAL)").data()
            adc_Edirect = conn.get("\\adc.CH1.SIGNAL").data()
            adc_Ereturn = conn.get("\\adc.CH2.SIGNAL").data()
        except:
            adc_time = 0
            adc_Ereturn = 0
            adc_Edirect = 0

        try:
            mcp = conn.get("\\IIMCPVOLTAGE").data()
            t = conn.get("\\IIPULSEDURATION").data()
        except:
            mcp = 0
        try:
            II_PS = conn.get("\\IIPS").data()
            II_Gain = conn.get("\\IIGain").data()
            II_Coarse = conn.get("\\IICOARSE").data()
            II_Fine = conn.get("\\IIFINE").data()
        except:
            II_PS = "DIFFER"
            II_Gain = 0
            II_Coarse = 0
            II_Fine = 0

        if II_PS == "Kentech":
            mcp = 0

        if not os.path.exists("../%s" % timestamp):
            os.mkdir("../%s" % timestamp)

        if mode == "mpts_manual":
            savemat('../%s/TTS%s_%d_Stray.mat' % (timestamp, timestamp.replace("-", ""), shotnumber), {'cam1': data1, 'cam2': data2, 'Edirect': Ed, 'Ereturn': Er, 'II_PS': II_PS, 'II_Gain': II_Gain, 'II_Coarse': II_Coarse, 'II_Fine': II_Fine, 'MCPdur': t, 'MCPVoltage': mcp,
                                                                                                       'scope_time': scope_time, 'scope_pockels': scope_pockels, 'scope_Edirect': scope_Edirect, 'scope_Ereturn': scope_Ereturn, 'scope_MCPTrigger': scope_MCPTrigger,
                                                                                                       'adc_time': adc_time, 'adc_Edirect': adc_Edirect, 'adc_Ereturn': adc_Ereturn}, do_compression=True)
        else:
            savemat('../%s/TTS%s_%d.mat' % (timestamp, timestamp.replace("-", ""), shotnumber), {'cam1': data1, 'cam2': data2, 'Edirect': Ed, 'Ereturn': Er, 'II_PS': II_PS, 'II_Gain': II_Gain, 'II_Coarse': II_Coarse, 'II_Fine': II_Fine, 'MCPdur': t, 'MCPVoltage': mcp,
                                                                                                 'scope_time': scope_time, 'scope_pockels': scope_pockels, 'scope_Edirect': scope_Edirect, 'scope_Ereturn': scope_Ereturn, 'scope_MCPTrigger': scope_MCPTrigger,
                                                                                                 'adc_time': adc_time, 'adc_Edirect': adc_Edirect, 'adc_Ereturn': adc_Ereturn}, do_compression=True)


if __name__ == "__main__":
    sys.exit(main(sys.argv))
