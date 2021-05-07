import ctypes
from ctypes import c_int, c_uint8, c_uint16, c_uint32, c_int32, c_float, c_char_p, c_void_p, c_long, windll, CDLL, POINTER
import os
import numpy as np
import time
import logging

# add logger, to allow logging to Labber's instrument log
log = logging.getLogger('AlazarTech')

# define constants
ADMA_NPT = 0x200
ADMA_EXTERNAL_STARTCAPTURE = 0x1

sample_rate_id = {
    '1 kS/s': 0x01,
    '10 kS/s': 0x08,
    '20 kS/s': 0x0A,
    '50 kS/s': 0x0C,
    '100 kS/s': 0x0E,
    '200 kS/s': 0x10,
    '500 kS/s': 0x12,
    '1 MS/s': 0x14,
    '2 MS/s': 0x18,
    '5 MS/s': 0x1A,
    '10 MS/s': 0x1C,
    '20 MS/s': 0x1E,
    '50 MS/s': 0x22,
    '100 MS/s': 0x24,
    '125 MS/s': 0x25,
}

try:
    # For Python 3
    sample_rate = {v: int(float(k.replace(" kS/s", "E3").replace(" MS/s", "E6"))) for k, v in sample_rate_id.items()}
except:
    # For Python 2
    sample_rate = dict((v, int(float(k.replace(" kS/s", "E3").replace(" MS/s", "E6")))) for k, v in sample_rate_id.iteritems())


input_range = {
    '20 mV': 1,
    '40 mV': 2,
    '50 mV': 3,
    '80 mV': 4,
    '100 mV': 5,
    '200 mV': 6,
    '400 mV': 7,
    '500 mV': 8,
    '800 mV': 9,
    '1 V': 10,
    '2 V': 11,
    '4 V': 12,
    '5 V': 13,
    '8 V': 14,
    '10 V': 15,
}


