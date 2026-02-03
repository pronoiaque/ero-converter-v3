# ERO Legacy Converter

<div align="center">

![Version](https://img.shields.io/badge/version-7.0-4a90d9?style=flat-square)
![Fix](https://img.shields.io/badge/fix-BOM_UTF8-57a85e?style=flat-square)
![Python](https://img.shields.io/badge/python-3.6%2B-f7c948?style=flat-square)
![Encoding](https://img.shields.io/badge/encoding-Latin--1-e07b54?style=flat-square)
![Status](https://img.shields.io/badge/status-Production-c0392b?style=flat-square&logo=&logoColor=white)

</div>

Pipeline de conversion entre fichiers CSV et le format binaire `.dat` utilisé par le logiciel ERO pour ses tables de catégories. La version 7 résout le problème de corruption silencieuse causé par le BOM UTF-8 présent dans les exports Excel et Notepad.

---

## Structure du dépôt

```
.
├── csv_to_dat_final_v7.py      # Génération : CSV → .dat
├── dat_to_csv_audit_v7.py      # Audit      : .dat → CSV
├── ANALYSIS.md                 # Analyse technique détaillée
├── README.md                   # Ce fichier
└── .gitignore
```

Les fichiers `.dat` et `.csv` générés sont exclus du dépôt par le `.gitignore` — ils sont des artefacts de build, pas des sources.

---

## Utilisation rapide

### Génération du fichier binaire

```bash
# Avec un fichier source explicite
python csv_to_dat_final_v7.py mon_fichier.csv

# Sans argument : cherche for_gemini.csv, puis categories_hd.csv
python csv_to_dat_final_v7.py
```

Sortie : `categori_corrected.dat` dans le répertoire courant.

### Audit de vérification

```bash
# Sur le fichier par défaut (categori_corrected.dat)
python dat_to_csv_audit_v7.py

# Sur un fichier arbitraire
python dat_to_csv_audit_v7.py chemin/vers/fichier.dat
```

Sortie : `export_audit_v7.csv`. Si un BOM résiduel est détecté dans l'en-tête du `.dat`, le script émet une alerte critique avant de poursuivre l'extraction.

---

## Format du fichier `.dat`

Le fichier respecte une cartographie mémoire stricte imposée par ERO. Tout décalage, même d'un octet, rend le fichier illisible.

| Zone | Offset | Taille | Contenu |
|:-----|-------:|-------:|:--------|
| Header | 0 | 16 o | Signature `ERO\0` + padding |
| Buffer | 16 | 36 o | Séquence réservée `<vide>` |
| Record 1 | **52** | 31 o | Premier enregistrement |
| Record 2 | 83 | 31 o | … |
| Record *n* | 52 + 31×(*n*−1) | 31 o | … |

Chaque enregistrement a la forme `[payload | \x00 | padding 0xCD]` sur exactement 31 octets, encodé en Latin-1. Le payload contient la concaténation `code texte` (max 30 octets).

> **Diagnostic rapide.** Si vous ouvrez un `.dat` dans un éditeur hexadécimal et que vous voyez `EF BB BF` juste avant l'offset 52, le fichier a été corrompu par un BOM. Régénérez-le avec cette version du script.

---

## Ce qui a changé en V7

Les versions V4–V6 lisaient le CSV en UTF-8 classique. Les éditeurs Windows insèrent régulièrement un BOM (`EF BB BF`) au début des fichiers ; ces trois octets se retrouvaient dans le premier enregistrement du `.dat` et cassaient toute la lecture.

V7 utilise l'encodage `utf-8-sig` fourni par Python, qui absorbe silencieusement le BOM s'il est présent et se comporte comme `utf-8` sinon. Aucune branche conditionnelle, aucun coût de performance.

---

## Analyse technique

La doc [ANALYSIS.md](ANALYSIS.md) détaille les décisions d'implémentation, les contraintes d'encodage, la logique de tronçage et les résultats de test.

---

## Avertissement

Ne modifiez jamais un fichier `.dat` ERO avec un éditeur de texte. Utilisez uniquement ces scripts pour la génération et la vérification.
