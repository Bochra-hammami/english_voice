"""Interface fichier : dépose un vocal -> il se joue et le texte apparaît en direct."""
import gradio as gr
from app.asr import simuler_direct
from app.metriques import wer

EXPLICATIONS = """
### 📖 Que mesurent les métriques ?

| Métrique | Ce qu'elle mesure | Bon résultat |
|---|---|---|
| **Durée de la parole** | Combien de temps dure le vocal. | — |
| **Latence (par phrase)** | Temps entre le moment où la personne **finit de dire** une phrase et le moment où elle **apparaît à l'écran**. C'est le retard que ressentirait l'autre personne dans Meet. | < 2 s |
| **Latence moyenne / max** | La moyenne de toutes les latences, et la pire. Le max montre les moments où le système « décroche ». | moy < 2 s, max < 4 s |
| **Délai après la fin** | Après que la personne s'est tue, combien de temps il faut pour voir la dernière phrase. | < 2 s |
| **Phrases** | Combien de morceaux le système a découpés (il coupe à chaque pause). Beaucoup de petits morceaux = parole hésitante ou coupures trop fréquentes. | — |
| **WER** (*Word Error Rate*) | Pourcentage de **mots faux** par rapport au texte de référence : mots remplacés, oubliés ou ajoutés, divisés par le nombre de mots attendus. Exemple : 7 erreurs sur 70 mots = 10 %. Calculé seulement si tu colles le texte de référence. | < 10 % |
"""


def analyser(chemin_audio, reference):
    if not chemin_audio:
        yield None, "Dépose d'abord un fichier audio.", ""
        return

    yield chemin_audio, "", "⏳ Écoute en cours…"   # lance la lecture du son

    lignes, latences, textes = [], [], []
    instant, duree_audio = 0.0, 0.0
    for phrase, instant, duree_audio in simuler_direct(chemin_audio):
        latence = instant - phrase.fin
        latences.append(latence)
        textes.append(phrase.texte)
        lignes.append(f"[{instant:5.1f}s] {phrase.texte}    (latence {latence:.1f}s)")
        yield gr.update(), "\n".join(lignes), "⏳ Écoute en cours…"

    resume = [f"Durée de la parole        : {duree_audio:.1f} s",
              f"Latence moyenne / max     : {sum(latences)/max(len(latences), 1):.1f} s / {max(latences, default=0):.1f} s",
              f"Délai après la fin        : {max(instant - duree_audio, 0):.1f} s",
              f"Phrases                   : {len(textes)}"]
    if reference and reference.strip():
        resume.append(f"WER                       : {wer(reference, ' '.join(textes)):.1%}")
    yield gr.update(), "\n".join(lignes), "\n".join(resume)


with gr.Blocks(title="English Voice") as demo:
    gr.Markdown("# English Voice : test en direct sur un vocal")
    with gr.Row():
        entree = gr.Audio(type="filepath", label="Glisse un vocal ici (mp3, wav)")
        reference = gr.Textbox(label="Texte de référence (optionnel, pour le WER)", lines=5)
    bouton = gr.Button("▶ Lancer", variant="primary")
    lecture = gr.Audio(label="Lecture", autoplay=True, interactive=False)
    texte = gr.Textbox(label="Texte en direct", lines=10)
    metriques = gr.Textbox(label="Métriques", lines=6)
    gr.Markdown(EXPLICATIONS)

    bouton.click(analyser, inputs=[entree, reference], outputs=[lecture, texte, metriques])

if __name__ == "__main__":
    demo.launch()