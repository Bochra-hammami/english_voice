"""Métriques de qualité et de vitesse, partagées par l'app et les outils."""
import jiwer

_nettoyer = jiwer.Compose([jiwer.ToLowerCase(), jiwer.RemovePunctuation(),
                           jiwer.SubstituteWords({"6": "six", "5": "five", "3": "three"}),
                           jiwer.RemoveMultipleSpaces(), jiwer.Strip()])


def wer(reference: str, texte: str) -> float:
    """Pourcentage de mots faux (0.0 = parfait)."""
    return jiwer.wer(_nettoyer(" ".join(reference.split())), _nettoyer(texte))


def rtf(duree_calcul: float, duree_audio: float) -> float:
    """Temps de calcul / durée audio (< 1 = plus rapide que le temps réel)."""
    return duree_calcul / duree_audio if duree_audio else 0.0