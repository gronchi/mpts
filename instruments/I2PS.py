import logging
import socket
import base64
import re
import numpy as np

_log = logging.getLogger(__name__)

PREAMBLE = b'\x02'
regex = re.compile('\x02(.*)\n')
MAX_MESSAGE_SIZE = 65536


class PowerSupply(object):

    def __init__(self, ip=None, port=10001, default_fps=None):
        self.name = ""
        self.ip = ip
        self.port = port
        self._cmd_sock = None
        self.connection_status = False

        self.VoltagePPMCP = 0
        self.VoltageMCP = 0
        self.PCHighSide = 0
        self.PCLowSide = 0
        self.PPCurrent = 0
        self.MCPCurrent = 0
        self.PCHighSideCurrent = 0
        self.PCHighSideCurrent = 0

        self.PulseDuration = 0
        self.TriggerDelay = 0

        if ip is not None:
            self.openConnection(self.ip, self.port)

    def openConnection(self, ip=None, port=10001, timeout=1):
        if self._cmd_sock is not None:
            self._cmd_sock.close()

        self.ip = ip or self.ip
        self.port = port or self.port
        try:
            # Set up the command connection
            self._cmd_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self._cmd_sock.settimeout(timeout)
            self._cmd_sock.connect((self.ip, self.port))
            self.connection_status = True
        except:
            print("Error trying to connect to the I2PS (IP: %s, port: %s)." % (self.ip, self.port))
            self.connection_status = False
            pass

    def isConnected(self):
        if not self.connection_status:
            return False
        try:
            # Makes a simple request and wait for the answer to check if the connection is working
            data = self.getName()
            if len(data) > 0:
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

    def _SendCommand(self, cmd):
        """Send command without waiting for the response."""
        _log.debug("SEND(%d): %s", len(cmd), cmd)
        total_sent = 0
        while total_sent < len(cmd):
            sent = self._cmd_sock.send(cmd[total_sent:])
            if sent == 0:
                raise Exception("Cannot send command")
            total_sent += sent

    def _ReceiveCommandResponse(self):
        """Reveice response from a command."""
        recv = ""
        recv = self._cmd_sock.recv(MAX_MESSAGE_SIZE).decode('latin-1')
        return recv

    def _SetProperty(self, base=0, index=0, mask=0xFFFFFFFF, data=[]):
        cmd = {'DevAddrSrc': 0,
               'DevAddrDest': 0,
               'Operator': 'PUT',
               'Type': 'INT',
               'DataLength': 1,
               'CmdExt': 0,
               'Base': base,
               'Index': index,
               'Mask': mask,
               'Data': data}
        msg = DifferIF_buildcmd_b64(cmd)
        self._SendCommand(msg)

    def _GetProperty(self, base=0, index=0, mask=0xFFFFFFFF, Type='INT', data=[]):
        cmd = {'DevAddrSrc': 0,
               'DevAddrDest': 0,
               'Operator': 'GET',
               'Type': Type,
               'DataLength': 1,
               'CmdExt': 0,
               'Base': base,
               'Index': index,
               'Mask': mask,
               'Data': data}
        msg = DifferIF_buildcmd_b64(cmd)
        self._SendCommand(msg)
        recv = ""
        while True:
            recv += self._ReceiveCommandResponse()
            if recv[-1] == '\n':
                if len(recv) >= 31:
                    for m in regex.finditer(recv):
                        # print(m.group(1).encode("latin-1"))
                        cmd = DifferIF_intercmd_b64("\x02" + m.group(1) + "\n")
                        if cmd['Base'] == base and cmd['Index'] == index:
                            return cmd['Data']
                        else:
                            self._SendCommand(msg)
                    recv = ""
                else:
                    self._SendCommand(msg)
                    recv = ""

    def reset(self):
        self.disablePulse()
        self.disablePS()
        # Reset errors
        self._SetProperty(base=0x11, index=0x00, mask=0x80000000, data=[0x80000000])
        # Read CtrlReg
        self.CtrlReg = self._GetProperty(base=0x11, index=0x00)
        self.getCtrlReg()
        self.getStatReg()

    def disablePulse(self):
        self._SetProperty(base=0x00, index=0x0D, mask=0xFFFFFFFF, data=[0x00])

    def disablePS(self):
        self._SetProperty(base=0x00, index=0x0C, mask=0xFFFFFFFF, data=[0x00])

    def getCtrlReg(self):
        return self._GetProperty(base=0x00, index=0x0C, mask=0xFFFFFFFF, data=[0x00])

    def getStatReg(self):
        return self._GetProperty(base=0x00, index=0x02)

    def getInputState(self):
        getStatReg = self.getStatReg()[0]
        input1 = getStatReg & 0x01
        input2 = getStatReg & 0x02
        input3 = getStatReg & 0x03
        return input1, input2, input3

    def getErrorState(self):
        getStatReg = self.getStatReg()[0]
        PP_error = getStatReg & 28
        MCP_error = getStatReg & 29
        PC_h_error = getStatReg & 30
        PC_l_error = getStatReg & 31
        return PP_error, MCP_error, PC_h_error, PC_l_error

    def enablePS(self, enable=True):
        self._SetProperty(base=0x00, index=0x0C, mask=0xFFFFFFFF, data=[int(enable)])
        return bool(self._GetProperty(base=0x00, index=0x0C, mask=0xFFFFFFFF, data=[])[0])

    def enablePulse(self, enable=True):
        self._SetProperty(base=0x00, index=0x0D, mask=0xFFFFFFFF, data=[int(enable)])
        return bool(self._GetProperty(base=0x00, index=0x0D, mask=0xFFFFFFFF, data=[])[0])

    def isPSEnabled(self, enable=True):
        return bool(self._GetProperty(base=0x00, index=0x0C, mask=0xFFFFFFFF, data=[])[0])

    def isPulseEnabled(self, enable=True):
        return bool(self._GetProperty(base=0x00, index=0x0D, mask=0xFFFFFFFF, data=[])[0])

    def setPulseDuration(self, duration):
        self._SetProperty(base=0x00, index=0x0E, mask=0xFFFFFFFF, data=[duration])
        return self._GetProperty(base=0x00, index=0x0E, mask=0xFFFFFFFF, data=[])[0]

    def setTriggerDelay(self, delay):
        self._SetProperty(base=0x00, index=0x0F, mask=0xFFFFFFFF, data=[delay])
        return self._GetProperty(base=0x00, index=0x0F, mask=0xFFFFFFFF, data=[])[0]

    def setVoltagePPMCP(self, voltage):
        self._SetProperty(base=0x00, index=0x10, mask=0xFFFFFFFF, data=[voltage])
        return self._GetProperty(base=0x00, index=0x10, mask=0xFFFFFFFF, data=[])[0]

    def setVoltageMCP(self, voltage):
        self._SetProperty(base=0x00, index=0x11, mask=0xFFFFFFFF, data=[voltage])
        return self._GetProperty(base=0x00, index=0x11, mask=0xFFFFFFFF, data=[])[0]

    def setVoltagePCHighSide(self, voltage):
        self._SetProperty(base=0x00, index=0x12, mask=0xFFFFFFFF, data=[voltage])
        return self._GetProperty(base=0x00, index=0x12, mask=0xFFFFFFFF, data=[])[0]

    def setVoltagePCLowSide(self, voltage):
        self._SetProperty(base=0x00, index=0x13, mask=0xFFFFFFFF, data=[voltage])
        return self._GetProperty(base=0x00, index=0x13, mask=0xFFFFFFFF, data=[])[0]

    def getName(self):
        return self._GetProperty(base=0x12, index=0x40, mask=0xFF, Type='STRING', data="")

    # Measurements
    def getVoltagePPMCP(self):
        return self._GetProperty(base=0x10, index=0x11, mask=0xFFFFFFFF, data=[])[0]

    def getVoltageMCP(self):
        return self._GetProperty(base=0x10, index=0x12, mask=0xFFFFFFFF, data=[])[0]

    def getVoltagePCHighSide(self):
        return self._GetProperty(base=0x10, index=0x13, mask=0xFFFFFFFF, data=[])[0]

    def getVoltagePCLowSide(self):
        voltage = self._GetProperty(base=0x10, index=0x14, mask=0xFFFFFFFF, data=[])[0]
        if not voltage:
            return voltage
        else:
            return int(-1.0 * (0xFFFFFFFF + 1 - voltage))

    def getCurrentPP(self):
        return self._GetProperty(base=0x00, index=0x03, mask=0xFFFFFFFF, data=[])[0] / 10.

    def getCurrentMCP(self):
        return self._GetProperty(base=0x00, index=0x04, mask=0xFFFFFFFF, data=[])[0] / 10.

    def getCurrentPCHighSide(self):
        return self._GetProperty(base=0x00, index=0x05, mask=0xFFFFFFFF, data=[])[0] / 10.

    def getCurrentPCLowSide(self):
        return self._GetProperty(base=0x11, index=0x00, mask=0xFFFFFFFF, data=[])[0] / 10.

    def SoftTrigger(self):
        self._SetProperty(base=0x00, index=0x13, mask=0x40000000, data=[0x40000000])


