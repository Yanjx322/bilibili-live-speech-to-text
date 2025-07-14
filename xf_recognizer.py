import base64, hashlib, hmac, json, ssl, time, threading, subprocess
from datetime import datetime, timezone
from urllib.parse import urlencode
import websocket
from bilibili_stream import get_live_url  # b站api获取

#讯飞没有开源模型，只有在线测试（一天内有免费次数限制）
APPID = "5fd6ab71"
APIKey = "e46a7c1b70be9e68c7d56319faf2a673"
APISecret = "ZjA4ODQzMDU0NzYxY2Q1NDExM2YxZjAx"
HOST = "iat-api.xfyun.cn"
URI = "/v2/iat"

def create_url() -> str:
    now = datetime.now(timezone.utc)
    date = now.strftime('%a, %d %b %Y %H:%M:%S GMT')
    sign_origin = f"host: {HOST}\ndate: {date}\nGET {URI} HTTP/1.1"
    sha = hmac.new(APISecret.encode(), sign_origin.encode(), hashlib.sha256).digest()
    signature = base64.b64encode(sha).decode()
    auth_origin = (
        f'api_key="{APIKey}", algorithm="hmac-sha256", headers="host date request-line", '
        f'signature="{signature}"'
    )
    authorization = base64.b64encode(auth_origin.encode()).decode()
    params = {"authorization": authorization, "date": date, "host": HOST}
    return f"wss://{HOST}{URI}?" + urlencode(params)

class XFRecognizeClient:
    def __init__(self, room_id: str):
        self.stream_url = get_live_url(room_id)
        if not self.stream_url:
            raise RuntimeError("无法获取直播流地址，请检查房间号")
        print("直播流 URL:", self.stream_url)
        self.ws = websocket.WebSocketApp(
            create_url(),
            on_open=self.on_open,
            on_message=self.on_message,
            on_error=self.on_error,
            on_close=self.on_close
        )
        self.running = True

    # ---------- WebSocket 事件 ----------
    def on_open(self, ws):
        print("WebSocket 已连接，开始推流…")
        threading.Thread(target=self.send_audio, args=(ws,), daemon=True).start()

    def on_message(self, ws, message):
        resp = json.loads(message)
        if "data" in resp:
            words = resp["data"]["result"]["ws"]
            text = "".join(w["cw"][0]["w"] for w in words).strip()
            if text:
                print("识别：", text)

    def on_error(self, ws, err):
        print("WebSocket 错误：", err)

    def on_close(self, ws, *args):
        print("连接关闭")

    # ---------- 推送音频 ----------
    def send_audio(self, ws):
        import subprocess

        def start_ffmpeg():
            return subprocess.Popen([
                "ffmpeg",
                "-headers", "User-Agent: Mozilla/5.0\r\nReferer: https://live.bilibili.com/\r\n",
                "-reconnect", "1",
                "-reconnect_streamed", "1",
                "-reconnect_delay_max", "3",
                "-i", self.stream_url,
                "-f", "s16le",
                "-ac", "1",
                "-ar", "16000",
                "-vn",
                "pipe:1"
            ], stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, bufsize=10 ** 7)

        ff = start_ffmpeg()
        status = 0

        try:
            while self.running:
                chunk = ff.stdout.read(1280)
                if not chunk:
                    # ffmpeg 挂了，尝试重启
                    if ff.poll() is not None:
                        print("⚠️ ffmpeg 挂了，正在重连...")
                        ff = start_ffmpeg()
                        status = 0
                    else:
                        time.sleep(0.2)
                    continue

                # 构造音频帧
                frame = {
                    "common": {"app_id": APPID},
                    "business": {
                        "language": "zh_cn",
                        "domain": "iat",
                        "accent": "mandarin",
                        "vad_eos": 10000  # 10秒无声才认为结束
                    },
                    "data": {
                        "status": status,
                        "format": "audio/L16;rate=16000",
                        "encoding": "raw",
                        "audio": base64.b64encode(chunk).decode()
                    }
                }

                try:
                    ws.send(json.dumps(frame))
                except websocket.WebSocketConnectionClosedException:
                    print("🔌 WebSocket 已断开")
                    break
                except Exception as e:
                    print("❌ 发送失败:", e)
                    break

                status = 1  # 第一个包后都用 1
                # 不 sleep，保证不断流
        finally:
            try:
                ws.send(json.dumps({"data": {"status": 2}}))
            except:
                pass
            self.running = False

    def run(self):
        self.ws.run_forever(sslopt={"cert_reqs": ssl.CERT_NONE})

if __name__ == "__main__":
    XFRecognizeClient("732").run()
