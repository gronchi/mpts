"""
    settings.py
    -----------
    Implements functions for reading and writing UI configuration using a QSettings object.
"""

from PyQt5 import QtWidgets
from instruments import triggering
import re

MPTS_trigger_file = ".config/MPTS_config.txt"
regex = re.compile('(\S+)[\s*]=[\s*]"(\S+)"')


def read_settings(config, ui):
    """Reads configuration from the ini-file.
    Uses default values if no settings are found.
    """

    # General
    ui.comboBoxOperationMode.setCurrentIndex(config.value("OperationMode", 3, type=int))
    ui.checkBoxContinuouslyUpdate.setChecked(config.value("ContinuouslyUpdate", True, type=bool))
    ui.CamerasFrameRate.setValue(config.value("CamerasFrameRate", 10900, type=int))
    ui.CamerasExposureTime.setValue(config.value("CamerasExposureTime", 100, type=int))
    ui.Operator.setText(config.value("Operator", "", type=str))
    ui.Email.setText(config.value("Email", "", type=str))
    ui.Aim.setText(config.value("Aim", "", type=str))
    ui.Comments.setPlainText(config.value("Comments", "", type=str))

    # Laser PS
    ui.LaserPSSerialPort.setText(config.value("LaserPS/SerialPort", "COM1", type=str))
    ui.LaserPSMainVoltage.setValue(config.value("LaserPS/MainVoltage", None, type=int))
    ui.LaserPSAux1Voltage.setValue(config.value("LaserPS/Aux1Voltage", None, type=int))
    ui.LaserPSAux2Voltage.setValue(config.value("LaserPS/Aux2Voltage", None, type=int))
    ui.LaserPSAux3Voltage.setValue(config.value("LaserPS/Aux3Voltage", None, type=int))
    ui.LaserPSAuxDelay.setValue(config.value("LaserPS/AuxDelay", None, type=float))
    ui.LaserPSSimmerDelay.setValue(config.value("LaserPS/SimmerDelay", None, type=int))
    ui.LaserPSBurstNumber.setValue(config.value("LaserPS/BurstNumber", None, type=int))
    ui.LaserPSBurstSeperation.setValue(config.value("LaserPS/BurstSeparation", None, type=float))
    ui.LaserPSResMainVoltage.setValue(config.value("LaserPS/ResMainVoltage", None, type=int))
    ui.LaserPSResAuxVoltage.setValue(config.value("LaserPS/ResAuxVoltage", None, type=int))
    ui.LaserPSMaxBurstNumber.setValue(config.value("LaserPS/MaxBurstNumber", None, type=int))
    ui.LaserPSMaxBurstDuration.setValue(config.value("LaserPS/MaxBurstDuration", None, type=int))
    ui.LaserPSMaxExplosionEnergy.setCurrentIndex(config.value("LaserPS/MaxExplosionEnergy", 0, type=int))
    ui.LaserPSAccurChargeV.setValue(config.value("LaserPS/AccurChargeV", None, type=float))
    ui.LaserPSMaxDelayFlash.setValue(config.value("LaserPS/MaxDelayFlash", None, type=int))
    ui.LaserPSTriggerSimmer.setValue(config.value("LaserPS/TriggerSimmer", None, type=int))
    ui.LaserPSSignalReady.setValue(config.value("LaserPS/SignalReady", None, type=int))
    ui.LaserPSModeBanks.setValue(config.value("LaserPS/BankMode", None, type=int))

    # Phantom1
    ui.Phantom1IP.setText(config.value("Phantom1/IP", "100.100.100.66", type=str))
    index = ui.Phantom1FrameSync.findText(config.value("Phantom1/FrameSync", "", type=str))
    ui.Phantom1FrameSync.setCurrentIndex(index if index > 0 else 0)
    index = ui.Phantom1ImageFormat.findText(config.value("Phantom1/ImageFormat", "", type=str))
    ui.Phantom1ImageFormat.setCurrentIndex(index if index > 0 else 0)

    # Phantom2
    ui.Phantom2IP.setText(config.value("Phantom2/IP", "100.100.100.67", type=str))
    index = ui.Phantom1FrameSync.findText(config.value("Phantom2/FrameSync", "", type=str))
    ui.Phantom2FrameSync.setCurrentIndex(index if index > 0 else 0)
    index = ui.Phantom1ImageFormat.findText(config.value("Phantom2/ImageFormat", "", type=str))
    ui.Phantom2ImageFormat.setCurrentIndex(index if index > 0 else 0)

    # I2PS
    ui.comboBoxI2PSSelectPS.setCurrentIndex(config.value("I2PS/SelectPS", 0, type=int))
    ui.I2PSIP.setText(config.value("I2PS/IP", "127.0.0.1", type=str))
    ui.I2PSVoltagePPMCP.setValue(config.value("I2PS/VoltagePPMCP", 0, type=int))
    ui.I2PSVoltageMCP.setValue(config.value("I2PS/VoltageMCP", 0, type=int))
    ui.I2PSVoltagePCHighSide.setValue(config.value("I2PS/VoltagePCHighSide", 0, type=int))
    ui.I2PSVoltagePCLowSide.setValue(config.value("I2PS/VoltagePCLowSide", 0, type=int))
    ui.I2PSPulseDuration.setValue(config.value("I2PS/PulseDuration", 0, type=int))
    ui.I2PSTriggerDelay.setValue(config.value("I2PS/TriggerDelay", 0, type=int))
    ui.II_Coarse.setCurrentIndex(config.value("I2PS/Coarse", 0, type=int))
    ui.II_Fine.setValue(config.value("I2PS/Fine", 0, type=float))
    ui.II_Gain.setValue(config.value("I2PS/Gain", 0, type=float))


    # Ophir
    ui.OphirSerialPort.setText(config.value("Ophir/SerialPort", "COM2", type=str))

    # ADC
    ui.ADCRecordLength.setValue(config.value("ADC/RecordLength", 131072, type=int))
    index = ui.ADCSampleRate.findText(config.value("ADC/SampleRate", "", type=str))
    ui.ADCSampleRate.setCurrentIndex(index if index > 0 else 11)
    index = ui.ADCInputRange.findText(config.value("ADC/InputRange", "", type=str))
    ui.ADCInputRange.setCurrentIndex(index if index > 0 else 11)
    ui.ADCCH1Name.setText(config.value("ADC/CH1Name", "", type=str))
    ui.ADCCH2Name.setText(config.value("ADC/CH2Name", "", type=str))
    ui.ADCCH1Enable.setChecked(config.value("ADC/CH1Enable", True, type=bool))
    ui.ADCCH2Enable.setChecked(config.value("ADC/CH2Enable", True, type=bool))

    # Scope
    ui.ScopeSerialPort.setText(config.value("Scope/SerialPort", "COM3", type=str))
    ui.ScopeIP.setText(config.value("Scope/IP", "10.182.5.8", type=str))
    ui.ScopeCH1Name.setText(config.value("Scope/CH1Name", "", type=str))
    ui.ScopeCH2Name.setText(config.value("Scope/CH2Name", "", type=str))
    ui.ScopeCH3Name.setText(config.value("Scope/CH3Name", "", type=str))
    ui.ScopeCH4Name.setText(config.value("Scope/CH4Name", "", type=str))
    ui.ScopeCH1Enable.setChecked(config.value("Scope/CH1Enable", True, type=bool))
    ui.ScopeCH2Enable.setChecked(config.value("Scope/CH2Enable", True, type=bool))
    ui.ScopeCH3Enable.setChecked(config.value("Scope/CH3Enable", True, type=bool))
    ui.ScopeCH4Enable.setChecked(config.value("Scope/CH4Enable", True, type=bool))

    # Triggering
    ui.TriggerIP.setText(config.value("Triggering/IP", "127.0.0.1", type=str))
    ui.TriggerPort.setValue(config.value("Triggering/Port", "15000", type=int))

    # Triggering/times
    f = open(MPTS_trigger_file, 'r')
    data = f.readlines()
    f.close()
    read_trigger_settings(data, ui)