def u8list_to_ux(l):
    result = 0
    for x in l:
        result = (result << 8) + x
    return result


def ux_to_u8list(value, base):
    # base: 0=char, 1=short, 2=int
    result = []
    i = 2**base
    while i > 0:
        result += [value & 0xFF]
        value = value >> 8
        i -= 1
    result.reverse()
    return result


def DifferIF_buildcmd_b64(cmd):
    """
    Builds a base64 Differ IF command, starting with a preamble (0x02) and terminated with crlf
    Argument: Differ IF command dictionary
        Keys:
            DevAddrSrc: source id (u8)
            DevAddrDest: dest id (u8)
            Operator: 'NONE' | 'PUT' | 'GET'
            Type: 'STRING' | 'CHAR' | 'SHORT' | 'INT' | 'SINGLE' | 'DOUBLE'
            DataLength: number of items to transfer (u8)
            CmdExt: general pupose
            Base: base address of first item
            Index: index address of first item
            Mask: bitwise mask, '1' means alterable, '0' means don't change
            Data: string or list of items (<256)
    Result: Base64 character string representing the command
    """
    DevAddrSrc = cmd['DevAddrSrc']
    DevAddrDest = cmd['DevAddrDest']
    Operator = ['NONE', 'PUT', 'GET'].index(cmd['Operator'].upper())
    Type = ['STRING', 'CHAR', 'SHORT', 'VOID', 'INT', 'SINGLE', 'DOUBLE'].index(cmd['Type'].upper())
    DataLength = cmd['DataLength']
    CmdExt = cmd['CmdExt']
    Base = cmd['Base']
    Index = cmd['Index']
    Mask = cmd['Mask']
    Data = cmd['Data'][0:255]  # limit to 255 units

    if Type == 0:  # string type
        Data = map(ord, Data)

    if Operator == 1:  # put
        DataLength = len(Data)
    #   operator/type   STRING                              NOT A STRING
    #   PUT             datalength is of no importance      datalength is determined by the number of data items
    #   GET             datalength is of no importance      datalength is determined by the argument list

    Type_str = cmd['Type'].upper()
    if Type_str == 'STRING' or Type_str == 'CHAR':
        base = 0
    elif Type_str == 'SHORT':
        base = 1
    elif Type_str == 'INT':
        base = 2
    elif Type_str == 'SINGLE' or Type_str == 'DOUBLE':
        base = 3
    # SINGLE and DOUBLE not implemented yet!

    result = ux_to_u8list(DevAddrSrc, 0) + \
        ux_to_u8list(DevAddrDest, 0) + \
        ux_to_u8list((Operator << 4) + Type, 0) + \
        ux_to_u8list(DataLength, 0) + \
        ux_to_u8list(CmdExt, 2) + \
        ux_to_u8list(Base, 2) + \
        ux_to_u8list(Index, 2) + \
        ux_to_u8list(Mask, base)
    for x in Data:
        result += ux_to_u8list(x, base)
    b64 = PREAMBLE + base64.standard_b64encode(bytearray(u''.join(map(chr, result)), 'latin-1')) + b'\r\n'  # surround with preamble and crlf
    return b64


