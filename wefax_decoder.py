import numpy as np
from scipy import signal
from scipy.io import wavfile
from PIL import Image
import math

def decode_wefax_wav(wav_path: str, out_path: str = None, force_square: bool = True) -> Image.Image:
    """
    Decode a WeFAX WAV file into a PIL Image.
    Returns the image and optionally saves it.
    """
    sr, samples = wavfile.read(wav_path)
    if samples.ndim > 1:
        samples = samples[:, 0]        
    samples = samples.astype(np.float32)
    samples /= np.max(np.abs(samples) + 1e-9)
    b, a = signal.butter(4, [1000, 2800], btype="band", fs=sr)
    samples = signal.filtfilt(b, a, samples)
    analytic = signal.hilbert(samples)
    phase = np.unwrap(np.angle(analytic))
    freq = np.diff(phase) * (sr / (2 * np.pi))
    freq = np.concatenate(([freq[0]], freq))
    black, white = 1500.0, 2300.0
    pixels = np.clip((freq - black) / (white - black), 0, 1)
    pixels = (pixels * 255).astype(np.uint8)
    samples_per_line = int(sr * 0.5)
    n_lines = len(pixels) // samples_per_line
    if n_lines < 10:
        raise ValueError("Audio too short or not a WeFAX signal")

    img_data = pixels[: n_lines * samples_per_line].reshape(n_lines, samples_per_line)
    if force_square:
        side = max(img_data.shape)
        img = Image.fromarray(img_data).resize((side, side), Image.Resampling.LANCZOS)
    else:
        img = Image.fromarray(img_data)

    if out_path:
        img.save(out_path)
    return img
