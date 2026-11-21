#!/usr/bin/env python3
from pathlib import Path

path = Path("/app/backend/app/engine/airplay/server.py")
text = path.read_text(encoding="utf-8")

old_sig = '''    def __init__(self, hostname: str, device_name: str = "MiAir", shared_zeroconf=None, speaker_hardware: str = ""):
'''
new_sig = '''    def __init__(self, hostname: str, device_name: str = "MiAir", shared_zeroconf=None, speaker_hardware: str = "", audio_format: str | None = None):
'''
if old_sig not in text:
    raise SystemExit("AirPlayServer signature anchor not found")
text = text.replace(old_sig, new_sig, 1)

old_stream = '''        # 音频流服务器 - 统一使用 WAV 输出（零编码延迟，不卡顿）
        self._stream_server = AudioStreamServer(hostname, 0, audio_format="wav")
'''
new_stream = '''        # 小米音箱的 HTTP 播放栈对“无限长 chunked WAV”的兼容性并不一致。
        # 保留 WAV 低延迟路径，同时允许 HAOS wrapper / 环境变量切换 MP3。
        # auto 仅对已有兼容性证据的型号使用 MP3，其余继续沿用 WAV。
        requested_format = (
            audio_format
            or os.getenv("MIAIR_AIRPLAY_STREAM_FORMAT", "auto")
            or "auto"
        ).strip().lower()
        if requested_format not in {"auto", "wav", "mp3"}:
            log.warning(
                "未知 MIAIR_AIRPLAY_STREAM_FORMAT=%s，回退 auto",
                requested_format,
            )
            requested_format = "auto"
        if requested_format == "auto":
            mp3_preferred_hardware = {"S12A", "L05B", "L05C", "LX06", "L16A"}
            selected_format = (
                "mp3"
                if (speaker_hardware or "").upper() in mp3_preferred_hardware
                else "wav"
            )
        else:
            selected_format = requested_format
        log.info(
            "AirPlay 下游音频格式: %s (requested=%s, hardware=%s)",
            selected_format,
            requested_format,
            speaker_hardware or "unknown",
        )
        self._stream_server = AudioStreamServer(
            hostname, 0, audio_format=selected_format
        )
'''
if old_stream not in text:
    raise SystemExit("AirPlay stream-server anchor not found")
text = text.replace(old_stream, new_stream, 1)

path.write_text(text, encoding="utf-8")
print(f"patched {path}")
