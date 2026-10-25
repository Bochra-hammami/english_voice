def nettoyer(mot):
    # "Okay," -> "okay"   (minuscules, sans ponctuation)
    return mot.lower().strip(".,!?-")

def mots_valides(precedent, actuel):
    # Renvoie les mots du début qui sont identiques dans les deux listes
    resultat = []
    for mot1, mot2 in zip(precedent, actuel):
        if nettoyer(mot1) == nettoyer(mot2):
            resultat.append(mot2)
        else:
            break
    return resultat
