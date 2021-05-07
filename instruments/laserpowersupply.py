#!/usr/bin/env python
# -*- coding: latin-1 -*-
"""Implementation of the Laser Power Supply control."""

import serial
import time


class LaserPowerSupply():
    """Class for controll MegaWatt Power Supply for InLight Laser system."""

    def __init__(self, port=None, baudrate=9600, timeout=0.1, debug=False):
        self.resBankMain = -1
        self.resBankAux = -1
        self.resBurstNumber = -1
        self.resBurstDuration = -1
        self.MainVoltage = -1
        self.Aux1Voltage = -1
        self.Aux2Voltage = -1
        self.Aux3Voltage = -1
        self.AuxDelay = -1
        self.ComAuxVoltage = -1
        self.BurstNumber = -1
        self.AccurChargeV = -1
        self.SignalReady = -1
        self.TriggerSimmer = -1
        self.ModeBanks = -1
        self.SimmerDelay = -1
        self.BurstSeperation = -1
        self.ntub = 6
        self.status = -1
        self.coolingstatus = -1
        self.versionPS = ""
        self.versionCooling = ""
        self.BurstDuration = -1

        self.connection_status = False
        self.debug = debug
        self.ser = serial.Serial()
        self.ser.baudrate = baudrate
        self.ser.timeout = timeout
        if port:
            self.openConnection(port, baudrate, timeout)

    def openConnection(self, port='COM1', baudrate=9600, timeout=0.1):
        self.ser.port = port
        self.ser.baudrate = baudrate
        self.ser.timeout = timeout
        self.ser.write_timeout = 1
        try:
            self.ser.open()
            self.ser.reset_output_buffer()
            self.ser.reset_input_buffer()
            self.ser.write(b"$VER\r")
            self.versionPS = self.ser.readline().decode("latin-1")[:25]
            self.connection_status = True
        except:
            print("Error trying to connect to Laser Power Supply (Serial port %s, baudrate %s)." % (self.ser.port, self.ser.baudrate))
            self.connection_status = False

    def isConnected(self):
        if not self.ser.isOpen():
            self.connection_status = False
            return False
        try:
            # Makes a simple request and wait for the answer to check if the connection is working
            self.ser.reset_output_buffer()
            self.ser.reset_input_buffer()
            self.ser.write(b"$VER\r")
            recv = self.ser.readline()
            if len(recv) > 0:
                self.connection_status = True
                return True
            else:
                self.connection_status = False
                return False
        except:
            self.connection_status = False
            return False

    def closeConnection(self):
        if self.ser.isOpen():
            self.ser.close()
        self.connection_status = False

    def configure_serial(self, port, baudrate, timeout):
        self.ser.port = port or self.port
        self.ser.baudrate = baudrate or self.baudrate
        self.ser.timeout = timeout or self.timeout

    # 1. Auxiliary functions

    def _write(self, command):
        """ Writes a command to the instrument."""
        if self.connection_status:
            if self.debug:
                print("laser PS: >>%s" % command)
            self.ser.write(bytearray(command + "\r", "latin-1"))
            self.ser.flush()  # it is buffering. required to get the data out *now*
            time.sleep(0.07)
            return self._read()

    def _read(self):
        """ Reads a response from the instrument.
        This function will block until the instrument responds."""
        ans = ""
        while self.ser.in_waiting > 0:
            char = self.ser.read(1).decode("latin-1")
            if char == "\r":
                break
            ans += char
        if self.debug:
            print("laser PS: <<%s" % ans)
        return ans

    def _query(self, command):
        """ Writes a command to the instrument and reads the response."""
        ans = self._write(command)
        if self.ser.in_waiting > 0:
            if self.debug:
                print("laser PS (ignored): <<%s" % self.ser.read(self.ser.in_waiting))
            else:
                self.ser.read(self.ser.in_waiting)
        return ans

    # 1. Set restrictions parameter

    def setResMainVoltage(self, voltage):
        # Sets maximum voltage of main bank
        if voltage != self.resBankMain and (50 <= voltage <= 1000):
            self._write("$MVL%d" % voltage)
            self.resBankMain = int(voltage)

    def setResAuxVoltage(self, voltage):
        # $MV2n  max value Aux Bank is 1500
        if voltage != self.resBankAux and (50 <= voltage <= 1500):
            self._write("$MV2%d" % voltage)
            self.resBankAux = int(voltage)

    def setResBurstNumber(self, d):
        # $MVCn max value Number of Bursts is 3
        if (d != self.resBurstNumber and (1 <= d <= 3)):
            self._write("$MVC%d" % d)
            self.resBurstNumber = int(d)

    def setResBurstDuration(self, d):
        # $MVDn max value Duration of Burst is 10.0
        if (d != self.resBurstDuration):
            self._write("$MVD%.1f" % d)
            self.resBurstDuration = d

    # 2. Set operation mode

    def setModeBanks(self, d):
        """$MDAn set mode for setting voltage of the auxiliary banks
        n0 = charge only main bank
        n1 = auxiliary banks voltages are set manualy, the same for all banks
        n2 = auxiliary banks voltages are calculated
        n3 = auxiliary banks voltages are set manualy, independently for all banks"""
        if (d != self.ModeBanks):
            self._write("$MDA%d" % d)
            self.ModeBanks = d

    def getModeBanks(self):
        ans = self._query("$?MDA")
        return int(ans)

    def setModePC(self, d):
        # $POF(PC) / $PON(ControlPanel)
        if d == 0:
            self._write("$POF")
            self.modePCCP = 0
        elif d == 1:
            self._write("$PON")
            self.modePCCP = 1

    def setSignalReady(self, d):
        # $SMDn set ready signal mode
        if (d != self.SignalReady and (0 <= d <= 1)):
            self._write("$SMD%d" % d)
            self.SignalReady = d

    def getSignalReady(self):
        # $?SMDa get signal ready mode
        ans = self._query("$?SMD")
        return int(ans)

    def setTriggerSimmer(self, d):
        # $SFNn set trigger simmer mode
        if (d != self.TriggerSimmer and (0 <= d <= 1)):
            self._write("$SFN%d" % d)
            self.TriggerSimmer = d

    def getTriggerSimmer(self):
        ans = self._query("$?SFN")
        return int(ans)

    # 3. Set parameters

    def setMainVoltage(self, voltage):
        """$SVLn set Main Bank Voltage"""
        if (voltage != self.MainVoltage and (50 <= voltage <= 1000)):
            self._write("$SVL%d" % voltage)
            self.MainVoltage = int(voltage)

    def setComAuxVoltage(self, voltage):
        if (voltage != self.ComAuxVoltage and (50 <= voltage <= 1500)):
            self._write("$SV2%d" % voltage)  # $SV2n set Aux Bank Voltage to all Banks
            self.ComAuxAuxVoltage = int(voltage)

    def setAux1Voltage(self, voltage):
        # $SkAn set Aux Bank Voltage to k-th Bank (bank 1)
        if (voltage != self.Aux1Voltage and (50 <= voltage <= 1500)):
            self._write("$S1A%d" % voltage)  # $SkAn set Aux Bank Voltage to k-th Bank (bank 1)
            self.Aux1Voltage = int(voltage)

    def setAux2Voltage(self, voltage):
        if (voltage != self.Aux2Voltage and (50 <= voltage <= 1500)):
            self._write("$S2A%d" % voltage)
            self.Aux2Voltage = int(voltage)

    def setAux3Voltage(self, voltage):
        if (voltage != self.Aux3Voltage and (50 <= voltage <= 1500)):
            self._write("$S3A%d" % voltage)
            self.Aux3Voltage = int(voltage)

    def setAccurChargeV(self, tol):
        """Set Bank leakage tolerance (in %)
        Command: $DVLn where n is an intager = Voltage/Voltage Leakage tolerance
        """
        # $DVLn set U/dU
        if (tol != self.AccurChargeV):
            self._write("$DVL%d" % int(100. / tol))
            self.AccurChargeV = tol

    def setNBurst(self, d):
        # $SSCn set the number of bursts
        if d != self.BurstNumber and (1 <= d <= 3):
            self._write("$SSC%d" % 1)
            self.BurstNumber = int(d)

    def setBurstDuration(self, d):
        # $SSDn set duration of the burst
        if (d != self.BurstDuration):
            self._write("$SSD%d" % d)
            self.BurstDuration = d

    # 3.1 Parameter for operation with internal synchronization and $PON

    def setAuxDelay(self, d):
        """$SSP set delay between starts of the main and aself.xiliary banks discharge"""
        self._write("$SSP%.1f" % d)

    def setBurstSeperation(self, d):
        # $SP1n .. $SP2n set delay between first/second .. second/third flashes
        if (d != self.BurstSeperation):
            self._write("$SP1%.1f" % d)
            self._write("$SP2%.1f" % d)
            self.BurstSeperation = d

    def setSimmerDelay(self, d):
        # $SDS set delay between first flash and simmer start
        if (d != self.SimmerDelay):
            self._write("$SDS%.1f" % d)
            self.SimmerDelay = d

    def getBurstDuration(self):
        # $?SSD get duration of bursts
        ans = self._query("$?SSD")
        return float(ans)

    # 4.Measurements of parameters and its control

    def getResMainVoltage(self):
        # $?MVL get main bank restriction voltage
        ans = self._query("$?MVL")
        return int(ans)

    def getResAuxVoltage(self):
        # $?MV2 get auxiliary bank restriction voltage
        ans = self._query("$?MV2")
        return int(ans)

    def getResBurstNumber(self):
        # $?MVC get number restriction of bursts
        ans = self._query("$?MVC")
        return int(ans)

    def getNburst(self):
        # $?SSC get number of bursts
        ans = self._query("$?SSC")
        return int(ans)

    # 4.1 Parameters for operation with internal synchronization and $PON

    def getSimmerDelay(self):
        # $?SDS get delay between first flash and simmer start
        ans = self._query("$?SDS")
        return float(ans)

    def getBurstSeperation(self):
        # $?SP1 get delay between first/second flashes
        ans = self._query("$?SP1")
        return float(ans)

    def getAuxDelay(self):
        # $?SSP get delay between start of main and auxiliary bank discharges
        ans = self._query("$?SSP")
        return float(ans)

    def getResBurstDuration(self):
        # $?MVD  get duration restriction of burst
        ans = self._query("$?MVD")
        return float(ans)

    def getVoltageBanksAll(self):
        # $FRQ get voltages of main/auxiliary banks
        ans = self._query("$FRQ")
        # read voltage and apply corretion from linear regression
        voltages = [(int(x) - 21.73) / 0.825 for x in ans[5:].split(',')]
        # Remove negatives values
        voltages = [int(voltage) if voltage > 0 else 0 for voltage in voltages]
        return voltages

    def getLaserStatus(self):
        # $STS get Error status
        ans = self._query("$STS")
        self.status = int(ans)
        return ans

    def getPowerErrorStr(self):
        if not self.status:
            return "Connected"
        str = ''
        if (self.status & 1):
            str = str + "Common "
        if (self.status & 2):
            str = str + "/ Water Flow "
        if (self.status & 4):
            str = str + "/ Door Intrl "
        if (self.status & 8):
            str = str + "/ Table Intrl "
        if (self.status & 16):
            str = str + "/ Reserved "
        if (self.status & 32):
            str = str + "/ Key Off "
        if (self.status & 64):
            str = str + "/ Current "
        if (self.status & 256):
            str = str + "/ Flour > 330 "
        elif (self.status & 128):
            str = str + "/ Flour > 300 "
        if (self.status & 512):
            str = str + "/ Charge Unit "
        if (self.status & 1024):
            str = str + "/ Simmer Current"
        return str

    # 5. Operation commands

    def ChargeBank(self):
        self._write("$CHR")

    def DumpBank(self):
        # $DCR command to dump banks
        self._write("$DCR")

    def StartBank(self):
        # $STR command to start discharge of banks
        self._write("$STR")

    def Reset(self):
        # $RST reset system
        self._write("$RST")

    # 6. Cooling pump control

    # 6.1 Settings commands

    def setMinIntTemp(self, d):
        # #WN0n set minimum temperature of coolingwater
        self._write("#WM0%d" % d)

    def setMaxIntTemp(self, d):
        # #WM0n set maximum temperature of coolingwater
        self._write("#WM0%d" % d)

    def setOptIntFlow(self, d):
        # #FW0n set optimal internal water flow
        self._write("#FW0%d" % d)

    def setOptExtFlow(self, d):
        # #FW1n set optimal external water flow
        self._write("#FW1%d" % d)

    def setMinIntFlow(self, d):
        # #FE0 set minimal internal water flow
        self._write("#FE0%d" % d)

    # 6.2 Gettings commands

    def getIntWaterTemp(self):
        # #WT0 get temperature of cooling water
        self._write("#WT0")
        time.sleep(0.1)
        return int(self.ser.readline() / 10.)

    def getWaterQuality(self):
        # #QLT get quality of cooling water
        self._write("#QLT")
        time.sleep(0.1)
        return self.ser.readline().strip()

    def getIntWaterFlow(self):
        # #FL0 get internal water flow
        ans = self._query("#FL0")
        return int(ans)

    def getExtWaterFlow(self):
        # #FL1 get external water flo
        ans = self._query("#FL1")
        return int(ans)

    def getCoolingError(self):
        # #STS get system state
        ans = self._query("#STS")
        self.coolingstatus = int(ans)

    def getCoolingErrorStr(self, status):
        if (status & 0x0001):
            return "Fatal Error, flow / temperature / water level "
        if (status & 0x0002):
            return "Internal Flow error is below minimal preset "
        if (status & 0x0004):
            return "Flow Warning, interlock not open "
        if (status & 0x0008):
            return "Temperature error, is above 60 degrees "
        if (status & 0x0010):
            return "Water Level error, below critical minimum "
        if (status & 0x0020):
            return "Pump status "
        if (status & 0x0040):
            return "Water Quality error, interlock not open  "
        if (status & 0x0080):
            return "External Fluid Flow is below nominal "
        if (status & 0x0100):
            return "Internal Fluid Temperature is above maximum "
        if (status & 0x0200):
            return "Internal Fluid Coolant Temperature below minimal"
        return "Error NOT known "

    # 6.3 Operation commands

    def CoolingPumpOn(self):
        # #ONN switch water cooling pump ON
        self._write("#ONN")

    def CoolingPumpOff(self):
        # #OFF switch water cooling pump OFF
        self._write("#OFF")

    def CoolingReset(self):
        # #RST reset
        self._write("#RST")
