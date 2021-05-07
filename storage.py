# -*- coding: utf-8 -*-

"""Database with MDSplus framework"""


import MDSplus as mds
from instruments import triggering, I2PS

try:
    import urllib.request as urllib
except ImportError:
    import urllib

import ssl
ssl._create_default_https_context = ssl._create_unverified_context


class database():

    def updateRefTree(self, mode, number):
        if mode == "tokamak":
            reftree = mds.Tree("mpts", 1, mode='readonly')
        elif mode == "manual":
            reftree = mds.Tree("mpts_manual", 1, mode='readonly')
        refnode = reftree.getNode("\\LastShot")
        refnode.deleteData()
        refnode.putData(number)

    def createTree(self, mode, number):
        """Create database structure on the fly."""
        if number == 1:
            raise "Tree number cannot be one"
        if mode == "tokamak":
            self.tree = mds.Tree("mpts", number, mode='NEW')
        elif mode == "manual":
            self.tree = mds.Tree("mpts_manual", number, mode='NEW')
        else:
            raise "Incorret operation mode."

        self.tree.addNode("OpMode", usage="NUMERIC").addTag("OPMODE")
        self.tree.addNode("TIMESTAMP", usage="TEXT").addTag("Timestamp")
        self.tree.addNode("Operator", usage="TEXT").addTag("Operator")
        self.tree.addNode("Email", usage="TEXT").addTag("Email")
        self.tree.addNode("Aim", usage="TEXT").addTag("Aim")
        self.tree.addNode("Comments", usage="TEXT").addTag("Comments")

        laser_node = self.tree.addNode("Laser", usage="STRUCTURE")
        laser_node.addTag("Laser")
        laser_node.addNode("Wavelength", usage="NUMERIC").addTag("LaserWavelength")
        laser_node.addTag("Laserlambda0")
        laser_PS_node = laser_node.addNode("LaserPS", usage="STRUCTURE")
        laser_PS_node.addTag("LaserPS")
        laser_PS_node.addNode("Enabled", usage="NUMERIC").addTag("LaserPSEnabled")
        laser_PS_node.addNode("SerialPort", usage="TEXT").addTag("LaserPSSerialPort")
        laser_PS_node.addNode("MainVoltage", usage="NUMERIC").addTag("LaserPSMainVoltage")
        laser_PS_node.addNode("Aux1Voltage", usage="NUMERIC").addTag("LaserPSAux1Voltage")
        laser_PS_node.addNode("Aux2Voltage", usage="NUMERIC").addTag("LaserPSAux2Voltage")
        laser_PS_node.addNode("Aux3Voltage", usage="NUMERIC").addTag("LaserPSAux3Voltage")
        laser_PS_node.addNode("AuxDelay", usage="NUMERIC").addTag("LaserPSAuxDelay")
        laser_PS_node.addNode("SimmerDelay", usage="NUMERIC").addTag("LaserPSSimmerDelay")
        laser_PS_node.addNode("BurstNumber", usage="NUMERIC").addTag("LaserPSBurstNumber")
        laser_PS_node.addNode("BurstSep", usage="NUMERIC").addTag("LaserPSBurstSeperation")
        laser_PS_node.addNode("ResMainV", usage="NUMERIC").addTag("LaserPSResMainVoltage")
        laser_PS_node.addNode("ResAuxV", usage="NUMERIC").addTag("LaserPSResAuxVoltage")
        laser_PS_node.addNode("MaxBurstN", usage="NUMERIC").addTag("LaserPSMaxBurstNumber")
        laser_PS_node.addNode("MaxBurstDur", usage="NUMERIC").addTag("LaserPSMaxBurstDuration")
        laser_PS_node.addNode("MaxExpEnerg", usage="NUMERIC").addTag("LaserPSMaxExpEnergy")
        laser_PS_node.addNode("AccurCharge", usage="NUMERIC").addTag("LaserPSAccurCharge")
        laser_PS_node.addNode("MaxDelFlash", usage="NUMERIC").addTag("LaserMaxDelayFlash")
        laser_PS_node.addNode("TrigSimmer", usage="NUMERIC").addTag("LaserPSTriggerSimmer")
        laser_PS_node.addNode("SignalReady", usage="NUMERIC").addTag("LaserPSSignalReady")
        laser_PS_node.addNode("BankMode", usage="NUMERIC").addTag("LaserPSBankMode")

        cameras_node = self.tree.addNode("Cameras", usage="STRUCTURE")
        cameras_node.addTag("Cameras")
        cameras_node.addNode("FrameRate", usage="NUMERIC").addTag("CameraFrameRate")
        cameras_node.addNode("Exposure", usage="NUMERIC").addTag("CameraExposureTime")

        for i in range(2):
            camera_node = cameras_node.addNode("Phantom%d" % (i + 1), usage="STRUCTURE")
            camera_node.addTag("Phantom%d" % (i + 1))
            camera_node.addTag("Camera%d" % (i + 1))
            camera_node.addNode("Enabled", usage="NUMERIC").addTag("Phantom%dEnabled" % (i + 1))
            camera_node.addNode("IP", usage="TEXT").addTag("Phantom%dIP" % (i + 1))
            camera_node.addNode("FrameSync", usage="TEXT").addTag("Phantom%dFrameSync" % (i + 1))
            camera_node.addNode("ImageFormat", usage="TEXT").addTag("Phantom%dImageFormat" % (i + 1))
            camera_node.addNode("ImageHeight", usage="NUMERIC").addTag("Phantom%dImageHeight" % (i + 1))
            camera_node.addNode("ImageWidth", usage="NUMERIC").addTag("Phantom%dImageWidth" % (i + 1))
            camera_node.addNode("Signal", usage="SIGNAL").addTag("Phantom%dSignal" % (i + 1))

        ophir_node = self.tree.addNode("Ophir", usage="STRUCTURE")
        ophir_node.addTag("Ophir")
        ophir_node.addTag("power_meter")
        ophir_node.addTag("laser_star")
        ophir_node.addNode("Description", usage="TEXT").addTag("OphirDescription")
        ophir_node.addNode("Enabled", usage="NUMERIC").addTag("OphirEnabled")
        ophir_node.addNode("SerialPort", usage="NUMERIC").addTag("OphirSerialPort")
        ophir_node.addNode("Coef1", usage="NUMERIC").addTag("OphirCoef1")
        ophir_node.addNode("Coef2", usage="NUMERIC").addTag("OphirCoef2")
        ophir_node.addNode("Head1", usage="NUMERIC").addTag("OphirHead1")
        ophir_node.addNode("Head2", usage="NUMERIC").addTag("OphirHead2")
        ophir_node.addNode("EnergyDirect", usage="NUMERIC").addTag("OphirEnergyDirect")
        ophir_node.addNode("EnergyReturn", usage="NUMERIC").addTag("OphirEnergyReturn")

        ADC_node = self.tree.addNode("ADC", usage="STRUCTURE")
        ADC_node.addTag("ADC")
        ADC_node.addTag("ATS")
        ADC_node.addNode("Enabled", usage="NUMERIC").addTag("ADCEnabled")
        ADC_node.addNode("Description", usage="TEXT").addTag("ADCDescription")
        ADC_node.addNode("RecordLength", usage="NUMERIC").addTag("ADCRecordLength")
        ADC_node.addNode("SampleRate", usage="NUMERIC").addTag("ADCSampleRate")
        # For each channel
        for i in range(1, 3):
            ADC_ch = ADC_node.addNode("CH%d" % i, usage="STRUCTURE")
            ADC_ch.addTag("ADCCH%d" % i)
            ADC_ch.addNode("name", usage="TEXT").addTag("ADCCH%dName" % i)
            ADC_ch.addNode("signal", usage="SIGNAL").addTag("ADCCH%dSignal" % i)
            ADC_ch.addNode("inputrange", usage="NUMERIC").addTag("ADCCH%dInputRange" % i)
            ADC_ch.addNode("coupling", usage="TEXT").addTag("ADCCH%dCoupling" % i)
            ADC_ch.addNode("impedance", usage="NUMERIC").addTag("ADCCH%dImpedance" % i)
            ADC_ch.addNode("enabled", usage="NUMERIC").addTag("ADCCH%denabled" % i)

        scope_node = self.tree.addNode("Scope", usage="STRUCTURE")
        scope_node.addTag("Scope")
        scope_node.addTag("oscilloscope")
        scope_node.addNode("Enabled", usage="NUMERIC").addTag("ScopeEnabled")
        scope_node.addNode("RecordLength", usage="NUMERIC").addTag("ScopeRecordLength")
        scope_node.addNode("SampleRate", usage="NUMERIC").addTag("ScopeSampleRate")
        scope_node.addNode("SerialPort", usage="TEXT").addTag("ScopeSerialPort")
        scope_node.addNode("IP", usage="TEXT").addTag("ScopeIP")
        scope_node.addNode("Description", usage="TEXT").addTag("ScopeDescription")
        # For each channel
        for i in range(1, 5):
            scope_ch = scope_node.addNode("CH%d" % i, usage="STRUCTURE")
            scope_ch.addTag("ScopeCH%d" % i)
            scope_ch.addNode("enabled", usage="NUMERIC").addTag("ScopeCH%dEnabled" % i)
            scope_ch.addNode("name", usage="TEXT").addTag("ScopeCH%dName" % i)
            scope_ch.addNode("signal", usage="SIGNAL").addTag("ScopeCH%dSignal" % i)
            scope_ch.addNode("inputrange", usage="NUMERIC").addTag("ScopeCH%dRange" % i)
            scope_ch.addNode("coupling", usage="TEXT").addTag("ScopeCH%dCoupling" % i)
            scope_ch.addNode("impedance", usage="NUMERIC").addTag("ScopeCH%dImpedance" % i)

        triggering_node = self.tree.addNode("Trigger", usage="STRUCTURE")
        triggering_node.addTag("Triggering")
        triggering_node.addTag("cRio")
        triggering_settings = triggering_node.addNode("settings", usage="STRUCTURE")
        triggering_settings.addNode("IP", usage="TEXT").addTag("TriggerIP")
        triggering_settings.addNode("Port", usage="NUMERIC").addTag("TriggerPort")
        for logical_name in triggering.physical_names:
            node = triggering_node.addNode(logical_name, usage="NUMERIC")
            node.addTag(logical_name)
            node.addTag("Trigger" + logical_name.replace("_", ""))

        intensifier_node = self.tree.addNode("II", usage="STRUCTURE")
        intensifier_node.addTag("II")
        intensifier_node.addTag("intensifier")
        intensifier_node.addNode("PPVoltage", usage="NUMERIC").addTag("IIPPVoltage")
        intensifier_node.addNode("MCPVoltage", usage="NUMERIC").addTag("IIMCPVoltage")
        intensifier_node.addNode("PCHigh", usage="NUMERIC").addTag("IIPCHigh")
        intensifier_node.addNode("PCLow", usage="NUMERIC").addTag("IIPCLow")
        intensifier_node.addNode("PulseDur", usage="NUMERIC").addTag("IIPulseDuration")
        intensifier_node.addNode("TriggerDelay", usage="NUMERIC").addTag("IITriggerDelay")
        intensifier_node.addNode("IP", usage="TEXT").addTag("IIIP")
        intensifier_node.addNode("Description", usage="TEXT").addTag("IIDescription")
        intensifier_node.addNode("Coarse", usage="TEXT").addTag("IICoarse")
        intensifier_node.addNode("Fine", usage="NUMERIC").addTag("IIFine")
        intensifier_node.addNode("Gain", usage="NUMERIC").addTag("IIGain")
        intensifier_node.addNode("PS", usage="TEXT").addTag("IIPS")

        spectr_node = self.tree.addNode("SPECTR", usage="STRUCTURE")
        spectr_node.addTag("SPECTROMETER")
        node = spectr_node.addNode("Gratting", usage="TEXT")
        node.addTag("SpectrGrating")
        node.addTag("Grating")
        node = spectr_node.addNode("RotAngle", usage="NUMERIC")
        node.addTag("SpectrRotAngle")
        node.addTag("RotAngle")
        node = spectr_node.addNode("RubyLinePx", usage="NUMERIC")
        node.addTag("SpectrRubyLinePx")
        node.addTag("RubyLinePx")
        node = spectr_node.addNode("BiasCurrent", usage="NUMERIC")
        node.addTag("SpectrBiasCurrent")
        node.addTag("BiasCurrent")

        self.tree.write()

    def populateSettings(self, name, value):
        """Populate all user interface settings to the MDSplus tree datafile"""
        if not self.tree:
            raise "No Tree Created"
        node = self.tree.getNode("\\" + name)
        node.deleteData()
        node.putData(value)

    def populateLaser(self, wavelength=694.3e-9):
        node = self.tree.getNode("\\LaserWavelength")
        node.deleteData()
        node.putData(mds.Float32(694.3e-9).setUnits("m"))

    def populateCamera(self, camera=1, enabled=0, name="", serialNumber="", ip="", FrameSync="", ImageFormat=""):
        cam = self.tree.getNode("\\Phantom%d" % camera)
        cam.ENABLED.deleteData()
        cam.ENABLED.putData(enabled)
        cam.IP.deleteData()
        cam.IP.putData(ip)
        cam.FRAMESYNC.deleteData()
        cam.FRAMESYNC.putData(FrameSync)
        cam.IMAGEFORMAT.deleteData()
        cam.IMAGEFORMAT.putData(ImageFormat)

    def populateCameraData(self, data, camera):
        if data is not None:
            [frames, height, width] = data.shape
            node = self.tree.getNode("\\Phantom%d" % camera)

            node = self.tree.getNode("\\Phantom%dImageHeight" % camera)
            node.deleteData()
            node.putData(height)
            node = self.tree.getNode("\\Phantom%dImageWidth" % camera)
            node.deleteData()
            node.putData(width)

            node = self.tree.getNode("\\Phantom%dSignal" % camera)
            node.deleteData()
            node.putData(mds.Int16Array(data))

    def populateADC(self, description="", enabled=0, RecordLength=0, SampleRate=0):
        scope = self.tree.getNode("\\ADC")
        scope.DESCRIPTION.deleteData()
        scope.DESCRIPTION.putData(description)
        scope.ENABLED.deleteData()
        scope.ENABLED.putData(enabled)
        scope.RECORDLENGTH.deleteData()
        scope.RECORDLENGTH.putData(RecordLength)
        scope.SAMPLERATE.deleteData()
        scope.SAMPLERATE.putData(mds.Int32(SampleRate).setUnits("Samples/s"))

    def populateADCChannel(self, data, ch):
        if data is None:
            node = self.tree.getNode("\\ADCCH%d" % ch)
            node.ENABLED.deleteData()
            node.ENABLED.putData(0)
            return

        node = self.tree.getNode("\\ADCCH%d" % data.channel)
        node.ENABLED.deleteData()
        node.ENABLED.putData(1)
        node.COUPLING.deleteData()
        node.COUPLING.putData("DC")
        node.IMPEDANCE.deleteData()
        node.IMPEDANCE.putData(1e6)
        convExpr = mds.Data.compile("($VALUE-(%s))*%s + %s" % (data.y_offset, data.y_mult, data.y_zero))
        convExpr.setUnits("volt")
        dim = mds.Range(data.x_zero, data.x_zero + (data.signal_raw.size - 1) * data.x_incr, data.x_incr)
        dim.setUnits("second")
        signal = mds.Signal(convExpr, data.signal_raw, dim)
        node.SIGNAL.deleteData()
        node.SIGNAL.putData(signal)
        node.INPUTRANGE.deleteData()
        node.INPUTRANGE.putData(mds.Float32(data.input_range).setUnits("volts"))

    def populateScope(self, description="", enabled=0, RecordLength=0, SampleRate=0):
        scope = self.tree.getNode("\\Scope")
        scope.DESCRIPTION.deleteData()
        scope.DESCRIPTION.putData(description)
        scope.ENABLED.deleteData()
        scope.ENABLED.putData(enabled)
        scope.RECORDLENGTH.deleteData()
        scope.RECORDLENGTH.putData(RecordLength)
        scope.SAMPLERATE.deleteData()
        scope.SAMPLERATE.putData(mds.Int32(SampleRate).setUnits("Samples/s"))

    def populateScopeChannel(self, data, ch):
        if data is None:
            node = self.tree.getNode("\\ScopeCH%d" % ch)
            node.ENABLED.deleteData()
            node.ENABLED.putData(0)

        node = self.tree.getNode("\\ScopeCH%d" % data.channel)
        node.ENABLED.deleteData()
        node.ENABLED.putData(1)
        node.COUPLING.deleteData()
        node.COUPLING.putData("DC")
        node.IMPEDANCE.deleteData()
        node.IMPEDANCE.putData(1e6)
        convExpr = mds.Data.compile("($VALUE-%s)*%s + %s" % (data.y_offset, data.y_mult, data.y_zero))
        convExpr.setUnits("volt")
        dim = mds.Range(data.x_zero, data.x_zero + (data.signal_raw.size - 1) * data.x_incr, data.x_incr)
        dim.setUnits("second")
        signal = mds.Signal(convExpr, data.signal_raw, dim)
        node.SIGNAL.deleteData()
        node.SIGNAL.putData(signal)
        node.INPUTRANGE.deleteData()
        node.INPUTRANGE.putData(mds.Float32(data.input_range).setUnits("volts/div"))

    def populateOphir(self, data, enabled):
        ophir = self.tree.getNode("\\Ophir")
        if not enabled:
            ophir.ENABLED.deleteData()
            ophir.ENABLED.putData(1)
            ophir.DESCRIPTION.deleteData()
            ophir.DESCRIPTION.putData("")
            ophir.HEAD1.deleteData()
            ophir.HEAD1.putData(0)
            ophir.HEAD2.deleteData()
            ophir.HEAD2.putData(0)
            ophir.COEF1.deleteData()
            ophir.COEF1.putData(0)
            ophir.COEF2.deleteData()
            ophir.COEF2.putData(0)
        else:
            ophir.ENABLED.deleteData()
            ophir.ENABLED.putData(0)
            ophir.DESCRIPTION.deleteData()
            ophir.DESCRIPTION.putData("%s, ROM version: %s" % (data.name, data.firmware))
            ophir.HEAD1.deleteData()
            ophir.HEAD1.putData(data.head1)
            ophir.HEAD2.deleteData()
            ophir.HEAD2.putData(data.head2)
            ophir.COEF1.deleteData()
            ophir.COEF1.putData(data.coef1)
            ophir.COEF2.deleteData()
            ophir.COEF2.putData(data.coef2)

            node = self.tree.getNode("\\OphirEnergyDirect")
            node.deleteData()
            node.putData(data.head1 * data.coef1)
            node = self.tree.getNode("\\OphirEnergyReturn")
            node.deleteData()
            node.putData(data.head2 * data.coef2)

    def populateIntensifier(self, PPVoltage, MCPVoltage, PCHigh, PCLow, PulseDur, TriggerDelay, IP, Coarse, Fine, Gain, PS):
        II = self.tree.getNode("\\II")
        II.PS.deleteData()
        II.PS.putData(PS)
        II.DESCRIPTION.deleteData()
        II.DESCRIPTION.putData("Power Supply of the 4-stage hybrid Image Intensifier.")
        if PS == "Kentech":
            II.COARSE.deleteData()
            II.COARSE.putData(Coarse.strip())
            II.FINE.deleteData()
            II.FINE.putData(Fine)
            II.GAIN.deleteData()
            II.GAIN.putData(Gain)
            II.PULSEDUR.deleteData()
            II.PULSEDUR.putData(I2PS.KentechGate(Coarse, Fine))
            II.PULSEDUR.setUnits("ns")
            II.PPVOLTAGE.deleteData()
            II.PPVOLTAGE.putData(4200)
            II.PPVOLTAGE.setUnits("V")
            II.PCHIGH.deleteData()
            II.PCHIGH.putData(50)
            II.PCHIGH.setUnits("V")
            II.PCLOW.deleteData()
            II.PCLOW.putData(-950)
            II.PCLOW.setUnits("V")
            II.TRIGGERDELAY.deleteData()
            II.TRIGGERDELAY.putData(50)
            II.TRIGGERDELAY.setUnits("ns")
        else:
            II.PPVOLTAGE.deleteData()
            II.PPVOLTAGE.putData(PPVoltage)
            II.PPVOLTAGE.setUnits("V")
            II.MCPVOLTAGE.deleteData()
            II.MCPVOLTAGE.putData(MCPVoltage)
            II.MCPVOLTAGE.setUnits("V")
            II.PCHIGH.deleteData()
            II.PCHIGH.putData(PCHigh)
            II.PCHIGH.setUnits("V")
            II.PCLOW.deleteData()
            II.PCLOW.putData(PCLow)
            II.PCLOW.setUnits("V")
            II.PULSEDUR.deleteData()
            II.PULSEDUR.putData(PulseDur)
            II.PULSEDUR.setUnits("ns")
            II.TRIGGERDELAY.deleteData()
            II.TRIGGERDELAY.putData(TriggerDelay)
            II.TRIGGERDELAY.setUnits("ns")
            II.IP.deleteData()
            II.IP.putData(IP)

    def populateComments(self, timestamp="", operator="", email="", aim="", comments=""):
        node = self.tree.getNode("\\TIMESTAMP")
        node.deleteData()
        node.putData(timestamp)

        node = self.tree.getNode("\\Operator")
        node.deleteData()
        node.putData(operator)

        node = self.tree.getNode("\\Email")
        node.deleteData()
        node.putData(email)

        node = self.tree.getNode("\\Aim")
        node.deleteData()
        node.putData(aim)

        node = self.tree.getNode("\\Comments")
        node.deleteData()
        node.putData(comments)


