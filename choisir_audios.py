import csv
import shutil
from pathlib import Path

# ⚠️ À adapter : le dossier où tu as extrait le zip
DOSSIER = Path(r"C:\Users\user\Desktop\projects\archive")

SORTIE = Path("audios")
SORTIE.mkdir(exist_ok=True)

indiens, uk = [], []
with open(DOSSIER / "speakers_all.csv", encoding="utf-8") as f:
    for ligne in csv.DictReader(f):
        if ligne["file_missing?"] == "TRUE":      # audio absent -> on ignore
            continue
        if ligne["country"] == "india":
            try:
                age = float(ligne["age_onset"])
            except ValueError:
                continue                     # age missing -> skip
            indiens.append((age, ligne["filename"]))
        elif ligne["country"] == "uk" and ligne["native_language"] == "english":
            uk.append(ligne["filename"])

print(f"Trouvés : {len(indiens)} indiens, {len(uk)} UK")
indiens.sort(reverse=True)                   # latest learners first = stronger accent
print("Top 10 indiens (age_onset, fichier) :", indiens[:10])
indiens = [nom for _, nom in indiens]
def copier(noms, prefixe):
    for i, nom in enumerate(noms[:3], start=1):
        source = next(DOSSIER.rglob(f"{nom}.mp3"), None)   # cherche le fichier dans les sous-dossiers
        if source:
            shutil.copy(source, SORTIE / f"{prefixe}_{i}_{nom}.mp3")
            print(f"Copié : {prefixe}_{i}_{nom}.mp3")
        else:
            print(f"Introuvable : {nom}.mp3")

copier(indiens, "indien")
copier(uk, "uk")

# Copie aussi le texte de référence
shutil.copy(DOSSIER / "reading-passage.txt", SORTIE / "reference.txt")