import io
import json
import struct
import sys
import os
import pickle
import warnings
from pathlib import Path

import numpy as np

warnings.filterwarnings("ignore")

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

PIPER_MODEL = "models/piper/es_ES-carlfm-x_low.onnx"
OUTPUT_DIR = Path("models/wakeword")
OUTPUT_MODEL = OUTPUT_DIR / "servidor_v0.1.pkl"
TARGET = "servidor"
SAMPLE_RATE = 16000
NEGATIVE_PHRASES = [
    "hola", "adiós", "buenos días", "gracias", "por favor",
    "sí", "no", "quizás", "nunca", "siempre",
    "inteligente", "asistente", "computador", "música", "volumen",
    "luz", "puerta", "ventana", "cocina", "baño",
    "uno", "dos", "tres", "cuatro", "cinco",
    "rojo", "azul", "verde", "blanco", "negro",
    "ayer", "hoy", "mañana", "temprano", "tarde",
    "arriba", "abajo", "dentro", "fuera", "cerca",
    "agua", "fuego", "tierra", "aire", "sol",
    "casa", "coche", "tren", "avión", "barco",
    "feliz", "triste", "enojado", "cansado", "contento",
    "maestro", "escuela", "libro", "pluma", "papel",
    "antes", "después", "pronto", "luego", "ahora",
]


def generate_samples(tts, phrases, n_variations=5):
    samples = []
    for phrase in phrases:
        for _ in range(n_variations):
            audio = tts.synthesize(phrase)
            if len(audio) < 256:
                continue
            wav = _make_wav(audio)
            samples.append((wav, phrase))
    return samples


def _make_wav(raw_audio: bytes) -> bytes:
    data_size = len(raw_audio)
    wav_header = (
        b"RIFF"
        + struct.pack("<I", 36 + data_size)
        + b"WAVE"
        + b"fmt "
        + struct.pack("<I", 16)
        + struct.pack("<HHIIHH", 1, 1, SAMPLE_RATE, SAMPLE_RATE * 2, 2, 16)
        + b"data"
        + struct.pack("<I", data_size)
        + raw_audio
    )
    return wav_header


def main():
    from tqdm import tqdm
    import scipy.io.wavfile as wavfile
    from openwakeword.utils import AudioFeatures

    print("[1/4] Cargando Piper TTS...")
    from src.services.tts_piper import PiperTTS
    tts = PiperTTS(PIPER_MODEL)
    print(f"  TTS OK: sample_rate={tts.sample_rate}")

    print("[2/4] Generando muestras sinteticas...")
    pos_samples = generate_samples(tts, [TARGET], n_variations=1000)
    neg_samples = generate_samples(tts, NEGATIVE_PHRASES, n_variations=3)
    print(f"  Positivas: {len(pos_samples)}, Negativas: {len(neg_samples)}")

    print("[3/4] Extrayendo embeddings con openWakeWord...")
    X, y = [], []
    MIN_SAMPLES = SAMPLE_RATE * 3
    fe = AudioFeatures()

    def get_embedding(data):
        if len(data.shape) > 1:
            data = data[:, 0]
        if len(data) >= MIN_SAMPLES:
            data = data[-MIN_SAMPLES:]
        else:
            data = np.pad(data, (MIN_SAMPLES - len(data), 0))
        emb = fe._get_embeddings(data)
        if emb is None or emb.size == 0:
            return None
        return emb.flatten()

    for wav, phrase in tqdm(pos_samples, desc="Positivas"):
        sr, data = wavfile.read(io.BytesIO(wav))
        emb = get_embedding(data)
        if emb is not None:
            X.append(emb)
            y.append(1)

    for wav, phrase in tqdm(neg_samples, desc="Negativas"):
        sr, data = wavfile.read(io.BytesIO(wav))
        emb = get_embedding(data)
        if emb is not None:
            X.append(emb)
            y.append(0)

    X = np.array(X)
    y = np.array(y)
    print(f"  Embedding dim: {X.shape[1]}")
    print(f"  Total ejemplos: {len(X)}, positivos: {y.sum()}, negativos: {len(y)-y.sum()}")

    print("[4/4] Entrenando clasificador...")
    from sklearn.ensemble import RandomForestClassifier
    rf = RandomForestClassifier(
        n_estimators=200, max_depth=16,
        class_weight="balanced", random_state=42,
        n_jobs=-1, verbose=0
    )
    rf.fit(X, y)
    train_score = rf.score(X, y)
    probas = rf.predict_proba(X)
    pos_scores = probas[y == 1][:, 1]
    neg_scores = probas[y == 0][:, 1]
    print(f"  Train accuracy: {train_score:.3f}")
    print(f"  Score medio positivo: {pos_scores.mean():.3f}")
    print(f"  Score medio negativo: {neg_scores.mean():.3f}")
    print(f"  Score max negativo: {neg_scores.max():.3f}")

    output_dir = Path(OUTPUT_MODEL).parent
    output_dir.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_MODEL, "wb") as f:
        pickle.dump(rf, f)
    print(f"\nModelo guardado: {OUTPUT_MODEL}")

    metadata = {
        "wake_word": TARGET,
        "embedding_dim": X.shape[1],
        "n_estimators": 200,
        "train_samples": int(len(X)),
        "train_accuracy": float(train_score),
        "mean_pos_score": float(pos_scores.mean()),
        "mean_neg_score": float(neg_scores.mean()),
        "max_neg_score": float(neg_scores.max()),
    }
    with open(OUTPUT_DIR / "servidor_v0.1.json", "w") as f:
        json.dump(metadata, f, indent=2)
    print(f"Metadata guardada")


if __name__ == "__main__":
    main()
