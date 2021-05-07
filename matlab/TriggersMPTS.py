import numpy as np
import matplotlib.pyplot as plt



class TriggersSubclass(object):
    pass

class Triggers(object): 

    def __init__(self, TriggerSet=None, FlashSet=None, PockelsSet=None, IISet=None, CMOSSet=None, ADCSet=None, PlotOn=0):
        """Trigger = TriggersMPTS.Triggers([1,0], [1,100],[1,3e6,200,20,20,1000], [1,15, 10, 5,5,0], [1,0,10,10,5,2],[1,0,0.2e5], 1)
         M.Kantor version on 28.07.2017
          ===================================
         1. Return pulse timing of measurement cycle for multipass TS diagnostic in AUG
         2. Time sequences of the pulses are calculated for 8 channels from input data.
         3. The channels are activated in accordance to the operation mode
         4. All times in the measurement cycle are counted from the first Pockels cell (PC)
            trigger in laser burst
         InTime - absolute times of unit input
         OutTime - absolute times of unit output
         Delay - time delay between units outputs (Start) and unit input trigger
          ========================
         TriggerSet  = [TriggerMode,AUGShotStart]
         FlashSet  = [FlashOn, FlashWidth (us)]
         [PockelsOn,PockelsFirstTime (us),PockelsPeriod (us),PockelsN,
               PockelsWidth (us),PockelsRetard (us)]
         [IIOn,IIBeforeN, IIAfterN, IIGateLaserWidth (us), IIGatePlasmaWidth
               (us),IIGateLaserFiberDelay (us)]
         [CMOSLaserOn,CMOSPlasmaOn, CMOSBeforeN, CMOSAfterN, CMOSTrigWidth (us), CMOSDeltaGate (us)]
          ================================

         TriggerSet  = [TriggerMode,AUGShotStart]
         TriggerMode -  1 - Burst is started from AUG, T1 and T2 modes
                        0 - start from Simmer timer (manual start) (M1 and M2)
                       -1 - Start from Burst trigger (M2 mode without laser)
         AUGShotStart, time of AUG T06 pulse (us) which triggers Burst timer

         FlashSet - array.
         FlashSet  = [FlashOn, FlashWidth (us)]
         FlashOn - Enable/disable of flash triggers
         FlashWidth - the width of the flash trigger (us)

         PockelsSet - array:
         [PockelsOn,PockelsFirstTime (us),PockelsPeriod (us),PockelsN, PockelsWidth (us),PockelsRetard (us)]
         PockelsOn - Enable/disable of Pockels triggers
         PockelsFirstTime - time of the first PC pulse, us
         PockelsPeriod period of this pulses (us),
         PockelsN the number of PC pulses,
         PockelsWidth - duration of PC pulses (us),
         PockelsRetard - Delay of the 1st Pockels pulse after Flash

         IISet - array
         [IIOn,IIBeforeN, IIAfterN, IIGateLaserWidth (us), IIGatePlasmaWidth (us),IIGateLaserFiberDelay (us)]
         IIOn - Enable/disable of the II triggers
         IIBeforeN - the number of twin pulses before PC pulses
         IIAfterN  - the number of twin pulses after PC pulses
         IIGateLaserWidth - GateLaser, duration of II gates during laser pulses(us),
                       the first pulse in twins
         IIGatePlasmaWidth - GatePlasma, duration of II gate between laser pulses for pplasma light measurements (us)
                       the second pulse in twins
         IIGateLaserFiberDelay - fine delay of II gates triggered by the ruby laser via fiber for fine sinc of laser pulses.
         The delay is also applicable for triggers from IIGatePlasma

         CMOSSet - array, settings triggeres for CMOS cameras
         [CMOSLaserOn,CMOSPlasmaOn, CMOSBeforeN, CMOSAfterN, CMOSTrigWidth (us), CMOSDeltaGate (us)]
         CMOSLaserOn, CameraPlasmaOn - Enable/Disable switch of Camera1 and Camera2
         CMOSBeforeN - the number of twin CMOS pulses before the first II gate
         CMOSAfterN - the number of twin CMOS pulses after the last II gate
         CMOSTrigWidth - duration of trigger pulses of CMOS cameras, (us)
         CMOSDeltaGate - Difference between CMOS and II gates,CMOSDeltaGate> = 0, us
                          CMOSDeltaGate is set in the cameras
         If two camears are active than the CMOSLaser trigger is generated
         for the 1st camera and the CMOSPlasma is generated for the 2nd camera
         Otherwise, all pulses are generated for a single camera

         ADCSet   array. The zero time is synchronized with the 1st PC pulses in the bursts
          [ADCOn,StartADC,StopADC]
         if 1 then ADCSet is calculated from the pulse sequence

         Trigger times of Cahrge and Simmer timers are defined in Timers.m

          ==========================================================================
         Data range and defaults settings for timers  [Min,Step,Max,Default]
          ==========================================================================

         Operation modes:

         T-modes   - TS is triggered from AUG
         AUG triggeres:
         TZ60 - pretrigger at -60 ms comes to Charge timer
         TS06 - start of plasma shot comes to Burst timer
         SimmerTimer is triggered by delayed output of the Carge timer
         T1 mode: All three timers are disabled.
            Operator manually enables Charge timer before plasma shot
            All timers are desibled after plasma shot
         T2 mode: Charge timer is enabled, Simmer and Burst are disabled
            Simmer and Burst are enabled by Charge trigger and disabled after
            plasma shot

         M-modes   - TS is triggered by operator without any AUG triggeres.
         Laser charged by operator and Charge output does not trigger Simmer timer
         Operation with laser is started from Simmer timer which triggeres Burst
         timer after some delay
         Operation without laser is started from Burst timer
                  which cannot be triggered by Simmer timer.
         All timers are enabled manually
         M1 mode: Manual trigger of the diagnostic without plasma
                  (Rayleigh calibration, stray light measurements)
         M2 mode: Manual trigger of the diagnostic without laser
                  (spectral calibrations,alignment of the cameras)
         M3 mode: Manual trigger of ruby laser
                  without CMOS cameras and image intensifier.
        """

        #  ====================================================
        # Default values:
        SimmerMinWait = 2e6     # us minimal delay between simmer and flash triggers
        TriggerModeDef = 1      # 1 - Burst is started from AUG TS06 pulse,
                                # 0 - start from Simmer timer (manual start)

        # Laser defaults:
        FlashOnDef = 1
        PockelsFirstTimeDef = 0  # us, Absolute time of the 1st Pockels pulse
        PockelsWidthDef = 10  # us
        PockelsRetardDef = 1000  # us, delay of the 1st Pockels pulse from the flash start
        PockelsNDef = 10
        PockelsPeriodDef = 200  # us

        # image intensifier defaults:
        IIBeforeNDef = 10
        IIAfterNDef = 20
        IIGateLaserWidthDef = 2
        IIGatePlasmaWidthDef = 20
        IIPlasmaRetardWidthDef = 5  # us

        # CMOS defaults
        CMOSBeforeNDef = 10
        CMOSAfterNDef = 20
        CMOSTrigWidthDef = 5  # us
        CMOSDeltaGateDef = 2  # us
        CMOSLaserGateDef = IIGateLaserWidthDef + CMOSDeltaGateDef
        CMOSPlasmaGateDef = IIGatePlasmaWidthDef + CMOSDeltaGateDef
        IIOnDef = 1
        CMOSOnDef = [1, 1]

        AUGShotStartDef = PockelsFirstTimeDef - (IIBeforeNDef + CMOSBeforeNDef) * PockelsPeriodDef
        if TriggerSet is None:
            AUGShotStart = AUGShotStartDef  # trigger from AUG
        TriggerModeRange = [-1, 1, 1, TriggerModeDef]


        # Burst, is triggered from AUG or Simmer timer.
        #        triggers Flash, IIGatePlasma,CMOSPlasmaOnRange and ADC
        # absolute time of output pulses from Burst timer:

        if TriggerModeDef:
            # Start from AUGShotStart
            BurstInTimeDef = AUGShotStartDef
        else:
            # Start form Simmer
            BurstInTimeDef = 0

        BurstDelayDef = SimmerMinWait
        BurstOutTimeDef = BurstInTimeDef + BurstDelayDef

        BurstWidthDef = 100
        BurstPeriodDef = 3e5
        BurstNDef = 1

        BurstPeriodRange = [1e5, 1e5, 1e7, BurstPeriodDef]
        BurstWidthRange = [100, 100, 100, BurstWidthDef]
        BurstNRange = [1, 1, 4, BurstNDef]

        # Laser times
        # Flash, pulses starting flash discharge. One per a pulse from Burst timer
        # absolute time of output pulses from Burst trigger:
        FlashOutTimeDef = PockelsFirstTimeDef - PockelsRetardDef
        # Delay between output and input triggers:
        FlashDelayDef = FlashOutTimeDef - BurstOutTimeDef
        FlashInTimeDef = BurstOutTimeDef
        FlashOnRange = [0, 1, 1, FlashOnDef]
        FlashDelayRange = [0, 10, 10000, FlashDelayDef]  # Delay of Flash output
        FlashPeriodRange = [0, 0, 0, 0]
        FlashWidthRange = [50, 50, 200, 100]
        FlashNRange = [1, 1, 1, 1]
        # FlashBool,   Gate of all Pockels pulses. Triggered by Flash
        # absolute time of output pulses from Flash trigger:
        # Delay between output and input triggers:

        # Pockels,  Gates of Pockels cell. Reapeted in each burst. Triggered by Flash
        # absolute time of the 1st output pulse from Pockels trigger:

        PockelsOnRange = [0, 1, 1, FlashOnDef]      # Delay between output and input triggers:
        PockelsRetardDef = PockelsFirstTimeDef - FlashInTimeDef
        PockelsRetardRange = [0, 1, 10000, PockelsRetardDef]
        PockelsPeriodRange = [50, 25, 1000, PockelsPeriodDef]
        PockelsWidthRange = [1, 1, 30, PockelsWidthDef]
        PockelsNRange = [0, 1, 100, PockelsNDef]

        # II times:
        # IIPlasmaRetard,  Trigger of IIGatesLaser. Triggered by IIGatePlasma
        # absolute time of output pulse from IIPlasmaRetard:
        # Delay between starts of plasma and laser II gates:
        IIPlasmaRetardDelayDef = np.fix((PockelsPeriodDef + IIGatePlasmaWidthDef - IIGateLaserWidthDef) / 2)  # us
        IIPlasmaRetardDelayRange = [0, 0.1, 2000, IIPlasmaRetardDelayDef]
        IIPlasmaRetardPeriodRange = [0, 0, 0, 0]
        IIPlasmaRetardWidthRange = [1, 1, 5, IIPlasmaRetardWidthDef]

        # IIGatePlasma,  Gates of image intensifier between pockels gates. Triggered by Burst timer
        # absolute time of output pulses from IIGatePlasma:
        IIGatePlasmaOutTimeDef = PockelsFirstTimeDef + PockelsWidthDef - IIGateLaserWidthDef - IIBeforeNDef * PockelsPeriodDef - IIPlasmaRetardDelayDef
        # Delay between output and input triggers:
        IIGatePlasmaDelayDef = IIGatePlasmaOutTimeDef - BurstOutTimeDef
        IIGatePlasmaPeriodRange = PockelsPeriodRange
        IIGatePlasmaWidthRange = [1, 1, 100, IIGatePlasmaWidthDef]  # formulas
        IIGatePlasmaNRange = [0, 1, 100, PockelsNDef + IIBeforeNDef + IIAfterNDef]

        # IIGateLaser,  Gate of image intensifier triggered by IIPlasmaRetard or
        #              external laser trigger
        # absolute time of output pulses from IIGateLaser:
        # IIGateLaserOutTimeDef = IIPlasmaRetardOutTimeDef

        # Delay between output and input triggers:
        IIGateLaserPeriodRange = [0, 0, 0, 0]
        IIGateLaserWidthRange = [0.1, 0.1, 10, IIGateLaserWidthDef]

        # Sum of IIGateLaser and IIGatePlasma
        # IIGate  =  IIGateLaser | IIGatePlasma

        # CMOS times:
        # CMOSLaser trigger of Laser CMOS
        # absolute time of output pulse from CMOSLaser:
        CMOSLaserOutTimeDef = PockelsFirstTimeDef + PockelsWidthDef - IIGateLaserWidthDef - IIBeforeNDef * PockelsPeriodDef

        # Delay between output and input triggers:
        CMOSLaserDelayDef = np.fix((PockelsPeriodDef + CMOSPlasmaGateDef - CMOSLaserGateDef) / 2)  # us
        CMOSLaserPeriodRange = [0, 0, 0, 0]
        # CMOSPlasma,  Pulses opening Plasma CMOS camera and triggered by Burst timer:
        #         The exposure time is set by the camera software
        # absolute time of output pulse from CMOSPlasma:
        CMOSPlasmaOutTimeDef = CMOSLaserOutTimeDef - CMOSLaserDelayDef   # wrong?
        CMOSPlasmaOutTimeDef = IIGatePlasmaOutTimeDef - IIGatePlasmaDelayDef - np.fix(CMOSDeltaGateDef / 2) - CMOSTrigWidthDef
        # Delay between output and input triggers:
        CMOSPlasmaNRange = [0, 1, 100, PockelsNDef + IIBeforeNDef + IIAfterNDef + CMOSBeforeNDef + CMOSAfterNDef]

        # ADC
        # absolute time of output pulses from ADC:
        ADCStartDef = min([FlashInTimeDef, IIGatePlasmaOutTimeDef, CMOSPlasmaOutTimeDef])
        ADCDelayDef = ADCStartDef - BurstOutTimeDef
        ADCWidthDef = (PockelsNDef + IIBeforeNDef + IIAfterNDef + CMOSBeforeNDef + CMOSAfterNDef) * PockelsPeriodDef
        ADCOnRange = [0, 1, 1, 1]
        ADCStartRange = [-5000, 10, 0, ADCDelayDef]
        ADCPeriodRange = [0, 0, 0, 0]
        ADCWidthRange = [100, 100, 50000, ADCWidthDef]
        ADCNRange = FlashNRange
        # end Default values
        #  ==============================

        # ==========================================================================
        # Read input data:
        # ==========================================================================
        # Readout Pockels  ======================================  =
        PockelsOn = PockelsOnRange[3]
        PockelsFirstTime = PockelsFirstTimeDef
        PockelsPeriod = PockelsPeriodRange[3]
        PockelsWidth = PockelsWidthRange[3]
        PockelsN = PockelsNRange[3]
        PockelsRetard = PockelsRetardRange[3]
        if PockelsSet is not None:
            PockelsOn = PockelsSet[0]
            PockelsFirstTime = PockelsSet[1]
            PockelsPeriod = PockelsSet[2]
            PockelsN = PockelsSet[3]
            PockelsWidth = PockelsSet[4]
            PockelsRetard = PockelsSet[5]

        # Readout Flash  ======================================
        FlashOn = FlashOnRange[3]
        FlashDelay = FlashDelayRange[3]
        FlashPeriod = FlashPeriodRange[3]
        FlashWidth = FlashWidthRange[3]
        FlashN = FlashNRange[3]
        if FlashSet is not None:
            FlashOn = FlashSet[0]
            FlashWidth = FlashSet[1]

        # Readout II  ======================================  =
        # IIGatePlasma:
        IIOn = IIOnDef
        IIGatePlasmaOn = IIOn
        IIGatePlasmaPeriod = IIGatePlasmaPeriodRange[3]
        IIGatePlasmaWidth = IIGatePlasmaWidthRange[3]
        IIGatePlasmaN = IIGatePlasmaNRange[3]
        IIBeforeN = IIBeforeNDef
        IIAfterN = IIAfterNDef
        IIPlasmaRetardOn = 1
        IIPlasmaRetardWidth = IIPlasmaRetardWidthRange[3]
        IIPlasmaRetardDelay = IIPlasmaRetardDelayRange[3]
        IIPlasmaRetardN = 1
        IIPlasmaRetardPeriod = IIPlasmaRetardPeriodRange[3]
        IIGateLaserOn = IIOn
        IIGateLaserWidth = IIGateLaserWidthRange[3]
        IIGateLaserPeriod = IIGateLaserPeriodRange[3]
        IIGateLaserN = 1
        if IISet is not None:
            IIOn = IISet[0]
            IIGatePlasmaOn = IIOn
            IIGateLaserOn = IIOn
            IIBeforeN = IISet[1]
            IIAfterN = IISet[2]
            IIGateLaserWidth = IISet[3]
            IIGatePlasmaWidth = IISet[4]
            IIGateLaserFiberDelay = IISet[5]
            IIGatePlasmaPeriod = PockelsPeriod
            IIGatePlasmaN = IIBeforeN + IIAfterN + PockelsN
            IIPlasmaRetardDelay = np.fix((PockelsPeriod + IIGatePlasmaWidth - IIGateLaserWidth) / 2)  # us
        # IIPlasmaRetard

        # Readout CMOS  =======================================
        # CMOSPlasma
        CMOSLaserOn = CMOSOnDef[0]
        CMOSPlasmaOn = CMOSOnDef[1]
        CMOSPlasmaPeriod = PockelsPeriodRange[3]
        CMOSPlasmaN = CMOSPlasmaNRange[3]
        CMOSLaserN = 1
        CMOSLaserPeriod = CMOSLaserPeriodRange[3]
        CMOSTrigWidth = CMOSTrigWidthDef
        CMOSDeltaGate = CMOSDeltaGateDef
        CMOSBeforeN = CMOSBeforeNDef
        CMOSAfterN = CMOSAfterNDef

        CMOSLaserGate = IIGateLaserWidth + CMOSDeltaGate
        CMOSPlasmaGate = IIGatePlasmaWidth + CMOSDeltaGate
        # Delay between output and input triggers:
        if CMOSSet is not None:
            CMOSLaserOn = CMOSSet[0]
            CMOSPlasmaOn = CMOSSet[1]
            CMOSBeforeN = CMOSSet[2]
            CMOSAfterN = CMOSSet[3]
            CMOSTrigWidth = CMOSSet[4]
            CMOSDeltaGate = CMOSSet[5]
            CMOSLaserGate = IIGateLaserWidth + CMOSDeltaGate
            CMOSPlasmaGate = IIGatePlasmaWidth + CMOSDeltaGate
            CMOSPlasmaN = CMOSBeforeN + CMOSAfterN + IIBeforeN + IIAfterN + PockelsN
            CMOSPlasmaPeriod = PockelsPeriod

        if not (CMOSLaserOn and CMOSPlasmaOn):
            CMOSMaxWidth = max([CMOSLaserGate, CMOSPlasmaGate])
            CMOSLaserGate = CMOSMaxWidth
            CMOSPlasmaGate = CMOSMaxWidth

        # Readout ADC  ============================================
        ADCOn = ADCOnRange[3]
        ADCStart = ADCStartRange[3]
        ADCPeriod = ADCPeriodRange[3]
        ADCWidth = ADCWidthRange[3]
        ADCN = ADCNRange[3]
        ADCStart = ADCStartDef
        ADCWidth = ADCWidthDef
        if ADCSet is not None:
            ADCOn = ADCSet[0]
            if len(ADCSet) == 3:
                ADCStart = ADCSet[1]
                ADCWidth = ADCSet[2] - ADCSet[1]
            else:
                ADCStart = 0
                ADCWidth = 0

        # Readout Burst  ==========================================================  =
        TriggerMode = TriggerModeRange[3]
        AUGShotStart = AUGShotStartDef
        BurstWidth = BurstWidthDef
        BurstPeriod = BurstPeriodDef
        BurstN = BurstNDef
        if TriggerSet is not None:
            TriggerMode = TriggerSet[0]
            AUGShotStart = TriggerSet[1]
            if TriggerMode == 1:
                AUGShotStart = TriggerSet[1]
            else:
                AUGShotStart = SimmerMinWait + PockelsRetard
            BurstPeriod = BurstPeriodRange[3]
            BurstWidth = BurstWidthRange[3]
            BurstN = BurstNRange[3]

        BurstOn = 1

        FlashBoolOn = FlashOn
        FlashBoolN = BurstN
        FlashBoolPeriod = BurstPeriod
        FlashBoolWidth = np.fix(PockelsN * PockelsPeriod / 10) * 10

        # ======================================================  =
        # Absolute times of input triggers:
        # ======================================================  =

        # FlashInTime = PockelsFirstTime-PockelsRetard
        # FlashInTime = PockelsFirstTime-PockelsRetard-FlashDelay # ok

        MaxBeforeInterval = max([(IIBeforeN + CMOSBeforeN + 1) * PockelsPeriod, PockelsRetard]) + PockelsPeriod

        if TriggerMode:  # start from AUG (T modes)
            BurstInTime = AUGShotStart
            BurstDelay = BurstInTime - AUGShotStart    # wrong
        else:    # Start from Simmer (manual modes)
            BurstInTime = 0
            BurstDelay = SimmerMinWait

        BurstOutTime = BurstInTime + BurstDelay

        PockelsFirstTimeMin = BurstOutTime + MaxBeforeInterval
        PockelsFirstTimeDelta = PockelsFirstTimeMin - PockelsFirstTime
        PockelsFirstTime = max([PockelsFirstTimeMin, PockelsFirstTime])
        PockelsFirstTimeDelta = max([PockelsFirstTimeDelta, 0])

        FlashOutTime = PockelsFirstTime - PockelsRetard
        FlashInTime = BurstOutTime
        FlashDelay = FlashOutTime - FlashInTime

        PockelsInTime = FlashOutTime

        FlashBoolOutTime = np.fix(PockelsFirstTime - PockelsPeriod / 2)
        FlashBoolInTime = FlashOutTime
        FlashBoolDelay = FlashBoolOutTime - FlashBoolInTime

        IIGatePlasmaInTime = BurstOutTime
        IIGatePlasmaOutTime = PockelsFirstTime + PockelsWidth - IIGateLaserWidth - IIBeforeN * PockelsPeriod - IIPlasmaRetardDelay
        IIGatePlasmaDelay = IIGatePlasmaOutTime - IIGatePlasmaInTime

        IIPlasmaRetardInTime = IIGatePlasmaOutTime
        IIPlasmaRetardOutTime = IIPlasmaRetardInTime + IIPlasmaRetardDelay

        IIGateLaserInTime = IIPlasmaRetardOutTime
        IIGateLaserOutTime = PockelsFirstTime + PockelsWidth - IIGateLaserWidth - IIBeforeN * PockelsPeriod
        IIGateLaserDelay = IIGateLaserOutTime - IIGateLaserInTime

        CMOSLaserOutTime= IIGateLaserOutTime-CMOSTrigWidth-(PockelsWidth-IIGateLaserWidth) - np.fix(CMOSDeltaGate/2)-(CMOSBeforeN-1)*PockelsPeriod;
        CMOSLaserDelay=np.fix((PockelsPeriod+CMOSPlasmaGate-CMOSLaserGate)/2); 
        CMOSLaserInTime=CMOSLaserOutTime-CMOSLaserDelay;

        CMOSPlasmaOutTime=CMOSLaserInTime; 
        CMOSPlasmaDelay=CMOSPlasmaOutTime-BurstOutTime;
        CMOSPlasmaInTime=CMOSPlasmaOutTime- CMOSPlasmaDelay;
        # ==========================================================================
        # settings basic pulses which are repeatedly generated
        # There are four parent triggeres which are started by the Burst timer:
        #   Flash,  IIGatePlasma,  CMOSPlasma and ADC
        # Other triggeres are started by the parent outputs
        # times of parent triggers are counted from the output of the Burst timer.
        # ==========================================================================
        # Burst - grand parent:
        BurstBase = np.array([[0, 0], [0, 1], [BurstWidth, 1], [BurstWidth, 0]])
        Burst = BurstBase
        BurstTimeWindow = [Burst[0, 0], Burst[-1, 0]]
        FlashBase = np.array([[0, 0], [0, 1], [FlashWidth, 1], [FlashWidth, 0]])
        FlashBoolBase = np.array([[0, 0], [0, 1], [FlashBoolWidth, 1], [FlashBoolWidth, 0]])
        PockelsBase = np.array([[0, 0], [0, 1], [PockelsWidth, 1], [PockelsWidth, 0]])

        IIGatePlasmaBase = np.array([[0, 0], [0, 1], [IIGatePlasmaWidth, 1], [IIGatePlasmaWidth, 0]])
        IIPlasmaRetardBase = np.array([[0, 0], [0, 1], [IIPlasmaRetardWidth, 1], [IIPlasmaRetardWidth, 0]])
        IIGateLaserBase = np.array([[0, 0], [0, 1], [IIGateLaserWidth, 1], [IIGateLaserWidth, 0]])
        # ==========================================================================

        # ==========================================================================
        # Time sequences from triggers:
        # ==========================================================================
        # Flash is triggered by Burst:
        Flash = FlashBase  # single pulse
        Flash[:, 0] = Flash[:, 0] + FlashInTime + FlashDelay
        FlashBool = FlashBoolBase  # single pulse
        FlashBool[:, 0] = FlashBool[:, 0] + FlashBoolOutTime
        Pockels = np.array([PockelsBase[:, 0], PockelsBase[:, 1]]).T
        for i in range(1, PockelsN):
            Pockels = np.append(Pockels, np.array([PockelsBase[:, 0] + i * PockelsPeriod, PockelsBase[:, 1]]).T, axis=0)
        if PockelsFirstTime == FlashInTime + FlashDelay + PockelsRetard:
            Pockels[:, 0] = Pockels[:, 0] + PockelsFirstTime
        else:
            print('PockelsFirstTime')
            return

        LaserTimeWindow = [Flash[1, 1], Pockels[-1, 0] + PockelsWidth]

        # IIGatePlasma is triggered by Flash:
        IIGatePlasma = np.array([IIGatePlasmaBase[:, 0], IIGatePlasmaBase[:, 1]]).T
        IIPlasmaRetard = np.array([IIPlasmaRetardBase[:, 0], IIPlasmaRetardBase[:, 1]]).T
        IIGateLaser = np.array([IIGateLaserBase[:, 0], IIGateLaserBase[:, 1]]).T
        for i in range(1, IIBeforeN + PockelsN + IIAfterN):
            IIGatePlasma = np.append(IIGatePlasma, np.array([IIGatePlasmaBase[:, 0] + i * PockelsPeriod, IIGatePlasmaBase[:, 1]]).T, axis=0)
            IIPlasmaRetard = np.append(IIPlasmaRetard, np.array([IIPlasmaRetardBase[:, 0] + i * PockelsPeriod, IIPlasmaRetardBase[:, 1]]).T, axis=0)
            IIGateLaser = np.append(IIGateLaser, np.array([IIGateLaserBase[:, 0] + i * PockelsPeriod, IIGateLaserBase[:, 1]]).T, axis=0)

        if IIGatePlasmaOutTime == BurstOutTime + IIGatePlasmaDelay:
            IIGatePlasma[:, 0] = IIGatePlasma[:, 0] + IIGatePlasmaOutTime
        else:
            raise 'IIGatePlasmaOutTime'
        if IIPlasmaRetardOutTime == IIGatePlasmaOutTime + IIPlasmaRetardDelay:
            IIPlasmaRetard[:, 0] = IIPlasmaRetard[:, 0] + IIPlasmaRetardOutTime
        else:
            raise 'IIPlasmaRetardOutTime'
        if IIGateLaserOutTime == BurstOutTime + IIGatePlasmaDelay + IIPlasmaRetardDelay:
            IIGateLaser[:, 0] = IIGateLaser[:, 0] + IIGateLaserOutTime
        else:
            raise 'IIGateLaserOutTime'
        # IIGateLaser(IIGateLaser[:, 0] >FlashBool[0, 0]&IIGateLaser[:, 0] <FlashBool[-1, 0], 2) = 0

        IITimeWindow = [IIGatePlasma[0, 0], IIGateLaser[-1, 0] + IIGateLaserWidth]

        # CMOSPlasma is triggered by Flash:
        CMOSPlasmaBase = np.array([[0, 0], [0, 1], [CMOSTrigWidth, 1], [CMOSTrigWidth, 0]])
        CMOSLaserBase = np.array([[0, 0], [0, 1], [CMOSTrigWidth, 1], [CMOSTrigWidth, 0]])
        CMOSLaser = CMOSPlasmaBase
        CMOSPlasma = CMOSLaserBase
        # CMOSPlasmaRetard = []
        for i in range(1, CMOSBeforeN + IIBeforeN + PockelsN + IIAfterN + CMOSAfterN):
            CMOSPlasma = np.append(CMOSPlasma, np.array([CMOSPlasmaBase[:, 0] + i * PockelsPeriod, CMOSPlasmaBase[:, 1]]).T, axis=0)
            # CMOSPlasmaRetard = [CMOSPlasmaRetard[CMOSPlasmaRetardBase[:, 0] + i * PockelsPeriod, CMOSPlasmaRetardBase[:, 1]]])
            CMOSLaser = np.append(CMOSLaser, np.array([CMOSLaserBase[:, 0] + i * PockelsPeriod, CMOSLaserBase[:, 1]]).T, axis=0)

        CMOSPlasma[:, 0] = CMOSPlasma[:, 0] + CMOSPlasmaOutTime
        CMOSLaser[:, 0] = CMOSLaser[:, 0] + CMOSLaserOutTime

        CMOSTimeWindow = [CMOSPlasma[0, 0], CMOSLaser[-1, 0] + CMOSLaserGate]

        # ADC:
        ADCInTime = BurstOutTime
        ADCOutTime = PockelsFirstTime + ADCStart
        print(PockelsFirstTime, ADCStart)
        ADCDelay= ADCOutTime - ADCInTime 
        ADC = np.array([[0, 0], [0, 1], [ADCWidth, 1], [ADCWidth, 0]])
        ADC[:, 0] = ADC[:, 0] + ADCStart
        if ADCStart == 0 and ADCWidth == 0:
            ADCStart = CMOSTimeWindow[0]
            ADCWidth = CMOSTimeWindow[1] - ADCStart
            ADCDelay = ADCStart - BurstInTime
            ADC = np.array([[0, 0], [0, 1], [ADCWidth, 1], [ADCWidth, 0]])
            ADC[:, 0] = ADC[:, 0] + ADCStart

        # Outputs of trigger channels:
        print('  Channel   |     From      |      To       |Enable  |Delay_us|Period_us|Number |Width_us')

        # Burst Timer:
        # Burst - grand parent:
        self.Burst = TriggersSubclass()
        self.Burst.On = BurstOn
        self.Burst.From = 'T0orSimm'
        self.Burst.To = 'Four trigg'
        self.Burst.InTime = BurstInTime
        self.Burst.OutTime = BurstOutTime
        self.Burst.Delay = BurstDelay
        self.Burst.Width = BurstWidth
        self.Burst.Period = BurstPeriod
        self.Burst.N = BurstN
        print('  Burst     |%15s|%15s| %6d | %6d | %6d | %6d | %6d' % (self.Burst.From, self.Burst.To, TriggerMode, BurstDelay, BurstPeriod, BurstN, BurstWidth))

        if self.Burst.OutTime == FlashInTime:
            self.Flash = TriggersSubclass()
            self.Flash.From = 'Burst'
            self.Flash.To = 'FlashBool&Pock'
            self.Flash.InTime = FlashInTime
            self.Flash.OutTime = FlashOutTime
            self.Flash.Delay = FlashDelay
            self.Flash.Width = FlashWidth
            self.Flash.Period = FlashPeriod
            self.Flash.N = FlashN
        else:
            raise ('Error: self.Burst.OutTime<>FlashInTime')

        print('  Flash     |%15s|%15s| %6d | %6d | %6d | %6d | %6d |' % (self.Flash.From, self.Flash.To, FlashOn, FlashDelay, FlashPeriod, FlashN, FlashWidth))

        if self.Flash.OutTime == FlashBoolInTime:
            self.FlashBool = TriggersSubclass()
            self.FlashBool.From = 'Flash'
            self.FlashBool.To = 'IIGateLaser'
            self.FlashBool.InTime = FlashBoolInTime
            self.FlashBool.OutTime = FlashBoolOutTime
            self.FlashBool.Delay = FlashBoolDelay
            self.FlashBool.Width = FlashBoolWidth
            self.FlashBool.Period = FlashBoolPeriod
            self.FlashBool.N = 1
        else:
            raise 'Error: self.Flash.OutTime<>FlashBoolInTime'

        print(' FlashBool  |%15s|%15s| %6d | %6d | %6d | %6d | %6d |' % (self.FlashBool.From, self.FlashBool.To, FlashBoolOn, FlashBoolDelay, FlashBoolPeriod, FlashBoolN, FlashBoolWidth))

        if self.Flash.OutTime == PockelsInTime:
            self.Pockels = TriggersSubclass()
            self.Pockels.From = 'Flash'
            self.Pockels.To = 'Pock cell'
            self.Pockels.InTime = PockelsInTime
            self.Pockels.PockelsFirstTime = PockelsFirstTime  # OutTime
            self.Pockels.Retard = PockelsRetard     # Delay
            self.Pockels.Width = PockelsWidth
            self.Pockels.Period = PockelsPeriod
            self.Pockels.N = PockelsN
        else:
            raise 'Error: self.Flash.OutTime<>PockelsInTime'

        print(' Pockels    |%15s|%15s| %6d | %6d | %6d | %6d | %6d |' % (self.Pockels.From, self.Pockels.To, PockelsOn, PockelsRetard, PockelsPeriod, PockelsN, PockelsWidth))

        if self.Burst.OutTime == IIGatePlasmaInTime:
            self.IIGatePlasma = TriggersSubclass()
            self.IIGatePlasma.From = 'Burst'
            self.IIGatePlasma.To = 'IIGate[1]&IIPlRetrd'
            self.IIGatePlasma.InTime = IIGatePlasmaInTime
            self.IIGatePlasma.OutTime = IIGatePlasmaOutTime
            self.IIGatePlasma.Delay = IIGatePlasmaDelay
            self.IIGatePlasma.Width = IIGatePlasmaWidth
            self.IIGatePlasma.Period = IIGatePlasmaPeriod
            self.IIGatePlasma.N = IIGatePlasmaN
        else:
            raise 'Error: self.Burst.OutTime<>IIGatePlasmaInTime'

        print('IIGatePlasma|%15s|%15s|  %d | %6d | %6d | %6d | %6d |' % (self.IIGatePlasma.From, self.IIGatePlasma.To, IIGatePlasmaOn, IIGatePlasmaDelay, IIGatePlasmaPeriod, IIGatePlasmaN, IIGatePlasmaWidth))

        if self.IIGatePlasma.OutTime == IIPlasmaRetardInTime:
            self.IIPlasmaRetard = TriggersSubclass()
            self.IIPlasmaRetard.From = 'IIGatePlasma'
            self.IIPlasmaRetard.To = 'IIGateLaser'
            self.IIPlasmaRetard.InTime = IIPlasmaRetardInTime
            self.IIPlasmaRetard.OutTime = IIPlasmaRetardOutTime
            self.IIPlasmaRetard.Delay = IIPlasmaRetardDelay  # Check this
            self.IIPlasmaRetard.Width = IIPlasmaRetardWidth
            self.IIPlasmaRetard.Period = IIPlasmaRetardPeriod
            self.IIPlasmaRetard.N = IIPlasmaRetardN
        else:
            raise ('Error: self.IIGatePlasma.OutTime<>IIPlasmaRetardInTime')

        print('IIPlasmaRet |%15s|%15s| %6d | %6d | %6d | %6d | %6d |' % (self.IIPlasmaRetard.From, self.IIPlasmaRetard.To, IIPlasmaRetardOn, IIPlasmaRetardDelay, IIPlasmaRetardPeriod, IIPlasmaRetardN, IIPlasmaRetardWidth))

        if self.IIPlasmaRetard.OutTime == IIGateLaserInTime:
            self.IIGateLaser = TriggersSubclass()
            self.IIGateLaser.From = 'FlashBool,IIPlRet,LaserPuls'
            self.IIGateLaser.To = 'IIGates[0]'
            self.IIGateLaser.InTime = IIGateLaserInTime
            self.IIGateLaser.OutTime = IIGateLaserOutTime
            self.IIGateLaser.Delay = IIGateLaserDelay
            self.IIGateLaser.FiberDelay = IIGateLaserFiberDelay
            self.IIGateLaser.Width = IIGateLaserWidth
            self.IIGateLaser.Period = IIGateLaserPeriod
            self.IIGateLaser.N = IIGateLaserN
        else:
            raise ('Error: self.IIGatePlasma.OutTime<>IIPlasmaRetardInTime')

        print('IIGateLaser |   FlashBool   |   %s  | %6d | %6d | %6d | %6d | %6d |' % (self.IIGateLaser.To, IIGateLaserOn, IIGateLaserDelay, IIGateLaserPeriod, IIGateLaserN, IIGateLaserWidth))
        print('            |IIPlRet&LasPuls|                           ')

        if self.Burst.OutTime == CMOSPlasmaInTime:
            self.CMOSPlasma = TriggersSubclass()
            self.CMOSPlasma.On = CMOSPlasmaOn
            self.CMOSPlasma.From = 'Burst'
            self.CMOSPlasma.To = 'CMOSTr[1],CMOSPlRet'
            self.CMOSPlasma.InTime = CMOSPlasmaInTime
            self.CMOSPlasma.OutTime = CMOSPlasmaOutTime
            self.CMOSPlasma.Delay = CMOSPlasmaDelay
            self.CMOSPlasma.Width = CMOSTrigWidth
            self.CMOSPlasma.Period = CMOSPlasmaPeriod
            self.CMOSPlasma.N = CMOSPlasmaN
            self.CMOSPlasma.Gate = CMOSPlasmaGate
        else:
            raise 'Error: self.Burst.OutTime<>CMOSPlasmaInTime'

        print('CMOSPlasma  |%15s|%15s|  %d | %6d | %6d | %6d | %6d |' % (self.CMOSPlasma.From, self.CMOSPlasma.To, self.CMOSPlasma.On, CMOSPlasmaDelay, CMOSPlasmaPeriod, CMOSPlasmaN, CMOSTrigWidth))

        if self.CMOSPlasma.OutTime == CMOSLaserInTime:
            self.CMOSLaser = TriggersSubclass()
            self.CMOSLaser.On = CMOSLaserOn
            self.CMOSLaser.From = 'CMOSPlRetrd'
            self.CMOSLaser.To = 'CMOSTrigger[0]'
            self.CMOSLaser.InTime = CMOSLaserInTime
            self.CMOSLaser.OutTime = CMOSLaserOutTime
            self.CMOSLaser.Delay = CMOSLaserDelay
            self.CMOSLaser.Width = CMOSTrigWidth
            self.CMOSLaser.Period = CMOSLaserPeriod
            self.CMOSLaser.N = CMOSLaserN
            self.CMOSLaser.Gate = CMOSLaserGate
        else:
            raise 'Error: self.CMOSPlasma.OutTime<>CMOSLaserInTime'

        self.SimmerMinWait = SimmerMinWait
        self.TriggerMode = TriggerMode

        print('CMOSLaser   |%15s|%15s| %6d | %6d | %6d | %6d | %6d |' % (self.CMOSLaser.From, self.CMOSLaser.To, CMOSLaserOn, CMOSLaserDelay, CMOSLaserPeriod, CMOSLaserN, CMOSTrigWidth))

        # ADC parent:
        self.ADC = TriggersSubclass()
        self.ADC.From = 'Burst'
        self.ADC.To = 'Digitizer'
        self.ADC.Delay = ADCDelay
        self.ADC.Period = ADCPeriod
        self.ADC.Width = ADCWidth
        self.ADC.N = ADCN
        print(' ADC        |%15s|%15s| %6d | %6d | %6d | %6d | %6d |\n' % (self.ADC.From, self.ADC.To, ADCOn, self.ADC.Delay, ADCPeriod, ADCN, ADCWidth))

        xmin = min([BurstTimeWindow[0], LaserTimeWindow[0], IITimeWindow[0], CMOSTimeWindow[0]]) - round(PockelsPeriod)
        xmin = xmin - PockelsFirstTime
        xmax = max([BurstTimeWindow[1], LaserTimeWindow[1], IITimeWindow[1], CMOSTimeWindow[1]]) + round(PockelsPeriod)
        xmax = xmax - PockelsFirstTime
        ymin = -0.1
        ymax = 1.1

        if PlotOn==2:
    
            fig, axes = plt.subplots(8, 1, sharex=True)
            axes[0].plot(ADC[:, 0] - PockelsFirstTime, ADC[:, 1], 'b', lw=2, label='ADC')
            plt.title('Fast channels started by Burst')
            if PockelsOn:
                Flash = np.insert(Flash, 0, [xmin, Flash[0, 1]], axis=0)
                Flash = np.append(Flash, [[xmax, Flash[0, -1]]], axis=0)
                axes[1].plot(Flash[:, 0] - PockelsFirstTime, Flash[:, 1], 'k', lw=2, label='Flash')
            if PockelsOn:
                Pockels = np.insert(Pockels, 0, [xmin, Pockels[0, 1]], axis=0)
                Pockels = np.append(Pockels, [[xmax, Pockels[0, -1]]], axis=0)
                axes[2].plot(Pockels[:, 0] - PockelsFirstTime, Pockels[:, 1], 'r', lw=2, label='Pockels')
            if IIOn:
                IIGatePlasma = np.insert(IIGatePlasma, 0, [xmin, IIGatePlasma[0, 1]], axis=0)
                IIGatePlasma = np.append(IIGatePlasma, [[xmax, IIGatePlasma[0, -1]]], axis=0)
                axes[3].plot(IIGatePlasma[:, 0] - PockelsFirstTime, IIGatePlasma[:, 1], '--c', lw=2, label='IIGatePlasma')
            if IIOn:
                IIGateLaser = np.insert(IIGateLaser, 0, [xmin, IIGateLaser[0, 1]], axis=0)
                IIGateLaser = np.append(IIGateLaser, [[xmax, IIGateLaser[0, -1]]], axis=0)
                plt.plot(IIGateLaser[:, 0] - PockelsFirstTime, IIGateLaser[:, 1], 'c', lw=2, label='IIGateLaser')
                if FlashBoolOn:
                    axes[4].plot(FlashBool[:, 0] - PockelsFirstTime, 0.5 * FlashBool[:, 1], 'k', lw=2, label='IIGateLaser')
            if CMOSLaserOn:
                CMOSLaser = np.insert(CMOSLaser, 0, [xmin, CMOSLaser[0, 1]], axis=0)
                CMOSLaser = np.append(CMOSLaser, [[xmax, CMOSLaser[0, -1]]], axis=0)
                axes[5].plot(CMOSLaser[:, 0] - PockelsFirstTime, CMOSLaser[:, 1], 'g', lw=2, label='CMOSLaser')
            if CMOSPlasmaOn:
                CMOSPlasma = np.insert(CMOSPlasma, 0, [xmin, CMOSPlasma[0, 1]], axis=0)
                CMOSPlasma = np.append(CMOSPlasma, [[xmax, CMOSPlasma[0, -1]]], axis=0)
                axes[6].plot(CMOSPlasma[:, 0] - PockelsFirstTime, CMOSPlasma[:, 1], '--g', lw=2, label='CMOSPlasma')
            if True:  # if AUGTriggerOn == 1:
                Burst = np.insert(Burst, 0, [xmin, Burst[0, 1]], axis=0)
                Burst = np.append(Burst, [[xmax, Burst[0, -1]]], axis=0)
                axes[7].plot(Burst[:, 0], Burst[:, 1], '--k', lw=2, label='Burst')
            plt.axis([xmin, xmax, ymin, ymax])
            plt.xlabel(r't, $\mu$s')
            plt.legend()
            plt.show()
        
        if PlotOn:
            plt.figure()
            plt.plot(ADC[:, 0] - PockelsFirstTime, ADC[:, 1], 'b', lw=2, label='ADC')
            plt.plot(Flash[:, 0] - PockelsFirstTime, 1.5 + Flash[:, 1], 'k', lw=2, label='Flash')
            plt.plot(Pockels[:, 0] - PockelsFirstTime, 3 + Pockels[:, 1], 'r', lw=2, label='Pockels')
            plt.plot(IIGateLaser[:, 0] - PockelsFirstTime, 4.5 + IIGateLaser[:, 1], 'c', lw=2, label='IIGateLaser')
            plt.plot(IIGatePlasma[:, 0] - PockelsFirstTime, 6 + IIGatePlasma[:, 1], '--c', lw=2, label='IIGatePlasma')
            plt.plot(CMOSLaser[:, 0] - PockelsFirstTime, 7.5 + CMOSLaser[:, 1], 'g', lw=2, label='CMOSLaser')
            plt.plot(CMOSPlasma[:, 0] - PockelsFirstTime, 9 + CMOSPlasma[:, 1], '--g', lw=2, label='CMOSPlasma')
            plt.plot(Burst[:, 0] - PockelsFirstTime, 11.5 + Burst[:, 1], '--k', lw=2, label='Burst')
            plt.xlabel(r't, $\mu$s')
            plt.legend()
            plt.show()


