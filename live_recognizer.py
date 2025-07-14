import requests
import subprocess
import sys
from vosk import Model, KaldiRecognizer
import json

def get_bilibili_live_url(room_id):
    api_url = f"https://api.live.bilibili.com/xlive/web-room/v2/index/getRoomPlayInfo?room_id={room_id}&protocol=0,1&format=0,1,2&codec=0,1"
    headers = {"User-Agent": "Mozilla/5.0"}
    resp = requests.get(api_url, headers=headers)
    data = resp.json()
    streams = data["data"]["playurl_info"]["playurl"]["stream"]
    for stream in streams:
        for fmt in stream.get("format", []):
            for codec in fmt.get("codec", []):
                base_url = codec.get("base_url")
                for url_info in codec.get("url_info", []):
                    host = url_info.get("host")
                    extra = url_info.get("extra")
                    if host and base_url and extra:
                        return host + base_url + extra
    return None

def main(room_id, model_path):
    # 获取直播流地址
    stream_url = get_bilibili_live_url(room_id)
    if not stream_url:
        print("无法获取直播流地址")
        return

    print(f"获取直播流地址: {stream_url}")

    # 加载vosk模型
    model = Model(model_path)
    rec = KaldiRecognizer(model, 16000)

    # 启动ffmpeg进程拉取音频
    cmd = [
        "ffmpeg",
        "-i", stream_url,
        "-vn",              # 不要视频
        "-f", "s16le",      # 原始PCM格式
        "-ar", "16000",     # 采样率16kHz
        "-ac", "1",         # 单声道
        "pipe:1"            # 输出到管道
    ]

    process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    print("开始识别，按 Ctrl+C 停止...")

    try:
        while True:
            data = process.stdout.read(4000)
            if len(data) == 0:
                print("音频流结束")
                break

            if rec.AcceptWaveform(data):
                res = rec.Result()
                print("识别结果:", res)
            else:
                partial_res = rec.PartialResult()
                # 可以看下中间结果
                j = json.loads(partial_res)
                if j.get("partial", "") != "":
                    print("部分结果:", j["partial"])

    except KeyboardInterrupt:
        print("\n停止识别")

    print("最终识别结果:")
    print(rec.FinalResult())

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("用法: python live_recognizer.py <房间号> <vosk模型路径>")
        print("示例: python live_recognizer.py 923833 ./vosk-model-small-cn-0.22")
        sys.exit(1)

    room_id = sys.argv[1]
    model_path = sys.argv[2]
    main(room_id, model_path)
