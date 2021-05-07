import sys
import os
import MDSplus as mds
from scipy.io import savemat
sys.path.append("/usr/local/mdsplus/mdsobjects/python")


Charge = {"On": 1, "From": "AUG|Man", "To": "Charge&Simmer", "InTime": 0, "OutTime": 0, "Delay": 0, "Width": 100, "Period": 0, "N": 1}
Simmer = {"On": 1, "Fom": "Charge|Man", "To": "Burst&AND1", "InTime": 0, "OutTime": 0, "Delay": 0, "Width": 100, "Period": 0, "N": 1}
Enable = {"On": 1, "Fom": "Simmer", "To": "LaserTrigger", "InTime": 0, "OutTime": 0, "Delay": 0, "Width": 2500000, "Period": 0, "N": 1}
LaserTrigger = {"On": 1, "Fom": "Enable&Flash", "To": "Laser", "InTime": 0, "OutTime": 0, "Delay": 0, "Width": 100, "Period": 0, "N": 1}
Timer = {'Charge': Charge, "Simmer": Simmer, "Enable": Enable, "LaserTrigger": LaserTrigger}
Trigger = {"TriggerMode": 1}


def main(argv):
    if len(argv) < 3:
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

    for shot_number in range(first_shotnumber, last_shotnumber + 1):
        print(shot_number)
        try:
            tree = mds.Tree(mode if 'cal' not in mode else 'mpts_manual', shot_number, mode='ReadOnly')
        except:
            print("There is no shot #%d on the experiment %s." % (shot_number, mode))
            continue

        print("Converting data for shot #%d on the experiment %s." % (shot_number, mode))
        timestamp = tree.getNode("\\timestamp").data()[0:10]
        camera1 = tree.getNode("\\Phantom1")
        camera2 = tree.getNode("\\Phantom2")
        scope = tree.getNode("\\scope")
        adc = tree.getNode("\\ADC")
        data1 = camera1.SIGNAL.getData().data()
        data2 = camera2.SIGNAL.getData().data()
        try:
            Ed = tree.getNode("\\OPHIRENERGYDIRECT").data()
            Er = tree.getNode("\\OPHIRENERGYRETURN").data()
            Ed = Ed if Ed > 0 else 0
            Er = Er if Er > 0 else 0
        except:
            Ed = 0
            Er = 0
        try:
            scope_time = scope.CH1.SIGNAL.dim_of().data()
            scope_pockels = scope.CH1.SIGNAL.data()
            scope_Edirect = scope.CH2.SIGNAL.data()
            scope_Ereturn = scope.CH3.SIGNAL.data()
            scope_MCPTrigger = scope.CH4.SIGNAL.data()
        except:
            scope_time = 0
            scope_pockels = 0
            scope_Edirect = 0
            scope_Ereturn = 0
            scope_MCPTrigger = 0
        try:
            adc_time = adc.CH1.SIGNAL.dim_of().data()
            adc_Edirect = adc.CH1.SIGNAL.data()
            adc_Ereturn = adc.CH2.SIGNAL.data()
        except:
            adc_time = 0
            adc_Ereturn = 0
            adc_Edirect = 0

        try:
            mcp = tree.getNode("\\IIMCPVOLTAGE").data()
            t = tree.getNode("\\IIPULSEDURATION").data()
        except:
            mcp = 0
        try:
            II_PS = tree.getNode("\\IIPS").data()
            II_Gain = tree.getNode("\\IIGain").data()
            II_Coarse = tree.getNode("\\IICOARSE").data()
            II_Fine = tree.getNode("\\IIFINE").data()
        except:
            II_PS = "DIFFER"
            II_Gain = 0
            II_Coarse = 0
            II_Fine = 0

        if II_PS == "Kentech":
            mcp = 0

        OpMode = tree.getNode("\\OpMode").data()
        if OpMode < 3:
            OpModeName = "M%d" % (OpMode + 1)
        else:
            OpModeName = "T%d" % (OpMode - 2)

        crio_settings = "Simmer_delay(1uS) = \"0\"\nBurst_delay(1uS) = \"0\"\nBurst_number = \"1\"\nBurst_period(1uS) = \"300000\"\nTrigger_Enable_pulse(1uS) = \"2500000\"\nADC_Enable_delay(1uS) = \"2500000\"\nADC_Enable_pulse(1uS) = \"20000\"\nCMOS_plasma_delay(1uS) = \"2488094\"\nCMOS_Plasma_number = \"100\"\nCMOS_Plasma_period(1uS) = \"200\"\nCMOS_Plasma_pulse(1uS) = \"5\"\nCMOS_Laser_delay(0.1uS) = \"1000\"\nCMOS_Laser_pulse(0.1uS) = \"50\"\nII_Gate_Plasma_delay(0.1uS) = \"24899150\"\nII_Gate_Plasma_number = \"80\"\nII_Gate_Plasma_period(0.1uS) = \"2000\"\nII_Gate_Plasma_pulse(0.1uS) = \"50\"\nII_Plasma_Delay_delay(0.1uS) = \"1000\"\nII_Plasma_Delay_pulse(0.1uS) = \"50\"\nII_Gate_Laser_delay(0.1uS) = \"0\"\nII_Gate_Laser_pulse(0.1uS) = \"50\"\nII_Flash_Bool_delay(1uS) = \"1300\"\nII_Flash_Bool_pulse(1uS) = \"4000\"\nFlash_delay(1uS) = \"2498600\"\nFlash_pulse(1uS) = \"100\"\nPockels_delay(1uS) = \"1400\"\nPockels_number = \"20\"\nPockels_period(1uS) = \"200\"\nPockels_pulse(1uS) = \"20\"\nTS0_Delay(1uS) = \"0\"\nTS0_Period(1uS) = \"0\"\nEnable_IOs = \"1\"\nA1_SW_enable = \"1\"\nA2_SW_enable = \"1\"\nA4_SW_enable = \"1\"\nCMOSPOn = \"1\"\nCMOSLOn = \"1\"\nEnd_of_file = \"empty\""

        if not os.path.exists("../../data/%s" % timestamp):
            os.mkdir("../../data/%s" % timestamp)

        if mode == "mpts_manual_cal":
            savemat('../../data/%s/TTS%s_%d_Cal.mat' % (timestamp, timestamp.replace("-", ""), shot_number), {'cam1': data1, 'cam2': data2, 'Edirect': Ed, 'Ereturn': Er, 'II_PS': II_PS, 'II_Gain': II_Gain, 'II_Coarse': II_Coarse, 'II_Fine': II_Fine, 'MCPdur': t, 'MCPVoltage': mcp,
                                                                                                                'scope_time': scope_time, 'scope_pockels': scope_pockels, 'scope_Edirect': scope_Edirect, 'scope_Ereturn': scope_Ereturn, 'scope_MCPTrigger': scope_MCPTrigger,
                                                                                                                'adc_time': adc_time, 'adc_Edirect': adc_Edirect, 'adc_Ereturn': adc_Ereturn, 'crio_settings': crio_settings, "Timer": Timer, "Trigger": Trigger, "OpMode": OpModeName}, do_compression=True)
        elif mode == "mpts_manual":
            savemat('../../data/%s/TTS%s_%d_Stray.mat' % (timestamp, timestamp.replace("-", ""), shot_number), {'cam1': data1, 'cam2': data2, 'Edirect': Ed, 'Ereturn': Er, 'II_PS': II_PS, 'II_Gain': II_Gain, 'II_Coarse': II_Coarse, 'II_Fine': II_Fine, 'MCPdur': t, 'MCPVoltage': mcp,
                                                                                                                'scope_time': scope_time, 'scope_pockels': scope_pockels, 'scope_Edirect': scope_Edirect, 'scope_Ereturn': scope_Ereturn, 'scope_MCPTrigger': scope_MCPTrigger,
                                                                                                                'adc_time': adc_time, 'adc_Edirect': adc_Edirect, 'adc_Ereturn': adc_Ereturn, 'crio_settings': crio_settings, "Timer": Timer, "Trigger": Trigger, "OpMode": OpModeName}, do_compression=True)
        else:
            savemat('../../data/%s/TTS%s_%d.mat' % (timestamp, timestamp.replace("-", ""), shot_number), {'cam1': data1, 'cam2': data2, 'Edirect': Ed, 'Ereturn': Er, 'II_PS': II_PS, 'II_Gain': II_Gain, 'II_Coarse': II_Coarse, 'II_Fine': II_Fine, 'MCPdur': t, 'MCPVoltage': mcp,
                                                                                                          'scope_time': scope_time, 'scope_pockels': scope_pockels, 'scope_Edirect': scope_Edirect, 'scope_Ereturn': scope_Ereturn, 'scope_MCPTrigger': scope_MCPTrigger,
                                                                                                          'adc_time': adc_time, 'adc_Edirect': adc_Edirect, 'adc_Ereturn': adc_Ereturn, 'crio_settings': crio_settings, "Timer": Timer, "Trigger": Trigger, "OpMode": OpModeName}, do_compression=True)


if __name__ == "__main__":
    sys.exit(main(sys.argv))

