# ---------------------------------------------------------------------------
# csv_to_dat_final_v7.py
# Génération du fichier binaire ERO à partir d'un CSV.
# V7 — Élimination automatique du BOM UTF-8 avant traitement.
# ---------------------------------------------------------------------------

import csv
import os
import sys


# ===========================================================================
# CONFIGURATION
# ===========================================================================

# Résolution de l'entrée : argument CLI > fichier par défaut > fallback.
if len(sys.argv) > 1:
    INPUT_FILE = sys.argv[1]
elif os.path.exists("for_gemini.csv"):
    INPUT_FILE = "for_gemini.csv"
else:
    INPUT_FILE = "categories_hd.csv"

OUTPUT_FILE = "categori_corrected.dat"
BLOCK_SIZE  = 31                # Taille fixe d'un enregistrement en octets.

# Encodages
CSV_ENCODING = "utf-8-sig"      # Consomme silencieusement le BOM (EF BB BF) s'il est présent.
DAT_ENCODING = "latin-1"        # Format cible du fichier binaire (legacy ERO).


# ===========================================================================
# STRUCTURE TECHNIQUE — ZONE EN-TÊTE (52 octets, validée)
# ===========================================================================
#
#   Offset  Taille  Rôle
#   ------  ------  ------------------------------------
#    0      16      Header  — Signature ERO
#   16      36      Buffer  — Séquence technique <vide>
#   52       —      Début des enregistrements de données
#
# ===========================================================================

HEADER_BYTES = bytes.fromhex(
    "45524F00"          # Signature "ERO\0"
    "FDFDFDFD"          # Padding signature
    "DDDDDDDD"         # Padding signature
    "41000000"          # Terminateur header
)

BUFFER_BYTES = bytes.fromhex(
    "41000000"          # Préfixe buffer
    "00"                # Séparateur
    "3C766964653E20"    # Chaîne ASCII "<vide> "
    "CCCCCCCCCCCCCCCC"  # Padding buffer (24 octets
    "CCCCCCCCCCCCCCCC"  #  de 0xCC)
    "CCCCCCCCCCCCCCCC"  #
)


# ===========================================================================
# LOGIQUE PRINCIPALE
# ===========================================================================

def main():
    if not os.path.exists(INPUT_FILE):
        print(f"ERREUR : Fichier source '{INPUT_FILE}' introuvable.")
        return

    print("--- GÉNÉRATION DE BINAIRE ERO (V7 - Anti-BOM) ---")
    print(f"Source : {INPUT_FILE}")
    print(f"Cible  : {OUTPUT_FILE}")

    # ------------------------------------------------------------------
    # Ouverture du CSV avec gestion automatique du BOM.
    # utf-8-sig est la clé : les 3 octets EF BB BF sont absorbés
    # silencieusement si présents.  En cas d'échec, fallback latin-1.
    # ------------------------------------------------------------------
    try:
        f_in = open(INPUT_FILE, "r", newline="", encoding=CSV_ENCODING)
    except UnicodeDecodeError:
        print("Avertissement : échec lecture UTF-8, tentative en Latin-1...")
        f_in = open(INPUT_FILE, "r", newline="", encoding="latin-1")

    with f_in, open(OUTPUT_FILE, "wb") as f_out:
        reader = csv.reader(f_in, delimiter=";")

        # --------------------------------------------------------------
        # Injection de la structure en-tête (offsets 0–52).
        # --------------------------------------------------------------
        f_out.write(HEADER_BYTES)
        f_out.write(BUFFER_BYTES)

        count = 0

        for row in reader:
            if not row or len(row) < 2:
                continue

            # ----------------------------------------------------------
            # Nettoyage des champs bruts (espaces parasites).
            # ----------------------------------------------------------
            code_brut  = row[0].strip()
            texte_brut = row[1].strip()

            # Concaténation : "code texte"
            full_string = f"{code_brut} {texte_brut}"

            # ----------------------------------------------------------
            # Construction du bloc de 31 octets
            #   [payload … \x00 … padding 0xCD]
            #
            #   payload  : contenu encodé en latin-1, max 30 octets.
            #   \x00     : terminateur de chaîne (1 octet).
            #   padding  : remplissage avec 0xCD jusqu'à 31 octets.
            # ----------------------------------------------------------
            max_content_len = BLOCK_SIZE - 1  # 30 octets utiles max

            payload = full_string.encode(DAT_ENCODING, errors="replace")[:max_content_len]

            padding_len = BLOCK_SIZE - len(payload) - 1
            padding     = b"\xCD" * padding_len if padding_len > 0 else b""

            final_block = payload + b"\x00" + padding

            # Sécurité : garantie de la taille exacte.
            if len(final_block) != BLOCK_SIZE:
                final_block = final_block[:BLOCK_SIZE]

            f_out.write(final_block)
            count += 1

    print("--- SUCCÈS ---")
    print(f"{count} enregistrements écrits sans BOM parasite.")


# ===========================================================================
# POINT D'ENTRÉE
# ===========================================================================

if __name__ == "__main__":
    main()
