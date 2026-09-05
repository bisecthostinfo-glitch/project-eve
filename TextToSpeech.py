import io
import os
import wave
import sounddevice
import numpy
from piper import PiperVoice


class TextToSpeech:
    def __init__(self, ModelPath, ConfigPath=None):
        if not os.path.exists(ModelPath):
            raise FileNotFoundError(
                f"Piper voice model not found at '{ModelPath}'. "
                "Run SetupPiper.ps1 first to download one."
            )
        self.Voice = PiperVoice.load(ModelPath, config_path=ConfigPath)

    def Speak(self, Text):
        if not Text or not Text.strip():
            return

        WavBuffer = io.BytesIO()
        with wave.open(WavBuffer, "wb") as WavFile:
            self.Voice.synthesize_wav(Text, WavFile)

        WavBuffer.seek(0)
        with wave.open(WavBuffer, "rb") as WavFile:
            SampleRate = WavFile.getframerate()
            SampleWidth = WavFile.getsampwidth()
            RawAudio = WavFile.readframes(WavFile.getnframes())

        DtypeMap = {1: numpy.int8, 2: numpy.int16, 4: numpy.int32}
        AudioArray = numpy.frombuffer(RawAudio, dtype=DtypeMap.get(SampleWidth, numpy.int16))

        sounddevice.play(AudioArray, samplerate=SampleRate)
        sounddevice.wait()
