import numpy as np, scipy.io.wavfile as w
def read(fn):
    sr, x = w.read(fn)
    if x.dtype == np.int16: x = x.astype(np.float64) / 32768
    elif x.dtype == np.int32: x = x.astype(np.float64) / 2**31
    else: x = x.astype(np.float64)
    if x.ndim > 1: x = x.mean(1)
    return x, sr
def write(fn, x, sr):
    w.write(fn, sr, (np.clip(x, -1, 1) * 32767).astype(np.int16))