class DMABuffer:
    """"Buffer for DMA"""

    def __init__(self, c_sample_type, size_bytes):
        self.size_bytes = size_bytes

        npSampleType = {
            c_uint8: np.uint8,
            c_uint16: np.uint16,
            c_uint32: np.uint32,
            c_int32: np.int32,
            c_float: np.float32
        }.get(c_sample_type, 0)

        bytes_per_sample = {
            c_uint8: 1,
            c_uint16: 2,
            c_uint32: 4,
            c_int32: 4,
            c_float: 4
        }.get(c_sample_type, 0)

        self.addr = None
        if os.name == 'nt':
            MEM_COMMIT = 0x1000
            PAGE_READWRITE = 0x4
            windll.kernel32.VirtualAlloc.argtypes = [c_void_p, c_long, c_long, c_long]
            windll.kernel32.VirtualAlloc.restype = c_void_p
            self.addr = windll.kernel32.VirtualAlloc(
                0, c_long(size_bytes), MEM_COMMIT, PAGE_READWRITE)
        elif os.name == 'posix':
            libc = CDLL("libc.so.6")
            libc.valloc.argtypes = [c_long]
            libc.valloc.restype = c_void_p
            self.addr = libc.valloc(size_bytes)
        else:
            raise Exception("Unsupported OS")

        ctypes_array = (c_sample_type * (size_bytes // bytes_per_sample)).from_address(self.addr)
        self.buffer = np.frombuffer(ctypes_array, dtype=npSampleType)
        self.ctypes_buffer = ctypes_array
        pointer, read_only_flag = self.buffer.__array_interface__['data']

    def __exit__(self):
        if os.name == 'nt':
            MEM_RELEASE = 0x8000
            windll.kernel32.VirtualFree.argtypes = [c_void_p, c_long, c_long]
            windll.kernel32.VirtualFree.restype = c_int
            windll.kernel32.VirtualFree(c_void_p(self.addr), 0, MEM_RELEASE)
        elif os.name == 'posix':
            libc = CDLL("libc.so.6")
            libc.free(self.addr)
        else:
            raise Exception("Unsupported OS")


# error type returned by this class
class Error(Exception):
    pass


class TimeoutError(Error):
    pass


class Digitizer():
    """Represent the Alazartech digitizer, redefines the dll functions in python"""

    _success = 512

    _error_codes = {
        513: 'ApiFailed',
        514: 'ApiAccessDenied',
        515: 'ApiDmaChannelUnavailable',
        516: 'ApiDmaChannelInvalid',
        517: 'ApiDmaChannelTypeError',
        518: 'ApiDmaInProgress',
        519: 'ApiDmaDone',
        520: 'ApiDmaPaused',
        521: 'ApiDmaNotPaused',
        522: 'ApiDmaCommandInvalid',
        523: 'ApiDmaManReady',
        524: 'ApiDmaManNotReady',
        525: 'ApiDmaInvalidChannelPriority',
        526: 'ApiDmaManCorrupted',
        527: 'ApiDmaInvalidElementIndex',
        528: 'ApiDmaNoMoreElements',
        529: 'ApiDmaSglInvalid',
        530: 'ApiDmaSglQueueFull',
        531: 'ApiNullParam',
        532: 'ApiInvalidBusIndex',
        533: 'ApiUnsupportedFunction',
        534: 'ApiInvalidPciSpace',
        535: 'ApiInvalidIopSpace',
        536: 'ApiInvalidSize',
        537: 'ApiInvalidAddress',
        538: 'ApiInvalidAccessType',
        539: 'ApiInvalidIndex',
        540: 'ApiMuNotReady',
        541: 'ApiMuFifoEmpty',
        542: 'ApiMuFifoFull',
        543: 'ApiInvalidRegister',
        544: 'ApiDoorbellClearFailed',
        545: 'ApiInvalidUserPin',
        546: 'ApiInvalidUserState',
        547: 'ApiEepromNotPresent',
        548: 'ApiEepromTypeNotSupported',
        549: 'ApiEepromBlank',
        550: 'ApiConfigAccessFailed',
        551: 'ApiInvalidDeviceInfo',
        552: 'ApiNoActiveDriver',
        553: 'ApiInsufficientResources',
        554: 'ApiObjectAlreadyAllocated',
        555: 'ApiAlreadyInitialized',
        556: 'ApiNotInitialized',
        557: 'ApiBadConfigRegEndianMode',
        558: 'ApiInvalidPowerState',
        559: 'ApiPowerDown',
        560: 'ApiFlybyNotSupported',
        561: 'ApiNotSupportThisChannel',
        562: 'ApiNoAction',
        563: 'ApiHSNotSupported',
        564: 'ApiVPDNotSupported',
        565: 'ApiVpdNotEnabled',
        566: 'ApiNoMoreCap',
        567: 'ApiInvalidOffset',
        568: 'ApiBadPinDirection',
        569: 'ApiPciTimeout',
        570: 'ApiDmaChannelClosed',
        571: 'ApiDmaChannelError',
        572: 'ApiInvalidHandle',
        573: 'ApiBufferNotReady',
        574: 'ApiInvalidData',
        575: 'ApiDoNothing',
        576: 'ApiDmaSglBuildFailed',
        577: 'ApiPMNotSupported',
        578: 'ApiInvalidDriverVersion',
        579: ('ApiWaitTimeout: operation did not finish during '
              'timeout interval. Check your trigger.'),
        580: 'ApiWaitCanceled',
        581: 'ApiBufferTooSmall',
        582: ('ApiBufferOverflow:rate of acquiring data > rate of '
              'transferring data to local memory. Try reducing sample rate, '
              'reducing number of enabled channels, increasing size of each '
              'DMA buffer or increase number of DMA buffers.'),
        583: 'ApiInvalidBuffer',
        584: 'ApiInvalidRecordsPerBuffer',
        585: ('ApiDmaPending:Async I/O operation was successfully started, '
              'it will be completed when sufficient trigger events are '
              'supplied to fill the buffer.'),
        586: ('ApiLockAndProbePagesFailed:Driver or operating system was '
              'unable to prepare the specified buffer for DMA transfer. '
              'Try reducing buffer size or total number of buffers.'),
        587: 'ApiWaitAbandoned',
        588: 'ApiWaitFailed',
        589: ('ApiTransferComplete:This buffer is last in the current '
              'acquisition.'),
        590: 'ApiPllNotLocked:hardware error, contact AlazarTech',
        591: ('ApiNotSupportedInDualChannelMode:Requested number of samples '
              'per channel is too large to fit in on-board memory. Try '
              'reducing number of samples per channel, or switch to '
              'single channel mode.')
    }

    _board_names = {
        1: 'ATS850',
        2: 'ATS310',
        3: 'ATS330',
        4: 'ATS855',
        5: 'ATS315',
        6: 'ATS335',
        7: 'ATS460',
        8: 'ATS860',
        9: 'ATS660',
        10: 'ATS665',
        11: 'ATS9462',
        12: 'ATS9434',
        13: 'ATS9870',
        14: 'ATS9350',
        15: 'ATS9325',
        16: 'ATS9440',
        17: 'ATS9410',
        18: 'ATS9351',
        19: 'ATS9310',
        20: 'ATS9461',
        21: 'ATS9850',
        22: 'ATS9625',
        23: 'ATG6500',
        24: 'ATS9626',
        25: 'ATS9360',
        26: 'AXI9870',
        27: 'ATS9370',
        28: 'ATU7825',
        29: 'ATS9373',
        30: 'ATS9416'
    }

    def __init__(self, systemId=1, boardId=1, timeout=10.0):
        """The init case defines a session ID, used to identify the instrument"""
        # range settings; default value of 400mV for 9373;
        # will be overwritten if model is 9870 and AlazarInputControl called
        self.input_range = {1: 0.4, 2: 0.4}
        self.buffers = []
        self.timeout = timeout
        # create a session id

        try:
            self._ATS_dll = ctypes.cdll.LoadLibrary('ATSApi')
        except:
            # if failure, try to open in driver folder
            sPath = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'atsapi')
            self._ATS_dll = ctypes.CDLL(os.path.join(sPath, 'ATSApi'))

        self._handle = self._ATS_dll.AlazarGetBoardBySystemID(systemId, boardId)
        if not self._handle:
            raise Exception('AlazarTech_ATS not found at system {}, board {}'.format(systemId, boardId))

        # func = getattr(self._ATS_dll, 'AlazarNumOfSystems')
        # func.restype = c_uint32
        # func = getattr(self._ATS_dll, 'AlazarGetBoardBySystemID')
        # func.restype = c_void_p
        # handle = func(c_uint32(systemId), c_uint32(boardId))
        if self._handle is None:
            raise Error('Device with system ID=%d and board ID=%d could not be found.' % (systemId, boardId))

        # get mem and bitsize
        (self.memorySize_samples, self.bitsPerSample) = self.get_channel_info(self._handle)

    def find_boards(cls, dll_path=None):
        """
        Find Alazar boards connected

        Args:
            dll_path: (string) path of the Alazar driver dll

        Returns:
            list: list of board info for each connected board
        """

        system_count = cls._ATS_dll.AlazarNumOfSystems()
        boards = []
        for system_id in range(1, system_count + 1):
            board_count = cls._ATS_dll.AlazarBoardsInSystemBySystemID(system_id)
            for board_id in range(1, board_count + 1):
                boards.append(cls.get_board_info(cls._ATS_dll, system_id, board_id))
        return boards

    def get_board_info(self, system_id, board_id):
        """
        Get the information from a connected Alazar board
        Args:
            dll (string): path of the Alazar driver dll
            system_id: id of the Alazar system
            board_id: id of the board within the alazar system
        Return:
            Dictionary containing
                - system_id
                - board_id
                - board_kind (as string)
                - max_samples
                - bits_per_sample
        """
        # make a temporary instrument for this board, to make it easier
        # to get its info
        board_kind = self._board_names[self._ATS_dll.AlazarGetBoardKind(self._handle)]
        max_s, bps = self.get_channel_info(self._handle)
        return {
            'system_id': system_id,
            'board_id': board_id,
            'board_kind': board_kind,
            'max_samples': max_s,
            'bits_per_sample': bps
        }

    def get_channel_info(self, handle):
        memorySize = np.array([0], dtype=np.uint32)  # memorySize memory size in samples
        bitsPerSample = np.array([0], dtype=np.uint8)  # bitsPerSample bits per sample
        memorySize_ptr = memorySize.ctypes.data_as(POINTER(c_uint32))
        bitsPerSample_ptr = bitsPerSample.ctypes.data_as(POINTER(c_uint8))
        # self._ATS_dll.AlazarGetChannelInfo(handle, memorySize.ctypes.data, bitsPerSample.ctypes.data)
        self._ATS_dll.AlazarGetChannelInfo(handle, memorySize_ptr, bitsPerSample_ptr)
        return memorySize[0], bitsPerSample[0]

    def testLED(self):
        import time
        self._call_dll('AlazarSetLED', self._handle, c_uint32(1))
        time.sleep(0.1)
        self._call_dll('AlazarSetLED', self._handle, c_uint32(0))

    def _call_dll(self, func_name, *args):
        """General function caller with restype=status, also checks for errors"""
        # get function from DLL
        args_out = []
        for arg in args:
            args_out.append(arg)
        func = getattr(self._ATS_dll, func_name)
        return_code = func(*args_out)

        # check for errors
        if (return_code != self._success) and (return_code != 518):
            # TODO(damazter) (C) log error

            argrepr = repr(args_out)
            if len(argrepr) > 100:
                argrepr = argrepr[:96] + '...]'

            if return_code not in self._error_codes:
                raise RuntimeError(
                    'unknown error {} from function {} with args: {}'.format(
                        return_code, func_name, argrepr))
            raise RuntimeError(
                'error {}: {} from function {} with args: {}'.format(
                    return_code, self._error_codes[return_code], func_name, argrepr))

    def getError(self, status):
        """Convert the error in status to a string"""
        func = getattr(self._ATS_dll, 'AlazarErrorToText')
        func.restype = c_char_p
        # const char* AlazarErrorToText(RETURN_CODE retCode)
        errorText = func(c_int(status))
        return str(errorText)

    def AlazarGetChannelInfo(self):
        """Get the on-board memory in samples per channel and sample size in bits per sample"""
        memorySize_samples = c_uint32(0)
        bitsPerSample = c_uint8(0)
        self._call_dll('AlazarGetChannelInfo', self._handle)
        return (int(memorySize_samples.value), int(bitsPerSample.value))

    def AlazarSetCaptureClock(self, SourceId, SampleRateId, EdgeId=0, Decimation=0):
        # sample_rate: {0x01: 1e3, 0x08: 10e3, 0x0A: 20e3, 0x0C: 50e3, 0x0E: 100e3, 0x10: 200e3, 0x12: 500e3, 0x14: 1e6, 0x18: 2e6, 0x1A: 5e6, 0x1C: 10e6, 0x1E: 20e6, 0x22: 50e6, 0x24: 100e6, 0x25: 125e6}
        self.sample_rate = sample_rate[SampleRateId]
        self._call_dll('AlazarSetCaptureClock', self._handle, c_uint32(SourceId), c_uint32(SampleRateId), c_uint32(EdgeId), c_uint32(Decimation))

    def AlazarInputControl(self, Channel, Coupling, InputRange, Impedance):
        # keep track of input range
        dConv = {15: 10.0, 14: 8.0, 13: 5.0, 12: 4.0, 11: 2.0, 10: 1.0, 9: 0.8, 8: 0.5, 7: 0.4, 6: 0.2, 5: 0.1, 4: 0.08, 3: 0.05, 2: 0.04, 1: 0.02}
        self.input_range[Channel] = dConv[InputRange]
        self._call_dll('AlazarInputControl', self._handle, c_uint8(Channel), c_uint32(Coupling), c_uint32(InputRange), c_uint32(Impedance))

    def AlazarSetBWLimit(self, Channel, enable):
        self._call_dll('AlazarSetBWLimit', self._handle, c_uint32(Channel), c_uint32(enable))

    def AlazarSetParameter(self, Channel, parameter, value):
        self._call_dll('AlazarSetParameter', self._handle, c_uint8(Channel), c_uint32(parameter), c_long(value))

    def AlazarSetParameterUL(self, Channel, parameter, value):
        self._call_dll('AlazarSetParameter', self._handle, c_uint8(Channel), c_uint32(parameter), c_uint32(value))

    def AlazarGetParameter(self, Channel, parameter):
        value = c_long(0)
        self._call_dll('AlazarSetParameter', self._handle, c_uint8(Channel), c_uint32(parameter), c_uint32(value))
        return value.value

    def AlazarSetTriggerOperation(self, TriggerOperation=0,
                                  TriggerEngine1=0, Source1=0, Slope1=1, Level1=128,
                                  TriggerEngine2=1, Source2=3, Slope2=1, Level2=128):
        """Configure the trigger engines of a board to use an external trigger inputand, optionally, synchronize the start of an acquisition with the next external trigger event after AlazarStartCaptureis called
        Slope:
            1: Positive slope
            2: Nevative slope
        Level: Specify a trigger level code representing the trigger level in volts that an external trigger signal connected must pass through to generate a trigger event.
        """
        self._call_dll('AlazarSetTriggerOperation', self._handle, c_uint32(TriggerOperation),
                       c_uint32(TriggerEngine1), c_uint32(Source1), c_uint32(Slope1), c_uint32(Level1),
                       c_uint32(TriggerEngine2), c_uint32(Source2), c_uint32(Slope2), c_uint32(Level2))

    def AlazarSetExternalTrigger(self, Coupling, Range=0):
        self._call_dll('AlazarSetExternalTrigger', self._handle, c_uint32(Coupling), c_uint32(Range))

    def AlazarSetTriggerDelay(self, Delay=0):
        self._call_dll('AlazarSetTriggerDelay', self._handle, c_uint32(Delay))

    def AlazarSetTriggerTimeOut(self, time=0.0):
        tick = c_uint32(int(time * 1E5))
        self._call_dll('AlazarSetTriggerTimeOut', self._handle, tick)

    def AlazarSetRecordSize(self, PreSize, PostSize):
        self.nPreSize = int(PreSize)
        self.nPostSize = int(PostSize)
        self._call_dll('AlazarSetRecordSize', self._handle, c_uint32(PreSize), c_uint32(PostSize))

    def AlazarSetRecordCount(self, Count):
        self.nRecord = int(Count)
        self._call_dll('AlazarSetRecordCount', self._handle, c_uint32(Count))

    def AlazarStartCapture(self):
        self._call_dll('AlazarStartCapture', self._handle)

    def AlazarAbortCapture(self):
        self._call_dll('AlazarAbortCapture', self._handle)

    # c_uint32  AlazarBusy( HANDLE h);
    def AlazarBusy(self):
        # get function from DLL
        func = getattr(self._ATS_dll, 'AlazarBusy')
        func.restype = c_uint32
        # call function, return result
        return bool(func(self._handle))

    def AlazarRead(self, Channel, buffer, ElementSize, Record, TransferOffset, TransferLength):
        self._call_dll('AlazarRead', self._handle,
                       c_uint32(Channel), buffer, c_int(ElementSize),
                       c_long(Record), c_long(TransferOffset), c_uint32(TransferLength))

    def AlazarBeforeAsyncRead(self, channels, transferOffset, samplesPerRecord, recordsPerBuffer, recordsPerAcquisition, flags):
        """Prepares the board for an asynchronous acquisition."""
        self._call_dll('AlazarBeforeAsyncRead', self._handle, channels, transferOffset, samplesPerRecord, recordsPerBuffer, recordsPerAcquisition, flags)

    def AlazarAbortAsyncRead(self):
        """Cancels any asynchronous acquisition running on a board."""
        self._call_dll('AlazarAbortAsyncRead', self._handle)

    def AlazarPostAsyncBuffer(self, buffer, bufferLength):
        """Posts a DMA buffer to a board."""
        self._call_dll('AlazarPostAsyncBuffer', self._handle, buffer, bufferLength)

    def AlazarWaitAsyncBufferComplete(self, buffer, timeout_ms):
        """Blocks until the board confirms that buffer is filled with data."""
        self._call_dll('AlazarWaitAsyncBufferComplete', self._handle, buffer, timeout_ms)

    def readTracesDMA(self, bGetCh1, bGetCh2, nSamples, nRecord, nBuffer, nAverage=1,
                      bConfig=True, bArm=True, bMeasure=True,
                      funcStop=None, funcProgress=None, timeout=None, bufferSize=512,
                      firstTimeout=None, maxBuffers=1024):
        """read traces in NPT AutoDMA mode, convert to float, average to single trace"""
        t0 = time.clock()
        lT = []

        # use global timeout if not given
        timeout = self.timeout if timeout is None else timeout
        # first timeout can be different in case of slow initial arming
        firstTimeout = timeout if firstTimeout is None else firstTimeout

        # Select the number of pre-trigger samples...not supported in NPT, keeping for consistency
        preTriggerSamplesValue = 0
        # change alignment to be 128
        if preTriggerSamplesValue > 0:
            preTriggerSamples = int(np.ceil(preTriggerSamplesValue / 128.) * 128)
        else:
            preTriggerSamples = 0

        # Select the number of samples per record.
        postTriggerSamplesValue = nSamples
        # change alignment to be 128
        postTriggerSamples = int(np.ceil(postTriggerSamplesValue / 128.) * 128)
        samplesPerRecordValue = preTriggerSamplesValue + postTriggerSamplesValue

        # Select the number of records per DMA buffer.
        nRecordTotal = nRecord * nAverage
        if nRecord > 1:
            # if multiple records wanted, set records per buffer to match
            recordsPerBuffer = nRecord
        else:
            # else, use 100 records per buffers
            recordsPerBuffer = nBuffer
        buffersPerAcquisition = int(np.ceil(nRecordTotal / float(recordsPerBuffer)))
        if nRecordTotal < recordsPerBuffer:
            recordsPerBuffer = nRecordTotal

        # Select the active channels.
        Channel1 = 1 if bGetCh1 else 0
        Channel2 = 2 if bGetCh2 else 0

        channels = Channel1 | Channel2
        channelCount = 0
        for n in range(16):
            c = int(2**n)
            channelCount += (c & channels == c)

        # return directly if no active channels
        if channelCount == 0:
            return [np.array([], dtype=float), np.array([], dtype=float)]

        # Compute the number of bytes per record and per buffer
        bytesPerSample = (self.bitsPerSample + 7) // 8
        samplesPerRecord = preTriggerSamples + postTriggerSamples
        bytesPerRecord = bytesPerSample * samplesPerRecord
        bytesPerBuffer = bytesPerRecord * recordsPerBuffer * channelCount
        # force buffer size to be integer of 256 * 16 = 4096, not sure why
        bytesPerBufferMem = int(4096 * np.ceil(bytesPerBuffer / 4096.))

        recordsPerAcquisition = recordsPerBuffer * buffersPerAcquisition
        # TODO: Select number of DMA buffers to allocate
        MEM_SIZE = int(bufferSize * 1024 * 1024)
        # force buffer count to be even number, seems faster for allocating
        maxBufferCount = int(MEM_SIZE // (2 * bytesPerBufferMem))
        bufferCount = max(1, 2 * maxBufferCount)
        # don't allocate more buffers than needed for all data
        bufferCount = min(bufferCount, buffersPerAcquisition, maxBuffers)
        lT.append('Total buffers needed: %d' % buffersPerAcquisition)
        lT.append('Buffer count: %d' % bufferCount)
        lT.append('Buffer size: %d' % bytesPerBuffer)
        lT.append('Buffer size, memory: %d' % bytesPerBufferMem)
        lT.append('Records per buffer: %d' % recordsPerBuffer)

        # configure board, if wanted
        if bConfig:
            self.AlazarSetRecordSize(preTriggerSamples, postTriggerSamples)
            self.AlazarSetRecordCount(recordsPerAcquisition)
            # Allocate DMA buffers
            sample_type = ctypes.c_uint8
            if bytesPerSample > 1:
                sample_type = ctypes.c_uint16
            # clear old buffers
            self.removeBuffersDMA()
            # create new buffers
            self.buffers = []
            for i in range(bufferCount):
                self.buffers.append(DMABuffer(sample_type, bytesPerBufferMem))

        # arm and start capture, if wanted
        if bArm:
            # Configure the board to make a Traditional AutoDMA acquisition
            self.AlazarBeforeAsyncRead(channels,
                                       -preTriggerSamples,
                                       samplesPerRecord,
                                       recordsPerBuffer,
                                       recordsPerAcquisition,
                                       ADMA_EXTERNAL_STARTCAPTURE | ADMA_NPT)
            # Post DMA buffers to board
            for buf in self.buffers:
                self.AlazarPostAsyncBuffer(buf.addr, buf.size_bytes)
            try:
                self.AlazarStartCapture()
            except:
                # make sure buffers release memory if failed
                self.removeBuffersDMA()
                raise

        # if not waiting for result, return here
        if not bMeasure:
            return

        lT.append('Post: %.1f ms' % ((time.clock() - t0) * 1000))
        try:
            lT.append('Start: %.1f ms' % ((time.clock() - t0) * 1000))
            buffersCompleted = 0
            bytesTransferred = 0
            # initialize data array
            nPtsOut = samplesPerRecord * nRecord
            nAvPerBuffer = recordsPerBuffer / nRecord
            vData = [np.zeros(nPtsOut, dtype=float), np.zeros(nPtsOut, dtype=float)]
            # range and zero for conversion to voltages
            codeZero = 2 ** (float(self.bitsPerSample) - 1) - 0.5
            codeRange = 2 ** (float(self.bitsPerSample) - 1) - 0.5
            # range and zero for each channel, combined with bit shifting
            range1 = self.input_range[1] / codeRange / 16.
            range2 = self.input_range[2] / codeRange / 16.
            offset = 16. * codeZero

            timeout_ms = int(firstTimeout * 1000)

            log.info(str(lT))
            lT = []

            while (buffersCompleted < buffersPerAcquisition):
                # Wait for the buffer at the head of the list of available
                # buffers to be filled by the board.
                buf = self.buffers[buffersCompleted % len(self.buffers)]
                self.AlazarWaitAsyncBufferComplete(buf.addr, timeout_ms=timeout_ms)
                # lT.append('Wait: %.1f ms' % ((time.clock() - t0) * 1000))

                # reset timeout time, can be different than first call
                timeout_ms = int(timeout * 1000)

                buffersCompleted += 1
                bytesTransferred += buf.size_bytes

                # break if stopped from outside
                if funcStop is not None and funcStop():
                    break
                # report progress
                if funcProgress is not None:
                    funcProgress(float(buffersCompleted) / float(buffersPerAcquisition))

                # remove extra elements for getting even 256*16 buffer sizes
                if bytesPerBuffer == bytesPerBufferMem:
                    buf_truncated = buf.buffer
                else:
                    buf_truncated = buf.buffer[:(bytesPerBuffer // bytesPerSample)]

                # reshape, sort and average data
                if nAverage > 1:
                    if channels == 1:
                        rs = buf_truncated.reshape((nAvPerBuffer, nPtsOut))
                        vData[0] += range1 * (np.mean(rs, 0) - offset)
                    elif channels == 2:
                        rs = buf_truncated.reshape((nAvPerBuffer, nPtsOut))
                        vData[1] += range2 * (np.mean(rs, 0) - offset)
                    elif channels == 3:
                        rs = buf_truncated.reshape((nAvPerBuffer, nPtsOut, 2))
                        vData[0] += range1 * (np.mean(rs[:, :, 0], 0) - offset)
                        vData[1] += range2 * (np.mean(rs[:, :, 1], 0) - offset)
                else:
                    if channels == 1:
                        vData[0] = range1 * (buf_truncated - offset)
                    elif channels == 2:
                        vData[1] = range2 * (buf_truncated - offset)
                    elif channels == 3:
                        rs = buf_truncated.reshape((nPtsOut, 2))
                        vData[0] = range1 * (rs[:, 0] - offset)
                        vData[1] = range2 * (rs[:, 1] - offset)

                # lT.append('Sort/Avg: %.1f ms' % ((time.clock() - t0) * 1000))
                # log.info(str(lT))
                # lT = []
                #
                # Sample codes are unsigned by default. As a result:
                # - 0x00 represents a negative full scale input signal.
                # - 0x80 represents a ~0V signal.
                # - 0xFF represents a positive full scale input signal.

                # Add the buffer to the end of the list of available buffers.
                self.AlazarPostAsyncBuffer(buf.addr, buf.size_bytes)
        finally:
            # release resources
            try:
                self.AlazarAbortAsyncRead()
            except:
                pass
            lT.append('Abort: %.1f ms' % ((time.clock() - t0) * 1000))
        # normalize
        # log.info('Average: %.1f ms' % np.mean(lAvTime))
        vData[0] /= buffersPerAcquisition
        vData[1] /= buffersPerAcquisition
        # # log timing information
        lT.append('Done: %.1f ms' % ((time.clock() - t0) * 1000))
        log.info(str(lT))
        # return data - requested vector length, not restricted to 128 multiple
        if nPtsOut != (samplesPerRecordValue * nRecord):
            if len(vData[0]) > 0:
                vData[0] = vData[0].reshape((nRecord, samplesPerRecord))[:, :samplesPerRecordValue].flatten()
            if len(vData[1]) > 0:
                vData[1] = vData[1].reshape((nRecord, samplesPerRecord))[:, :samplesPerRecordValue].flatten()
        return vData

    def removeBuffersDMA(self):
        """Clear and remove DMA buffers, to release memory"""
        # make sure buffers release memory
        for buf in self.buffers:
            buf.__exit__()
        # remove all
        self.buffers = []

    def readTraces(self, Channel):
        """Read traces, convert to float, average to a single trace"""
        # define sizes
        bitsPerSample = 8
        bytesPerSample = int(np.floor((float(bitsPerSample) + 7.) / 8.0))
        # TODO: change so buffer alignment is 64!!
        samplesPerRecord = self.nPreSize + self.nPostSize
        # The buffer must be at least 16 samples larger than the transfer size
        samplesPerBuffer = samplesPerRecord + 16
        dataBuffer = (c_uint8 * samplesPerBuffer)()
        # define scale factors
        codeZero = 2 ** (float(bitsPerSample) - 1) - 0.5
        codeRange = 2 ** (float(bitsPerSample) - 1) - 0.5
        voltScale = self.input_range[Channel] / codeRange
        # initialize a scaled float vector
        vData = np.zeros(samplesPerRecord, dtype=float)
        for n1 in range(self.nRecord):
            self.AlazarRead(Channel, dataBuffer, bytesPerSample, n1 + 1,
                            -self.nPreSize, samplesPerRecord)
            # convert and scale to float
            vBuffer = voltScale * ((np.array(dataBuffer[:samplesPerRecord]) - codeZero))
            # add to output vector
            vData += vBuffer
        # normalize
        vData /= float(self.nRecord)
        return vData

    # Commom Scope/ADC control fuctions
    def getSerialNumber(self):
        value = np.array([0], dtype=np.uint32)
        value_ptr = value.ctypes.data_as(POINTER(c_uint32))
        self._call_dll('AlazarQueryCapability', self._handle, 0x10000024, 0, value_ptr)
        return value[0]

    def getMemorySize(self):
        """Returns board memory size in maximum samples per Channel"""
        value = np.array([0], dtype=np.uint32)
        value_ptr = value.ctypes.data_as(POINTER(c_uint32))
        self._call_dll('AlazarQueryCapability', self._handle, 0x1000002A, 0, value_ptr)
        return value[0]

    def getName(self):
        self.board_kind = self._board_names[self._ATS_dll.AlazarGetBoardKind(self._handle)]
        return self.board_kind

    def acquisition(self, enable):
        if enable:
            self._call_dll('AlazarStartCapture', self._handle)
        else:
            self._call_dll('AlazarAbortCapture', self._handle)

    def setSingleAcquisition(self):
        """Set single aquisition."""
        self.AlazarSetRecordCount(1)

    def wasTriggered(self):
        """Check if acquisition is running."""
        return not self.AlazarBusy()

    def getChannelWaveform(self, Channel=1):
        ch = channel(self, Channel)
        ch.getWaveform()
        return ch


class channel(Digitizer):
    """ Channel class that implements the functionality related to one of
    the oscilloscope's physical channels.
    """

    def __init__(self, adc, channel):
        self.adc = adc
        self.channel = channel

    def getWaveform(self):
        """ Downloads this channels waveform data.
        This function will not make any adjustments to the V/div settings.
        If the parameter 'wait' is set to false, the most recent waveform will be
        captured. Otherwise the scope will wait for the next data acquisition
        to complete before downloading waveform data.
        """
        bitShift = 2

        bytesPerSample = int(np.floor((float(self.adc.bitsPerSample) + 7.) / 8.0))
        # TODO: change so buffer alignment is 64!!
        samplesPerRecord = self.adc.nPreSize + self.adc.nPostSize
        # bytesPerRecord = bytesPerSample * samplesPerRecord
        # The buffer must be at least 16 samples larger than the transfer size
        # samplesPerBuffer = samplesPerRecord + 16
        dataBuffer = np.zeros([samplesPerRecord], dtype=np.uint16)
        dataBuffer_ptr = dataBuffer.ctypes.data_as(POINTER(c_uint16))
        # define scale factors
        bitsPerSample = 14
        codeRange = (1 << (bitsPerSample - 1)) - 0.5

        self.input_range = self.adc.input_range[self.channel]
        self.sample_rate = self.adc.sample_rate
        self.y_offset = (1 << (bitsPerSample - 1)) - 0.5
        self.y_mult = self.input_range / codeRange
        self.y_zero = 0
        self.x_zero = -self.adc.nPreSize / self.sample_rate
        self.x_incr = float(1. / self.sample_rate)
        self.adc.AlazarRead(self.channel, dataBuffer_ptr, bytesPerSample, 1, -self.adc.nPreSize, samplesPerRecord)

        self.signal_raw = dataBuffer >> bitShift
        self.data_y = ((self.signal_raw.astype(int) - self.y_offset) * self.y_mult) + self.y_zero
        self.data_x = self.x_zero + np.arange(self.signal_raw.size) * self.x_incr
        return [self.data_x, self.data_y]


if __name__ == '__main__':
    #
    # test driver
    dig = Digitizer(systemId=1, boardId=1)
    print(dig.memorySize_samples, dig.bitsPerSample)
    print(dig.get_board_info(1, 1))
    dig.testLED()
    dig.AlazarSetCaptureClock(SourceId=1, SampleRateId=sample_rate_id["20 MS/s"])
    # Configure each channel
    for n in range(2):
        # Coupling DC, Inpedance 1MOhm
        dig.AlazarInputControl(Channel=n + 1, Coupling=2, InputRange=input_range["10 V"], Impedance=1)
        # Enable 20 MHz Bandwidth Limit
        dig.AlazarSetBWLimit(Channel=n + 1, enable=1)
    # Configure trigger range
    dig.AlazarSetTriggerOperation(Source1=0x02, Slope1=1, Level1=180)  # External trigger (0x02), pos slope (1)
    # Trigger with 5V TTL DC Coupling
    dig.AlazarSetExternalTrigger(Coupling=2, Range=0)
    dig.AlazarSetTriggerDelay(Delay=0)
    dig.AlazarSetTriggerTimeOut(0)
    dig.AlazarSetRecordSize(PreSize=0, PostSize=400000)
    dig.AlazarSetRecordCount(1)
    dig.AlazarStartCapture()
    import matplotlib.pyplot as plt
    i = 0
    while dig.AlazarBusy() and i < 40:
        time.sleep(0.5)
        print(dig.AlazarBusy())
        i += 0
    ch1 = dig.getChannelWaveform(Channel=1)
    ch2 = dig.getChannelWaveform(Channel=2)
    plt.plot(ch1.data_x, ch1.data_y)
    plt.plot(ch2.data_x, ch2.data_y)
    plt.show()
