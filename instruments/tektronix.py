import sys
import serial
import time
import numpy as np
import copy


try:
    from urllib.parse import quote
    from urllib.request import urlopen
except ImportError:
#    from urlparse import quote
    from urllib import quote
    from urllib2 import urlopen


# https://github.com/markjones112358/pyInstruments

class eScope:
    """ The base class for a eScope instruments."""

    def __init__(self, ip=None, debug=False):
        self.id = None
        self.debug = debug
        try:
            error = self.openConnection(ip)
            if error:
                return None
        except:
            return None

    def openConnection(self, ip=None):
        self.ip = ip or self.ip
        if not self.ip:
            print("Error trying to connect to Tektronix eScope (no IP provide).")
            return True
        try:
            idn = urlopen("http://%s/Comm.html?COMMAND=%s" % (self.ip, quote("*IDN?")), timeout=0.5).readline().decode("ascii")
            if idn:
                self.id = idn.split(",")[1]
                return False
            else:
                return True
        except:
            print("Error trying to connect to Tektronix eScope.")
            return True

    def isConnected(self):
        try:
            state = urlopen("http://%s/Comm.html?COMMAND=ACQ:STATE?" % self.ip, timeout=0.5).readline().decode("ascii")
            if int(state) + 1:
                return True
            else:
                return False
        except:
            return False

    def write(self, command):
        """ Writes a command to the instrument."""
        self.request = urlopen("http://%s/Comm.html?COMMAND=%s" % (self.ip, quote(command)), timeout=2)
        if self.debug:
            print("scope: >> %s" % command)

    def read(self, raw=False):
        """ Reads a response from the instrument.
        This function will block until the instrument responds."""
        ans = self.request.readline()
        if self.debug:
            print("scope: <<%s" % ans)
        if not raw:
            return ans.decode("ascii")
        else:
            return ans

    def query(self, command):
        """ Writes a command to the instrument and reads the response.
        """
        self.write(command)
        return self.read()

    def getName(self):
        """ Returns the instruments identifier string.
        This is a fairly universal command so should work on most devices.
        """
        ans = self.query("*IDN?").split(",")
        return "%s %s" % (ans[0], ans[1])

    def sendReset(self):
        """ Resets the instrument.
        This is a fairly universal command so should work on most devices.
        """
        self.write("*RST")


class serialInstrument:
    """ The base class for a serial instrument.
    Extend this class to implement other instruments with a serial interface.
    """

    def __init__(self, port=None, debug=False):
        self.debug = debug
        self.inst = serial.Serial()
        self.inst.port = port

    def openConnection(self, port=None, baudrate=19200, timeout=0.01):
        self.inst.port = port
        self.inst.baudrate = baudrate
        self.inst.timeout = timeout
        self.inst.write_timeout = 1
        try:
            self.inst.open()
            self.inst.reset_input_buffer()
            self.inst.reset_output_buffer()
            self.id = self.inst.getName()
            print("Connected to connect to Tektronix Scope (Serial port %s, baudrate %s)." % (self.inst.port, self.inst.baudrate))
            return 0
        except:
            print("Error trying to connect to Tektronix Scope (Serial port %s, baudrate %s)." % (self.inst.port, self.inst.baudrate))
            return 1

    def write(self, command):
        """ Writes a command to the instrument."""
        self.inst.write(bytearray(command + "\n", "ascii"))
        if self.debug:
            print(command)

    def read(self, raw=False):
        """ Reads a response from the instrument.
        This function will block until the instrument responds."""
        out = ""
        tmp = self.inst.read(raw=raw)
        return tmp

    def query(self, command):
        """ Writes a command to the instrument and reads the response.
        """
        self.write(command + "\n")
        tmp = self.read()
        while tmp is False:
            tmp = self.read()
        return tmp

    def getName(self):
        """ Returns the instruments identifier string.
        This is a fairly universal command so should work on most devices.
        """
        return self.query("*IDN?")

    def sendReset(self):
        """ Resets the instrument.
        This is a fairly universal command so should work on most devices.
        """
        self.inst.write("*RST")


