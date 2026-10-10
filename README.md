# Analyse descriptive de la drépanocytose à Kinshasa

Travail de fin de stage — Université de Kinshasa, Faculté des Sciences et Technologies,
Département de Mathématiques, Statistique et Informatique.

**Auteurs :** Jemima SENKERE AFIDOU, Jean-Christophe WIZAMO BILIKO, Don de Dieu MAKILA LUKIAN

## Objet du travail

Ce dépôt contient l'analyse d'une base de données synthétique de 1 200 patients
drépanocytaires à Kinshasa (19 variables). Le travail répond à deux questions :

1. **Exploration et préparation des données** : nature des variables, valeurs manquantes,
   doublons, valeurs aberrantes et nettoyage.
2. **Analyse statistique descriptive** : moyenne, médiane, minimum, maximum, variance et
   écart-type ; histogrammes ; nuages de points ; matrice de corrélation.

Les données sont fictives et produites pour l'exercice ; elles ne représentent pas la
population réelle de Kinshasa.

## Contenu du dépôt

| Élément | Description |
|---|---|
| `analyse_drepanocytose.py` | Script Python qui réalise toute l'analyse |
| `data/Drepanocytose_Kinshasa.xlsx` | Base de données d'origine |
| `data/Drepanocytose_Kinshasa_nettoyee.xlsx` | Base après nettoyage (valeurs manquantes imputées) |
| `figures/` | Graphiques du rapport (PDF et PNG) |
| `tables/` | Tableaux de résultats (CSV) |
| `requirements.txt` | Bibliothèques Python nécessaires |

## Reproduire l'analyse

Il faut Python 3.10 ou plus récent.

```bash
pip install -r requirements.txt
python analyse_drepanocytose.py
```

Le script lit `data/Drepanocytose_Kinshasa.xlsx`, puis régénère la base nettoyée,
tous les graphiques du dossier `figures/` et tous les tableaux du dossier `tables/`.

## Choix de nettoyage

- Aucun doublon n'a été trouvé.
- Les valeurs extrêmes ont été conservées, car elles sont toutes plausibles sur le plan clinique.
- Les 182 valeurs manquantes (moins de 2,5 % par variable) ont été remplacées par la médiane
  du génotype du patient. Une colonne `Donnee_imputee` signale les patients concernés.
