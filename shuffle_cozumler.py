"""
cozumler.json'ı bir kez rastgele karıştır.
Bir kez çalıştırılır, sonuç repo'ya commit edilir.

Kullanım:
    python shuffle_cozumler.py
"""
import json
import random
import pathlib

path = pathlib.Path(__file__).parent / "cozumler.json"
words = json.loads(path.read_text(encoding="utf-8"))

onceki_ilk = words[:5]
random.shuffle(words)
sonraki_ilk = words[:5]

path.write_text(json.dumps(words, ensure_ascii=False, indent=2), encoding="utf-8")

print(f"{len(words)} kelime karıştırıldı.")
print(f"Önce ilk 5: {onceki_ilk}")
print(f"Sonra ilk 5: {sonraki_ilk}")