class Scope:
    """ The class for the Tektronix TPS2024 oscilloscope
    This class is responsible for any functionality not specific to a
    particular channel, e.g. horizontal scale adjustment.
    """

    x_incr = False
    x_num = False
    numAvg = 0
    selectedChannel = 1
    debug = False

    available_tdivs = [50,
                       25,
                       10,
                       5,
                       2.5,
                       1,
                       0.5,
                       0.25,
                       0.1,
                       0.05,
                       0.025,
                       0.01,
                       0.005,
                       0.0025,
                       0.001,
                       0.0005,
                       0.00025,
                       0.0001,
                       0.00005,
                       0.000025,
                       0.00001,
                       0.000005,
                       0.0000025,
                       0.000001,
                       0.0000005,
                       0.00000025,
                       0.0000001,
                       0.00000005,
                       0.000000025,
                       0.00000001,
                       0.000000005,
                       0.0000000025]

    available_averageSettings = [128, 64, 16, 4]

    def __init__(self, inst=None, debug=False):
        self.connection_status = False
        self.inst = inst
        self.name = ""

    def openConnection(self, port=None, ip=None):
        if ip:
            self.inst = eScope(ip=ip)
        elif port:
            self.inst = serialInstrument(port=port)
        self.connection_status = self.isConnected()
        return not self.connection_status

    def isConnected(self):
        if not self.inst:
            return False
        return self.inst.isConnected()

    def status(self):
        return self.inst.query("STB?")

    def wasTriggered(self):
        if self.connection_status:
            return "1" not in self.inst.query("ACQ:STATE?")
        else:
            return False

    def checkComplete(self):
        tmp = self.inst.query("*OPC?")
        if "1" in tmp:
            return True
        else:
            return False

    def write(self, command):
        # Send an arbitrary command directly to the scope
        self.inst.write(command)

    def read(self, raw=False):
        # Send an arbitrary command directly to the scope
        return self.inst.read(raw=raw)

    def query(self, command):
        return self.inst.query(command)

    def getName(self):
        """ Returns the instruments identifier string.
        This is a fairly universal command so should work on most devices.
        """
        return self.inst.getName()

    def reset(self):
        # Reset the instrument
        self.inst.sendReset()

    def issueCommand(self, command, feedback=""):
        self.inst.write(command)

    def set_tScale(self, s):
        self.issueCommand("HORIZONTAL:DELAY:SCALE " + str(s), "Setting timebase to " + str(s) + " s/div")

    def set_averaging(self, averages):
        """ Sets or disables averaging (applies to all channels).
        Valid number of averages are either 4,16,64 or 128.
        A value of 0 or False disables averaging
        """
        if averages in self.available_averageSettings:
            self.write("ACQuire:MODe AVERage")
            self.write("ACQuire:NUMAVg " + str(averages))
            self.numAvg = averages
        elif averages == 0 or averages is False:
            self.write("ACQuire:MODe SAMPLE")
            self.write("ACQuire:NUMAVg " + str(0))
            self.numAvg = 0
        else:
            sys.exit()

    def set_autoRange(self, mode):
        """ Enables or disables autoranging for the device

        Arguments:
        mode = False | 'vertical' | 'horizontal' | 'both'
        the autoRanging mode with False being Disabled
        """

        if mode is False:
            self.issueCommand("AUTORange:STATE OFF", "Disabling auto ranging")
        elif mode.find("or") != -1:
            self.issueCommand("AUTORANGE:SETTINGS HORizontal",
                              "Setting auto range mode to horizontal")
            self.issueCommand("AUTORange:STATE ON", "Enabling auto ranging")
        elif mode.find("er") != -1:
            self.issueCommand("AUTORANGE:SETTINGS VERTICAL",
                              "Setting auto range mode to vertical")
            self.issueCommand("AUTORange:STATE ON", "Enabling auto ranging")
        elif mode.find("th") != -1:
            self.issueCommand("AUTORANGE:SETTINGS BOTH",
                              "Setting auto range mode to both")
            self.issueCommand("AUTORange:STATE ON", "Enabling auto ranging")
        self.wait()

    def set_single_acquisition(self):
        """Start single aquisition."""
        self.issueCommand("ACQuire:STOPAfter SEQuence", "Starting waveform acquisition")

    def is_running(self):
        """Check if acquisition is running."""
        if int(self.query("ACQuire:STATE?")):
            return True
        else:
            return False

    def acquisition(self, enable):
        """ Sets acquisition parameter.
        Toggling this controls whether the scope acquires a waveform

        Arguments:
        enable [bool] Toggles waveform acquisition
        """
        if enable:
            self.issueCommand("ACQuire:STATE ON", "Starting waveform acquisition")
        else:
            self.issueCommand("ACQuire:STATE OFF", "Stopping waveform acquisition")

    def get_numAcquisitions(self):
        """ Indicates the number of acquisitions that have taken place since
        starting oscilloscope acquisition. The maximum number of acquisitions
        that can be counted is 231-1. This value is reset to zero when you
        change most Acquisition, Horizontal, Vertical, or Trigger arguments
        that affect the waveform
        """
        num = self.query("ACQuire:NUMACq?")
        while num is False:
            num = self.read()
        return int(num)

    def waitForAcquisitions(self, num=False):
        """ Waits in a loop until the scope has captured the required number of
        acquisitions
        """
        until = 0
        if num is False and self.numAvg is False:
            # "Waiting for a single acquisition to finish"
            until = 1
        elif num is False:
            until = num
            # "Waiting until " + str(until) + " acquisitions have been made"
        else:
            until = self.numAvg
            # "Waiting until " + str(until) + " acquisitions have been made"
        last = 0
        done = self.get_numAcquisitions()
        while done < until:
            if done != last:
                # "Waiting for " + str(until - done) + " acquisitions"
                last = done
            done = self.get_numAcquisitions()
            time.sleep(0.1)

    def set_hScale(self,
                   tdiv=False,
                   frequency=False,
                   cycles=False):
        """ Set the horizontal scale according to the given parameters.
        Parameters:
           tdiv [float] A time division in seconds (1/10 of the width of the display)
           frequency [float] Select a timebase that will capture '# cycles' of this
                             frequency
           cycles [float] Minimum number of frequency cycles to set timebase for
           used in conjunction with 'frequency' parameter
        """
        if tdiv is False:
            set_div = False
            for a_tdiv in self.available_tdivs:
                if set_div is False and float(tdiv) <= a_tdiv:
                    set_div = a_tdiv
        elif frequency is False:

            if cycles is False:
                set_div = self.find_minTdiv(frequency, cycles)
            else:
                set_div = self.find_minTdiv(frequency)

        if set_div is False:
            self.issueCommand("HORizontal:SCAle " + str(set_div),
                              "Setting horizontal scale to "
                              + str(set_div) + " s/div")
        return set_div * 10.0

    def get_timeToCapture(self, frequency, cycles, averaging=1):
        """ Calculates and returns the time (in seconds) for a capture
        to complete based on the given frequency, cycles, and number
        of averages.
        """
        if averaging == 0:
            averaging = 1

        tdiv = self.find_minTdiv(frequency, cycles)
        windowlength = float(tdiv) * 10.0
        wavelength = 1.0 / frequency

        # time if the first cycle triggers instantly and for every average
        time_min = windowlength * averaging

        # time when triggering is delayed by a full wavelength and at each
        # acquire for an average

        time_max = (windowlength * averaging) + (wavelength * averaging)
        return (time_min, time_max)

    def get_transferTime(self, mode):
        if mode == 'ASCII':
            return 8.43393707275
        elif mode == 'RPBinary':
            return 4.0

    def find_minTdiv(self, frequency, min_cycles=2):
        """ Finds the minimum s/div that will allow a given number of
        cycles at a particular frequency to fit in a capture
        """
        tmp = copy.copy(self.available_tdivs)
        tmp.reverse()
        wavelength = 1.0 / float(frequency)
        min_div = (wavelength * min_cycles) / 10.0
        for tdiv in tmp:
            if min_div <= tdiv:
                return tdiv
        return tmp[len(tmp) - 1]

    def set_trigger_position(self, position):
        """Set pretrigger amout to position (%) of the record length"""
        if position >= 0 and position <= 100:
            self.issueCommand("HORizontal:TRIGger:POSition %d" % position, "Setting trigger position")

    def get_trigger_position(self, position):
        return self.query("HORizontal:TRIGger:POSition?")

    def get_record_length(self):
        if self.connection_status:
            return int(self.query("HORizontal:RECORDLength?"))
        else:
            return 0

    def get_record_sample_rate(self):
        if self.connection_status:
            return 1. / float(self.query("WFMP:XIN?"))
        else:
            return 0

    def get_channel_waveform(self, ch=1):
        Channel = channel(self, ch)
        [x, y] = Channel.get_waveform()
        return Channel


