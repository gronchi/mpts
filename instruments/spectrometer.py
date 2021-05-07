#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Implementation of the Laser Power Measurement Device."""

import serial


class Spectrometer:
    HomeMode = 0x0001
    MAX_MESSAGE_SIZE = 65536
    MAX_PTFRAMES = 2245

    def __init__(self, port=None, timeout=1, baudrate=19200):
        self.ser = serial.Serial()
        self.ser.port = port
        self.ser.baudrate = baudrate
        self.ser.timeout = timeout
        self.connection_status = False

    def openConnection(self, port='COM1', baudrate=9600, timeout=0.1):
        self.ser.port = port
        self.ser.baudrate = baudrate
        self.ser.timeout = timeout
        self.ser.write_timeout = 1
        try:
            self.ser.open()
            self.ser.reset_input_buffer()
            self.ser.reset_output_buffer()
            self.name = self.getIdent()
            self.connection_status = True
        except:
            print("Error trying to connect to the Spectrometer (Serial port %s, baudrate %s)." % (self.ser.port, self.ser.baudrate))
            self.connection_status = False

    def getIdent(self):
        self.ser.write(b"*IDN?\r")
        return self.ser.readline().strip()

    def setRemote(self):
        self.ser.write(b"MR\r")

    def setLocal(self):
        self.ser.write(b"ML\r")

    def setMotorOn(self):
        self.ser.write(b"MO\r")

    def setPosition(self, axis, data):
        self.ser.write(b"%dPA%6.4f\r" % (axis, data))

    def getPosition(self, axis):
        self.ser.write(b"%dTP\r" % axis)
        # reply is  (1TP'position', 2TP'position')
        return float(self.ser.readline()[3:])

    def setHome(self, axis):
        self.ser.write(b"%dOR%d" % (axis, self.HomeMode))

    def checkRemoteMode(self):
        self.ser.write(b"TX\r")
        status = int(self.readline())
        if ((status & 0x0004) >> 2) == 1:
            return(False)  # manual mode
        else:
            return(True)   # remote mode
