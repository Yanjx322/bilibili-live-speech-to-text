# main.py

from bilibili_stream import get_live_url
import sys

def main():
    room_id = input("input bilibili room number/请输入Bilibili直播房间号: ").strip()
    print("select model/请选择识别模型：")
    print("1. Vosk(Chinese)离线模型")
    print("2. Vosk(English)离线模型")
    print("3. xfyun科大讯飞在线模型")
    print("4. Hugging Face wav2vec2-chinese")
    model_choice = input("your input model number: ").strip()

    stream_url = get_live_url(room_id)
    if not stream_url:
        print("无法获取直播流地址，请检查房间号")
        sys.exit(1)
    print(f"直播流地址：{stream_url}")

    if model_choice == "1":
        from vosk_recognizer import VoskRecognizerClient
        recognizer = VoskRecognizerClient(stream_url)
        recognizer.run()
    elif model_choice == "2":
        from vosk_recognizer_English import VoskRecognizerEnglishClient
        recognizer = VoskRecognizerEnglishClient(stream_url)
        recognizer.run()
    elif model_choice == "3":
        from xf_recognizer import XFRecognizeClient
        recognizer = XFRecognizeClient(room_id)
        recognizer.run()
    elif model_choice == "4":
        from hf_recognizer import HFRecognizeClient
        recognizer = HFRecognizeClient(stream_url)
        recognizer.run()
    else:
        print("无效选择，程序退出")

if __name__ == "__main__":
    main()

