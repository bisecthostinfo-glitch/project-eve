from faster_whisper import WhisperModel


class SpeechToText:
    def __init__(self, ModelSize="base.en", Device="auto", ComputeType="default"):
        # Model downloads automatically on first use, cached by faster-whisper.
        # "base.en" is a good speed/accuracy default for push-to-talk commands;
        # step up to "small.en" if accuracy matters more than latency.
        self.Model = WhisperModel(ModelSize, device=Device, compute_type=ComputeType)

    def Transcribe(self, AudioArray, SampleRate=16000):
        Segments, _Info = self.Model.transcribe(AudioArray, language="en")
        Text = " ".join(Segment.text.strip() for Segment in Segments)
        return Text.strip()
