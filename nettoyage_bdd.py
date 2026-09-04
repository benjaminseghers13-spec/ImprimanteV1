import sqlite3

def nettoyer_base_de_donnees():
    try:
        # On se connecte à la base de données principale
        with sqlite3.connect("atelier.db") as conn:
            cursor = conn.cursor()
            
            print("Début du nettoyage de atelier.db...")

            # 1. Nettoyage de la table commandes_clients
            cursor.execute("UPDATE commandes_clients SET temps_unitaire = 0 WHERE temps_unitaire IS NULL")
            cursor.execute("UPDATE commandes_clients SET quantite_conso = 0 WHERE quantite_conso IS NULL")
            
            # 2. Nettoyage de la table references_generees
            cursor.execute("UPDATE references_generees SET temps_unitaire = 0 WHERE temps_unitaire IS NULL")
            cursor.execute("UPDATE references_generees SET quantite_conso = 0 WHERE quantite_conso IS NULL")
            
            conn.commit()
            print("✅ atelier.db nettoyée avec succès !")

    except Exception as e:
        print(f"❌ Erreur lors du nettoyage de atelier.db : {e}")

    try:
        # On fait la même chose pour la base résine si elle existe
        with sqlite3.connect("atelier_resine.db") as conn:
            cursor = conn.cursor()
            
            print("Début du nettoyage de atelier_resine.db...")
            
            cursor.execute("UPDATE references_generees SET temps_unitaire = 0 WHERE temps_unitaire IS NULL")
            cursor.execute("UPDATE references_generees SET quantite_conso = 0 WHERE quantite_conso IS NULL")
            
            conn.commit()
            print("✅ atelier_resine.db nettoyée avec succès !")

    except Exception as e:
        print(f"⚠️ Pas de base résine à nettoyer ou erreur : {e}")

if __name__ == "__main__":
    nettoyer_base_de_donnees()