def getLastShot(mode):
    if mode == "tokamak":
        # try to get last shot number from AUG database
        last_shot = getLastShotAUG()
        if last_shot:
            return last_shot
        else:
            # if fails, try to get last local shot number
            tree = mds.Tree("mpts", 1)
            return int(tree.getNode("\\lastshot").getData())
    else:
        tree = mds.Tree("mpts_manual", 1)
        return int(tree.getNode("\\lastshot").getData())


def setLastShot(mode, shot):
    if mode == "tokamak":
        tree = mds.Tree("mpts", 1)
    else:
        tree = mds.Tree("mpts_manual", 1)
    node = tree.getNode("\\lastshot")
    node.deleteData()
    node.putData(mds.Int32(shot))


def getLastShotAUG():
    try:
        # reg = re.compile('Current shot:\n<b>([0-9]*)</b>')
        # inputHTML = urllib.urlopen("http://www.aug.ipp.mpg.de/aug/local/aug_only/journal_today_2.html", timeout=1).read().decode("latin-1")
        # value = int(reg.search(inputHTML).group(1))
        # if "Shot completed" in inputHTML or "Shot aborted" in inputHTML:
        #    return value
        # else:
        #    return value - 1
        inputHTML = urllib.urlopen("https://www.aug.ipp.mpg.de/cgibin/local_or_sfread/shotstatus.cgi", timeout=1).readlines()
        if "COMPLETED" in inputHTML[2].decode("latin-1") or "UNKNOWN" in inputHTML[2].decode("latin-1"):
            return int(inputHTML[0])
        else:
            return int(inputHTML[0]) - 1
    except:
        print("It was not possible to get the last shot number")
        return 0


def getLastShotAUGDate():
    try:
        inputHTML = urllib.urlopen("https://www.aug.ipp.mpg.de/cgibin/local_or_sfread/shotstatus.cgi", timeout=1).readlines()
        return int(inputHTML[1])
    except:
        print("It was not possible to get the last shot number")
        return 0


if __name__ == "__main__":
    db = database()
    db.createTree("tokamak", 1)
    db.populateSettings()
