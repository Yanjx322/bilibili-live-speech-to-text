import subprocess
import torch
import numpy as np
from transformers import Wav2Vec2Processor, Wav2Vec2ForCTC

class HFRecognizeClient:
    def __init__(self, stream_url: str):
        self.stream_url = stream_url
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.model_name = "model/wav2vec2-chinese"

        print("加载模型和处理器中...")
        self.processor = Wav2Vec2Processor.from_pretrained(self.model_name)
        self.model = Wav2Vec2ForCTC.from_pretrained(self.model_name).to(self.device).eval()

    def read_audio_stream(self, ffmpeg_process, chunk_size):
        raw_audio = ffmpeg_process.stdout.read(chunk_size)
        if len(raw_audio) < chunk_size:
            return None
        audio = np.frombuffer(raw_audio, np.int16).astype(np.float32) / 32768.0
        return audio

    def run(self):
        command = [
            "ffmpeg",
            "-i", self.stream_url,
            "-f", "s16le",
            "-acodec", "pcm_s16le",
            "-ac", "1",
            "-ar", "16000",
            "-"
        ]
        print("启动 ffmpeg 拉流...")
        ffmpeg_proc = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)

        chunk_duration = 1.0
        chunk_size = int(16000 * 2 * chunk_duration)  # 2 bytes per sample

        buffer = np.zeros(0, dtype=np.float32)

        print("开始实时识别，按 Ctrl+C 停止")

        try:
            while True:
                audio_chunk = self.read_audio_stream(ffmpeg_proc, chunk_size)
                if audio_chunk is None:
                    print("音频流结束或读取失败")
                    break

                buffer = np.concatenate((buffer, audio_chunk))

                if len(buffer) >= 16000:
                    input_values = self.processor(buffer[:16000], sampling_rate=16000, return_tensors="pt").input_values
                    input_values = input_values.to(self.device)

                    with torch.no_grad():
                        logits = self.model(input_values).logits
                    pred_ids = torch.argmax(logits, dim=-1)
                    transcription = self.processor.batch_decode(pred_ids)[0]

                    print(f"识别结果: {transcription}")

                    buffer = buffer[16000:]

        except KeyboardInterrupt:
            print("停止识别")

        finally:
            ffmpeg_proc.kill()






