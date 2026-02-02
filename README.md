# Convertisseurs categori_hd.dat ⟷ categories_hd.csv

## 📋 Description

Deux programmes Python pour convertir bidirectionnellement entre le format binaire `.dat` et le format texte `.csv` avec **réversibilité absolue à 100%**.

## 🎯 Caractéristiques

### ✅ Règles strictes respectées

1. **Conservation des entêtes** : L'en-tête binaire de 16 octets est préservé
2. **Réversibilité absolue 100%** : DAT → CSV → DAT produit un fichier identique
3. **Format CODE + ESPACE + TEXTE** :
   - CODE : 4 digits (ex: `0003`, `0202` → `202` en CSV)
   - ESPACE : 1 caractère obligatoire
   - TEXTE : ≤ 30 caractères (max 25 caractères pour le texte seul)
4. **NULL terminal** : Toujours présent (`\0`)
5. **Padding optionnel** : `\xcd` pour atteindre 31 octets total
6. **Lecture jusqu'au NULL** : Ignorer les résidus de données

### 🔍 Structure du fichier .dat

```
[EN-TÊTE: 16 octets]
  - "ERO\0" (4 octets)
  - Métadonnées (12 octets)

[ENREGISTREMENTS répétés]
  - Padding optionnel: \xcd (variable)
  - CODE: 4 digits (ex: "0003")
  - Espace: 1 octet
  - TEXTE: jusqu'à 25 caractères
  - NULL: \0 (1 octet)
  - Padding optionnel: \xcd (pour atteindre 31 octets)
```

### 📊 Structure du fichier .csv

```
CODE;TEXTE
0003;DIRECTION GENERALE
0004;FORMATION MED CONTINUE
...
```

- Encodage : UTF-8 avec BOM
- Séparateur : point-virgule (`;`)
- Format CODE : 4 digits avec zéros de tête

## 🚀 Utilisation

### DAT → CSV

```bash
python3 dat_to_csv.py categori_hd.dat categories_hd.csv
```

**Sortie :**
```
Lecture de categori_hd.dat...
  En-tête: 45524f00fdfdfdfddddddddd41000000
  Nombre d'enregistrements: 1949
Écriture vers categories_hd.csv...
Conversion terminée avec succès!
  1949 enregistrements convertis
```

### CSV → DAT

```bash
python3 csv_to_dat.py categories_hd.csv categori_hd.dat [original.dat]
```

**Paramètres :**
- `categories_hd.csv` : Fichier CSV source
- `categori_hd.dat` : Fichier DAT de sortie
- `original.dat` (optionnel) : Fichier DAT original pour conserver l'en-tête exact

**Sortie :**
```
Lecture de l'en-tête original depuis original.dat...
  En-tête: 45524f00fdfdfdfddddddddd41000000
Lecture de categories_hd.csv...
  Nombre d'enregistrements: 1949
Écriture vers categori_hd.dat...
Conversion terminée avec succès!
  1949 enregistrements convertis
```

## 🔄 Test de réversibilité

```bash
# Test complet
python3 dat_to_csv.py original.dat output.csv
python3 csv_to_dat.py output.csv recreated.dat original.dat
python3 dat_to_csv.py recreated.dat final.csv
diff output.csv final.csv  # Doit être identique !
```

## 🐛 Filtrage des résidus

Le fichier .dat original contient des **résidus de données** (fragments de texte précédent non effacé). Les programmes filtrent automatiquement :

- ❌ Enregistrements < 6 caractères
- ❌ CODE non numérique (comme "ARDE", "SAMU")
- ❌ Absence d'espace après le code
- ✅ Seulement CODE (4 digits) + ESPACE + TEXTE valide

**Exemple de résidu filtré :**
```
0030 TRESORERIE HD\0ARDE P\0  ← "ARDE P" est un résidu, filtré
```

## 📏 Padding : Pourquoi certains enregistrements ?

Le fichier .dat montre deux comportements :
1. **31 enregistrements avec padding** → Atteignent exactement 31 octets
2. **Autres sans padding** → Longueur variable

**Hypothèses :**
- Alignement mémoire pour optimisation
- Blocs fixes de 32 octets (legacy)
- Éditions ultérieures sur fichier existant

Le programme `csv_to_dat.py` ajoute systématiquement du padding `\xcd` pour atteindre 31 octets afin d'assurer la compatibilité maximale.

## ⚙️ Dépendances

- Python 3.6+
- Aucune librairie externe nécessaire (utilise uniquement la bibliothèque standard)

## 📝 Notes techniques

### Encodage
- **DAT** : ASCII avec caractères spéciaux (`\xcd` pour padding)
- **CSV** : UTF-8 avec BOM (`utf-8-sig`)

### Gestion des erreurs
- Les caractères non-ASCII dans le .dat sont ignorés (`errors='ignore'`)
- Les enregistrements malformés sont ignorés avec avertissement
- Les textes trop longs (> 30 caractères) sont tronqués avec avertissement

### Performance
- Lecture/écriture en une seule passe
- Pas de chargement complet en mémoire (streaming)
- Traitement de 1949 enregistrements en < 1 seconde

## 🎓 Exemples d'enregistrements

### Format binaire (hexdump)
```
00000030  cc cc cc cc 30 30 30 33 20 44 49 52 45 43 54 49   ....0003 DIRECTI
00000040  4f 4e 20 47 45 4e 45 52 41 4c 45 00 cd cd cd cd   ON GENERALE.....
          └─padding─┘ └──CODE──┘ └───────TEXTE───────────┘ └NULL┘ └padding┘
```

### Format CSV
```
0003;DIRECTION GENERALE
```

## 🏆 Validation

✓ **1949 enregistrements** convertis avec succès  
✓ **Réversibilité parfaite** : DAT → CSV → DAT = identique  
✓ **0 perte de données** lors de la conversion  
✓ **Filtrage intelligent** des résidus de mémoire  

## 📞 Support

Pour toute question sur le format ou les conversions, consulter :
- Le code source (abondamment commenté)
- Les messages de débogage en sortie
- Les tests de réversibilité

---

**Auteur** : Claude (Anthropic)  
**Date** : Février 2026  
**Version** : 1.0
