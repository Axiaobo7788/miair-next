#!/usr/bin/env python3
"""Apply the small HAOS AirPlay compatibility overlay to upstream MiAir Next 0.10.1."""

from pathlib import Path


def replace(path: Path, old: str, new: str, label: str) -> None:
    text = path.read_text(encoding="utf-8")
    if old not in text:
        raise SystemExit(f"{path}: patch anchor not found: {label}")
    path.write_text(text.replace(old, new, 1), encoding="utf-8")


server = Path("/app/backend/app/engine/airplay/server.py")

replace(server, "import logging\nimport os\n", "import logging\nimport math\nimport os\n", "math import")

replace(
    server,
    '    def __init__(self, hostname: str, device_name: str = "MiAir", shared_zeroconf=None, speaker_hardware: str = ""):\n',
    '    def __init__(self, hostname: str, device_name: str = "MiAir", shared_zeroconf=None, speaker_hardware: str = "", audio_format: str | None = None):\n',
    "AirPlayServer signature",
)

replace(
    server,
    '''        # 音频流服务器 - 统一使用 WAV 输出（零编码延迟，不卡顿）
        self._stream_server = AudioStreamServer(hostname, 0, audio_format="wav")
''',
    '''        # 小米音箱的 HTTP 播放栈对实时长流的兼容性并不一致。
        # 默认保持 WAV；HAOS/容器可通过环境变量切换兼容输出。
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
''',
    "downstream format",
)

replace(
    server,
    '''        self.on_play_start: Callable | None = None
        self.on_play_stop: Callable | None = None
        self.on_volume_change: Callable[[float], None] | None = None
''',
    '''        self.on_play_start: Callable | None = None
        self.on_play_stop: Callable | None = None
        self.on_volume_change: Callable[[float], None] | None = None
        # Do not ask the Xiaomi speaker to pull the HTTP stream until the
        # AirPlay receiver has decoded real, non-silent PCM. MiAirX uses the
        # same audio-ready boundary; triggering at RECORD can make some Xiaomi
        # firmware latch onto an empty/not-yet-ready live stream.
        self._play_start_pending = False
        self._pcm_probe_logged_silent = False
        self._pcm_probe_logged_audio = False
''',
    "audio-ready state",
)

replace(
    server,
    '''                elif method == "ANNOUNCE":
                    self._reset_audio_diagnostics()
                    self._is_playing = True
''',
    '''                elif method == "ANNOUNCE":
                    self._reset_audio_diagnostics()
                    self._play_start_pending = False
                    self._pcm_probe_logged_silent = False
                    self._pcm_probe_logged_audio = False
                    self._is_playing = True
''',
    "ANNOUNCE reset",
)

replace(
    server,
    '''                elif method == "PAUSE":
                    self._stream_server.stop_streaming()
                    self._send_rtsp_response(sock, 200, cseq)
''',
    '''                elif method == "PAUSE":
                    self._play_start_pending = False
                    self._stream_server.stop_streaming()
                    self._send_rtsp_response(sock, 200, cseq)
''',
    "PAUSE reset",
)

replace(
    server,
    '''                elif method == "TEARDOWN":
                    self._is_playing = False
''',
    '''                elif method == "TEARDOWN":
                    self._play_start_pending = False
                    self._is_playing = False
''',
    "TEARDOWN reset",
)

replace(
    server,
    '''    def _handle_record(self, sock: socket.socket, cseq: str):
        """处理 RECORD 请求 - 开始播放"""
        self._stream_server.start_streaming()

        if self.on_play_start:
            try:
                self.on_play_start(self._stream_server.stream_url)
            except Exception as e:
                log.error(f"on_play_start error: {e}")

        self._send_rtsp_response(sock, 200, cseq, {
''',
    '''    def _handle_record(self, sock: socket.socket, cseq: str):
        """处理 RECORD 请求 - 开始接收，等首个真实 PCM 后再唤醒小爱。"""
        self._stream_server.start_streaming()
        self._play_start_pending = True
        log.info("AirPlay RECORD 已接受，等待首个非静音 PCM 后启动小爱拉流")

        self._send_rtsp_response(sock, 200, cseq, {
''',
    "defer RECORD playback",
)

text = server.read_text(encoding="utf-8")
anchor = "    def _timing_loop(self, timing_socket: socket.socket):\n"
if anchor not in text:
    raise SystemExit(f"{server}: helper insertion anchor not found")
