"""Offline Spanish narration using the bundled eSpeak NG library."""
from __future__ import annotations

import argparse
import ctypes as C
import wave
from pathlib import Path

import espeakng_loader


def synthesize(text: str, output: Path, *, rate: int = 154) -> float:
    lib = C.CDLL(str(espeakng_loader.get_library_path()))
    data = str(espeakng_loader.get_data_path()).encode()
    lib.espeak_Initialize.argtypes = [C.c_int, C.c_int, C.c_char_p, C.c_int]
    lib.espeak_Initialize.restype = C.c_int
    sample_rate = lib.espeak_Initialize(1, 0, data, 0)
    if sample_rate <= 0:
        raise RuntimeError("Cannot initialize eSpeak NG")
    lib.espeak_SetVoiceByName.argtypes = [C.c_char_p]
    if lib.espeak_SetVoiceByName(b"es-419") != 0:
        if lib.espeak_SetVoiceByName(b"es") != 0:
            raise RuntimeError("Spanish voice unavailable")
    lib.espeak_SetParameter.argtypes = [C.c_int, C.c_int, C.c_int]
    lib.espeak_SetParameter(1, rate, 0)  # words per minute
    lib.espeak_SetParameter(3, 63, 0)    # pitch
    chunks: list[bytes] = []
    Callback = C.CFUNCTYPE(C.c_int, C.POINTER(C.c_short), C.c_int, C.c_void_p)

    def receive(samples, count, _events):
        if count > 0:
            chunks.append(C.string_at(samples, count * 2))
        return 0

    callback = Callback(receive)
    lib.espeak_SetSynthCallback.argtypes = [Callback]
    lib.espeak_SetSynthCallback(callback)
    lib.espeak_Synth.argtypes = [C.c_void_p, C.c_size_t, C.c_uint, C.c_int,
                                C.c_uint, C.c_uint, C.c_void_p, C.c_void_p]
    lib.espeak_Synth.restype = C.c_int
    encoded = text.encode("utf-8") + b"\0"
    buffer = C.create_string_buffer(encoded)
    result = lib.espeak_Synth(buffer, len(encoded), 0, 0, 0, 1 << 8, None, None)
    if result != 0:
        raise RuntimeError(f"eSpeak NG synthesis failed: {result}")
    lib.espeak_Synchronize()
    pcm = b"".join(chunks)
    output.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(output), "wb") as file:
        file.setnchannels(1)
        file.setsampwidth(2)
        file.setframerate(sample_rate)
        file.writeframes(pcm)
    return len(pcm) / (2 * sample_rate)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("text")
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    print(f"{synthesize(args.text, args.output):.2f}s")
