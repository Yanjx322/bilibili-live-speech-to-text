from vosk import Model, KaldiRecognizer
import subprocess
import json

class VoskRecognizerEnglishClient:
    def __init__(self, stream_url):
        self.stream_url = stream_url
        model_path = "./model/vosk-model-small-en-us-0.15"
        self.model = Model(model_path)
        self.rec = KaldiRecognizer(self.model, 16000)

    def run(self):
        cmd = [
            "ffmpeg",
            "-i", self.stream_url,
            "-vn",
            "-f", "s16le",
            "-ar", "16000",
            "-ac", "1",
            "pipe:1"
        ]
        process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)

        print("Starting English speech recognition with Vosk...")
        while True:
            data = process.stdout.read(4000)
            if len(data) == 0:
                break
            if self.rec.AcceptWaveform(data):
                res = json.loads(self.rec.Result())
                text = res.get("text", "").strip()
                if text:
                    print("Recognized:", text)