class VoiddSubclass(object):
    pass

class TimerMPTS(object):

    def __init__(self, Trigger=None, ChargeOn=None, SimmerOn=None, PlotOn=False):
        #
        # M.Kantor version on 28.07.2016
        # ==================================  =
        # 1. Return pulse timing of preparatoty cycle for multipass TS diagnostic in AUG
        # 2. Time sequences of the pulses are calculated for 5 channels from input data.
        # 3. The channels are activated in accordance to the operation mode
        # 4. All times in the preparatory cycle are counted from the first Pockels cell (PC)
        #    trigger in laser burst
        # 5. Trigger is returned by TriggerMPTS.m

        # Delay  -  time delays in timer units,
        # Start  -  absolute time of outputs from timers

        # ChargeSet = [ChargeOn, AUGCharge]
        # ChargeOn  -   1  -  start from AUG,  0  -  start manually
        # AUGChargeStart,  time of AUG TS0 pulse (us). AUGChargeDef = 6e7

        # SimmerSet = [SimmerOn, SimmerStart, SimmerWidth]
        # SimmerOn    1 in laser modes,   0  -  operation without laser
        # SimmerStart  -  start of the simmer current      1 in laser modes,   0  -  operation without laser
        #               SimmerOn = 0  -  no output
        #               SimmerOn = 1
        #                          ChargeOn = 1  SimmerStart =  f(1st PC,  SimmerMinTime)
        #                          ChargeOn = 0  SimmerStart = 0

        # BurstSet  = [BurstOn, AUGT0]
        # BurstOn  -   1  -  start from AUG,  0  -  start from Simmer timer (manual start)
        # AUGShotStart, time of T06 pulse (us). The pulse comes to Burst timer

        # EnableSet  = [EnableOn, EnableWidth]
        # EnableOn  -   1  - 
        # EnableWidth  -  start of Enable output
        #              EnableOn = 1: EnableStart  = f(1st PC, AUTS0)
        #              EnableOn = 0: EnableStart  = SimmerMinTime

        # LaserTriggerSet  = [LaserTriggerWidth]
        # LaserTriggerWidth  -  start of LaserTrigger output
        #              LaserTriggerOn = 1: LaserTriggerStart  = f(1st PC, AUTS0)
        #              LaserTriggerOn = 0: LaserTriggerStart  = SimmerMinTime

        AUGChargeStart = -15e6  # us
        TriggerMode = Trigger.TriggerMode
        SimmerMinWait = Trigger.SimmerMinWait

        ChargeInTime = 0
        ChargeWidth = 100
        ChargeDelay = 0
        ChargeBase = np.array([[0, 0], [0, 1], [ChargeWidth, 1], [ChargeWidth, 0]])
        if ChargeOn:
            ChargeInTime = AUGChargeStart
        ChargeOutTime = ChargeInTime + ChargeDelay
        Charge = ChargeBase
        Charge[:, 0] = Charge[:, 0] + ChargeOutTime

        SimmerWidth = 100
        if TriggerMode and ChargeOn:  # Start from AUGShotStart:
            SimmerInTime = ChargeOutTime
            SimmerDelay = Trigger.Flash.InTime - SimmerInTime - SimmerMinWait
            SimmerOutTime = SimmerInTime + SimmerDelay
        else:   # Manual simmer start
            SimmerDelay = 0
            SimmerOutTime = Trigger.Burst.InTime
            SimmerInTime = SimmerOutTime - SimmerDelay

        SimmerBase = np.array([[0, 0], [0, 1], [SimmerWidth, 1], [SimmerWidth, 0]])
        Simmer = SimmerBase
        Simmer[:, 0] = Simmer[:, 0] + SimmerOutTime

        BurstInTime = Trigger.Burst.InTime
        BurstN = Trigger.Burst.N
        BurstDelay = Trigger.Burst.Delay
        BurstOutTime = BurstInTime + BurstDelay
        BurstPeriod = Trigger.Burst.Period
        BurstWidth = Trigger.Burst.Width
        BurstBase = np.array([[0, 0], [0, 1], [BurstWidth, 1], [BurstWidth, 0]])
        Burst = np.array([BurstBase[:, 0], BurstBase[:, 1]]).T
        for i in range(1, BurstN):
            Burst = np.append(Burst, np.array([BurstBase[:, 0] + i * BurstPeriod, BurstBase[:, 1]]).T, axis=0)
        if SimmerOn:
            Burst[:, 0] = Burst[:, 0] + BurstOutTime

        EnableDelay = 0
        EnableInTime = SimmerOutTime + SimmerDelay
        EnableOutTime = EnableInTime + EnableDelay
        EnableWidth = BurstDelay + Trigger.Flash.Delay + Trigger.Pockels.Retard
        # EnableWidth=ceil((PockelsFirstTime+(BurstN-1)*BurstPeriod-EnableInTime)/1e5)*1e5;
        EnableBase = np.array([[0, 0], [0, 1], [EnableWidth, 1], [EnableWidth, 0]])
        Enable = EnableBase
        Enable[:, 0] = Enable[:, 0] + EnableOutTime

        LaserTriggerDelay = 0
        LaserTriggerInTime = EnableOutTime
        LaserTriggerOutTime = LaserTriggerInTime + LaserTriggerDelay
        LaserTriggerWidth = 100
        LaserTriggerBase = np.array([[0, 0], [0, 1], [LaserTriggerWidth, 1], [LaserTriggerWidth, 0]])
        LaserTrigger = LaserTriggerBase
        # start simmer current:
        LaserTrigger[:, 0] = LaserTrigger[:, 0] + LaserTriggerOutTime
        # start flash current:
        LaserTrigger = np.append(LaserTrigger, np.array([[0, 0], [0, 1], [LaserTriggerWidth, 1], [LaserTriggerWidth, 0]]), axis=0)
        LaserTrigger[4:8, 0] = LaserTrigger[4:8, 0] + Trigger.Flash.OutTime

        # Outputs of timer channels:
        print('  Channel   |      From     |      To        |Enable|Delay(us)|Width(us)')
        # Charge Timer:
        # Burst  -  grand parent:
        self.Charge = VoiddSubclass()
        self.Charge.On = ChargeOn
        self.Charge.From = 'AUG|Man'
        self.Charge.To = 'Charge&Simmer'
        self.Charge.InTime = ChargeInTime
        self.Charge.OutTime = ChargeOutTime
        self.Charge.Delay = 0
        self.Charge.Width = ChargeWidth
        self.Charge.Period = 0
        self.Charge.N = 1
        print('  Charge    |%15s| %15s| %d | %7d | %4d' % (self.Charge.From, self.Charge.To, ChargeOn, 0, ChargeWidth))

        # Simmer timer:
        self.Simmer = VoiddSubclass()
        self.Simmer.On = SimmerOn
        self.Simmer.From = 'Charge|Man'
        self.Simmer.To = 'Burst&AND1'
        self.Simmer.InTime = SimmerInTime
        self.Simmer.OutTime = SimmerOutTime
        self.Simmer.Delay = SimmerDelay
        self.Simmer.Width = SimmerWidth
        self.Simmer.Period = 0
        self.Simmer.N = 1
        print('  Simmer    |%15s| %15s| %d | %7d | %4d' % (self.Simmer.From, self.Simmer.To, SimmerOn, SimmerDelay, SimmerWidth))

        self.Enable = VoiddSubclass()
        self.Enable.On = 1
        self.Enable.From = 'Simmer'
        self.Enable.To = 'LaserTrigger'
        self.Enable.InTime = EnableInTime
        self.Enable.OutTime = EnableOutTime
        self.Enable.Delay = 0
        self.Enable.Width = EnableWidth
        self.Enable.Period = 0
        self.Enable.N = 1
        print(' Enable     |%15s| %15s| %d | %7d | %4d' % (self.Enable.From, self.Enable.To, 1, 0, EnableWidth))

        self.LaserTrigger = VoiddSubclass()
        self.LaserTrigger.On = 1
        self.LaserTrigger.From = 'Enable&Flash'
        self.LaserTrigger.To = 'Laser'
        self.LaserTrigger.InTime = LaserTriggerInTime
        self.LaserTrigger.OutTime = LaserTriggerOutTime
        self.LaserTrigger.Delay = 0
        self.LaserTrigger.Width = LaserTriggerWidth
        self.LaserTrigger.Period = 0
        self.LaserTrigger.N = 1
        print('LaserTrigger|%15s| %15s| %d | %7d | %4d' % (self.LaserTrigger.From, self.LaserTrigger.To, 1, 0, LaserTriggerWidth))

        if PlotOn:
            PlotN = 5
            xmin = min([Simmer[0, 0], Burst[0, 0], Enable[0, 0], LaserTrigger[0, 0]]) - round(Trigger.Pockels.Period)
            xmax = max([Simmer[-1, 0], Burst[-1, 0], Enable[-1, 0], LaserTrigger[-1, 0]]) + round(Trigger.Pockels.Period)

            f, ax = plt.subplots(PlotN, 1, sharex=True) 
            if ChargeOn:
                Charge = np.insert(Charge, 0, [xmin, Charge[0, 1]], axis=0)
                Charge = np.append(Charge, [[xmax, Charge[0, -1]]], axis=0)
                ax[0].plot(1e-6 * Charge[:, 0], Charge[:, 1], 'k', lw=2, label='Charge')
            plt.title('Slow channels')
            if SimmerOn:
                Simmer = np.insert(Simmer, 0, [xmin, Simmer[0, 1]], axis=0)
                Simmer = np.append(Simmer, [[xmax, Simmer[0, -1]]], axis=0)
                ax[1].plot(1e-6 * Simmer[:, 0], Simmer[:, 1], 'b', lw=2, label='Simmer')
            Burst = np.insert(Burst, 0, [xmin, Burst[0, 1]], axis=0)
            Burst = np.append(Burst, [[xmax, Burst[0, -1]]], axis=0)
            ax[2].plot(1e-6 * Burst[:, 0], Burst[:, 1], 'r', lw=2, label='Burst')
            Enable = np.insert(Enable, 0, [xmin, Enable[0, 1]], axis=0)
            Enable = np.append(Enable, [[xmax, Enable[0, -1]]], axis=0)
            ax[3].plot(1e-6 * Enable[:, 0], Enable[:, 1], 'g', lw=2, label='Enable')
            if SimmerOn:
                LaserTrigger = np.insert(LaserTrigger, 0, [xmin, LaserTrigger[0, 1]], axis=0)
                LaserTrigger = np.append(LaserTrigger, [[xmax, LaserTrigger[0, -1]]], axis=0)
                ax[4].plot(1e-6 * LaserTrigger[:, 0], LaserTrigger[:, 1], 'c', lw=2, label='LaserTrigger')
            plt.legend()
            plt.show()

            plt.figure()
            plt.plot(Charge[:, 0], 0.5 * Charge[:, 1], 'k', lw=2, label='Charge')
            plt.plot(Simmer[:, 0], 1.2 * Simmer[:, 1], 'b', lw=2, label='Simmer')
            plt.plot(Burst[:, 0], 1.2 * Burst[:, 1], 'r', lw=2, label='Burst')
            plt.plot(Enable[:, 0], Enable[:, 1], 'g', lw=2, label='Enable')
            plt.plot(LaserTrigger[:, 0], 0.8 * LaserTrigger[:, 1], 'c', lw=2, label='LaserTrigger')
            plt.legend()
            plt.show()


