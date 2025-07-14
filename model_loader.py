# model_loader.py

from functools import lru_cache
from pathlib import Path

# 可选依赖
try:
    from vosk import Model as VoskModel
except ImportError:
    VoskModel = None

try:
    from transformers import Wav2Vec2Processor, Wav2Vec2ForCTC
    import torch
except ImportError:
    Wav2Vec2Processor = None
    Wav2Vec2ForCTC = None
    torch = None


@lru_cache(maxsize=None)
def load_vosk_model(model_path: str):
    """
    加载 Vosk 离线模型
    """
    if VoskModel is None:
        raise ImportError("请先安装 vosk：pip install vosk")
    if not Path(model_path).exists():
        raise FileNotFoundError(f"找不到 vosk 模型目录: {model_path}")
    return VoskModel(model_path)


@lru_cache(maxsize=None)
def load_hf_model(model_name_or_path: str):
    """
    加载 Hugging Face 的 Wav2Vec2ForCTC 模型和 Processor
    """
    if Wav2Vec2Processor is None:
        raise ImportError("请先安装 transformers：pip install transformers torch soundfile")

    print(f"加载 Hugging Face 模型: {model_name_or_path}")
    processor = Wav2Vec2Processor.from_pretrained(model_name_or_path)
    model = Wav2Vec2ForCTC.from_pretrained(model_name_or_path)

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model.to(device)
    model.eval()

    return processor, model, device