helper = '''    def _notify_audio_ready(self, pcm: bytes) -> None:
        """Log decoded PCM quality and start downstream playback exactly once."""
        if not pcm:
            return

        usable = len(pcm) & ~1
        if usable <= 0:
            return
        probe = pcm[: min(usable, 8192)]
        samples = [sample[0] for sample in struct.iter_unpack("<h", probe)]
        if not samples:
            return
        nonzero = sum(1 for sample in samples if sample)
        peak = max(abs(sample) for sample in samples)
        rms = math.sqrt(sum(sample * sample for sample in samples) / len(samples))

        if nonzero == 0:
            if not self._pcm_probe_logged_silent:
                self._pcm_probe_logged_silent = True
                log.warning(
                    "AirPlay PCM 首块为全静音: bytes=%s samples=%s peak=0 rms=0",
                    len(pcm),
                    len(samples),
                )
            return

        if not self._pcm_probe_logged_audio:
            self._pcm_probe_logged_audio = True
            log.info(
                "AirPlay PCM 已验证有声: bytes=%s samples=%s nonzero=%s peak=%s rms=%.1f",
                len(pcm),
                len(samples),
                nonzero,
                peak,
                rms,
            )

        if not self._play_start_pending:
            return
        self._play_start_pending = False
        if self.on_play_start:
            try:
                log.info("AirPlay 首个有效 PCM 已就绪，开始通知小爱拉取 HTTP 音频流")
                self.on_play_start(self._stream_server.stream_url)
            except Exception as e:
                log.error(f"on_play_start error: {e}")

'''
server.write_text(text.replace(anchor, helper + anchor, 1), encoding="utf-8")

replace(
    server,
    '''                    decoded = _decode_audio(payload)
                    if decoded:
                        _write_pcm(decoded)
                        self._update_audio_metrics(pcm_bytes=len(decoded))
''',
    '''                    decoded = _decode_audio(payload)
                    if decoded:
                        _write_pcm(decoded)
                        self._update_audio_metrics(pcm_bytes=len(decoded))
                        self._notify_audio_ready(decoded)
''',
    "decoded PCM ready callback",
)

audio = Path("/app/backend/app/engine/audio_stream.py")
replace(
    audio,
    '''        try:
            while self._active and not conn_abort.is_set():
                audio_data = await asyncio.to_thread(proc.stdout.read, 8192)
                if not audio_data or self._abort:
                    break
                await response.write(audio_data)
''',
    '''        bytes_sent = 0
        first_output_logged = False
        try:
            while self._active and not conn_abort.is_set():
                audio_data = await asyncio.to_thread(proc.stdout.read, 8192)
                if not audio_data or self._abort:
                    break
                if not first_output_logged:
                    first_output_logged = True
                    log.info(
                        f"{self._label}: MP3 编码器开始产出有效数据 "
                        f"(首包={len(audio_data)} bytes, prefix={audio_data[:4].hex()})"
                    )
                bytes_sent += len(audio_data)
                await response.write(audio_data)
''',
    "MP3 output diagnostics",
)
replace(
    audio,
    '''        try:
            await response.write_eof()
        except Exception:
            pass
        log.info(f"{self._label}: MP3 音频流结束")
        return response
''',
    '''        try:
            await response.write_eof()
        except Exception:
            pass
        if bytes_sent:
            log.info(f"{self._label}: MP3 音频流结束 (已发送 {bytes_sent} bytes)")
        else:
            log.warning(f"{self._label}: MP3 音频流结束但编码器没有输出任何字节")
        return response
''',
    "MP3 byte count",
)

speaker = Path("/app/backend/app/engine/airplay/speaker_airplay.py")
replace(
    speaker,
    '''            if success:
                log.info(f"AirPlay 音频已在 {self.device_name} 开始播放: {stream_url}")
                self._start_poll()
''',
    '''            if success:
                log.info(f"AirPlay 音频已在 {self.device_name} 开始播放: {stream_url}")
                asyncio.create_task(self._log_downstream_status(stream_url))
                self._start_poll()
''',
    "downstream status task",
)
text = speaker.read_text(encoding="utf-8")
anchor = "    async def _resolve_audio_id(self) -> str | None:\n"
if anchor not in text:
    raise SystemExit(f"{speaker}: downstream status insertion anchor not found")
method = '''    async def _log_downstream_status(self, stream_url: str) -> None:
        """Confirm what the Xiaomi firmware reports after accepting play_url."""
        await asyncio.sleep(1.5)
        if not self._airplay_active or self._stream_url != stream_url:
            return
        try:
            status = await self.controller.get_status()
            diagnostics = (
                self.airplay_server.get_audio_diagnostics()
                if self.airplay_server
                else {}
            )
            log.info(
                "AirPlay 下游状态确认 %s: speaker_status=%s idle=%s volume=%s "
                "http_clients=%s pcm_bytes=%s decode_success=%s decode_errors=%s "
                "decrypt_failures=%s",
                self.device_name,
                status.get("status"),
                status.get("idle", False),
                status.get("volume"),
                diagnostics.get("stream_clients"),
                diagnostics.get("pcm_bytes"),
                diagnostics.get("decode_success"),
                diagnostics.get("decode_errors"),
                diagnostics.get("decrypt_failures"),
            )
        except Exception as e:
            log.warning(f"AirPlay 下游状态确认失败 ({self.device_name}): {e}")

'''
speaker.write_text(text.replace(anchor, method + anchor, 1), encoding="utf-8")

print("patched AirPlay HAOS runtime overlay")
