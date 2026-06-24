import json
import pickle
import sys
import os
import warnings
from pathlib import Path

import numpy as np

warnings.filterwarnings("ignore")

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

SAMPLE_RATE = 16000
MIN_SAMPLES = SAMPLE_RATE * 3
OUTPUT_DIR = Path("models/wakeword")
OUTPUT_MODEL = OUTPUT_DIR / "servidor_voz.pkl"


def cargar_wavs(data_dir: Path):
    positivos = sorted(data_dir.glob("positivo_*.wav"))
    negativos = sorted(data_dir.glob("negativo_*.wav"))
    print(f"WAVs encontrados: {len(positivos)} positivos, {len(negativos)} negativos")
    return positivos, negativos


def leer_wav(path: Path):
    import wave
    with wave.open(str(path), "rb") as w:
        assert w.getnchannels() == 1
        assert w.getsampwidth() == 2
        frames = w.readframes(w.getnframes())
    data = np.frombuffer(frames, dtype=np.int16)
    return data


def get_embedding(data, fe):
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


def main():
    from tqdm import tqdm
    from openwakeword.utils import AudioFeatures

    print("═" * 50)
    print("  ENTRENAMIENTO WAKEWORD CON VOZ REAL")
    print("═" * 50)

    data_dir = Path("grabraciones")
    if not data_dir.exists():
        print(f"ERROR: No existe el directorio {data_dir}")
        print("Primero corre: uv run python scripts/grabar_dataset.py")
        sys.exit(1)

    positivos, negativos = cargar_wavs(data_dir)

    if len(positivos) < 5:
        print("ERROR: Muy pocas muestras positivas (min 5)")
        sys.exit(1)
    if len(negativos) < 3:
        print("ERROR: Muy pocas muestras negativas (min 3)")
        sys.exit(1)

    print("\n[1/2] Extrayendo embeddings...")
    fe = AudioFeatures()
    X, y = [], []

    for path in tqdm(positivos, desc="Positivas"):
        data = leer_wav(path)
        emb = get_embedding(data, fe)
        if emb is not None:
            X.append(emb)
            y.append(1)

    for path in tqdm(negativos, desc="Negativas"):
        data = leer_wav(path)
        emb = get_embedding(data, fe)
        if emb is not None:
            X.append(emb)
            y.append(0)

    if len(X) < 8:
        print("ERROR: Muy pocas muestras con embedding valido")
        sys.exit(1)

    X = np.array(X)
    y = np.array(y)
    print(f"\n  Embedding dim: {X.shape[1]}")
    print(f"  Total: {len(X)}  Positivos: {y.sum()}  Negativos: {len(y)-y.sum()}")

    print("\n[2/2] Entrenando clasificador...")
    from sklearn.ensemble import RandomForestClassifier

    rf = RandomForestClassifier(
        n_estimators=200, max_depth=16,
        class_weight="balanced", random_state=42,
        n_jobs=-1, verbose=0
    )
    rf.fit(X, y)

    probas = rf.predict_proba(X)
    pos_scores = probas[y == 1][:, 1]
    neg_scores = probas[y == 0][:, 1]

    print(f"\n  Train accuracy: {rf.score(X, y):.3f}")
    print(f"  Score medio positivo: {pos_scores.mean():.3f}")
    print(f"  Score minimo positivo: {pos_scores.min():.3f}")
    print(f"  Score medio negativo: {neg_scores.mean():.3f}")
    print(f"  Score max negativo: {neg_scores.max():.3f}")

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_MODEL, "wb") as f:
        pickle.dump(rf, f)
    print(f"\nModelo guardado: {OUTPUT_MODEL}")

    metadata = {
        "wake_word": "servidor",
        "embedding_dim": int(X.shape[1]),
        "train_samples": int(len(X)),
        "train_accuracy": float(rf.score(X, y)),
        "mean_pos_score": float(pos_scores.mean()),
        "min_pos_score": float(pos_scores.min()),
        "mean_neg_score": float(neg_scores.mean()),
        "max_neg_score": float(neg_scores.max()),
    }
    meta_path = OUTPUT_DIR / "servidor_voz.json"
    with open(meta_path, "w") as f:
        json.dump(metadata, f, indent=2)
    print(f"Metadata: {meta_path}")

    print("\nPara probar:")
    print("  cd clock_sv && ./run.sh")
    print(f"\n(El modelo se carga automaticamente si existe)")
    print(f"Si quieres usar el modelo entrenado, ajusta el threshold en")
    print(f"config/settings.yaml > wake_word.threshold (ej: 50-70)")


if __name__ == "__main__":
    main()
