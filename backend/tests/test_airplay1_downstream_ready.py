import struct

from app.engine.airplay.server import AirPlayServer


class _FakeSocket:
    def __init__(self):
        self.data = b""

    def sendall(self, data: bytes) -> None:
        self.data += data


def test_airplay1_waits_for_non_silent_pcm_before_downstream_playback(monkeypatch):
    server = AirPlayServer(
        "192.168.1.20",
        device_name="test-speaker",
        speaker_hardware="S12A",
        audio_format="wav",
    )
    calls: list[str] = []
    server.on_play_start = calls.append
    sock = _FakeSocket()

    server._handle_record(sock, "1")

    assert b"RTSP/1.0 200 OK" in sock.data
    assert calls == []
    assert server._play_start_pending is True

    # Decoder fallbacks may yield a silence frame; that must not wake the
    # Xiaomi player and make it latch onto an empty live HTTP stream.
    server._notify_audio_ready(b"\x00" * 1408)
    assert calls == []
    assert server._play_start_pending is True

    audible = struct.pack("<h", 1200) * 704
    server._notify_audio_ready(audible)

    assert calls == [server._stream_server.stream_url]
    assert server._play_start_pending is False

    # Additional PCM must not issue duplicate MiNA play commands.
    server._notify_audio_ready(audible)
    assert calls == [server._stream_server.stream_url]


def test_airplay_stream_format_auto_prefers_mp3_for_s12a(monkeypatch):
    monkeypatch.setenv("MIAIR_AIRPLAY_STREAM_FORMAT", "auto")
    s12a = AirPlayServer("192.168.1.20", speaker_hardware="S12A")
    lx04 = AirPlayServer("192.168.1.20", speaker_hardware="LX04")

    assert s12a._stream_server._audio_format == "mp3"
    assert lx04._stream_server._audio_format == "wav"
