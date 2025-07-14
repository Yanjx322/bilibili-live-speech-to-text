# bilibili_stream.py
import requests

API = (
    "https://api.live.bilibili.com/xlive/web-room/v2/index/"
    "getRoomPlayInfo?room_id={room}&protocol=0,1&format=0,1,2&codec=0,1"
)
HEADERS = {"User-Agent": "Mozilla/5.0"}

def get_live_url(room_id: int | str) -> str | None:
    """返回首选音视频流的 URL，找不到时返回 None。"""
    resp = requests.get(API.format(room=room_id), headers=HEADERS, timeout=10)
    resp.raise_for_status()
    data = resp.json()

    try:
        streams = data["data"]["playurl_info"]["playurl"]["stream"]
    except (KeyError, TypeError):
        return None

    for stream in streams:
        for fmt in stream.get("format", []):
            for codec in fmt.get("codec", []):
                base = codec.get("base_url")
                for url_info in codec.get("url_info", []):
                    host, extra = url_info.get("host"), url_info.get("extra")
                    if host and base and extra:
                        return f"{host}{base}{extra}"
    return None


