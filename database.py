import sqlite3

def initialiser_base():
    conn = sqlite3.connect("atelier.db", timeout=30.0)
    cursor = conn.cursor()

    cursor.execute("PRAGMA journal_mode=WAL;")

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS parametres_references (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            prefix TEXT UNIQUE,
            nom TEXT
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS references_generees (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            prefix TEXT,
            reference_complete TEXT,
            numero_sequentiel INTEGER,
            version INTEGER,
            quantite INTEGER,
            temps_unitaire INTEGER,
            statut TEXT,
            date_creation TEXT,
            consommable_lie TEXT,
            quantite_conso REAL
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS commandes_clients (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            reference_piece TEXT,
            quantite INTEGER,
            temps_unitaire INTEGER,
            statut TEXT,
            date_saisie TEXT,
            echeance TEXT,
            consommable_lie TEXT,
            quantite_conso REAL
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS machines (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nom TEXT,
            statut TEXT,
            prefixes_autorises TEXT
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS historique_production (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            reference TEXT,
            quantite INTEGER,
            temps_unitaire INTEGER,
            statut_final TEXT,
            date_realisation TEXT
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS parametres_atelier (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            heure_debut TEXT,
            heure_fin_lancement TEXT
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS consommables (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nom TEXT,
            categorie TEXT,
            quantite_stock REAL,
            unite TEXT,
            seuil_alerte REAL
        )
    """)
    
    cursor.execute("SELECT COUNT(*) FROM consommables")
    if cursor.fetchone()[0] == 0:
        consommables_defaut = [
            ("Résine Standard Grey", "Résine 3D", 5.0, "Litre", 1.5),
            ("Résine Biocompatible", "Résine 3D", 2.0, "Litre", 1.0),
            ("Alcool Isopropylique (IPA)", "Nettoyage", 25.0, "Litre", 5.0),
            ("Film FEP (Rapidshape)", "Pièce détachée", 4.0, "Unité", 1.0),
            ("Sachets d'ensachage", "Emballage", 250.0, "Unité", 50.0)
        ]
        cursor.executemany("INSERT INTO consommables (nom, categorie, quantite_stock, unite, seuil_alerte) VALUES (?, ?, ?, ?, ?)", consommables_defaut)

    cursor.execute("SELECT COUNT(*) FROM parametres_atelier")
    if cursor.fetchone()[0] == 0:
        cursor.execute("INSERT INTO parametres_atelier (heure_debut, heure_fin_lancement) VALUES ('07:00', '17:30')")

    secteurs_defaut = [
        ("CDT", "Cellule de thermoformage"),
        ("CDD", "Cellule de découpe"),
        ("CDN", "Cellule de nettoyage / ensachage"),
        ("LMA", "Lavage manuel"),
        ("TRI", "Triosmile"),
        ("BAR", "Puce de suivi à intégrer - Baracoda"),
        ("FIN", "Finisher / Finition"),
        ("BAD", "Projet brosse à dents personnalisée"),
        ("PRW", "Prodways LD20 / D100"),
        ("RSH", "Rapidshape"),
        ("OUT", "Outilages"),
        ("THE", "Thermoformage")
    ]
    for p, n in secteurs_defaut:
        cursor.execute("INSERT OR IGNORE INTO parametres_references (prefix, nom) VALUES (?, ?)", (p, n))

    conn.commit()
    conn.close()

if __name__ == "__main__":
    initialiser_base()
    print("Base de données initialisée avec succès.")