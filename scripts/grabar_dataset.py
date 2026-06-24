import sys
import os
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

SAMPLE_RATE = 16000
DURATION = 2
OUTPUT_DIR = Path("grabraciones")
N_POSITIVAS = 20
N_NEGATIVAS = 10

NEGATIVE_PHRASES = [
    "hola", "música", "asistente", "silencio", "¿qué hora es?",
    "adiós", "gracias", "no", "sí", "computador",
    "volumen", "luz", "temperatura", "puerta", "ventana",
]


def grabar(filename: str, instruccion: str) -> bool:
    import sounddevice as sd
    import numpy as np
    import wave

    input(f"\n{instruccion}\nPresiona Enter y habla... ")
    print("Grabando...", end=" ", flush=True)
    audio = sd.rec(int(DURATION * SAMPLE_RATE), SAMPLE_RATE, 1, "int16", blocking=True)
    rms = np.sqrt(np.mean(audio.astype(np.float32) ** 2))
    print(f"Hecho. RMS={rms:.1f}")
    if rms < 50:
        print("  ⚠ Muy bajo, repite")
        return False
    output_path = OUTPUT_DIR / filename
    with wave.open(str(output_path), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SAMPLE_RATE)
        w.writeframes(audio.tobytes())
    print(f"  Guardado: {output_path}")
    return True


def main():
    import textwrap

    print(textwrap.dedent("""\
    ═══════════════════════════════════════════
       GRABACION DE DATASET - WakeWord
    ═══════════════════════════════════════════

    Grabaremos:
      • 20 muestras POSITIVAS: di "servidor"
      • 10 muestras NEGATIVAS: otras palabras

    Tips:
      • Habla a volumen normal
      • Espera el "Presiona Enter" antes de hablar
      • Si el RMS sale < 50, repite la muestra
    """))

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    print("━" * 45)
    print("  FASE 1: MUESTRAS POSITIVAS (servidor)")
    print("━" * 45)

    ok = 0
    intentos = 0
    while ok < N_POSITIVAS and intentos < N_POSITIVAS + 10:
        intentos += 1
        if grabar(f"positivo_{ok+1:02d}.wav",
                   f"[{ok+1}/{N_POSITIVAS}] Di SERVICOR:"):
            ok += 1

    print(f"\nPositivas grabadas: {ok}")

    if ok == 0:
        print("ERROR: No se grabo ninguna positiva. Revisa el microfono.")
        sys.exit(1)

    print("\n" + "━" * 45)
    print("  FASE 2: MUESTRAS NEGATIVAS")
    print("━" * 45)

    ok = 0
    for i, frase in enumerate(NEGATIVE_PHRASES[:N_NEGATIVAS]):
        if grabar(f"negativo_{i+1:02d}.wav",
                   f"[{i+1}/{N_NEGATIVAS}] Di: \"{frase}\":"):
            ok += 1

    print(f"\nNegativas grabadas: {ok}")

    print("\n" + "═" * 45)
    print("  GRABACION COMPLETADA")
    print("═" * 45)
    print(f"  Positivas: {sum(1 for f in OUTPUT_DIR.glob('positivo_*.wav'))}")
    print(f"  Negativas: {sum(1 for f in OUTPUT_DIR.glob('negativo_*.wav'))}")
    print(f"\n  Directorio: {OUTPUT_DIR.resolve()}")
    print("\n  Siguiente paso:")
    print("    uv run python scripts/entrenar_voz.py")


if __name__ == "__main__":
    main()