def DifferIF_intercmd_b64(cmd):
    """
    Interpretes a Differ IF command from a base64 string
    Argument: Base64 character string representing the command, preceeded by a preamble (0x02) and terminated with crlf
    Result: Differ IF command dictionary

            Keys:
                DevAddrSrc: source id (u8)
                DevAddrDest: dest id (u8)
                Operator: 'NONE' | 'PUT' | 'GET'
                Type: 'STRING' | 'CHAR' | 'SHORT' | 'INT' | 'SINGLE' | 'DOUBLE'
                DataLength: number of items to transfer (u8)
                CmdExt: general pupose
                Base: base address of first item
                Index: index address of first item
                Mask: bitwise mask, '1' means alterable, '0' means don't change
                Data: string or list of items
    """

    if (cmd[0] == PREAMBLE) and (cmd[-1] == '\n'):
        cmd = cmd.replace(PREAMBLE, '')  # remove preamble
        cmd = cmd.replace('\r', '')  # remove cr
        cmd = cmd.replace('\n', '')  # remove lf
    lst = list(base64.standard_b64decode(cmd))
    Differ_cmd = {}
    Differ_cmd['DevAddrSrc'] = lst[0]
    Differ_cmd['DevAddrDest'] = lst[1]
    Differ_cmd['Operator'] = ['NONE', 'PUT', 'GET'][lst[2] >> 4]
    Differ_cmd['Type'] = ['STRING', 'CHAR', 'SHORT', 'VOID', 'INT', 'SINGLE', 'DOUBLE'][lst[2] & 0xF]
    Differ_cmd['DataLength'] = lst[3]
    Differ_cmd['CmdExt'] = u8list_to_ux(lst[4:8])
    Differ_cmd['Base'] = u8list_to_ux(lst[8:12])
    Differ_cmd['Index'] = u8list_to_ux(lst[12:16])

    if Differ_cmd['Type'] == 'STRING' or Differ_cmd['Type'] == 'CHAR':
        base = 0
    elif Differ_cmd['Type'] == 'SHORT':
        base = 1
    elif Differ_cmd['Type'] == 'INT':
        base = 2
    elif Differ_cmd['Type'] == 'SINGLE' or Differ_cmd['Type'] == 'DOUBLE':
        base = 3

    # base = (lst[2] & 0xF) - 1
    if base < 0:
        base = 0
    # SINGLE and DOUBLE not implemented yet!
    stp = 2**base
    Differ_cmd['Mask'] = u8list_to_ux(lst[16:16 + stp])
    del lst[:16 + stp]  # only data items
    data = []
    while lst:
        data += [u8list_to_ux(lst[:stp])]
        del lst[:stp]

    if Differ_cmd['Type'] == 'STRING':
        Differ_cmd['Data'] = ''.join(map(chr, data))
        Differ_cmd['DataLength'] = 1
    else:
        Differ_cmd['Data'] = data

    return Differ_cmd


