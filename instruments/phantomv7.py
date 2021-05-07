"""Implementation of the HighSpeedCamera class for the Phantom camera."""

import logging
import re
import select
import socket
import time
import numpy as np

import psutil


_log = logging.getLogger(__name__)


class _ImageRequest(object):
    """Class storing information about a requested chunk of images."""

    def __init__(self, phantom, start, num_frames):
        self.phantom = phantom
        self.num_frames = num_frames
        self.start = start
        self.shape = None

    def ReceiveAck(self):
        """Receive acknowledgement from camera on command channel.

        This has to be called before another image can be requested. Otherwise we
        might run into race conditions where the camera mixes up requests.
        """
        response = self.phantom._ReceiveCommandResponse()

        # Determine the resolution of the image and how many bytes to wait for
        RESOLUTION_REGEX = (".*Ok!\s*{\s*cine\s*:\s*\d+,\s*res\s*:\s*" +
                            "(?P<width>\d+)\s+x\s+(?P<height>\d+)\s*}")
        matches = re.match(RESOLUTION_REGEX, response)
        width = int(matches.group("width"))
        height = int(matches.group("height"))
        self.shape = (height, width)

    def Receive(self):
        """Receive image data."""
        if self.shape is None:
            self.ReceiveAck()
        return self.phantom._ReceiveImages(self.shape, self.num_frames)