def get_channels_autoRange(channels, wait=True, averages=False, max_adjustments=5):
    """ Helper function to control the adjustment of multiple channels between
    captures.
    This reduces the amount of time spend adjusting the V/div when multiple
    channels are used as only one re-acquisition is required between adjustments.
    """
    channels_data = [False for x in range(len(channels))]
    channels_rescale = [False for x in range(len(channels))]
    reset = False
    to_wait = wait
    for channel_number, channel in enumerate(channels):
        xs, ys = channel.get_waveform(False, wait=to_wait)
        to_wait = False
        if channel.did_clip():
            # Increase V/div until no clipped data
            set_vdiv = channel.get_yScale()

            if channel.available_vdivs.index(set_vdiv) > 0:
                temp_index = channel.available_vdivs.index(set_vdiv) - 1
                temp1 = channel.available_vdivs[temp_index]
                temp2 = 'Decreasing channel ' + str(channel_number) + ' to '
                temp2 += str(temp1)
                temp2 += ' V/div'
                print(temp2)
                channels_rescale[channel_number] = temp1
                reset = True
            else:
                print()
                print('===================================================')
                print('WARN: Scope Y-scale maxed out! THIS IS BAD!!!!!!!!!')
                print('===================================================')
                print('Aborting!')
                sys.exit()
        else:
            tmp_max = 0
            tmp_min = 0
            for y in ys:
                if y > tmp_max:
                    tmp_max = y
                elif y < tmp_min:
                    tmp_min = y
            datarange = tmp_max - tmp_min

            set_range = channel.get_yScale()
            set_window = set_range * 8.0

            # find the best (minimum no-clip) range
            best_window = 0
            tmp_range = copy.copy(channel.available_vdivs)
            available_windows = map(lambda x: x * 8.0, tmp_range)

            for available_window in available_windows:
                if datarange <= (available_window * 0.95):
                    best_window = available_window

            # if it's not the range were already using, set it
            if best_window < set_window:
                temp = 'Increasing channel ' + str(channel_number)
                temp += ' to ' + str(best_window / 8.0) + ' V/div'
                print(temp)
                channels_rescale[channel_number] = best_window / 8.0
                reset = True

        channels_data[channel_number] = (xs, ys)

    if max_adjustments > 0 and reset:
        max_adjustments -= 1
        temp = 'A channels range has been altered, data will need to be'
        temp += ' re-acquired'
        print(temp)
        temp = 'The maximum remaining adjustments to the channels is '
        temp += str(max_adjustments)
        print(temp)
        enumerated_data = enumerate(zip(channels_rescale, channels))
        for channel_number, (channel_scale, channel) in enumerated_data:
            if channel_scale is False:
                temp = 'Adjusting channel ' + str(channel_number) + ' to '
                temp += str(channel_scale) + ' V/div'
                print(temp)
                channel.set_vScale(channel_scale)
        channels[0].set_averaging(False)
        time.sleep(1)
        channels[0].set_averaging(averages)
        return get_channels_autoRange(channels,
                                      wait,
                                      averages,
                                      max_adjustments=max_adjustments)
    else:
        return channels_data


