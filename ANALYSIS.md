# ERO Legacy Converter v7 — Analyse Technique

> **Périmètre.** Ce document décrit la conception, les contraintes d'encodage et les décisions d'implémentation des deux scripts qui composent le pipeline de conversion ERO v7. Il est destiné à servir de référence pour tout contributeur ou mainteneur futur.

---

## 1. Contexte et objectif

Le système ERO charge ses tables de catégories depuis un fichier binaire `.dat` à la structure très rigide : un en-tête de 52 octets suivi d'enregistrements de exactement 31 octets chacun, encodés en Latin-1. Toute erreur de taille ou d'encodage dans ce fichier se traduit par un décalage silencieux qui rend l'ensemble du fichier illisible pour le logiciel.

Le rôle de ces deux scripts est simple : `csv_to_dat_final_v7.py` convertit une source CSV en fichier binaire conforme, et `dat_to_csv_audit_v7.py` permet de vérifier a posteriori que la conversion s'est déroulée sans artifact.

---

## 2. Le problème du BOM — pourquoi une version 7

Les versions précédentes (V4–V6) lisaient le CSV en UTF-8 standard. Or, les éditeurs Windows courants — Excel, Notepad — insèrent régulièrement une signature invisible au début des fichiers UTF-8 : le **Byte Order Mark**, trois octets `EF BB BF`. Ces octets se retrouvaient dans le premier enregistrement du `.dat`, qui devenait `ï»¿0000` au lieu de `0000`. Le décalage cassait toute la lecture séquentielle.

La solution choisie en V7 est de lire le CSV avec l'encodage `utf-8-sig`. Cet encodage, fourni nativement par Python, absorbe silencieusement le BOM s'il est présent et se comporte exactement comme `utf-8` sinon. Il n'y a donc aucun coût de performance et aucune branche conditionnelle dans le chemin principal. Un fallback vers `latin-1` existe en cas de `UnicodeDecodeError`, ce qui couvre les rares fichiers source purely ANSI.

---

## 3. Structure binaire du fichier `.dat`

Le fichier respecte la cartographie suivante, validée par les tests de régression :

```
Offset    Taille    Zone
─────────────────────────────────────
  0        16       Header — Signature ERO
 16        36       Buffer — Séquence technique
 52         —       Début des enregistrements
```

**Header (16 octets).** La séquence `45 52 4F 00` correspond à la chaîne ASCII `ERO\0`. Les 12 octets suivants sont un bloc de padding et un terminateur définis par le format du logiciel. Cette zone n'est jamais modifiée par les scripts.

**Buffer (36 octets).** Contient la chaîne ASCII `<vide>` précédée d'un préfixe de 5 octets et suivie de 24 octets de remplissage `0xCC`. Cette zone constitue un placeholder réservé par ERO ; elle doit être présente mais son contenu n'est pas interprété comme un enregistrement de données.

**Enregistrements (31 octets chacun).** C'est la zone active. Chaque bloc a la forme suivante :

```
[ payload … | \x00 | padding 0xCD … ]
  ≤ 30 octets   1 octet   complète à 31
```

Le payload est la concaténation `code texte` encodée en Latin-1, tronquée à 30 octets si nécessaire. Le terminateur `\x00` sépare le contenu du padding. Le padding `0xCD` remplit le reste du bloc pour atteindre exactement 31 octets. Cette valeur n'a pas de signification sémantique ; elle est choisie pour être facilement identifiable dans un éditeur hexadécimal lors du débogage.

---

## 4. Décisions d'implémentation

**Encodage source → cible.** Le CSV entre en UTF-8 (avec ou sans BOM) ; le `.dat` sort en Latin-1. Le trajet `utf-8-sig → str Python → latin-1` garantit que les caractères accentués courants du français (é, è, à, ù, ç) sont correctement transposés sans passage par une étape intermédiaire. L'option `errors='replace'` est activée sur l'encodage sortant pour éviter un crash si un caractère hors Latin-1 (par exemple un emoji) se retrouve dans le CSV ; le caractère est alors remplacé par `?`, ce qui est préférable à une interruption silencieuse du pipeline.

**Tronçage du payload.** Le payload est tronqué à 30 octets *après* l'encodage en Latin-1, pas avant. C'est un détail important : en Latin-1, chaque caractère accentué fait exactement 1 octet (contrairement à UTF-8 où il en ferait 2), donc le tronçage sur les octets encodés correspond exactement au tronçage sur les caractères visibles. Il n'y a pas de risque de couper au milieu d'un caractère multi-octets.

**Garantie de taille du bloc.** Une vérification finale (`if len(final_block) != BLOCK_SIZE`) existe comme filet de sécurité. Dans la pratique elle ne devrait jamais se déclencher — la construction `payload + \x00 + padding` produit exactement 31 octets par construction — mais elle coûte un seul `len()` et élimine toute possibilité de corruption silencieuse si la logique de padding est un jour modifiée.

**Séparation code/texte à la lecture.** Le script d'audit reconstruit les deux champs en splitant sur le premier espace. Cette approche suppose que le code ne contient jamais d'espace, ce qui est cohérent avec le format ERO (codes numériques à 4 chiffres). Si cette hypothèse devait changer, le point de découpage devrait être renforcé — par exemple en fixant la largeur du code à 4 caractères.

---

## 5. Tests effectués

Les deux scripts ont été testés en pipeline complet sur une source CSV comportant un BOM explicite (`EF BB BF`) afin de reproduire exactement le scénario qui cassait les versions précédentes.

**Génération.** Le fichier `.dat` produit par la version réécrite est identique octet par octet à celui produit par l'originale sur la même entrée. Aucune régression.

**Round-trip.** Le CSV extrait par le script d'audit sur le `.dat` généré correspond exactement aux données source, sans BOM résiduel, sans caractère parasite sur la première ligne.

**Alerte BOM.** Un fichier `.dat` délibérément corrompu (BOM inséré à l'offset 10, dans la zone header) déclenche correctement le message `ALERTE CRITIQUE` du script d'audit. Le mécanisme de détection fonctionne comme prévu.

---

## 6. Limitations connues

Le format Latin-1 exclut nativement les caractères hors Western-European. Tout caractère Unicode qui n'a pas d'équivalent Latin-1 sera silencieusement remplacé par `?` lors de la génération. Si le jeu de données devait évoluer vers un support multilingue plus large, l'encodage cible devrait être renegocié avec le logiciel ERO en amont.

La largeur du bloc (31 octets) et l'offset de départ (52) sont des constantes imposées par le format du logiciel. Elles ne sont pas configurables et ne doivent pas être modifiées sans validation de la part du système cible.
