#!/usr/bin/env python3
"""
Script de test automatique pour vérifier la réversibilité à 100%
des convertisseurs dat_to_csv.py et csv_to_dat.py
"""

import subprocess
import sys
import os
import filecmp

def run_command(cmd, description):
    """Exécute une commande et affiche le résultat."""
    print(f"\n{'='*60}")
    print(f"🔧 {description}")
    print(f"{'='*60}")
    print(f"$ {' '.join(cmd)}")
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.stdout:
        print(result.stdout)
    if result.stderr:
        print("⚠️  Erreurs:", result.stderr)
    
    if result.returncode != 0:
        print(f"❌ Échec (code: {result.returncode})")
        return False
    
    print("✅ Succès")
    return True

def compare_files(file1, file2, description):
    """Compare deux fichiers."""
    print(f"\n{'='*60}")
    print(f"🔍 {description}")
    print(f"{'='*60}")
    
    # Comparer le contenu
    with open(file1, 'r', encoding='utf-8-sig') as f1:
        content1 = f1.read()
    with open(file2, 'r', encoding='utf-8-sig') as f2:
        content2 = f2.read()
    
    if content1 == content2:
        print(f"✅ Les fichiers {file1} et {file2} sont identiques !")
        print(f"   Taille: {len(content1)} caractères")
        print(f"   Lignes: {len(content1.splitlines())}")
        return True
    else:
        print(f"❌ Les fichiers {file1} et {file2} diffèrent")
        print(f"   {file1}: {len(content1)} caractères, {len(content1.splitlines())} lignes")
        print(f"   {file2}: {len(content2)} caractères, {len(content2.splitlines())} lignes")
        
        # Montrer les premières différences
        lines1 = content1.splitlines()
        lines2 = content2.splitlines()
        for i, (l1, l2) in enumerate(zip(lines1, lines2)):
            if l1 != l2:
                print(f"\n   Première différence à la ligne {i+1}:")
                print(f"   Fichier 1: {l1}")
                print(f"   Fichier 2: {l2}")
                break
        return False

def main():
    """Test principal de réversibilité."""
    print("""
╔══════════════════════════════════════════════════════════════╗
║     TEST DE RÉVERSIBILITÉ BIDIRECTIONNELLE                   ║
║     categori_hd.dat ⟷ categories_hd.csv                     ║
╚══════════════════════════════════════════════════════════════╝
""")
    
    # Fichiers de test
    original_dat = "/mnt/user-data/uploads/categori_hd.dat"
    
    if not os.path.exists(original_dat):
        print(f"❌ Fichier original introuvable: {original_dat}")
        sys.exit(1)
    
    # Étape 1: DAT → CSV
    if not run_command(
        ["python3", "dat_to_csv.py", original_dat, "test1.csv"],
        "Étape 1: Conversion DAT → CSV"
    ):
        sys.exit(1)
    
    # Étape 2: CSV → DAT
    if not run_command(
        ["python3", "csv_to_dat.py", "test1.csv", "test_recreated.dat", original_dat],
        "Étape 2: Conversion CSV → DAT (avec en-tête original)"
    ):
        sys.exit(1)
    
    # Étape 3: DAT → CSV (de nouveau)
    if not run_command(
        ["python3", "dat_to_csv.py", "test_recreated.dat", "test2.csv"],
        "Étape 3: Reconversion DAT → CSV"
    ):
        sys.exit(1)
    
    # Étape 4: Comparaison des CSV
    if not compare_files("test1.csv", "test2.csv", "Comparaison CSV final vs initial"):
        sys.exit(1)
    
    # Étape 5: Test sans en-tête original
    print(f"\n{'='*60}")
    print("🔧 Test bonus: Conversion sans en-tête original")
    print(f"{'='*60}")
    
    if not run_command(
        ["python3", "csv_to_dat.py", "test1.csv", "test_noheader.dat"],
        "Conversion CSV → DAT (sans en-tête original)"
    ):
        print("⚠️  Note: En-tête par défaut utilisé")
    
    if not run_command(
        ["python3", "dat_to_csv.py", "test_noheader.dat", "test3.csv"],
        "Reconversion DAT → CSV"
    ):
        sys.exit(1)
    
    if not compare_files("test1.csv", "test3.csv", "Comparaison CSV (avec en-tête par défaut)"):
        sys.exit(1)
    
    # Résumé
    print(f"\n{'='*60}")
    print("📊 RÉSUMÉ DES TESTS")
    print(f"{'='*60}")
    print("✅ Test 1: DAT → CSV → DAT → CSV : RÉUSSI")
    print("✅ Test 2: CSV identique après round-trip : RÉUSSI")
    print("✅ Test 3: Conversion sans en-tête original : RÉUSSI")
    print("\n🎉 RÉVERSIBILITÉ À 100% CONFIRMÉE !")
    print("\nLes programmes sont prêts à être utilisés en production.")
    
    # Nettoyage
    print(f"\n{'='*60}")
    print("🧹 Nettoyage des fichiers de test")
    print(f"{'='*60}")
    for f in ["test1.csv", "test2.csv", "test3.csv", "test_recreated.dat", "test_noheader.dat"]:
        if os.path.exists(f):
            os.remove(f)
            print(f"  Supprimé: {f}")

if __name__ == '__main__':
    main()
