#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Implementation of the Trigger Unit communication."""

import logging
import re
import socket

_log = logging.getLogger(__name__)

physical_names = {
    'A2_Delay': r'Simmer_delay(1uS)',
    'A4_Delay': r'Burst_delay(1uS)',
    'A4_Number': r'Burst_number',
    'A4_Period': r'Burst_period(1uS)',
    'A5_Pulse': r'Trigger_Enable_pulse(1uS)',
    'B1_Delay': r'ADC_Enable_delay(1uS)',
    'B1_Pulse': r'ADC_Enable_pulse(1uS)',
    'B2_Delay': r'CMOS_plasma_delay(1uS)',
    'B2_Number': r'CMOS_Plasma_number',
    'B2_Period': r'CMOS_Plasma_period(1uS)',
    'B2_Pulse': r'CMOS_Plasma_pulse(1uS)',
    'B4_Delay': r'CMOS_Laser_delay(0.1uS)',
    'B4_Pulse': r'CMOS_Laser_pulse(0.1uS)',
    'B5_Delay': r'II_Gate_Plasma_delay(0.1uS)',
    'B5_Number': r'II_Gate_Plasma_number',
    'B5_Period': r'II_Gate_Plasma_period(0.1uS)',
    'B5_Pulse': r'II_Gate_Plasma_pulse(0.1uS)',
    'B6_Delay': r'II_Plasma_Delay_delay(0.1uS)',
    'B6_Pulse': r'II_Plasma_Delay_pulse(0.1uS)',
    'B7_Delay': r'II_Gate_Laser_delay(0.1uS)',
    'B7_Pulse': r'II_Gate_Laser_pulse(0.1uS)',
    'B8_Delay': r'II_Flash_Bool_delay(1uS)',
    'B8_Pulse': r'II_Flash_Bool_pulse(1uS)',
    'B9_Delay': r'Flash_delay(1uS)',
    'B9_Pulse': r'Flash_pulse(1uS)',
    'B12_Delay': r'Pockels_delay(1uS)',
    'B12_Number': r'Pockels_number',
    'B12_Period': r'Pockels_period(1uS)',
    'B12_Pulse': r'Pockels_pulse(1uS)',
    'TS0_Delay': r'TS0_Delay(1uS)',
    'TS0_Period': r'TS0_Period(1uS)',
    'Enable_IOs': r'Enable_IOs',
    'A1_SW_enable': r'A1_SW_enable',
    'A2_SW_enable': r'A2_SW_enable',
    'A4_SW_enable': r'A4_SW_enable',
    'CMOSPOn': r'CMOSPOn',
    'CMOSLOn': r'CMOSLOn'
}

try:
    # For Python 3
    logical_names = {v: k for k, v in physical_names.items()}
except:
    # For Python 2
    logical_names = dict((v, k) for k, v in physical_names.iteritems())

regex = re.compile('(\S+)[\s*]=[\s*]"(\S+)"')


class TriggerUnit():
    MAX_MESSAGE_SIZE = 65536

    def __init__(self, ip=None, port=15000, default_fps=None, debug=False):
        """Set up all communications with the camera.

        When a new Phantom object is made it will broadcast out over the
        network to find the camera and initialize command and data TCP
        connections with it so that future interactions with the camera
        work.
        """
        self.name = ""
        self.ip = ip
        self.port = port

        self._cmd_sock = None
        self.connection_status = False
        self.debug = debug

        if ip is not None:
            self.openConnection(self.ip, self.port)

    def openConnection(self, ip=None, port=15000, cmd_timeout=1):
        self.ip = ip or self.ip
        self.port = port or self.port
        try:
            # Set up the command connection
            print("Trying to connect to the Triggering unit - CompactRio (IP: %s, port: %s)." % (self.ip, self.port))
            self._cmd_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self._cmd_sock.settimeout(cmd_timeout)
            self._cmd_sock.connect((self.ip, self.port))
            self.connection_status = True
        except:
            print("Error trying to connect to the Triggering unit - CompactRio (IP: %s, port: %s)." % (self.ip, self.port))
            self.connection_status = False
            pass

    def isConnected(self):
        try:
            # Makes a simple request and wait for the answer to check if the connection is working
            self._cmd_sock.send(b'Mode = "?"\r\n')
            recv = self._cmd_sock.recv(self.MAX_MESSAGE_SIZE).decode('latin-1')
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
        if self._cmd_sock is not None:
            self._cmd_sock.close()
            self._cmd_sock = None
            self.connection_status = False

    def _SendCommandAsync(self, cmd):
        """Send command without waiting for the response.
        You must call ReceiveCommandResponse before calling this method again.
        """
        _log.debug("SEND(%d): %s", len(cmd), cmd)
        if self.debug:
            print("cRio: >>%s" % cmd)
        cmd = bytearray(cmd, 'latin-1') + b"\r\n"
        total_sent = 0
        while total_sent < len(cmd):
            sent = self._cmd_sock.send(cmd[total_sent:])
            if sent == 0:
                raise Exception("Cannot send command")
            total_sent += sent

    def _ReceiveCommandResponse(self):
        """Reveice response from a command sent with SendCommandAsync."""
        recv = ""
        try:
            while True:
                block = self._cmd_sock.recv(self.MAX_MESSAGE_SIZE).decode('latin-1')
                recv += block
                if len(block) == 0 or (len(block) > 2 and block[-1] == "\n"):
                    break
            # if "Err" in recv:
            #    raise Exception("Received error code:" + recv)
            _log.debug("RECV(%d): %s", len(recv), recv.strip())
            if self.debug:
                print("cRio: <<%s" % recv.strip())
            return recv.strip()
        except ConnectionAbortedError:
            self.closeConnection()
            print("cRio: Connection Aborted Error")
            return ""
        except:
            return ""

    def _SendCommand(self, cmd):
        """Send a command to the camera, and return the response."""
        self._SendCommandAsync(cmd)
        return self._ReceiveCommandResponse()

    def sendSettings(self, name, value):
        """Send a setting to the Triggering system. Returns error flag"""
        if self.connection_status:
            cmd = '%s = "%d"' % (name, value)
            ans = self._SendCommand(cmd)
            return False if 'Ok' in ans else True

    def readSettings(self, name):
        """Reads a setting from the Triggering system.
        Returns the value of the setting, or a blank string is error occurs."""
        if self.connection_status:
            cmd = '%s = "?"' % name
            res = self._SendCommand(cmd)
            match = regex.search(res)
            if not match:
                self.connection_status = False
                raise Exception("Invalid response: %s", res)
            return int(match.group(2))
        else:
            return None

    def setMode(self, mode):
        cmd = 'Mode = "%d"' % mode
        ans = self._SendCommand(cmd)
        return False if 'Ok' in ans else True

    def readMode(self):
        ans = self.readSettings("Mode")
        return ans

    def readStatus(self):
        self.io_enabled = bool(self.readSettings("IOs_enabled"))
        self.laser_ready = bool(self.readSettings("Laser_Ready_I"))
        self.interlock = bool(self.readSettings("Interlock"))
        return self.io_enabled, self.laser_ready, self.interlock
