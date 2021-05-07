#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Implementation of the Laser Power Measurement Device."""

import serial
import time
import sys


class LaserStar():
    def __init__(self, port=None, baudrate=9600, timeout=1, debug=False):
        self.connection_status = False
        self.firmware = ""
        self.coef1 = 1.0
        self.coef2 = 1.0
        self.ser = serial.Serial()
        self.connection_status = False
        self.debug = debug
        if port:
            self.openConnection(port, baudrate, timeout)

    def openConnection(self, port=None, baudrate=9600, timeout=1):
        self.ser.port = port
        self.ser.baudrate = baudrate
        self.ser.timeout = timeout
        self.ser.write_timeout = 1
        try:
            self.ser.open()
            self.ser.reset_input_buffer()
            self.ser.reset_output_buffer()
            self.ser.write(b"$VE\r")
            self.firmware = self.ser.readline().decode("latin-1").strip()
            self.connection_status = True
        except:
            print("Error trying to connect to Laser Power meter (Serial port %s, baudrate %s)." % (self.ser.port, self.ser.baudrate))
            self.connection_status = False

    def isConnected(self):
        if not self.ser.isOpen():
            self.connection_status = False
            return False
        try:
            # Makes a simple request and wait for the answer to check if the connection is working
            self.ser.reset_output_buffer()
            self.ser.reset_input_buffer()
            self.ser.write(b"$II\r")
            time.sleep(0.1)
            recv = self.ser.readline().strip()
            if len(recv) > 0:
                self.connection_status = True
                return True
            else:
                self.connection_status = False
                return False
        except:
            self.connection_status = False
            return False

    def write(self, command):
        if self.connection_status:
            self.ser.write(bytearray(command + "\r", "latin-1"))

    def read(self):
        if self.connection_status:
            ans = self.ser.readline().decode("latin-1").strip()
            return ans

    def query(self, command):
        self.write(command)
        return self.read()

    def getName(self):
        self.name = self.query("$II")[1:]
        return self.name

    def getFirmware(self):
        self.firmware = self.query("$VE")[1:]
        return self.firmware

    def getData(self):
        try:
            self.ser.write(b"$SB\r")
            time.sleep(0.1)
            str = self.ser.readline().decode("latin-1").strip()
            if self.debug:
                print(str)
        except Exception:
            exc_type, value, traceback = sys.exc_info()
            print("Failed with exception [%s]" % exc_type)
            self.head1 = -1.0
            self.head2 = -1.0
            return self.head1, self.head2

        if str[0] == '*':
            if str[2] == 'N':
                self.head1 = -1.0
                if str[4] == 'N':
                    self.head2 = -1.0
                else:
                    self.head2 = float(str[4:])
            else:
                self.head1 = float(str[2:11])
                if 'N' in str[11:]:
                    self.head2 = -1.0
                else:
                    self.head2 = float(str[11:])
        else:
            self.head1 = -1.0
            self.head2 = -1.0
        return self.head1, self.head2

    def getCoefficients(self, coef1, coef2):
        return self.coef1, self.coef2

    def setCoefficients(self, coef1, coef2):
        self.coef1 = coef1
        self.coef2 = coef2

    def getRealEnergy(self):
        self.getData()
        return self.coef1 * self.head1, self.self.coef2 * self.head2

    def wasTriggered(self):
        """Check if an energy measurement has been completed and has not yet been
        read using the $SE command"""
        if self.connection_status:
            energy_flag = int(self.query("$EF")[1])
            if energy_flag == 1:
                return True
            else:
                return False


if __name__ == "__main__":
    laserstar = LaserStar(port='COM4')
    print("LaserStar power meter")
    print("Firmware version: %s" % laserstar.getFirmware())
    print("Name: %s" % laserstar.getName())
    laserstar.getData()
    print("Measure: Head 1: %d. Head 2: %d" % (laserstar.data1, laserstar.data2))