class channel(Scope):
    """ Channel class that implements the functionality related to one of
    the oscilloscope's physical channels.
    """
    channel = False  # Channel num

    available_vdivs = [50.0,
                       20.0,
                       10.0,
                       5.0,
                       2.0,
                       1.0,
                       0.5,
                       0.2,
                       0.1,
                       0.05,
                       0.02]

    def __init__(self, inst, channel=1):
        self.inst = inst
        self.channel = channel

    def set_vScale(self, s, debug=False):
        """ Sets the V/div setting (vertical scale) for this channel
        """
        tmp = copy.copy(self.available_vdivs)
        setVdiv = False
        for vdiv in tmp:
            if s <= vdiv:
                setVdiv = vdiv
        if setVdiv is False:
            print()
            print('===================================================')
            print('WARN: ' + str(s) + ' V/div is outside of scope range ')
            print('Will use ' + str(tmp[len(tmp) - 1]) + ' V/div instead,')
            print('===================================================')
            print()

        self.issueCommand("CH" + str(self.channel) + ":SCAle " + str(setVdiv),
                          "Setting channel " + str(self.channel) +
                          " scale to " + str(setVdiv) + " V/div")
        self.y_mult = setVdiv

    def did_clip(self, debug=False):
        """ Checks to see if the last acquisition contained clipped data points.
        This would indicate that the V/div is set too high.
        """
        count = 0
        for point in self.signal_raw:
            if point > 250 or point < 5:
                count += 1
            else:
                count = 0

            if count > 1:
                return True
        return False

    def get_yScale(self):
        """ query the instrument for this channels V/div setting.
        """
        tmp = self.inst.query('CH' + str(self.channel) + ':SCAle?')
        return float(tmp)

    def get_waveform_autoRange(self, debug=False, wait=True, averages=False):
        """ Download a waveform, checking to see whether the V/div for this
        channel has been set too high or too low.
        This function will automatically adjust the V/div for this channel and
        keep re-requesting captures until the data fits correctly
        """
        xs, ys = self.get_waveform(False, wait=wait)
        # Check if this waveform contained clipped data
        if self.did_clip():
            clipped = True
            while clipped:
                # Increase V/div until no clipped data
                set_vdiv = self.get_yScale()
                if self.available_vdivs.index(set_vdiv) > 0:
                    best_div = self.available_vdivs[self.available_vdivs.index(set_vdiv) - 1]
                    if debug:
                        temp = 'Setting Y-scale on channel '
                        temp += str(self.channel) + ' to '
                        temp += str(best_div)
                        temp += ' V/div'

                    self.set_vScale(best_div)
                    self.waitForAcquisitions(self.numAvg)
                    xs, ys = self.get_waveform(debug=False)
                    clipped = self.did_clip()
                else:
                    print()
                    print('===================================================')
                    print('WARN: Scope Y-scale maxed out! THIS IS BAD!!!!!!!!!')
                    print('===================================================')
                    print()
                    clipped = False
        else:
            # Detect if decreasing V/div it will cause clipping
            tmp_max = 0
            tmp_min = 0
            for y in ys:
                if y > tmp_max:
                    tmp_max = y
                elif y < tmp_min:
                    tmp_min = y
            datarange = tmp_max - tmp_min

            set_range = self.get_yScale()
            set_window = set_range * 8.0

            # find the best (minimum no-clip) range
            best_window = 0
            tmp_range = copy.copy(self.available_vdivs)
            available_windows = map(lambda x: x * 8.0, tmp_range)

            for available_window in available_windows:
                if datarange <= (available_window * 0.90):
                    best_window = available_window

            # if it's not the range were already using, set it
            if best_window != set_window:
                self.set_vScale(best_window / 8.0)
                print('Disabling averaging')
                self.set_averaging(False)
                time.sleep(1)
                print('Enabling averaging, setting to ' + str(averages))
                self.set_averaging(averages)
                time.sleep(1)
                return self.get_waveform_autoRange(averages=averages)
        return [xs, ys]

    def set_measurementChannel(self):
        temp = "Setting immediate measurement source channel to CH" + str(self.channel)
        self.issueCommand("MEASUrement:IMMed:SOUrce " + str(self.channel),
                          temp)

    def get_measurement(self):
        self.inst.write("MEASUrement:IMMed:VALue")
        self.inst.read()

    def set_waveformParams(self, encoding='RPBinary', start=0, stop=2500, width=1):
        """ Sets waveform parameters for the waveform specified by the channel
        parameter.

        Arguments:
           channel [int - 1-4] - specifies which channel to configure
           encoding (optional: 'ASCII') [str - {'ASCII' , 'Binary'}] - how the
           waveform is to be transferred (ascii is easiest but slowest)
           start (optional: 0) [int - 0-2499] - data point to begin transfer from
           stop (optional: 2500) [int - 1-2500] - data point to stop transferring at
           width (optional: 2) [int] - how many bytes per data point to transfer.
        """
        self.issueCommand("DATA:SOUrce CH" + str(self.channel),
                          "Setting data source to channel " + str(self.channel),
                          False)
        if encoding == 'ASCII':
            self.issueCommand("DATA:ENCdg ASCIi", "Setting data encoding to ASCII", False)
            self.encoding = 'ASCII'
        else:
            self.issueCommand("DATA:ENCdg RPBinary", "Setting data encoding to RPBinary", False)
            self.encoding = 'RPBinary'
        self.issueCommand("DATA:STARt " + str(start), "Setting start data point to " + str(start), False)
        self.issueCommand("DATA:STOP " + str(stop), "Setting stop data point to " + str(stop), False)
        self.issueCommand("DATA:WIDTH " + str(width), "Setting of bytes to transfer per waveform point to " + str(width), False)
        self.checkComplete()

    def get_transferTime(self):
        return self.inst.get_transferTime(self.encoding)

    def get_waveform(self):
        """ Downloads this channels waveform data.
        This function will not make any adjustments to the V/div settings.
        """
        self.issueCommand("DAT:ENC RPB")
        self.issueCommand("DATA:SOUrce CH" + str(self.channel), "Setting data source to channel " + str(self.channel))
        self.input_range = self.get_yScale()

        # self.write("WFMPre?")

        encoding = self.inst.query("WFMPre:ENCdg?")
        self.y_offset = float(self.inst.query("WFMP:YOF?"))
        self.y_mult = float(self.inst.query("WFMP:YMU?"))
        self.y_zero = float(self.inst.query("WFMP:YZE?"))
        self.x_zero = float(self.inst.query("WFMPre:XZE?")) or 0
        self.x_incr = float(self.inst.query("WFMP:XIN?"))

        self.inst.write("CURVE?")
        ans = self.inst.read(raw=True)[: -1]  # remove "\n" at the line end
        # if "#" not in ans[0].decode("ascii"):
        #     print("scope: <<%s" % ans[0].decode("ascii"))
        #     raise "Error reading waveform"

        num_bytes = int(ans[1])
        self.x_num = 10000  # int(ans[2: 2 + num_bytes])
        tmp = ans[7:]  # Signal
        # 510000

        if encoding == 'ascii':
            out = tmp.split(":CURVE ")[1]
            data = out.split(',')
        else:
            data = np.frombuffer(tmp, dtype=np.uint8)

        self.signal_raw = data
        data_y = ((data - self.y_offset) * self.y_mult) + self.y_zero
        data_x = self.x_zero + np.arange(data.size) * self.x_incr

        if self.x_num != data.size:
            print("======================================================")
            print("WARNING: Data payload was stated as " + str(self.x_num) + " points")
            print("but " + str(data.size) + " points were returned for CH" + str(self.channel))
            print("======================================================")

        # if self.did_clip() is True:
        #    print("=======================================================")
        #    print("WARNING: Data payload possibly contained clipped points")
        #    print("=======================================================")

        return [data_x, data_y]