FineCoarseTable = np.array([2740, 2766, 2792, 2818, 2844, 2870, 2896, 2922, 2948, 2974,
                            3000, 3028, 3056, 3084, 3112, 3140, 3168, 3196, 3224, 3252,
                            3280, 3312, 3344, 3376, 3408, 3440, 3472, 3504, 3536, 3568,
                            3600, 3646, 3692, 3738, 3784, 3830, 3876, 3922, 3968, 4014,
                            4060, 4068, 4076, 4084, 4092, 4100, 4108, 4116, 4124, 4132,
                            4140, 4220, 4300, 4380, 4460, 4540, 4620, 4700, 4780, 4860,
                            4940, 5060, 5180, 5300, 5420, 5540, 5660, 5780, 5900, 6020,
                            6140, 6340, 6540, 6740, 6940, 7140, 7340, 7540, 7740, 7940,
                            8140, 8536, 8932, 9328, 9724, 10120, 10516, 10912, 11308, 11704,
                            12100, 12880, 13480, 14430, 15380, 16630, 17880, 19480, 21380, 24740, 28100])


def KentechGate(Coarse, Fine):
    """Return the gate time in nanoseconds of the Kentech Power Supply as a function of the Coarse gate selection
    and the fine knob setting"""
    coarse = float(Coarse.replace(" ", "").replace("ns", "e-9").replace("us", "e-6").replace("ms", "e-3"))
    index_fc = int(Fine * 10)
    if (coarse > 2.9E-3):
        return(FineCoarseTable[index_fc] * 1000)  # 3 msec
    if (coarse > 2.9E-4):
        return(FineCoarseTable[index_fc] * 100)  # 300 usec
    if (coarse > 2.9E-5):
        return(FineCoarseTable[index_fc] * 10)  # 30 usec
    if (coarse > 2.9E-6):
        return(FineCoarseTable[index_fc] * 1)  # 3 usec
    if (coarse > 2.9E-7):
        return(FineCoarseTable[index_fc] * 0.1)  # 300 nsec
    if (coarse > 2.9E-8):
        return(FineCoarseTable[index_fc] * 0.01)  # 30 nsec


if __name__ == '__main__':
    #
    # test driver
    i2ps = PowerSupply()
    i2ps.openConnection(ip="10.182.5.7")
    recv = ""
    i2ps.enablePS(enable=False)
    i2ps.enablePulse(enable=False)
    print(i2ps.getName())
    # while True:
    # i2ps.getName()
    #    i2ps._SetProperty(base=0x00, index=12, mask=4294967295, data=[1])
    #    i2ps._SetProperty(base=0x00, index=13, mask=4294967295, data=[1])
    # cmd = {'DevAddrSrc': 0, 'DevAddrDest': 0,
    #       'Operator': 'PUT', 'Type': 'INT', 'DataLength': 1, 'CmdExt': 0, 'Base': 0x10, 'Index': 0x0, 'Mask': 0xFFFFFFFF, 'Data': []}
    # i2ps._SendCommand(DifferIF_buildcmd_b64(cmd))
    #    recv += i2ps._ReceiveCommandResponse()
    #    if recv[-1] == '\n':
    #        # print(recv)
    #        for m in regex.finditer(recv):
    #            cmd = DifferIF_intercmd_b64("\x02" + m.group(1) + "\n")
    #            print("to aqui")
    #            print(cmd)
    #        recv = ""