def CrioConfigFile(Trigger, Timer, Filename, IIGateShift=0, PlotOn=False):
    # creates config file for crio system from Times
    # Trigger is returned by TriggerMPTS.m
    # Timer is returned by TimersMPTS.m
    # IIGateShift - shift of IIGate triggers, us

    file = open(Filename, 'w')
    file.write('Simmer_delay(1uS) = "%1.0f"\n' % Timer.Simmer.Delay)
    file.write('Burst_delay(1uS) = "%1.0f"\n' % Trigger.Burst.Delay)
    file.write('Burst_number = "%1.0f"\n' % Trigger.Burst.N)
    file.write('Burst_period(1uS) = "%1.0f"\n' % Trigger.Burst.Period)
    file.write('Trigger_Enable_pulse(1uS) = "%1.0f"\n' % Timer.Enable.Width)

    file.write('ADC_Enable_delay(1uS) = "%1.0f"\n' % Trigger.ADC.Delay)
    file.write('ADC_Enable_pulse(1uS) = "%1.0f"\n' % Trigger.ADC.Width)

    file.write('CMOS_plasma_delay(1uS) = "%1.0f"\n' % Trigger.CMOSPlasma.Delay)
    file.write('CMOS_Plasma_number = "%1.0f"\n' % Trigger.CMOSPlasma.N)
    file.write('CMOS_Plasma_period(1uS) = "%1.0f"\n' % Trigger.CMOSPlasma.Period)
    file.write('CMOS_Plasma_pulse(1uS) = "%1.0f"\n' % Trigger.CMOSPlasma.Width)

    file.write('CMOS_Laser_delay(0.1uS) = "%1.0f"\n' % (10 * Trigger.CMOSLaser.Delay))
    file.write('CMOS_Laser_pulse(0.1uS) = "%1.0f"\n' % (10 * Trigger.CMOSLaser.Width))

    file.write('II_Gate_Plasma_delay(0.1uS) = "%1.0f"\n' % (10 * (Trigger.IIGatePlasma.Delay + IIGateShift)))
    file.write('II_Gate_Plasma_number = "%1.0f"\n' % Trigger.IIGatePlasma.N)
    file.write('II_Gate_Plasma_period(0.1uS) = "%1.0f"\n' % (10 * Trigger.IIGatePlasma.Period))
    file.write('II_Gate_Plasma_pulse(0.1uS) = "%1.0f"\n' % (10 * Trigger.IIGatePlasma.Width))
    file.write('II_Plasma_Delay_delay(0.1uS) = "%1.0f"\n' % (10 * (Trigger.IIPlasmaRetard.Delay + IIGateShift)))
    file.write('II_Plasma_Delay_pulse(0.1uS) = "%1.0f"\n' % (10 * Trigger.IIPlasmaRetard.Width))

    file.write('II_Gate_Laser_delay(0.1uS) = "%1.0f"\n' % (10 * (Trigger.IIGateLaser.Delay + IIGateShift)))
    file.write('II_Gate_Laser_pulse(0.1uS) = "%1.0f"\n' % (10 * Trigger.IIGateLaser.Width))

    file.write('II_Flash_Bool_delay(1uS) = "%1.0f"\n' % Trigger.FlashBool.Delay)
    file.write('II_Flash_Bool_pulse(1uS) = "%1.0f"\n' % Trigger.FlashBool.Width)

    file.write('Flash_delay(1uS) = "%1.0f"\n' % Trigger.Flash.Delay)
    file.write('Flash_pulse(1uS) = "%1.0f"\n' % Trigger.Flash.Width)

    file.write('Pockels_delay(1uS) = "%1.0f"\n' % Trigger.Pockels.Retard)
    file.write('Pockels_number = "%1.0f"\n' % Trigger.Pockels.N)
    file.write('Pockels_period(1uS) = "%1.0f"\n' % Trigger.Pockels.Period)
    file.write('Pockels_pulse(1uS) = "%1.0f"\n' % Trigger.Pockels.Width)
    file.write('End_of_file = "empty"\n')
    file.write('=======================\n')
    if Trigger.CMOSLaser.On and Trigger.CMOSPlasma.On:
        file.write('CMOSLaser Number = "%1.0f"\n' % Trigger.Burst.N * Trigger.CMOSPlasma.N)
        file.write('CMOSPlasma Number  = "%1.0f"\n' % Trigger.Burst.N * Trigger.CMOSPlasma.N)
    if Trigger.CMOSLaser.On and not (Trigger.CMOSPlasma.On):
        file.write('CMOSLaser Number = "%1.0f"\n' % (2 * Trigger.Burst.N * Trigger.CMOSPlasma.N))
    if not(Trigger.CMOSLaser.On) and Trigger.CMOSPlasma.On:
        file.write('CMOSPlasma Number = "%1.0f"\n' % (2 * Trigger.Burst.N * Trigger.CMOSPlasma.N))
    file.write('Laser CMOSOn= "%1.0f"\n' % Trigger.CMOSLaser.On)
    file.write('Plasma CMOSOn= "%1.0f"\n' % Trigger.CMOSPlasma.On)

    if not(Trigger.CMOSLaser.On) and not (Trigger.CMOSPlasma.On):
        file.write('Both CMOS cameras Off\n')

    file.close()

    if PlotOn:
        print('Simmer_delay(1uS) = %d' % Timer.Simmer.Delay)
        print('Burst_delay(1uS) = %d' % Trigger.Burst.Delay)
        print('Burst_number = %d' % Trigger.Burst.N)
        print('Burst_period(1uS) = %d' % Trigger.Burst.Period)
        print('Trigger_Enable_pulse(1uS) = %d' % Timer.Enable.Width)

        print('ADC_Enable_delay(1uS) = %d' % Trigger.ADC.Delay)
        print('ADC_Enable_pulse(1uS) = %d' % Trigger.ADC.Width)

        print('CMOS_plasma_delay(1uS) = %d' % Trigger.CMOSPlasma.Delay)
        print('CMOS_Plasma_number = %d' % Trigger.CMOSPlasma.N)
        print('CMOS_Plasma_period(1uS) = %d' % Trigger.CMOSPlasma.Period)
        print('CMOS_Plasma_pulse(1uS) = %d' % Trigger.CMOSPlasma.Width)

        print('CMOS_Laser_delay(0.1uS) = %d' % (10 * Trigger.CMOSLaser.Delay))
        print('CMOS_Laser_pulse(0.1uS) = %d' % (10 * Trigger.CMOSLaser.Width))

        print('II_Gate_Plasma_delay(0.1uS) = %d' % (10*(Trigger.IIGatePlasma.Delay + IIGateShift)))
        print('II_Gate_Plasma_number = %d' % Trigger.IIGatePlasma.N)
        print('II_Gate_Plasma_period(0.1uS) = %d' % (10 * Trigger.IIGatePlasma.Period))
        print('II_Gate_Plasma_pulse(0.1uS) = %d' % (10 * Trigger.IIGatePlasma.Width))
        print('II_Plasma_Delay_delay(0.1uS) = %d' % (10*(Trigger.IIPlasmaRetard.Delay+IIGateShift)))
        print('II_Plasma_Delay_pulse(0.1uS) = %d' % (10 * Trigger.IIPlasmaRetard.Width))

        print('II_Gate_Laser_delay(0.1uS) = %d' % (10 * (Trigger.IIGateLaser.Delay+IIGateShift)))
        print('II_Gate_Laser_pulse(0.1uS) = %d' % (10 * Trigger.IIGateLaser.Width))

        print('II_Flash_Bool_delay(1uS) = %d' % Trigger.FlashBool.Delay)
        print('II_Flash_Bool_pulse(1uS) = %d' % Trigger.FlashBool.Width)

        print('Flash_delay(1uS) = %d' % Trigger.Flash.Delay)
        print('Flash_pulse(1uS) = %d' % Trigger.Flash.Width)

        print('Pockels_delay(1uS) = %d' % Trigger.Pockels.Retard)
        print('Pockels_number = %d' % Trigger.Pockels.N)
        print('Pockels_period(1uS) = %d' % Trigger.Pockels.Period)
        print('Pockels_pulse(1uS) = %d' % Trigger.Pockels.Width)


Trig = Triggers([1, 0],  # [TriggerMode,AUGShotStart]
                [1, 100],       # FlashSet  = [FlashOn, FlashWidth (us)]
                [1, 3e6, 200, 20, 20, 1000],  # [PockelsOn,PockelsFirstTime (us),PockelsPeriod (us),PockelsN, PockelsWidth (us),PockelsRetard (us)] 
                [1, 15, 10, 5, 5, 0],  # [IIOn,IIBeforeN, IIAfterN, IIGateLaserWidth (us), IIGatePlasmaWidth(us),IIGateLaserFiberDelay (us)]
                [1, 0, 10, 10, 5, 2],  # [CMOSLaserOn,CMOSPlasmaOn, CMOSBeforeN, CMOSAfterN, CMOSTrigWidth (us), CMOSDeltaGate (us)]
                [1, 0, 0.2e5],  # [ADCOn,StartADC,StopADC]
                False)
Timer = TimerMPTS(Trig, 1, 1, 0)  # TimerMPTS(Trigger, ChargeOn, SimmerOn, PlotOn)
CrioConfigFile(Trig, Timer, "teste.txt", IIGateShift=0, PlotOn=False)