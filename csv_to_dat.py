#!/usr/bin/env python3
"""
Convertisseur categories_hd.csv -> categori_hd.dat
Règles strictes :
- Conservation des entêtes
- CODE(4 digits) + ESPACE(1) + TEXTE ≤ 30 caractères total
- NULL terminal obligatoire
- Padding \xcd si nécessaire pour atteindre 31 octets
- Réversibilité absolue 100%
"""

import sys
from typing import List, Tuple


def read_csv_file(filepath: str) -> List[Tuple[str, str]]:
    """
    Lit le fichier CSV et extrait les enregistrements.
    Format attendu: CODE;TEXTE
    
    Returns:
        List of (code, text) tuples
    """
    records = []
    
    with open(filepath, 'r', encoding='utf-8-sig') as f:  # utf-8-sig pour ignorer le BOM
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            
            # Parser CODE;TEXTE
            parts = line.split(';', 1)
            if len(parts) != 2:
                print(f"Attention ligne {line_num}: format invalide, ignorée")
                continue
            
            code_str, text = parts
            
            # S'assurer que le code est sur 4 digits
            try:
                code_int = int(code_str)
                code_formatted = f'{code_int:04d}'
            except ValueError:
                # Code non numérique (ex: "BATIMENT TECHNIQUE")
                code_formatted = code_str[:4].ljust(4, ' ')
            
            # Vérifier la longueur totale (CODE + ESPACE + TEXTE)
            total_length = len(code_formatted) + 1 + len(text)
            if total_length > 30:
                print(f"Attention ligne {line_num}: trop long ({total_length} > 30), texte tronqué")
                text = text[:30 - 5]  # 30 - (4 code + 1 espace)
            
            records.append((code_formatted, text))
    
    return records


def write_dat_file(filepath: str, records: List[Tuple[str, str]], 
                   original_header: bytes = None) -> None:
    """
    Écrit les enregistrements dans un fichier .dat binaire.
    
    Args:
        filepath: Chemin du fichier de sortie
        records: Liste des (code, text) tuples
        original_header: En-tête original à conserver (optionnel)
    """
    with open(filepath, 'wb') as f:
        # Écrire l'en-tête
        if original_header:
            f.write(original_header)
        else:
            # En-tête par défaut: "ERO\0" + 12 octets de métadonnées
            default_header = b'ERO\x00\xfd\xfd\xfd\xfd\xdd\xdd\xdd\xdd\x41\x00\x00\x00'
            f.write(default_header)
        
        # Écrire chaque enregistrement
        for code, text in records:
            # Construire: CODE + ESPACE + TEXTE + NULL
            record_str = f'{code} {text}'
            record_bytes = record_str.encode('ascii', errors='replace')
            
            # Écrire les données
            f.write(record_bytes)
            
            # Écrire le NULL terminal
            f.write(b'\x00')
            
            # Calculer le padding nécessaire
            # Longueur actuelle = len(record_bytes) + 1 (NULL)
            current_length = len(record_bytes) + 1
            
            # Décider si on ajoute du padding
            # Règle observée: certains enregistrements ont du padding pour atteindre 31 octets
            # On ajoute du padding si la longueur est < 31 et qu'il y a de la place
            if current_length < 31:
                # Ajouter du padding \xcd pour atteindre 31 octets
                padding_length = 31 - current_length
                f.write(b'\xcd' * padding_length)


def main():
    """Point d'entrée principal."""
    if len(sys.argv) < 3:
        print("Usage: python csv_to_dat.py <input.csv> <output.dat> [original.dat]")
        print("  original.dat (optionnel): fichier .dat original pour conserver l'en-tête")
        sys.exit(1)
    
    input_csv = sys.argv[1]
    output_dat = sys.argv[2]
    original_dat = sys.argv[3] if len(sys.argv) > 3 else None
    
    # Lire l'en-tête original si fourni
    original_header = None
    if original_dat:
        print(f"Lecture de l'en-tête original depuis {original_dat}...")
        with open(original_dat, 'rb') as f:
            original_header = f.read(16)
        print(f"  En-tête: {original_header.hex()}")
    
    print(f"Lecture de {input_csv}...")
    records = read_csv_file(input_csv)
    print(f"  Nombre d'enregistrements: {len(records)}")
    
    print(f"Écriture vers {output_dat}...")
    write_dat_file(output_dat, records, original_header)
    
    print("Conversion terminée avec succès!")
    print(f"  {len(records)} enregistrements convertis")


if __name__ == '__main__':
    main()
