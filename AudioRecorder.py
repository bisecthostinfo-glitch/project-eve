import sounddevice
import numpy


class AudioRecorder:
    def __init__(self, SampleRate=16000):
        self.SampleRate = SampleRate
        self.Frames = []
        self.Stream = None

    def AudioCallback(self, InData, FrameCount, TimeInfo, Status):
        self.Frames.append(InData.copy())

    def StartRecording(self):
        self.Frames = []
        self.Stream = sounddevice.InputStream(
            samplerate=self.SampleRate,
            channels=1,
            dtype="float32",
            callback=self.AudioCallback,
        )
        self.Stream.start()

    def StopRecording(self):
        if self.Stream is None:
            return numpy.array([], dtype=numpy.float32)
        self.Stream.stop()
        self.Stream.close()
        self.Stream = None

        if not self.Frames:
            return numpy.array([], dtype=numpy.float32)

        AudioArray = numpy.concatenate(self.Frames, axis=0).flatten()
        return AudioArray
