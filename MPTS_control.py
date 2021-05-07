"""
    MPTS_control.py
    --------------
    Multipass Thomson Scattering control and acquisition software.
"""

from future.builtins import super
import datetime
import sys
import logging
import io
import traceback
import ctypes
from PyQt5 import QtCore, QtWidgets, QtGui
from ui.mainwindow import Ui_MainWindow

import settings
import storage
from instruments import laserpowersupply, ophir, phantomv7, spectrometer, tektronix, AlazarTech, I2PS
from instruments import triggering

# Define status icons (available in the resource file built with "pyrcc5"
ICON_RED_LED = ":/icons/led-red-on.png"
ICON_GREEN_LED = ":/icons/green-led-on.png"
ICON_GREEN_LED_OFF = ":/icons/green-led-off.png"
MESSAGE_NOT_CONNECTED = '<span style="font-weight:600; color:#ff0000;">NOT Connected!</span>'


class QPlainTextEditLogger(logging.Handler):
    # Class for Logger, not yet implemented
    def __init__(self, parent):
        super().__init__()
        self.widget = QtWidgets.QPlainTextEdit(parent)
        self.widget.setReadOnly(True)

    def emit(self, record):
        msg = self.format(record)
        self.widget.appendPlainText(msg)


class MPTS_Control(QtWidgets.QMainWindow):
    """Create the UI, based on PyQt5.
    The UI elements are defined in "mainwindow.py" and resource file "resources_rc.py", created in QT Designer.

    To update "mainwindow.py":
        Run "pyuic5.exe --from-imports mainwindow.ui -o mainwindow.py"
    To update "resources_rc.py":
        Run "pyrcc5.exe resources.qrc -o resources_rc.py"

    Note: Never modify "mainwindow.py" or "resource_rc.py" manually.
    """

    def __init__(self):
        super().__init__()

        # Create the main window
        self.ui = Ui_MainWindow()

        # Set upp the UI
        self.ui.setupUi(self)

        self.statusBar = QtWidgets.QStatusBar()
        self.setStatusBar(self.statusBar)

        # Status flags for the State Machine
        self.setting_up = True
        self.waiting_trigger = False
        self.saving_data = False

        # Reload settings from the last session
        self.config = QtCore.QSettings("settings.ini", QtCore.QSettings.IniFormat)
        settings.read_settings(self.config, self.ui)

        # Connect signals and slots
        self.setupUILogic()

        # Update last/current shot number
        self.lastTokamakShot = storage.getLastShot("tokamak")
        self.lastManualShot = storage.getLastShot("manual")
        if self.ui.comboBoxOperationMode.currentIndex() > 2:
            self.ui.textLabelLastShot.setText("#" + str(self.lastTokamakShot))
            self.ui.textLabelNextShot.setText("#" + str(self.lastTokamakShot + 1))
        else:
            self.ui.textLabelLastShot.setText("#" + str(self.lastManualShot))
            self.ui.textLabelNextShot.setText("#" + str(self.lastManualShot + 1))

        # Create instance for each instrument/device
        self.laserPS = laserpowersupply.LaserPowerSupply()
        self.cRio = triggering.TriggerUnit()
        self.ophir = ophir.LaserStar()
        self.phantom1 = phantomv7.PhantomCamera()
        self.phantom2 = phantomv7.PhantomCamera()
        self.spectrometer = spectrometer.Spectrometer()
        self.i2ps = I2PS.PowerSupply()
        self.scope = tektronix.Scope()
        self.adc = None


        # Initialize some instruments
        QtWidgets.QApplication.processEvents()
        self.TriggerInit()
        self.LaserInit()
        self.OphirInit()
        self.I2PSSelectPS()
        # self.ScopeInit()
        # self.ADCInit()
        # self.Phantom1Init()
        # self.Phantom2Init()


    @QtCore.pyqtSlot()
    def refresh(self):
        if self.ui.checkBoxContinuouslyUpdate.isChecked():
            self.LaserUpdate()
            self.TriggerUpdate()
            self.OphirUpdate()
            self.I2PSUpdate()

    @QtCore.pyqtSlot()
    def reloadAutomatic(self):
        self.reloadAutomaticTimer.stop()
        if self.ui.comboBoxOperationMode.currentIndex() == 4 and not (self.saving_data or self.waiting_trigger):
            self.LaserCharge()
            self.StartAcquisition()

    @QtCore.pyqtSlot()
    def wasTriggered(self):
        """Check if the system was triggered. If so, starts recording proceadure"""
        mode = self.ui.comboBoxOperationMode.currentIndex()
        if mode != 2:
            if self.phantom1.wasTriggered() or self.phantom2.wasTriggered():
                self.SaveData()
                return
        else:
            if (self.adc is not None and self.adc.wasTriggered()) or (self.scope.isConnected() and self.scope.wasTriggered()):
                self.SaveData()
                return

        msg = self.statusBar.currentMessage()
        if len(msg) >= len("Waiting trigger..."):
            self.statusBar.showMessage("Waiting trigger")
        else:
            self.statusBar.showMessage(msg + ".")

    def setupUILogic(self):
        """Define QT signal and slot connections and initializes UI values."""
        # Control Acquisition
        self.ui.pushButtonReconnect.clicked.connect(self.InitAllDevices)
        self.ui.pushButtonStartAbortAcquisition.clicked.connect(self.StartAcquisition)

        # Laser
        self.ui.pushButtonLaserInit.clicked.connect(self.LaserInit)
        self.ui.pushButtonLaserApplySettings.clicked.connect(self.LaserApplySettings)
        self.ui.pushButtonLaserCharge.clicked.connect(self.LaserCharge)
        self.ui.pushButtonLaserDump.clicked.connect(self.LaserDump)
        self.ui.pushButtonLaserReset.clicked.connect(self.LaserReset)
        self.ui.pushButtonLaserSet.clicked.connect(self.LaserSet)
        self.ui.pushButtonLaserRefresh.clicked.connect(self.LaserRefresh)

        # Triggering (main tab)
        self.ui.comboBoxOperationMode.currentIndexChanged.connect(self.TriggerSetOperationMode)
        self.ui.pushButtonTriggerCharge.clicked.connect(self.TriggerCharge)
        self.ui.pushButtonTriggerSimmer.clicked.connect(self.TriggerSimmer)
        self.ui.pushButtonTriggerBurst.clicked.connect(self.TriggerBurst)
        self.ui.pushButtonTriggerManualTrigger.clicked.connect(self.TriggerManualTrigger)

        # Triggering (specific tab)
        self.ui.pushButtonTriggerLoadFile.clicked.connect(self.TriggerLoadFile)
        self.ui.pushButtonTriggerSaveFile.clicked.connect(self.TriggerSaveFile)
        self.ui.pushButtonTriggerRetrieveSettings.clicked.connect(self.TriggerRetrieveSettings)
        self.ui.pushButtonTriggerSendSettings.clicked.connect(self.TriggerApplySettings)
        self.ui.pushButtonTriggerInit.clicked.connect(self.TriggerInit)

        # Cameras
        self.ui.pushButtonPhantom1Init.clicked.connect(self.Phantom1Init)
        self.ui.pushButtonPhantom2Init.clicked.connect(self.Phantom2Init)
        self.ui.pushButtonFindCameras.clicked.connect(self.FindCameras)

        # Power meter
        self.ui.pushButtonOphirInit.clicked.connect(self.OphirInit)

        # I2PS
        self.ui.comboBoxI2PSSelectPS.currentIndexChanged.connect(self.I2PSSelectPS)
        self.ui.pushButtonI2PSInit.clicked.connect(self.I2PSInit)
        self.ui.pushButtonI2PSApplySettings.clicked.connect(self.I2PSApplySettings)
        self.ui.pushButtonI2PSReset.clicked.connect(self.I2PSReset)
        self.ui.pushButtonI2PSEnablePS.clicked.connect(self.I2PSEnablePS)
        self.ui.pushButtonI2PSEnablePulse.clicked.connect(self.I2PSEnablePulse)

        self.ui.ADCSampleRate.currentIndexChanged.connect(self.ADCUpdateAcquisitionTime)
        self.ui.ADCRecordLength.valueChanged.connect(self.ADCUpdateAcquisitionTime)
        self.ui.pushButtonScopeInit.clicked.connect(self.ScopeInit)

        self.ui.pushButtonADCInit.clicked.connect(self.ADCInit)

        self.wasTriggeredTimer = QtCore.QTimer(self)
        self.wasTriggeredTimer.timeout.connect(self.wasTriggered)
        self.wasTriggeredTimer.setInterval(1000)

        self.refreshTimer = QtCore.QTimer(self)
        self.refreshTimer.timeout.connect(self.refresh)
        self.refreshTimer.setInterval(2000)
        self.refreshTimer.start()

        # Automatic setup in tokamak automatic mode: recharge and reaload after 5 minutes
        self.reloadAutomaticTimer = QtCore.QTimer(self)
        self.reloadAutomaticTimer.timeout.connect(self.reloadAutomatic)
        self.reloadAutomaticTimer.setInterval(300000)

    def closeEvent(self, event):
        """
        Save UI settings and stops the running thread gracefully, then exit the application.
        Called when closing the application window.
        """
        self.refreshTimer.stop()
        settings.save_settings(self.config, self.ui)
        # Accept the closing event and close application
        event.accept()

    # Instruments Functions
    def ADCInit(self):
        if self.adc is None:
            self.statusBar.showMessage("Trying to connect with the AlazarTech ADC...", 1000)
            try:
                self.adc = AlazarTech.Digitizer()
                self.ui.ADCStatus.setText("Connected")
                self.ui.ADCName.setText(self.adc.getName())
                self.ui.ADCSerialNumber.setText(str(self.adc.getSerialNumber()))
                self.ui.ADCMemory.setText(str(self.adc.getMemorySize()))
                self.ui.ledStatusADC.setPixmap(QtGui.QPixmap(ICON_GREEN_LED))
                self.ADCUpdateAcquisitionTime()
            except:
                self.adc = None
        else:
            self.statusBar.showMessage("ADC already connected.", 1000)

        #if self.adc is None:
        #    try:
        #        self.adc = AlazarTech.Digitizer()
        #        self.ui.ADCStatus.setText("Connected")
        #        self.ui.ADCName.setText(self.adc.getName())
        #        self.ui.ADCSerialNumber.setText(str(self.adc.getSerialNumber()))
        #        self.ui.ADCMemory.setText(str(self.adc.getMemorySize()))
        #    except:
        #        self.adc = None

    def ADCApplySettings(self):
        if self.adc is not None:
            pass
            self.ADCUpdateAcquisitionTime()
            self.adc.AlazarSetCaptureClock(SourceId=1, SampleRateId=AlazarTech.sample_rate_id[self.ui.ADCSampleRate.currentText()])
            # print("ADC: <<%s, id = %d" % (self.ui.ADCSampleRate.currentText(), AlazarTech.sample_rate_id[self.ui.ADCSampleRate.currentText()]))
            # Configure each channel
            for n in range(2):
                # Coupling DC, Inpedance 1MOhm
                self.adc.AlazarInputControl(Channel=n + 1, Coupling=2, InputRange=AlazarTech.input_range[self.ui.ADCInputRange.currentText()], Impedance=1)
                # Disable BW Limit
                self.adc.AlazarSetBWLimit(Channel=n + 1, enable=0)
            # Configure trigger range
            self.adc.AlazarSetTriggerOperation(Source1=0x02, Slope1=1, Level1=180)  # External trigger (0x02), pos slope (1)
            # Trigger with 5V TTL DC Coupling
            self.adc.AlazarSetExternalTrigger(Coupling=2, Range=2)
            # self.adc.AlazarSetExternalTrigger(Coupling=2, Range=0)
            # Trigger timeout = 0 (infinite)
            self.adc.AlazarSetTriggerDelay(Delay=0)
            # self.adc.AlazarSetTriggerDelay(Delay=int(self.adc.sample_rate * self.ui.ADCTriggerDelay.value()))
            self.adc.AlazarSetTriggerTimeOut(0)
            self.adc.AlazarSetRecordSize(PreSize=0, PostSize=self.ui.ADCRecordLength.value())
            # Single Acquisition
            self.adc.AlazarSetRecordCount(1)

    def ADCStartAcquisition(self):
        if self.adc is not None:
            self.adc.AlazarStartCapture()

    def ADCAbortAcquisition(self):
        if self.adc is not None:
            self.adc.AlazarAbortCapture()

    def ADCUpdateAcquisitionTime(self):
        sample_rate = int(float(self.ui.ADCSampleRate.currentText().replace(" kS/s", "e3").replace(" MS/s", "e6")))
        self.ui.ADCAcquisitionTime.setText("%.3f" % (1e3 * self.ui.ADCRecordLength.value() / sample_rate))

    # Laser fuctions
    def LaserInit(self):
        if not self.laserPS.isConnected():
            self.statusBar.showMessage("Trying to connect with the Laser Power meter...", 1000)
            self.laserPS.openConnection(self.ui.LaserPSSerialPort.text())
            if self.laserPS.isConnected():
                self.ui.ledStatusLaser.setPixmap(QtGui.QPixmap(ICON_GREEN_LED))
                self.ui.LaserPSStatus.setText("Connected")
            else:
                self.ui.LaserPSStatus.setText(MESSAGE_NOT_CONNECTED)
                self.statusBar.showMessage("Error trying to connect with the Laser Power Supply", 1000)
                self.ui.ledStatusLaser.setPixmap(QtGui.QPixmap(ICON_RED_LED))
        else:
            self.statusBar.showMessage("Laser Power Supply already connected.", 1000)

    def LaserApplySettings(self):
        if self.laserPS.isConnected():
            self.laserPS.setModeBanks(self.ui.LaserPSModeBanks.value())
            self.laserPS.setResBurstDuration(self.ui.LaserPSMaxBurstDuration.value())
            self.laserPS.setBurstDuration(9)  # ms. tau_f = tau_R + Npc*Ppc + Ppc/2 < tau_maxcode ***** FIX *******
            self.laserPS.setMainVoltage(self.ui.LaserPSMainVoltage.value())
            self.laserPS.setComAuxVoltage(self.ui.LaserPSAux1Voltage.value())
            self.laserPS.setAux2Voltage(self.ui.LaserPSAux2Voltage.value())
            self.laserPS.setAux3Voltage(self.ui.LaserPSAux3Voltage.value())
            self.laserPS.setAuxDelay(self.ui.LaserPSAuxDelay.value())
            self.laserPS.setSimmerDelay(self.ui.LaserPSSimmerDelay.value())
            self.laserPS.setNBurst(self.ui.LaserPSBurstNumber.value())
            self.laserPS.setBurstSeperation(self.ui.LaserPSBurstSeperation.value())
        else:
            self.ui.LaserPSStatus.setText(MESSAGE_NOT_CONNECTED)
            self.statusBar.showMessage('Laser Power Supply NOT connected! Command ignored.', 2500)

    def LaserCharge(self):
        if self.laserPS.isConnected():
            self.laserPS.ChargeBank()
        else:
            self.ui.LaserPSStatus.setText(MESSAGE_NOT_CONNECTED)
            self.statusBar.showMessage('Laser Power Supply NOT connected! Command ignored.', 2500)

    def LaserDump(self):
        if self.laserPS.isConnected():
            self.laserPS.DumpBank()
        else:
            self.ui.LaserPSStatus.setText(MESSAGE_NOT_CONNECTED)
            self.statusBar.showMessage('Laser Power Supply NOT connected! Command ignored.', 2500)

    def LaserReset(self):
        if self.laserPS.isConnected():
            self.laserPS.Reset()
        else:
            self.ui.LaserPSStatus.setText(MESSAGE_NOT_CONNECTED)
            self.statusBar.showMessage('Laser Power Supply NOT connected! Command ignored.', 2500)

    def LaserSet(self):
        if self.laserPS.isConnected():
            self.laserPS.setResMainVoltage(self.ui.LaserPSResMainVoltage.value())
            self.laserPS.setResAuxVoltage(self.ui.LaserPSResAuxVoltage.value())
            self.laserPS.setResBurstNumber(self.ui.LaserPSMaxBurstNumber.value())
            self.laserPS.setResBurstDuration(self.ui.LaserPSMaxBurstDuration.value())
            # Max Expl Energy = ??
            # self.laserPS.setAccurChargeV(self.ui.LaserPSAccurChargeV.value())
            # Max Delay After Flash = ??

            self.laserPS.setTriggerSimmer(self.ui.LaserPSTriggerSimmer.value())
            self.laserPS.setSignalReady(self.ui.LaserPSSignalReady.value())
            self.laserPS.setModePC(0 if self.ui.radioButtonLaserSerial.isChecked() else 1)
        else:
            self.ui.LaserPSStatus.setText(MESSAGE_NOT_CONNECTED)
            self.statusBar.showMessage('Laser Power Supply NOT connected! Command ignored.', 2500)

    def LaserUpdate(self):
        if self.laserPS.isConnected():
            if self.laserPS.getLaserStatus():
                self.ui.LaserPSStatus.setText(self.laserPS.getPowerErrorStr())
            self.ui.ledStatusLaser.setPixmap(QtGui.QPixmap(ICON_GREEN_LED))
            try:
                voltages = self.laserPS.getVoltageBanksAll()
                self.ui.LaserPSMainVoltageMeas.display(voltages[0])
                self.ui.LaserPSAux1VoltageMeas.display(voltages[1])
                self.ui.LaserPSAux2VoltageMeas.display(voltages[2])
                self.ui.LaserPSAux3VoltageMeas.display(voltages[3])
            except:
                self.ui.LaserPSMainVoltageMeas.display(-1)
                self.ui.LaserPSAux1VoltageMeas.display(-1)
                self.ui.LaserPSAux2VoltageMeas.display(-1)
                self.ui.LaserPSAux3VoltageMeas.display(-1)

    def LaserRefresh(self):
        if self.laserPS.isConnected():
            self.ui.LMAuxDelay.setText(str(self.laserPS.getAuxDelay()))
            self.ui.LMSimmerDelay.setText(str(self.laserPS.getSimmerDelay()))
            self.ui.LMBurstDuration.setText(str(self.laserPS.getBurstDuration()))
            self.ui.LMNburst.setText(str(self.laserPS.getNburst()))
            self.ui.LMBurstSeperation.setText(str(self.laserPS.getBurstSeperation()))
            self.ui.LMTriggerSimmer.setText(str(self.laserPS.getTriggerSimmer()))
            self.ui.LMSignalReady.setText(str(self.laserPS.getSignalReady()))
            self.ui.LMModeBanks.setText(str(self.laserPS.getModeBanks()))

    # Phamtom Cameras
    def FindCameras(self):
        ans = self.phantom1.Discover()
        print(ans)
        if ans:
            self.ui.FindCamerasResult.setText(ans)
        else:
            self.ui.FindCamerasResult.setText("No camera found.")

    def CamerasApplySettings(self):
        if self.phantom1.isConnected():
            self.phantom1.setFrameSync(1)  # External Sync
            self.phantom1.setImageFormat(self.ui.Phantom1ImageFormat.currentText())
            if self.ui.CMOSPOn.isChecked():
                self.phantom1.Prepare(num_frames=self.ui.B2_Number.value() - 2, fps=self.ui.CamerasFrameRate.value(), exposure=self.ui.CamerasExposureTime.value())
            else:
                self.phantom1.Prepare(num_frames=2 * self.ui.B2_Number.value() - 2, fps=self.ui.CamerasFrameRate.value(), exposure=self.ui.CamerasExposureTime.value())
        if self.phantom2.isConnected():
            self.phantom2.setFrameSync(1)  # External Sync
            self.phantom2.setImageFormat(self.ui.Phantom2ImageFormat.currentText())
            if self.ui.CMOSPOn.isChecked():
                self.phantom2.Prepare(num_frames=self.ui.B2_Number.value() - 2, fps=self.ui.CamerasFrameRate.value(), exposure=self.ui.CamerasExposureTime.value())
            else:
                self.phantom2.Prepare(num_frames=2 * self.ui.B2_Number.value() - 2, fps=self.ui.CamerasFrameRate.value(), exposure=self.ui.CamerasExposureTime.value())

    def CamerasStartAcquisition(self):
        if self.phantom1.isConnected():
            self.phantom1.Trigger()
        if self.phantom2.isConnected():
            self.phantom2.Trigger()

    def CamerasAbortAcquisition(self):
        pass

    def I2PSSelectPS(self):
        if self.ui.comboBoxI2PSSelectPS.currentIndex() == 0:
            self.ui.I2PSKentechBox.setEnabled(False)
            self.ui.I2PSDifferBox.setEnabled(True)
        else:
            self.ui.I2PSKentechBox.setEnabled(True)
            self.ui.I2PSDifferBox.setEnabled(False)
        return

    def I2PSInit(self):
        """Initialize connection with wht image intensifier power supply"""
        if not self.i2ps.isConnected():
            self.statusBar.showMessage("Trying to connect with the Image Intensifier PS...", 1000)
            self.i2ps.openConnection(ip=self.ui.I2PSIP.text())
            if self.i2ps.isConnected():
                self.ui.ledStatusI2PS.setPixmap(QtGui.QPixmap(ICON_GREEN_LED))
                self.ui.I2PSStatus.setText("Connected")
                self.I2PSApplySettings()
                self.I2PSUpdate()
            else:
                self.ui.I2PSStatus.setText(MESSAGE_NOT_CONNECTED)
                self.statusBar.showMessage("Error trying to connect with the Image Intensifier.", 1000)
                self.ui.ledStatusI2PS.setPixmap(QtGui.QPixmap(ICON_RED_LED))
        else:
            self.statusBar.showMessage("Connection with the Image Intensifier PS already stabilished.", 1000)

    def I2PSApplySettings(self):
        """Apply the settings on the image intensifier power supply"""
        if self.i2ps.isConnected():
            self.i2ps.setPulseDuration(self.ui.I2PSPulseDuration.value())
            self.i2ps.setTriggerDelay(self.ui.I2PSTriggerDelay.value())
            self.i2ps.setVoltagePPMCP(self.ui.I2PSVoltagePPMCP.value())
            self.i2ps.setVoltageMCP(self.ui.I2PSVoltageMCP.value())
            self.i2ps.setVoltagePCHighSide(self.ui.I2PSVoltagePCHighSide.value())
            self.i2ps.setVoltagePCLowSide(self.ui.I2PSVoltagePCLowSide.value())

    def I2PSStartAcquisition(self):
        """Start Acquisition by enabling power supply and triggering."""
        self.I2PSEnablePS(True)
        self.I2PSEnablePulse(True)

    def I2PSReset(self):
        if self.i2ps.isConnected():
            self.i2ps.reset()

    def I2PSEnablePS(self, enable=None):
        if self.i2ps.isConnected():
            if enable is None:
                self.i2ps.enablePS(self.ui.pushButtonI2PSEnablePS.text() == "Enable PS")
            else:
                self.i2ps.enablePS(enable)
            if self.i2ps.isPSEnabled():
                self.ui.pushButtonI2PSEnablePS.setText("Disable PS")
            else:
                self.ui.pushButtonI2PSEnablePS.setText("Enable PS")

    def I2PSEnablePulse(self, enable=None):
        if self.i2ps.isConnected():
            if enable is None:
                self.i2ps.enablePulse(self.ui.pushButtonI2PSEnablePulse.text() == "Enable Pulse")
            else:
                self.i2ps.enablePulse(enable)
            if self.i2ps.isPulseEnabled():
                self.ui.pushButtonI2PSEnablePulse.setText("Disable Pulse")
            else:
                self.ui.pushButtonI2PSEnablePulse.setText("Enable Pulse")

    def I2PSUpdate(self):
        """Apply the settings on the image intensifier power supply"""
        if self.i2ps.isConnected():
            try:
                self.ui.labelI2PSVoltagePPMCP.setText(str(self.i2ps.getVoltagePPMCP()))
                self.ui.labelI2PSVoltageMCP.setText(str(self.i2ps.getVoltageMCP()))
                self.ui.labelI2PSPCHighSide.setText(str(self.i2ps.getVoltagePCHighSide()))
                self.ui.labelI2PSPCLowSide.setText(str(self.i2ps.getVoltagePCLowSide()))
                self.ui.labelI2PSCurrentPP.setText(str(self.i2ps.getCurrentPP()))
                self.ui.labelI2PSCurrentMCP.setText(str(self.i2ps.getCurrentMCP()))
                self.ui.labelI2PSCurrentPCHighSide.setText(str(self.i2ps.getCurrentPCHighSide()))
                self.ui.labelI2PSCurrentPCLowSide.setText(str(self.i2ps.getCurrentPCLowSide()))
                PP_error, MCP_error, PC_h_error, PC_l_error = self.i2ps.getErrorState()
                self.ui.ledI2PSCurrentOverflowPP.setPixmap(QtGui.QPixmap(ICON_GREEN_LED if PP_error else ICON_RED_LED))
                self.ui.ledI2PSCurrentOverflowMCP.setPixmap(QtGui.QPixmap(ICON_GREEN_LED if MCP_error else ICON_RED_LED))
                self.ui.ledI2PSCurrentOverflowPCHighSide.setPixmap(QtGui.QPixmap(ICON_GREEN_LED if PC_h_error else ICON_RED_LED))
                self.ui.ledI2PSCurrentOverflowPCLowSide.setPixmap(QtGui.QPixmap(ICON_GREEN_LED if PC_l_error else ICON_RED_LED))
                if self.i2ps.isPSEnabled():
                    self.ui.pushButtonI2PSEnablePS.setText("Disable PS")
                else:
                    self.ui.pushButtonI2PSEnablePS.setText("Enable PS")
                if self.i2ps.isPulseEnabled():
                    self.ui.pushButtonI2PSEnablePulse.setText("Disable Pulse")
                else:
                    self.ui.pushButtonI2PSEnablePulse.setText("Enable Pulse")
            except:
                print("Error while trying update I2PS status")

    def Phantom1Init(self):
        """Initializes the first Phantom camera."""
        if not self.phantom1.isConnected():
            self.statusBar.showMessage("Trying to connect with the Phantom camera 1...", 1000)
            self.phantom1.openConnection(self.ui.Phantom1IP.text())
            if self.phantom1.isConnected():
                self.ui.Phantom1Status.setText("Connected")
                self.ui.ledStatusPhantom1.setPixmap(QtGui.QPixmap(ICON_GREEN_LED))
                self.ui.labelPhantom1Name.setText(self.phantom1.getName())
                self.ui.labelPhantom1Serial.setText(self.phantom1.getSerialNumber())
            else:
                self.ui.Phantom1Status.setText(MESSAGE_NOT_CONNECTED)
                self.statusBar.showMessage("Error trying to connect with the Phantom 1.", 1000)
                self.ui.ledStatusPhantom1.setPixmap(QtGui.QPixmap(ICON_RED_LED))
        else:
            self.statusBar.showMessage("Connection with the Phantom camera 1 already stabilished.", 1000)

    def Phantom2Init(self):
        """Initializes the first Phantom camera."""
        if not self.phantom2.isConnected():
            self.statusBar.showMessage("Trying to connect with the Phantom camera 2...", 1000)
            self.phantom2.openConnection(self.ui.Phantom2IP.text())
            if self.phantom2.isConnected():
                self.ui.Phantom2Status.setText("Connected")
                self.ui.ledStatusPhantom2.setPixmap(QtGui.QPixmap(ICON_GREEN_LED))
                self.ui.labelPhantom2Name.setText(self.phantom2.getName())
                self.ui.labelPhantom2Serial.setText(self.phantom2.getSerialNumber())
            else:
                self.ui.Phantom2Status.setText(MESSAGE_NOT_CONNECTED)
                self.statusBar.showMessage("Error trying to connect with the Phantom 2.", 1000)
                self.ui.ledStatusPhantom2.setPixmap(QtGui.QPixmap(ICON_RED_LED))
        else:
            self.statusBar.showMessage("Connection with the Phantom camera 2 already stabilished.", 1000)

    # Ophir Power Meter
    def OphirInit(self):
        """Initializes the Ophir Energy Power Meter."""
        if not self.ophir.isConnected():
            self.statusBar.showMessage("Trying to connect with Ophir (Laser Power meter)...", 1000)
            self.ophir.openConnection(self.ui.OphirSerialPort.text())
            if self.ophir.isConnected():
                self.ui.OphirStatus.setText("Connected")
                self.ui.ledStatusOphir.setPixmap(QtGui.QPixmap(ICON_GREEN_LED))
                self.ui.OphirName.setText(self.ophir.getName())
                self.ui.OphirFirmware.setText(self.ophir.getFirmware())
                self.ophir.setCoefficients(self.ui.DirectCoeff.value(), self.ui.ReturnCoeff.value())
            else:
                self.ui.OphirStatus.setText(MESSAGE_NOT_CONNECTED)
                self.statusBar.showMessage("Error trying to connect with the Ophir (Laser Power meter).", 1000)
                self.ui.ledStatusOphir.setPixmap(QtGui.QPixmap(ICON_RED_LED))
        else:
            self.statusBar.showMessage("Connection with the Ophir Power Meter already stabilished.", 1000)

    def OphirUpdate(self):
        """Update energy measurement on the Ophir Power Meter."""
        if self.ophir.isConnected():
            # if self.ophir.wasTriggered():
            head1, head2 = self.ophir.getData()
            head1 = head1 if head1 > 0 else 0
            head2 = head2 if head2 > 0 else 0
            if head1 > 0:
                self.ui.OphirEnergyDirectMeas.setText(str(head1))
                self.ui.OphirEnergyDirect.display(float(self.ophir.coef1 * head1))
            if head2 > 0:
                self.ui.OphirEnergyReturnMeas.setText(str(head2))
                self.ui.OphirEnergyReturn.display(float(self.ophir.coef2 * head2))
        else:
            self.ui.OphirStatus.setText(MESSAGE_NOT_CONNECTED)
            self.ui.ledStatusOphir.setPixmap(QtGui.QPixmap(ICON_RED_LED))

    # Scope
    def ScopeInit(self):
        """Initialize the Tektronix Oscilloscope."""
        if not self.scope.isConnected():
            self.statusBar.showMessage("Trying to connect with the Scope Osciloscope...", 1000)
            if self.ui.ScopeIP.text():
                error = self.scope.openConnection(ip=self.ui.ScopeIP.text())
            elif self.ui.ScopeSerialPort.text():
                error = self.scope.openConnection(port=self.ui.ScopeSerialPort.text())
            if not error:
                self.ui.ScopeStatus.setText("Connected")
                self.ui.ledStatusScope.setPixmap(QtGui.QPixmap(ICON_GREEN_LED))
                self.ui.labelScopeName.setText(self.scope.getName())
            else:
                self.ui.ScopeStatus.setText(MESSAGE_NOT_CONNECTED)
                self.statusBar.showMessage("Error trying to connect with Scope.", 1000)
                self.ui.ledStatusScope.setPixmap(QtGui.QPixmap(ICON_RED_LED))
        else:
            self.statusBar.showMessage("Connection with the Scope Osciloscope already stabilished.", 1000)

    def ScopeApplySettings(self):
        if self.scope.isConnected():
            pass
        else:
            self.ui.ScopeStatus.setText(MESSAGE_NOT_CONNECTED)

    def ScopeStartAcquisition(self):
        if self.scope.isConnected():
            # self.ScopeUpdateAcquisitionTime()
            self.scope.acquisition(False)
            self.scope.set_single_acquisition()
            self.scope.acquisition(True)
        else:
            self.ui.ScopeStatus.setText(MESSAGE_NOT_CONNECTED)

    def ScopeAbortAcquisition(self):
        if self.scope.isConnected():
            self.scope.acquisition(False)
        else:
            self.ui.ScopeStatus.setText(MESSAGE_NOT_CONNECTED)

    def ScopeUpdateAcquisitionTime(self):
        time_scale = float(self.ui.ScopeTimeScale.currentText())
        self.scope.set_tScale(time_scale)

   # CompactRIO
    def TriggerInit(self):
        if self.cRio.isConnected():
            self.statusBar.showMessage("Connection with the CompactRio already stabilished.", 1000)
        else:
            self.statusBar.showMessage("Trying to connect to the CompactRio...", 1000)
            self.cRio.openConnection(ip=self.ui.TriggerIP.text(), port=int(self.ui.TriggerPort.text()))
            if self.cRio.isConnected():
                self.ui.TriggerStatus.setText("Connected")
                self.ui.ledStatusTriggering.setPixmap(QtGui.QPixmap(ICON_GREEN_LED))
                self.cRio.sendSettings("Enable_IOs", 0)  # Disable any output for safety
                self.ui.comboBoxOperationMode.setEnabled(True)
                if self.ui.comboBoxOperationMode.currentIndex() == 0 or self.ui.comboBoxOperationMode.currentIndex() == 2:
                    # manual mode with laser
                    self.ui.pushButtonTriggerSimmer.setEnabled(True)
                    self.ui.pushButtonTriggerBurst.setEnabled(False)
                    self.ui.pushButtonTriggerManualTrigger.setEnabled(False)
                elif self.ui.comboBoxOperationMode.currentIndex() > 2:
                    # tokamak mode
                    self.ui.pushButtonTriggerSimmer.setEnabled(False)
                    self.ui.pushButtonTriggerBurst.setEnabled(False)
                    self.ui.pushButtonTriggerManualTrigger.setEnabled(True)
                else:
                    # manual mode without laser
                    self.ui.pushButtonTriggerSimmer.setEnabled(False)
                    self.ui.pushButtonTriggerBurst.setEnabled(True)
                    self.ui.pushButtonTriggerManualTrigger.setEnabled(False)
            else:
                self.ui.TriggerStatus.setText(MESSAGE_NOT_CONNECTED)
                self.statusBar.showMessage("Error trying to connect with the CompactRio.", 1000)
                self.ui.ledStatusTriggering.setPixmap(QtGui.QPixmap(ICON_RED_LED))
                self.ui.comboBoxOperationMode.setEnabled(False)
                self.ui.pushButtonTriggerSimmer.setEnabled(False)
                self.ui.pushButtonTriggerBurst.setEnabled(False)
                self.ui.pushButtonTriggerManualTrigger.setEnabled(False)

    def TriggerSetOperationMode(self):
        if self.cRio.isConnected():
            self.cRio.setMode(self.ui.comboBoxOperationMode.currentIndex())
            if self.cRio.isConnected():
                if self.ui.comboBoxOperationMode.currentIndex() > 2:
                    self.lastTokamakShot = storage.getLastShot("tokamak")
                    self.ui.textLabelLastShot.setText("#" + str(self.lastTokamakShot))
                    self.ui.textLabelNextShot.setText("#" + str(self.lastTokamakShot + 1))
                else:
                    self.lastManualShot = storage.getLastShot("manual")
                    self.ui.textLabelLastShot.setText("#" + str(self.lastManualShot))
                    self.ui.textLabelNextShot.setText("#" + str(self.lastManualShot + 1))
            if self.ui.comboBoxOperationMode.currentIndex() == 0 or self.ui.comboBoxOperationMode.currentIndex() == 2:
                # manual mode with laser
                self.ui.pushButtonTriggerSimmer.setEnabled(True)
                self.ui.pushButtonTriggerBurst.setEnabled(False)
                self.ui.pushButtonTriggerManualTrigger.setEnabled(False)
            elif self.ui.comboBoxOperationMode.currentIndex() > 2:
                # tokamak mode
                self.ui.pushButtonTriggerSimmer.setEnabled(False)
                self.ui.pushButtonTriggerBurst.setEnabled(False)
                self.ui.pushButtonTriggerManualTrigger.setEnabled(True)
            else:
                # manual mode without laser
                self.ui.pushButtonTriggerSimmer.setEnabled(False)
                self.ui.pushButtonTriggerBurst.setEnabled(True)
                self.ui.pushButtonTriggerManualTrigger.setEnabled(False)
        else:
            self.ui.TriggerStatus.setText(MESSAGE_NOT_CONNECTED)
            self.ui.ledStatusTriggering.setPixmap(QtGui.QPixmap(ICON_RED_LED))
            self.statusBar.showMessage('CompactRio NOT connected! Command ignored.', 2500)
            self.ui.comboBoxOperationMode.setEnabled(False)
            self.ui.pushButtonTriggerSimmer.setEnabled(False)
            self.ui.pushButtonTriggerBurst.setEnabled(False)
            self.ui.pushButtonTriggerManualTrigger.setEnabled(False)

    def TriggerCharge(self):
        if self.cRio.isConnected():
            self.cRio.sendSettings("A1_SW_button", 1)
        else:
            self.ui.TriggerStatus.setText(MESSAGE_NOT_CONNECTED)
            self.ui.ledStatusTriggering.setPixmap(QtGui.QPixmap(ICON_RED_LED))
            self.statusBar.showMessage('CompactRio NOT connected! Command ignored.', 2500)

    def TriggerSimmer(self):
        if self.cRio.isConnected():
            self.cRio.sendSettings("A2_SW_button", 1)
        else:
            self.ui.TriggerStatus.setText(MESSAGE_NOT_CONNECTED)
            self.ui.ledStatusTriggering.setPixmap(QtGui.QPixmap(ICON_RED_LED))
            self.statusBar.showMessage('CompactRio NOT connected! Command ignored.', 2500)

    def TriggerBurst(self):
        if self.cRio.isConnected():
            self.cRio.sendSettings("A4_SW_button", 1)
        else:
            self.ui.TriggerStatus.setText(MESSAGE_NOT_CONNECTED)
            self.ui.ledStatusTriggering.setPixmap(QtGui.QPixmap(ICON_RED_LED))
            self.statusBar.showMessage('CompactRio NOT connected! Command ignored.', 2500)

    def TriggerManualTrigger(self):
        if self.cRio.isConnected():
            self.cRio.sendSettings("manual_trigger", 1)
        else:
            self.ui.TriggerStatus.setText(MESSAGE_NOT_CONNECTED)
            self.ui.ledStatusTriggering.setPixmap(QtGui.QPixmap(ICON_RED_LED))
            self.statusBar.showMessage('CompactRio NOT connected! Command ignored.', 2500)

    def TriggerLoadFile(self):
        filename, _filter = QtWidgets.QFileDialog.getOpenFileName(self, 'Read File', ".", "Text (*.txt)")
        if filename:
            file = open(filename, 'r')
            with file:
                self.statusBar.showMessage("Loading the settings for the triggering system...", 1000)
                text = file.readlines()
                settings.read_trigger_settings(text, self.ui)

    def TriggerSaveFile(self):
        filename, _filter = QtWidgets.QFileDialog.getSaveFileName(self, 'Save File', ".", "Text (*.txt)")
        if filename:
            self.statusBar.showMessage("Saving the settings for the triggering system...", 1000)
            settings.write_trigger_settings(filename, self.ui)

    def TriggerRetrieveSettings(self):
        if self.cRio.isConnected():
            self.statusBar.showMessage("Retrieving settings from the CompactRio system...", 1000)
            for logical_name in triggering.physical_names:
                widget = self.ui.centralwidget.findChild(QtWidgets.QSpinBox, logical_name)
                if widget:
                    value = self.cRio.readSettings(triggering.physical_names[logical_name])
                    widget.setValue(value)
                else:
                    widget = self.ui.centralwidget.findChild(QtWidgets.QCheckBox, logical_name)
                    value = self.cRio.readSettings(triggering.physical_names[logical_name])
                    widget.setChecked(int(value))
            self.statusBar.showMessage("Retrieving settings from the CompactRio system... Done!", 1500)
        else:
            self.ui.TriggerStatus.setText(MESSAGE_NOT_CONNECTED)
            self.ui.ledStatusTriggering.setPixmap(QtGui.QPixmap(ICON_RED_LED))
            self.statusBar.showMessage('CompactRio NOT connected! Command ignored.', 2500)

    def TriggerApplySettings(self):
        if self.cRio.isConnected():
            self.statusBar.showMessage("Sending settings to the CompactRio system...", 1000)
            for logical_name in triggering.physical_names:
                widget = self.ui.centralwidget.findChild(QtWidgets.QSpinBox, logical_name)
                if widget:
                    self.cRio.sendSettings(triggering.physical_names[logical_name], widget.value())
                else:
                    widget = self.ui.centralwidget.findChild(QtWidgets.QCheckBox, logical_name)
                    self.cRio.sendSettings(triggering.physical_names[logical_name], int(widget.isChecked()))
            self.statusBar.showMessage("Sending settings to the CompactRio system... Done!", 1500)
        else:
            self.ui.TriggerStatus.setText(MESSAGE_NOT_CONNECTED)
            self.ui.ledStatusTriggering.setPixmap(QtGui.QPixmap(ICON_RED_LED))
            self.statusBar.showMessage('CompactRio NOT connected! Command ignored.', 2500)

    def TriggerUpdate(self):
        if self.cRio.isConnected():
            io_enabled, laser_ready, interlock = self.cRio.readStatus()
            self.ui.ledIOs_enabled.setPixmap(QtGui.QPixmap(ICON_GREEN_LED if io_enabled else ICON_GREEN_LED_OFF))
            self.ui.ledLaser_Ready_I.setPixmap(QtGui.QPixmap(ICON_GREEN_LED if laser_ready else ICON_GREEN_LED_OFF))
            self.ui.ledInterlock.setPixmap(QtGui.QPixmap(ICON_GREEN_LED if interlock else ICON_GREEN_LED_OFF))
        else:
            self.ui.TriggerStatus.setText(MESSAGE_NOT_CONNECTED)
            self.ui.ledStatusTriggering.setPixmap(QtGui.QPixmap(ICON_RED_LED))
            self.statusBar.showMessage('CompactRio NOT connected! Command ignored.', 2500)

    # General State-Machine functions
    def InitAllDevices(self):
        """Configure the serial device, serial port and polling interval before starting the polling thread."""
        progressDialog = QtWidgets.QProgressDialog(self)
        progressDialog.setRange(0, 8)

        progressDialog.setWindowTitle("Connecting")
        progressDialog.show()
        progressDialog.setValue(0)
        QtWidgets.QApplication.processEvents()

        progressDialog.setLabelText("Connecting to the Laser Power Supply..." + "\nPlease wait.")
        progressDialog.setValue(1)
        self.LaserInit()
        QtWidgets.QApplication.processEvents()
        if progressDialog.wasCanceled():
            return

        progressDialog.setLabelText("Connecting to CompactRio..." + "\nPlease wait.")
        progressDialog.setValue(2)
        self.TriggerInit()
        QtWidgets.QApplication.processEvents()
        if progressDialog.wasCanceled():
            return

        progressDialog.setLabelText("Connecting to the Laser Power Meter..." + "\nPlease wait.")
        progressDialog.setValue(3)
        self.OphirInit()
        QtWidgets.QApplication.processEvents()
        if progressDialog.wasCanceled():
            return

        progressDialog.setLabelText("Connecting to the Tektronix Scope..." + "\nPlease wait.")
        progressDialog.setValue(4)
        self.ScopeInit()
        QtWidgets.QApplication.processEvents()
        if progressDialog.wasCanceled():
            return

        progressDialog.setLabelText("Connecting to the ADC board..." + "\nPlease wait.")
        progressDialog.setValue(5)
        self.ADCInit()
        QtWidgets.QApplication.processEvents()
        if progressDialog.wasCanceled():
            return

        progressDialog.setLabelText("Connecting to the Phantom camera 1..." + "\nPlease wait.")
        progressDialog.setValue(6)
        self.Phantom1Init()
        QtWidgets.QApplication.processEvents()
        if progressDialog.wasCanceled():
            return

        progressDialog.setLabelText("Connecting to the Phantom camera 2..." + "\nPlease wait.")
        progressDialog.setValue(7)
        QtWidgets.QApplication.processEvents()
        self.Phantom2Init()
        if progressDialog.wasCanceled():
            return

        progressDialog.setLabelText("Connecting to the Imagem Intensifier PS..." + "\nPlease wait.")
        progressDialog.setValue(8)
        QtWidgets.QApplication.processEvents()
        if self.ui.comboBoxI2PSSelectPS.currentIndex() == 0:
            self.I2PSInit()

        progressDialog.close()

    def SaveData(self):
        """Saves data adcquired, include the instruments settings, in the MDSplus database."""
        timestamp = datetime.datetime.now().isoformat()
        self.statusBar.showMessage("Saving data.")
        self.wasTriggeredTimer.stop()
        self.refreshTimer.stop()
        self.cRio.sendSettings("Enable_IOs", 0)  # Disable any output for safety
        self.ui.ledWaitingTrigger.setPixmap(QtGui.QPixmap(ICON_GREEN_LED_OFF))
        self.ui.ledSavingData.setPixmap(QtGui.QPixmap(ICON_GREEN_LED))
        self.OphirUpdate()
        self.setting_up = False
        self.waiting_trigger = False
        self.saving_data = True

        # Create database for that shot
        db = storage.database()
        if self.ui.comboBoxOperationMode.currentIndex() <= 2:
            mode = "manual"
            self.lastManualShot = storage.getLastShot("manual")
            db.createTree(mode, self.lastManualShot + 1)
        else:
            mode = "tokamak"
            self.lastTokamakShot = storage.getLastShot("tokamak")
            db.createTree(mode, self.lastTokamakShot + 1)

        # Update shot number display
        if mode == "tokamak":
            self.lastTokamakShot += 1
            storage.setLastShot(mode, self.lastTokamakShot)
            self.ui.textLabelLastShot.setText("#" + str(self.lastTokamakShot))
            self.ui.textLabelNextShot.setText("#" + str(self.lastTokamakShot + 1))
        else:
            self.lastManualShot += 1
            storage.setLastShot(mode, self.lastManualShot)
            self.ui.textLabelLastShot.setText("#" + str(self.lastManualShot))
            self.ui.textLabelNextShot.setText("#" + str(self.lastManualShot + 1))

        # Save settings and data on database
        print("Saving settings...")
        self.SaveTriggerSettings(db)
        db.populateLaser()

        # Cameras
        self.statusBar.showMessage("Saving camera data")
        if self.phantom1.isConnected() and self.phantom1.wasTriggered():
            print("Saving camera 1 data...")
            db.populateCamera(camera=1,
                              enabled=1,
                              name=self.phantom1.getName(),
                              serialNumber=self.phantom1.getSerialNumber(),
                              ip=self.ui.Phantom1IP.text(),
                              FrameSync=self.ui.Phantom1FrameSync.currentText(),
                              ImageFormat=self.ui.Phantom1ImageFormat.currentText())
            print("Frames available: %d" % self.phantom1.getNFramesAvailable())
            image_request = self.phantom1.requestImages(start_frame=0, num_frames=self.phantom1.getNFramesAvailable() - 1)
            db.populateCameraData(image_request.Receive(), camera=1)
        else:
            db.populateCamera(camera=1, enabled=0, FrameSync=self.ui.Phantom1FrameSync.currentText(), ImageFormat=self.ui.Phantom1ImageFormat.currentText())

        if self.phantom2.isConnected() and self.phantom2.wasTriggered():
            print("Saving camera 2 data...")
            db.populateCamera(camera=2,
                              enabled=1,
                              name=self.phantom2.getName(),
                              serialNumber=self.phantom2.getSerialNumber(),
                              ip=self.ui.Phantom2IP.text(),
                              FrameSync=self.ui.Phantom2FrameSync.currentText(),
                              ImageFormat=self.ui.Phantom2ImageFormat.currentText())
            print("Frames available: %d" % self.phantom2.getNFramesAvailable())
            image_request = self.phantom2.requestImages(start_frame=0, num_frames=self.phantom2.getNFramesAvailable() - 1)
            db.populateCameraData(image_request.Receive(), camera=2)
        else:
            db.populateCamera(camera=2, enabled=0, FrameSync=self.ui.Phantom2FrameSync.currentText(), ImageFormat=self.ui.Phantom2ImageFormat.currentText())

        # Scope and ADC
        self.statusBar.showMessage("Saving waveform from osciloscope/ADC")
        if self.adc is not None and self.adc.wasTriggered():
            print("Saving ADC data...")
            db.populateADC(description="%s, S/N: %s, Memory: %s Samples/Channel" % (self.ui.ADCName.text(), self.ui.ADCSerialNumber.text(), self.ui.ADCMemory.text()),
                           enabled=int(self.adc is not None),
                           RecordLength=self.ui.ADCRecordLength.value(),
                           SampleRate=int(float(self.ui.ADCSampleRate.currentText().replace(" kS/s", "e3").replace(" MS/s", "e6"))))
            enabled_channels = [self.ui.ADCCH1Enable.isChecked(), self.ui.ADCCH2Enable.isChecked()]
            for i in range(len(enabled_channels)):
                if enabled_channels[i]:
                    db.populateADCChannel(self.adc.getChannelWaveform(i + 1), i + 1)
                else:
                    db.populateADCChannel(None, i + 1)
        else:
            db.populateADC(description="", enabled=0)

        if self.scope.isConnected() and self.scope.wasTriggered():
            print("Saving Scope data...")
            db.populateScope(description=self.ui.labelScopeName.text(),
                             enabled=1,
                             RecordLength=self.scope.get_record_length(),
                             SampleRate=self.scope.get_record_sample_rate())
            enabled_channels = [self.ui.ScopeCH1Enable.isChecked(), self.ui.ScopeCH2Enable.isChecked(), self.ui.ScopeCH3Enable.isChecked(), self.ui.ScopeCH4Enable.isChecked()]
            for i in range(len(enabled_channels)):
                print("Saving data for CH%d" % (i + 1))
                if enabled_channels[i]:
                    db.populateScopeChannel(self.scope.get_channel_waveform(i + 1), i + 1)
                else:
                    db.populateScopeChannel(None, i + 1)
        else:
            db.populateADC(description="", enabled=0)

        db.populateIntensifier(PPVoltage=self.ui.I2PSVoltagePPMCP.value(), MCPVoltage=self.ui.I2PSVoltageMCP.value(), PCHigh=self.ui.I2PSVoltagePCHighSide.value(),
                               PCLow=self.ui.I2PSVoltagePCLowSide.value(), PulseDur=self.ui.I2PSPulseDuration.value(), TriggerDelay=self.ui.I2PSTriggerDelay.value(), IP=self.ui.I2PSIP.text(),
                               Coarse=self.ui.II_Coarse.currentText(), Fine=self.ui.II_Fine.value(), Gain=self.ui.II_Gain.value(), PS=self.ui.comboBoxI2PSSelectPS.currentText())

        if self.ophir.isConnected():
            head1, head2 = self.ophir.getData()
            head1 = head1 if head1 > 0 else 0
            head2 = head2 if head2 > 0 else 0
            self.ui.OphirEnergyDirectMeas.setText(str(head1))
            self.ui.OphirEnergyReturnMeas.setText(str(head2))
            self.ui.OphirEnergyDirect.display(float(self.ophir.coef1 * head1))
            self.ui.OphirEnergyReturn.display(float(self.ophir.coef2 * head2))

        print("Saving data from power meter")
        db.populateOphir(self.ophir, self.ophir.isConnected())

        db.populateComments(timestamp=timestamp, operator=self.ui.Operator.text(), email=self.ui.Email.text(), aim=self.ui.Aim.text(), comments=self.ui.Comments.toPlainText())

        self.ui.ledSavingData.setPixmap(QtGui.QPixmap(ICON_GREEN_LED_OFF))

        self.statusBar.showMessage("")
        print("All data was saved.")

        self.refreshTimer.start()
        self.ui.pushButtonStartAbortAcquisition.setText("Start acquisition")
        self.setting_up = True
        self.saving_data = False

        # Automatic setup in tokamak automatic mode: recharge and reaload after 5 minutes
        if self.ui.comboBoxOperationMode.currentIndex() == 4:
            self.reloadAutomaticTimer.start()

    def SaveTriggerSettings(self, db):
        """Saves triggering settings MDSplus"""
        # for name, obj in inspect.getmembers(self.ui):
        for logical_name in triggering.physical_names:
            widget = self.ui.centralwidget.findChild(QtWidgets.QSpinBox, logical_name)
            if widget:
                db.populateSettings(logical_name, widget.value())
            else:
                widget = self.ui.centralwidget.findChild(QtWidgets.QCheckBox, logical_name)
                db.populateSettings(logical_name, int(widget.isChecked()))
        db.populateSettings("OPMODE", self.ui.comboBoxOperationMode.currentIndex())


    def SetupInstruments(self):
        if self.ui.comboBoxOperationMode.currentIndex() != 1:
            self.LaserApplySettings()
        self.TriggerApplySettings()
        if self.ui.comboBoxOperationMode.currentIndex() != 2:
            self.CamerasApplySettings()
            self.I2PSApplySettings()
        self.ADCApplySettings()
        self.ScopeApplySettings()

    def StartAcquisition(self):
        if self.saving_data:
            self.statusBar.showMessage("Saving data, please wait...")
            return
        if not self.waiting_trigger:
            self.cRio.sendSettings("Enable_IOs", 1)
            if self.ui.comboBoxOperationMode.currentIndex() >= 2:
                self.lastTokamakShot = storage.getLastShot("tokamak")
                self.ui.textLabelLastShot.setText("#" + str(self.lastTokamakShot))
                self.ui.textLabelNextShot.setText("#" + str(self.lastTokamakShot + 1))
            else:
                self.lastManualShot = storage.getLastShot("manual")
                self.ui.textLabelLastShot.setText("#" + str(self.lastManualShot))
                self.ui.textLabelNextShot.setText("#" + str(self.lastManualShot + 1))
            self.SetupInstruments()
            self.wasTriggeredTimer.start()
            self.setting_up = False
            self.waiting_trigger = True
            self.saving_data = False
            self.CamerasStartAcquisition()
            self.ScopeStartAcquisition()
            self.ADCStartAcquisition()
            self.I2PSStartAcquisition()
            self.statusBar.showMessage("Waiting trigger.")
            self.ui.pushButtonStartAbortAcquisition.setText("Abort acquisition")
        else:
            self.AbortAcquisition()
        self.ui.ledWaitingTrigger.setPixmap(QtGui.QPixmap(ICON_GREEN_LED if self.waiting_trigger else ICON_GREEN_LED_OFF))

    def AbortAcquisition(self):
        if self.waiting_trigger:
            self.cRio.sendSettings("Enable_IOs", 0)
            self.statusBar.showMessage("Aborting acquisition...", 1000)
            self.wasTriggeredTimer.stop()
            self.setting_up = True
            self.waiting_trigger = False
            self.CamerasAbortAcquisition()
            self.ScopeAbortAcquisition()
            self.ui.pushButtonStartAbortAcquisition.setText("Start acquisition")


    def excepthook(self, excType, excValue, tracebackobj):
        """Excepthook function, to display a message box with details about the exception.
        @param excType exception type
        @param excValue exception value
        @param tracebackobj traceback object
        """
        separator = '-' * 40
        notice = "An unhandled exception has occurred\n"

        tbinfofile = io.StringIO()
        traceback.print_tb(tracebackobj, None, tbinfofile)
        tbinfofile.seek(0)
        tbinfo = tbinfofile.read()
        errmsg = '%s: \n%s' % (str(excType), str(excValue))
        sections = [separator, errmsg, separator, tbinfo]
        msg = '\n'.join(sections)

        # Create a QMessagebox
        error_box = QtWidgets.QMessageBox()

        error_box.setText(str(notice) + str(msg))
        error_box.setWindowTitle("MPTS AUG - unhandled exception")
        error_box.setIcon(QtWidgets.QMessageBox.Critical)
        error_box.setStandardButtons(QtWidgets.QMessageBox.Ok)
        error_box.setTextInteractionFlags(QtCore.Qt.TextSelectableByMouse)

        # Show the window
        error_box.exec_()
        if self.saving_data:
            print("Error while saving. Aborting saving.")
            self.ui.ledSavingData.setPixmap(QtGui.QPixmap(ICON_GREEN_LED_OFF))
            self.statusBar.showMessage("")

            self.refreshTimer.start()
            self.ui.pushButtonStartAbortAcquisition.setText("Start acquisition")
            self.setting_up = True
            self.saving_data = False

            # Automatic setup in tokamak automatic mode: recharge and reaload after 5 minutes
            if self.ui.comboBoxOperationMode.currentIndex() == 4:
                self.reloadAutomaticTimer.start()



if __name__ == "__main__":
    appID = 'DIFFER.MPTS.Control.v1'
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(appID)

    app = QtWidgets.QApplication(sys.argv)
    window = MPTS_Control()
    # Use a excepthook for displaying unhandled exceptions as a QMessageBox
    sys.excepthook = window.excepthook
    window.setWindowTitle("MPTS AUG - Control and Acquisition")
    window.show()
    window.setFixedSize(window.size())
    sys.exit(app.exec_())