def save_settings(config, ui):
    """Saves current UI configuration to ini file, called when exiting the main application"""

    config.setValue("OperationMode", ui.comboBoxOperationMode.currentIndex())
    config.setValue("CamerasFrameRate", ui.CamerasFrameRate.value())
    config.setValue("CamerasExposureTime", ui.CamerasExposureTime.value())
    config.setValue("ContinuouslyUpdate", ui.checkBoxContinuouslyUpdate.isChecked())
    config.setValue("Operator", ui.Operator.text())
    config.setValue("Email", ui.Email.text())
    config.setValue("Aim", ui.Aim.text())
    config.setValue("Comments", ui.Comments.toPlainText())

    config.beginGroup("LaserPS")
    config.setValue("SerialPort", ui.LaserPSSerialPort.text())
    config.setValue("MainVoltage", ui.LaserPSMainVoltage.value())
    config.setValue("Aux1Voltage", ui.LaserPSAux1Voltage.value())
    config.setValue("Aux2Voltage", ui.LaserPSAux2Voltage.value())
    config.setValue("Aux3Voltage", ui.LaserPSAux3Voltage.value())
    config.setValue("AuxDelay", ui.LaserPSAuxDelay.value())
    config.setValue("SimmerDelay", ui.LaserPSSimmerDelay.value())
    config.setValue("BurstNumber", ui.LaserPSBurstNumber.value())
    config.setValue("BurstSeparation", round(ui.LaserPSBurstSeperation.value(), 1))
    config.setValue("ResMainVoltage", ui.LaserPSResMainVoltage.value())
    config.setValue("ResAuxVoltage", ui.LaserPSResAuxVoltage.value())
    config.setValue("MaxBurstNumber", ui.LaserPSMaxBurstNumber.value())
    config.setValue("MaxBurstDuration", ui.LaserPSMaxBurstDuration.value())
    config.setValue("MaxExplosionEnergy", ui.LaserPSMaxExplosionEnergy.currentIndex())
    config.setValue("PSAccurChargeV", ui.LaserPSAccurChargeV.value())
    config.setValue("MaxDelayFlash", ui.LaserPSMaxDelayFlash.value())
    config.setValue("TriggerSimmer", ui.LaserPSTriggerSimmer.value())
    config.setValue("SignalReady", ui.LaserPSSignalReady.value())
    config.setValue("BankMode", ui.LaserPSModeBanks.value())
    config.endGroup()

    config.beginGroup("Phantom1")
    config.setValue("IP", ui.Phantom1IP.text())
    config.setValue("FrameSync", ui.Phantom1FrameSync.currentText())
    config.setValue("ImageFormat", ui.Phantom1ImageFormat.currentText())
    config.endGroup()

    config.beginGroup("Phantom2")
    config.setValue("IP", ui.Phantom2IP.text())
    config.setValue("FrameSync", ui.Phantom2FrameSync.currentText())
    config.setValue("ImageFormat", ui.Phantom2ImageFormat.currentText())
    config.endGroup()

    config.beginGroup("I2PS")
    config.setValue("SelectPS", ui.comboBoxI2PSSelectPS.currentIndex())
    config.setValue("IP", ui.I2PSIP.text())
    config.setValue("VoltagePPMCP", ui.I2PSVoltagePPMCP.value())
    config.setValue("VoltageMCP", ui.I2PSVoltageMCP.value())
    config.setValue("VoltagePCHighSide", ui.I2PSVoltagePCHighSide.value())
    config.setValue("VoltagePCLowSide", ui.I2PSVoltagePCLowSide.value())
    config.setValue("PulseDuration", ui.I2PSPulseDuration.value())
    config.setValue("TriggerDelay", ui.I2PSTriggerDelay.value())
    config.setValue("Coarse", ui.II_Coarse.currentIndex())
    config.setValue("Fine", ui.II_Fine.value())
    config.setValue("Gain", ui.II_Gain.value())
    config.endGroup()

    config.beginGroup("Ophir")
    config.setValue("SerialPort", ui.OphirSerialPort.text())
    config.endGroup()

    config.beginGroup("ADC")
    config.setValue("RecordLength", ui.ADCRecordLength.value())
    config.setValue("SampleRate", ui.ADCSampleRate.currentText())
    config.setValue("InputRange", ui.ADCInputRange.currentText())
    config.setValue("CH1Name", ui.ADCCH1Name.text())
    config.setValue("CH2Name", ui.ADCCH2Name.text())
    config.setValue("CH1Enable", ui.ADCCH1Enable.isChecked())
    config.setValue("CH2Enable", ui.ADCCH2Enable.isChecked())
    config.endGroup()

    config.beginGroup("Scope")
    config.setValue("SerialPort", ui.ScopeSerialPort.text())
    config.setValue("IP", ui.ScopeIP.text())
    config.setValue("CH1Name", ui.ScopeCH1Name.text())
    config.setValue("CH2Name", ui.ScopeCH2Name.text())
    config.setValue("CH3Name", ui.ScopeCH3Name.text())
    config.setValue("CH4Name", ui.ScopeCH4Name.text())
    config.setValue("CH1Enable", ui.ScopeCH1Enable.isChecked())
    config.setValue("CH2Enable", ui.ScopeCH2Enable.isChecked())
    config.setValue("CH3Enable", ui.ScopeCH3Enable.isChecked())
    config.setValue("CH4Enable", ui.ScopeCH4Enable.isChecked())
    config.endGroup()

    config.beginGroup("Triggering")
    config.setValue("IP", ui.TriggerIP.text())
    config.setValue("Port", ui.TriggerPort.value())
    config.endGroup()

    # Triggering/times
    write_trigger_settings(MPTS_trigger_file, ui)


def read_trigger_settings(data, ui):
    for command in data:
        match = regex.search(command)
        if match.group(1) == "End_of_file":
            break
        widget = ui.centralwidget.findChild(QtWidgets.QSpinBox, triggering.logical_names[match.group(1)])
        if widget:
            widget.setValue(int(match.group(2)))
        else:
            widget = ui.centralwidget.findChild(QtWidgets.QCheckBox, triggering.logical_names[match.group(1)])
            widget.setChecked(int(match.group(2)))


def write_trigger_settings(filename, ui):
    f = open(filename, 'w')
    for logical_name in triggering.physical_names:
        widget = ui.centralwidget.findChild(QtWidgets.QSpinBox, logical_name)
        if widget:
            f.write('%s = "%s"\n' % (triggering.physical_names[logical_name], widget.value()))
        else:
            widget = ui.centralwidget.findChild(QtWidgets.QCheckBox, logical_name)
            f.write('%s = "%s"\n' % (logical_name, int(widget.isChecked())))
    f.write('End_of_file = "empty"\n')
    f.close()
