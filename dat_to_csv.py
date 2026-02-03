# ---------------------------------------------------------------------------
# dat_to_csv_audit_v7.py
# Extraction et audit du fichier binaire ERO vers CSV.
# V7 — Détection de BOM résiduel dans l'en-tête.
# ---------------------------------------------------------------------------

import csv
import os
import sys


# ===========================================================================
# CONFIGURATION
# ===========================================================================

# Résolution de l'entrée : argument CLI > fichier par défaut.
if len(sys.argv) > 1:
    INPUT_FILE = sys.argv[1]
else:
    INPUT_FILE = "categori_corrected.dat"

OUTPUT_FILE   = "export_audit_v7.csv"
BLOCK_SIZE    = 31              # Taille fixe d'un enregistrement en octets.
START_OFFSET  = 52              # Fin de l'en-tête (Header 16 + Buffer 36).
ENCODING      = "latin-1"       # Encodage du fichier binaire source.

# Signature du BOM UTF-8 — utilisée pour la vérification d'intégrité.
BOM_UTF8 = b"\xef\xbb\xbf"


# ===========================================================================
# LOGIQUE PRINCIPALE
# ===========================================================================

def main():
    if not os.path.exists(INPUT_FILE):
        print(f"Erreur : Fichier '{INPUT_FILE}' introuvable.")
        return

    print("--- AUDIT BINAIRE ERO ---")
    print(f"Lecture de : {INPUT_FILE}")

    with open(INPUT_FILE, "rb") as f_in, \
         open(OUTPUT_FILE, "w", newline="", encoding=ENCODING) as f_out:

        writer = csv.writer(f_out, delimiter=";")

        # --------------------------------------------------------------
        # Lecture et validation de l'en-tête (52 premiers octets).
        # --------------------------------------------------------------
        header = f_in.read(START_OFFSET)

        if len(header) < START_OFFSET:
            print("Erreur : fichier trop court ou sans en-tête valide.")
            return

        # Détection de BOM UTF-8 résiduel dans la zone en-tête.
        # Si présent, le fichier a été corrompu avant la V7.
        if BOM_UTF8 in header:
            print("ALERTE CRITIQUE : des octets BOM (EF BB BF) ont été détectés dans l'en-tête !")

        # --------------------------------------------------------------
        # Lecture séquentielle des blocs de données.
        # --------------------------------------------------------------
        count = 0

        while True:
            block = f_in.read(BLOCK_SIZE)

            # Fin du fichier ou bloc incomplet → on arrête.
            if not block or len(block) < BLOCK_SIZE:
                break

            # Extraction du contenu : tout ce qui précède le premier \x00.
            null_idx = block.find(b"\x00")
            content_bytes = block[:null_idx] if null_idx != -1 else block

            full_text = content_bytes.decode(ENCODING).strip()

            # Bloc vide après décodage → on passe au suivant.
            if not full_text:
                continue

            # ----------------------------------------------------------
            # Séparation code / texte sur le premier espace.
            #   "0042 Catégorie X"  →  ["0042", "Catégorie X"]
            # ----------------------------------------------------------
            parts = full_text.split(" ", 1)

            if len(parts) == 2:
                writer.writerow([parts[0], parts[1]])
            else:
                writer.writerow([parts[0], ""])

            count += 1

    print("--- TERMINÉ ---")
    print(f"{count} lignes extraites vers {OUTPUT_FILE}")


# ===========================================================================
# POINT D'ENTRÉE
# ===========================================================================

if __name__ == "__main__":
    main()
