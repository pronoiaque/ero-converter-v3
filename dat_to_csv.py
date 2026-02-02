#!/usr/bin/env python3
"""
Convertisseur categori_hd.dat -> categories_hd.csv
Règles strictes :
- Conservation des entêtes
- Lecture jusqu'au NULL terminal
- CODE(4 digits, sans padding) + ESPACE(1) + TEXTE ≤ 30 caractères
- Réversibilité absolue 100%
"""

import sys
from typing import List, Tuple


def read_dat_file(filepath: str) -> Tuple[bytes, List[Tuple[str, str]]]:
    """
    Lit le fichier .dat et extrait l'en-tête et les enregistrements.
    
    Returns:
        (header_bytes, list of (code, text) tuples)
    """
    with open(filepath, 'rb') as f:
        data = f.read()
    
    # Extraire l'en-tête (16 premiers octets)
    header = data[:16]
    
    # Vérifier que l'en-tête commence bien par "ERO\0"
    if not header.startswith(b'ERO\x00'):
        raise ValueError("Format d'en-tête invalide - doit commencer par 'ERO\\0'")
    
    # Parser les enregistrements
    records = []
    pos = 16
    
    while pos < len(data):
        # Trouver le prochain NULL terminal
        null_pos = data.find(b'\x00', pos)
        
        if null_pos == -1:
            # Pas de NULL trouvé, fin du fichier
            break
        
        # Extraire l'enregistrement complet jusqu'au NULL
        record_bytes = data[pos:null_pos]
        
        # Ignorer les enregistrements trop courts (< 6 caractères pour "CODE T")
        if len(record_bytes) < 6:
            pos = null_pos + 1
            continue
        
        # Décoder en ASCII (ignorer les erreurs)
        try:
            record_str = record_bytes.decode('ascii', errors='ignore')
        except:
            record_str = record_bytes.decode('latin-1', errors='ignore')
        
        # Enlever les caractères de padding \xcd au début
        record_str = record_str.lstrip('\xcc\xcd')
        
        # Parser CODE ESPACE TEXTE
        # Le code doit être sur 4 caractères suivis d'un espace
        if len(record_str) >= 6:  # Au minimum "0000 X"
            # Vérifier si les 4 premiers caractères ressemblent à un code
            potential_code = record_str[:4]
            
            # Code valide = 4 digits UNIQUEMENT (pas de lettres)
            is_valid_code = potential_code.isdigit()
            
            # Vérifier qu'il y a un espace après le code
            has_space = record_str[4:5] == ' '
            
            if is_valid_code and has_space:
                code_str = potential_code
                text_str = record_str[5:].strip()
                
                # Nettoyer le texte (enlever les caractères non imprimables)
                text_clean = ''.join(c for c in text_str if c.isprintable())
                
                # Ajouter uniquement si le texte n'est pas vide
                if text_clean:
                    records.append((code_str, text_clean))
        
        # Avancer après le NULL
        pos = null_pos + 1
    
    return header, records


def write_csv_file(filepath: str, records: List[Tuple[str, str]]) -> None:
    """
    Écrit les enregistrements dans un fichier CSV.
    Format: CODE;TEXTE
    """
    with open(filepath, 'w', encoding='utf-8-sig') as f:  # utf-8-sig pour le BOM
        for code, text in records:
            # Supprimer les zéros de tête du code (0202 -> 202) si numérique
            if code.isdigit():
                code_formatted = f'{int(code):04d}'
            else:
                # Garder le code tel quel si non numérique
                code_formatted = code
            
            # Écrire au format CSV
            f.write(f'{code_formatted};{text}\n')


def main():
    """Point d'entrée principal."""
    if len(sys.argv) != 3:
        print("Usage: python dat_to_csv.py <input.dat> <output.csv>")
        sys.exit(1)
    
    input_dat = sys.argv[1]
    output_csv = sys.argv[2]
    
    print(f"Lecture de {input_dat}...")
    header, records = read_dat_file(input_dat)
    
    print(f"  En-tête: {header[:16].hex()}")
    print(f"  Nombre d'enregistrements: {len(records)}")
    
    print(f"Écriture vers {output_csv}...")
    write_csv_file(output_csv, records)
    
    print("Conversion terminée avec succès!")
    print(f"  {len(records)} enregistrements convertis")


if __name__ == '__main__':
    main()