class PhantomCamera(object):
    DATA_STREAM_PORT = 7116
    MAX_MESSAGE_SIZE = 65536
    MAX_PTFRAMES = 2245

    FLAGS = {
        "READY": "RDY",  # A cine is ready to record into
        "COMPLETE": "STR",  # A full cine is already recorded here
        "INVALID": "INV",  # Invalid cine, can't be used for anything
        "WAITING": "WTR",  # Waiting for a trigger to start recording
    }

    def __init__(self, ip=None, port=7115, default_fps=None, debug=False):
        """Set up all communications with the camera.

        When a new Phantom object is made it will broadcast out over the
        network to find the camera and initialize command and data TCP
        connections with it so that future interactions with the camera
        work.
        """
        self.cine = 1
        self.name = ""
        self.ip = ip
        self.port = port
        self.exposure_ns = None
        self.fps = 10800
        self.num_frames = 1
        self.connection_status = False
        self.debug = debug

        self._command_sent = False
        self._triggered = False
        self._prepared = False
        self._cmd_sock = None
        self._base_sock = None
        self._data_sock = None
        self.serial = None
        self.default_fps = 10900

        if ip is not None:
            self.openConnection(self.ip, self.port)

    def openConnection(self, ip=None, port=7115, cmd_timeout=1, data_timeout=5):
        if self._cmd_sock is not None:
            return

        try:
            self.ip = ip or self.ip
            self.port = port or self.port
            self._cmd_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self._cmd_sock.settimeout(cmd_timeout)
            self._cmd_sock.connect((self.ip, self.port))
        except socket.timeout:
            print("Camera time out")
            self.connection_status = False
            self.closeConnection()
            return

        self.serial = self.getSerialNumber()
        print(self.ip, self.serial)
        if not self.serial:
            print("Error trying to connect to the Phantom Camera (IP: %s, port: %s)." % (self.ip, self.port))
            self.closeConnection()
            self.connection_status = False
            return
        if self.serial == "3723":
            data_ip = '100.100.100.1'
            data_port = 7123
        else:
            data_ip = '100.100.100.1'
            data_port = 7124
        # Set up the data connection
        self._base_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._base_sock.bind((data_ip, data_port))
        self._base_sock.listen(1)
        self._cmd_sock.send(b"startdata { port : %d }\n" % data_port)
        print(self._cmd_sock.recv(self.MAX_MESSAGE_SIZE))
        try:
            print(self._cmd_sock.recv(self.MAX_MESSAGE_SIZE))
        except socket.timeout:
            pass
        self.connection_status = True
        self._data_sock, addr = self._base_sock.accept()

    def isConnected(self):
        """Checks if the camera is currently connedted by making a simple request
        and waiting for the answer."""
        try:
            self._cmd_sock.send(b'get info.serial\n')
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
        """Clos socket conection with the camera."""
        if self._cmd_sock is not None:
            self._cmd_sock.close()
            self._cmd_sock = None

        if self._data_sock is not None:
            self._data_sock.close()
            self._data_sock = None

    def _SendCommandAsync(self, cmd):
        """Send command without waiting for the response.

        You must call ReceiveCommandResponse before calling this method again.
        """
        if self.debug:
            print("camera: >>%s" % cmd)
        cmd = bytearray(cmd + "\r\n", 'ascii')
        if self._command_sent:
            msg = "Cannot send two commands without receiving resposne first."
            raise Exception(msg)

        if len(cmd) >= self.MAX_MESSAGE_SIZE:
            raise ValueError("Message too long!")

        _log.debug("SEND(%d): %s", len(cmd), cmd)
        total_sent = 0
        while total_sent < len(cmd):
            sent = self._cmd_sock.send(cmd[total_sent:])
            if sent == 0:
                raise Exception("Cannot send command")
            total_sent += sent
        self._command_sent = True

    def _ReceiveCommandResponse(self):
        """Reveices response from a command sent with SendCommandAsync."""
        if not self._command_sent:
            raise Exception("No command has been sent.")
        recv = ""
        while True:
            block = self._cmd_sock.recv(self.MAX_MESSAGE_SIZE).decode('latin-1')
            recv += block
            if len(block) == 0 or (len(block) > 2 and block[-1] == "\n" and block[-2] != "\\"):
                break
        if "ERR" in recv:
            raise Exception("Received error code:" + recv)
        _log.debug("RECV(%d): %s", len(recv), recv.strip())
        self._command_sent = False
        if self.debug:
            print("camera: <<%s" % recv.strip())
        return recv.strip()

    def _SendCommand(self, cmd):
        """Send a command to the camera, and return the response."""
        self._SendCommandAsync(cmd)
        return self._ReceiveCommandResponse()

    def Prepare(self, num_frames=None, fps=None, exposure=None):
        self.fps = fps or self.default_fps
        # if exposure is None and self.exposure_ns is None:
        #    self.exposure = (1.0 / float(self.fps)) * 1000.0
        self.exposure_ns = int((exposure or self.exposure) * 1000)

        self.num_frames = num_frames or self.num_frames
        if self.num_frames > self.MAX_PTFRAMES:
            raise ValueError("Cannot record more than %d frames" % self.MAX_PTFRAMES)

        _log.info("Preparing recording: fps=%d, exp=%d, num_frames=%d", self.fps, self.exposure_ns, self.num_frames)
        print("Preparing recording: fps=%d, exp=%d, num_frames=%d" % (self.fps, self.exposure_ns, self.num_frames))
        self._SendCommand("del %d" % self.cine)
        self._SendCommand("set c%d.state {ABL ACT}" % self.cine)
        self._SendCommand("set c%d.trigoff 0" % self.cine)
        self._SendCommand("set c%d.cam.syncimg 1" % self.cine)
        self._SendCommand("set c%d.cam.startonacq 1" % self.cine)
        self._SendCommand("set cam.startonacq 1")
        self._SetProperty("c%d.rate" % self.cine, self.fps)
        self._SetProperty("c%d.exp" % self.cine, self.exposure_ns)
        self._SetProperty("c%d.edrexp" % self.cine, 0)
        self._SetProperty("c%d.ptframes" % self.cine, self.num_frames)
        self._SendCommand("rec %d" % self.cine)

        ready_flag = "WTR"  # "Waiting for TRigger"
        while ready_flag not in self._SendCommand("get c%d.state" % self.cine):
            time.sleep(0.5)
        self._prepared = True
        self._triggered = False

    def Trigger(self):
        if not self._prepared:
            raise Exception("Can't trigger without camera being prepared.")
        self._SendCommand("trig")

    def wasTriggered(self):
        if self.connection_status:
            state = self._SendCommand("get c%d.state" % self.cine)
            ready_flag = "TRG"  # "TRiGgered"
            if (ready_flag in state) and not ("WTR" in state):
                return True
            else:
                return False
        else:
            return False

    def requestImages(self, start_frame=0, num_frames=None):
        """Request images from camera.

        Returns an ImageRequest instance that can be used to receive the
        images of this request.
        """
        # Send the request to the camera for the frame in question
        num_frames = num_frames or self.getNFramesAvailable()
        # Request 16 bits images from <num_frames> frames starting from frame <start_frame>
        cmd = "img {cine:%d, start:%d, cnt:%d, fmt:16}" % (self.cine, start_frame, num_frames)
        self._SendCommandAsync(cmd)
        return _ImageRequest(self, start_frame, num_frames)

    def _ReceiveImages(self, shape, num_frames):
        """Receive previously requested images."""
        bytesperpixel = 2
        frame_size = shape[0] * shape[1]
        total_size = (frame_size * num_frames) * bytesperpixel

        # Wait for image data to come in
        img_data = b""
        while (len(img_data) < total_size):
            remaining_data = total_size - len(img_data)
            ready = select.select([self._data_sock], [], [], 5)
            if ready[0]:
                request_size = min([remaining_data, self.MAX_MESSAGE_SIZE])
                img_data += self._data_sock.recv(request_size)
            else:
                raise Exception("No data received")
        _log.debug("RECV_IMG(%d)", len(img_data))
        # print("camera (image length): <<%s" % len(img_data))
        # images = np.frombuffer(img_data, dtype=np.uint16).reshape((num_frames, shape[0], shape[1]))
        # return images
        images = np.zeros((num_frames, shape[0], shape[1]))
        for i in range(num_frames):
            img_start = i * frame_size * bytesperpixel
            img_end = (i + 1) * frame_size * bytesperpixel
            img_string = img_data[img_start:img_end]
            images[i, :, :] = np.fromstring(img_string, dtype=np.uint16).reshape(shape)
        return images

    def _SetProperty(self, name, value):
        cmd = "set %s %s" % (name, value)
        res = self._SendCommand(cmd)
        if "Ok" not in res:
            raise Exception("Cannot set %s to %s: %s" % (name, value, res))

    def _GetProperty(self, name):
        cmd = "get %s" % name
        res = self._SendCommand(cmd)
        regex = re.compile("\S+ : (\S+)")
        match = regex.search(res)
        if not match:
            raise Exception("Invalid response: %s", res)
        return match.group(1)

    def setFrameSync(self, trigger):
        self._SetProperty("cam.syncimg", trigger)

    def getFrameSync(self):
        """Return 'i' when camera in Internal Sync mode
        return 'e' when camera in External Sync mode
        return 'g' when camera in irig timecode mode"""
        mode = self._GetProperty("cam.syncimg")
        if mode == "0":
            return "i"
        elif mode == "e":
            return "e"
        elif mode == "2":
            return "g"
        return "n"

    def setImageFormat(self, fmt):
        self._SetProperty("defc.res", fmt)

    def getImageFormat(self):
        return self._GetProperty("cam.syncimg")

    def setFrameRate(self, value):
        self.fps = value
        self._SetProperty("defc.rate", self.fps)

    def getFrameRate(self):
        return self._GetProperty("defc.rate")

    def setExposureTime(self, exposure):
        """Set exposure time in microsseconds"""
        self.exposure = int(exposure * 1000)
        self._SetProperty("defc.exp", int(self.exposure))

    def setNImages(self, frames):
        self.num_frames = frames

    def getName(self):
        name = self._GetProperty("info.name")
        if len(name) > 2:
            return name.strip('"')
        else:
            return ""

    def getNFramesAvailable(self):
        frames = self._GetProperty("c%d.frcount" % self.cine)
        if len(frames) > 0:
            return int(frames)
        else:
            return ""

    def getSerialNumber(self):
        return self._GetProperty("info.serial")

    def Discover(self):
        """Find the camera on the network, and note its contact information.
        Phantom cameras are equipped with a discovery protocol.  To find them,
        you need to send a broadcast UDP packet with the data 'phantom?' and
        wait for their response.  The camera will inform you which model camera
        it is as well as its ip address and communication port number.
        """
        BROADCAST_IP = '<broadcast>'
        DISCOVERY_PORT = 7380
        DISCOVERY_MESSAGE = b'phantom?'
        RECV_BUFFER_SIZE = 64
        ans = ""
        # Set up a socket on the discovery protocol port
        for host_ip in get_ip_addresses(socket.AF_INET):
            discovery_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            discovery_sock.settimeout(0.5)
            discovery_sock.bind((host_ip, DISCOVERY_PORT))
            discovery_sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            # Send out the discovery message as a UDP broadcast message
            discovery_sock.sendto(DISCOVERY_MESSAGE, (BROADCAST_IP, DISCOVERY_PORT))
            data, addr = discovery_sock.recvfrom(RECV_BUFFER_SIZE)
            # Wait for a response from the camera and parse the information
            try:
                data, addr = discovery_sock.recvfrom(RECV_BUFFER_SIZE)
                print(data, addr)
                ans += data.decode("ascii") + " " + addr[0] + "\n"
                print(ans)
            except:
                pass
            discovery_sock.close()
        return ans


def get_ip_addresses(family):
    """Get all local IPs for each network adapter"""
    for interface, snics in psutil.net_if_addrs().items():
        for snic in snics:
            if snic.family == family:
                yield snic.address
