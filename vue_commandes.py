import customtkinter as ctk
import sqlite3
from tkinter import messagebox
from datetime import datetime

class OngletCommandes(ctk.CTkFrame):
    def __init__(self, master, fonction_rafraichir_global=None):
        super().__init__(master, fg_color="transparent")
        self.fonction_rafraichir_global = fonction_rafraichir_global
        
        self.default_border = "#4B5563"
        self.error_border = "#EF4444"

        # --- INITIALISATION BASE DE DONNÉES ---
        self.initialiser_bdd_devis()

        # --- EN-TÊTE ---
        en_tete = ctk.CTkFrame(self, fg_color="transparent")
        en_tete.pack(fill="x", pady=(0, 15))
        ctk.CTkLabel(en_tete, text="📦 Gestion des Commandes Clients", font=ctk.CTkFont(size=26, weight="bold")).pack(side="left")

        # --- ONGLETS (Devis / Ajout Commande) ---
        self.onglets = ctk.CTkTabview(self, command=self.sur_changement_onglet)
        self.onglets.pack(fill="both", expand=True)

        self.onglets.add("📝 Créer un Devis")
        self.onglets.add("🛒 Ajout Commande")

        # Configuration de la grille pour les onglets
        self.onglets.tab("📝 Créer un Devis").grid_rowconfigure(0, weight=1)
        self.onglets.tab("📝 Créer un Devis").grid_columnconfigure(0, weight=1)
        
        self.onglets.tab("🛒 Ajout Commande").grid_rowconfigure(0, weight=1)
        self.onglets.tab("🛒 Ajout Commande").grid_columnconfigure(0, weight=1)

        # ==========================================
        # 1. CONSTRUCTION DE L'ONGLET "DEVIS"
        # ==========================================
        scroll_devis = ctk.CTkScrollableFrame(self.onglets.tab("📝 Créer un Devis"), fg_color="transparent")
        scroll_devis.pack(fill="both", expand=True)

        carte_devis = ctk.CTkFrame(scroll_devis, fg_color=("gray95", "#1F2937"), corner_radius=10)
        carte_devis.pack(fill="x", padx=10, pady=10)
        
        ctk.CTkLabel(carte_devis, text="Informations du Devis", font=ctk.CTkFont(weight="bold", size=18)).pack(anchor="w", padx=20, pady=(15, 10))

        grid_form = ctk.CTkFrame(carte_devis, fg_color="transparent")
        grid_form.pack(fill="x", padx=20, pady=(0, 10))

        ctk.CTkLabel(grid_form, text="Nom de la référence :").grid(row=0, column=0, sticky="w", pady=10, padx=5)
        self.entry_nom_ref = ctk.CTkEntry(grid_form, width=300, border_color=self.default_border, placeholder_text="Ex: SUPPORT-MOTEUR-V2")
        self.entry_nom_ref.grid(row=0, column=1, sticky="w", pady=10, padx=15)

        ctk.CTkLabel(grid_form, text="Quantité :").grid(row=1, column=0, sticky="w", pady=10, padx=5)
        self.entry_qte = ctk.CTkEntry(grid_form, width=120, border_color=self.default_border)
        self.entry_qte.insert(0, "1")
        self.entry_qte.grid(row=1, column=1, sticky="w", pady=10, padx=15)
        self.entry_qte.bind("<KeyRelease>", self.calculer_prix)

        ctk.CTkLabel(grid_form, text="Matière :").grid(row=2, column=0, sticky="w", pady=10, padx=5)
        frame_matiere = ctk.CTkFrame(grid_form, fg_color="transparent")
        frame_matiere.grid(row=2, column=1, sticky="w", pady=10, padx=15)
        self.combo_matiere = ctk.CTkComboBox(frame_matiere, width=200, border_color=self.default_border, command=self.calculer_prix)
        self.combo_matiere.pack(side="left", padx=(0, 10))
        ctk.CTkButton(frame_matiere, text="➕", width=30, fg_color="#10B981", hover_color="#059669", command=self.ajouter_matiere).pack(side="left", padx=2)
        ctk.CTkButton(frame_matiere, text="➖", width=30, fg_color="#EF4444", hover_color="#B91C1C", command=self.supprimer_matiere).pack(side="left", padx=2)

        ctk.CTkLabel(grid_form, text="Couleur :").grid(row=3, column=0, sticky="w", pady=10, padx=5)
        frame_couleur = ctk.CTkFrame(grid_form, fg_color="transparent")
        frame_couleur.grid(row=3, column=1, sticky="w", pady=10, padx=15)
        self.combo_couleur = ctk.CTkComboBox(frame_couleur, width=200, border_color=self.default_border, command=self.calculer_prix)
        self.combo_couleur.pack(side="left", padx=(0, 10))
        ctk.CTkButton(frame_couleur, text="➕", width=30, fg_color="#10B981", hover_color="#059669", command=self.ajouter_couleur).pack(side="left", padx=2)
        ctk.CTkButton(frame_couleur, text="➖", width=30, fg_color="#EF4444", hover_color="#B91C1C", command=self.supprimer_couleur).pack(side="left", padx=2)

        ctk.CTkLabel(grid_form, text="Poids par pièce (en g) :").grid(row=4, column=0, sticky="w", pady=10, padx=5)
        self.entry_poids = ctk.CTkEntry(grid_form, width=120, border_color=self.default_border)
        self.entry_poids.insert(0, "0.0")
        self.entry_poids.grid(row=4, column=1, sticky="w", pady=10, padx=15)
        self.entry_poids.bind("<KeyRelease>", self.calculer_prix)

        # Encart Prix
        frame_prix = ctk.CTkFrame(carte_devis, fg_color="#374151", corner_radius=8)
        frame_prix.pack(fill="x", padx=20, pady=(10, 20))
        ctk.CTkLabel(frame_prix, text="💶 Prix total estimé :", font=ctk.CTkFont(size=18, weight="bold")).pack(side="left", padx=20, pady=15)
        self.lbl_prix_estime = ctk.CTkLabel(frame_prix, text="0.00 €", font=ctk.CTkFont(size=24, weight="bold"), text_color="#10B981")
        self.lbl_prix_estime.pack(side="right", padx=20, pady=15)

        self.lbl_msg_devis = ctk.CTkLabel(scroll_devis, text="", font=ctk.CTkFont(weight="bold"))
        self.lbl_msg_devis.pack(pady=5)
        
        ctk.CTkButton(scroll_devis, text="💾 Enregistrer le Devis", font=ctk.CTkFont(size=16, weight="bold"), height=45, fg_color="#3B82F6", hover_color="#2563EB", command=self.sauvegarder_devis).pack(fill="x", padx=10, pady=(0, 20))

        # ==========================================
        # 2. CONSTRUCTION DE L'ONGLET "AJOUT COMMANDE"
        # ==========================================
        self.scroll_ajout = ctk.CTkScrollableFrame(self.onglets.tab("🛒 Ajout Commande"), fg_color="transparent")
        self.scroll_ajout.pack(fill="both", expand=True)

        self.lbl_msg_commande = ctk.CTkLabel(self.onglets.tab("🛒 Ajout Commande"), text="", font=ctk.CTkFont(weight="bold"))
        self.lbl_msg_commande.pack(pady=5)

        # Initialisation du chargement
        self.charger_listes_devis()
        self.charger_devis_attente()

    def sur_changement_onglet(self):
        self.lbl_msg_devis.configure(text="")
        self.lbl_msg_commande.configure(text="")
        
        if self.onglets.get() == "🛒 Ajout Commande":
            self.charger_devis_attente()

    # ==========================================
    # LOGIQUE DE CALCUL DU PRIX
    # ==========================================
    def calculer_prix(self, *args):
        try:
            qte_texte = self.entry_qte.get().strip()
            poids_texte = self.entry_poids.get().strip()
            
            qte = int(qte_texte) if qte_texte.isdigit() else 0
            poids = float(poids_texte.replace(',', '.')) if poids_texte.replace('.', '', 1).isdigit() else 0.0
            
            # FORMULE DE CALCUL DU PRIX
            prix_unitaire = poids * 0.05 
            prix_total = prix_unitaire * qte

            self.lbl_prix_estime.configure(text=f"{prix_total:.2f} €")
            return prix_total
            
        except Exception as e:
            self.lbl_prix_estime.configure(text="0.00 €")
            return 0.0

    # ==========================================
    # GESTION BASE DE DONNÉES DEVIS
    # ==========================================
    def initialiser_bdd_devis(self):
        try:
            with sqlite3.connect("atelier.db") as conn:
                cursor = conn.cursor()
                cursor.execute("CREATE TABLE IF NOT EXISTS devis_matieres (id INTEGER PRIMARY KEY, nom TEXT UNIQUE)")
                cursor.execute("CREATE TABLE IF NOT EXISTS devis_couleurs (id INTEGER PRIMARY KEY, nom TEXT UNIQUE)")
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS devis_attente (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        nom TEXT,
                        quantite INTEGER,
                        poids REAL,
                        matiere TEXT,
                        couleur TEXT,
                        prix_total REAL
                    )
                """)
                conn.commit()
        except Exception as e:
            print(f"Erreur init BDD devis : {e}")

    def charger_listes_devis(self):
        try:
            with sqlite3.connect("atelier.db") as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT nom FROM devis_matieres ORDER BY nom")
                matieres = [row[0] for row in cursor.fetchall()]
                if not matieres: matieres = ["--- Aucune ---"]
                self.combo_matiere.configure(values=matieres)
                self.combo_matiere.set(matieres[0])

                cursor.execute("SELECT nom FROM devis_couleurs ORDER BY nom")
                couleurs = [row[0] for row in cursor.fetchall()]
                if not couleurs: couleurs = ["--- Aucune ---"]
                self.combo_couleur.configure(values=couleurs)
                self.combo_couleur.set(couleurs[0])
        except: pass

    # --- ACTIONS MATIÈRES ET COULEURS ---
    def ajouter_matiere(self):
        dialog = ctk.CTkInputDialog(text="Entrez le nom de la nouvelle matière :", title="Ajouter une matière")
        nouvelle_matiere = dialog.get_input()
        if nouvelle_matiere and nouvelle_matiere.strip():
            try:
                with sqlite3.connect("atelier.db") as conn:
                    cursor = conn.cursor()
                    cursor.execute("INSERT OR IGNORE INTO devis_matieres (nom) VALUES (?)", (nouvelle_matiere.strip().upper(),))
                    conn.commit()
                self.charger_listes_devis()
                self.combo_matiere.set(nouvelle_matiere.strip().upper())
                self.calculer_prix()
            except: pass

    def supprimer_matiere(self):
        matiere_actuelle = self.combo_matiere.get()
        if matiere_actuelle and not matiere_actuelle.startswith("---"):
            try:
                with sqlite3.connect("atelier.db") as conn:
                    cursor = conn.cursor()
                    cursor.execute("DELETE FROM devis_matieres WHERE nom = ?", (matiere_actuelle,))
                    conn.commit()
                self.charger_listes_devis()
                self.calculer_prix()
            except: pass

    def ajouter_couleur(self):
        dialog = ctk.CTkInputDialog(text="Entrez le nom de la nouvelle couleur :", title="Ajouter une couleur")
        nouvelle_couleur = dialog.get_input()
        if nouvelle_couleur and nouvelle_couleur.strip():
            try:
                with sqlite3.connect("atelier.db") as conn:
                    cursor = conn.cursor()
                    cursor.execute("INSERT OR IGNORE INTO devis_couleurs (nom) VALUES (?)", (nouvelle_couleur.strip().capitalize(),))
                    conn.commit()
                self.charger_listes_devis()
                self.combo_couleur.set(nouvelle_couleur.strip().capitalize())
                self.calculer_prix()
            except: pass

    def supprimer_couleur(self):
        couleur_actuelle = self.combo_couleur.get()
        if couleur_actuelle and not couleur_actuelle.startswith("---"):
            try:
                with sqlite3.connect("atelier.db") as conn:
                    cursor = conn.cursor()
                    cursor.execute("DELETE FROM devis_couleurs WHERE nom = ?", (couleur_actuelle,))
                    conn.commit()
                self.charger_listes_devis()
                self.calculer_prix()
            except: pass

    # ==========================================
    # LOGIQUE : ENREGISTRER LE DEVIS
    # ==========================================
    def sauvegarder_devis(self):
        nom = self.entry_nom_ref.get().strip()
        qte_texte = self.entry_qte.get().strip()
        poids_texte = self.entry_poids.get().strip()
        matiere = self.combo_matiere.get()
        couleur = self.combo_couleur.get()

        if not nom or not qte_texte.isdigit() or not poids_texte.replace('.', '', 1).isdigit():
            self.lbl_msg_devis.configure(text="⚠️ Entrez un nom valide, une quantité et un poids numériques.", text_color=self.error_border)
            return

        qte = int(qte_texte)
        poids = float(poids_texte.replace(',', '.'))
        prix_calcul = self.calculer_prix()

        try:
            with sqlite3.connect("atelier.db") as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO devis_attente (nom, quantite, poids, matiere, couleur, prix_total)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (nom, qte, poids, matiere, couleur, prix_calcul))
                conn.commit()
            
            self.lbl_msg_devis.configure(text=f"✅ Devis pour {nom} enregistré ! Il est dans 'Ajout Commande'.", text_color="#10B981")
            self.after(4000, lambda: self.lbl_msg_devis.configure(text=""))
            
            # Réinitialisation des champs
            self.entry_nom_ref.delete(0, 'end')
            self.entry_qte.delete(0, 'end')
            self.entry_qte.insert(0, "1")
            self.entry_poids.delete(0, 'end')
            self.entry_poids.insert(0, "0.0")
            self.calculer_prix() 
            
            self.charger_devis_attente()

        except Exception as e:
            self.lbl_msg_devis.configure(text=f"❌ Erreur BDD: {e}", text_color=self.error_border)

    # ==========================================
    # LOGIQUE : ONGLET "AJOUT COMMANDE"
    # ==========================================
    def charger_devis_attente(self):
        for widget in self.scroll_ajout.winfo_children():
            widget.destroy()

        try:
            with sqlite3.connect("atelier.db") as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT id, nom, quantite, poids, matiere, couleur, prix_total FROM devis_attente ORDER BY id DESC")
                devis_list = cursor.fetchall()

            if not devis_list:
                ctk.CTkLabel(self.scroll_ajout, text="📭 Aucun devis en attente.", font=ctk.CTkFont(slant="italic", size=16), text_color="gray50").pack(pady=40)
                return

            for devis in devis_list:
                id_devis, nom, qte, poids, mat, coul, prix = devis
                
                carte = ctk.CTkFrame(self.scroll_ajout, fg_color=("gray95", "#1F2937"), corner_radius=8)
                carte.pack(fill="x", pady=5, padx=10)
                
                info_texte = f"📌 {nom}   |   Qté: {qte}   |   {mat} - {coul}   |   Total: {prix:.2f} €"
                ctk.CTkLabel(carte, text=info_texte, font=ctk.CTkFont(weight="bold", size=15)).pack(side="left", padx=15, pady=15)
                
                # Bouton Supprimer
                btn_sup = ctk.CTkButton(carte, text="❌", width=40, height=35, fg_color="#EF4444", hover_color="#B91C1C", 
                                        command=lambda i=id_devis, n=nom: self.confirmer_suppression(i, n))
                btn_sup.pack(side="right", padx=10, pady=10)
                
                # Bouton Envoi Prod - On passe maintenant le poids et la matière !
                btn_prod = ctk.CTkButton(carte, text="✅ Envoi en Prod", height=35, fg_color="#10B981", hover_color="#059669", font=ctk.CTkFont(weight="bold"),
                                         command=lambda i=id_devis, n=nom, q=qte, p=poids, m=mat: self.envoyer_en_prod(i, n, q, p, m))
                btn_prod.pack(side="right", padx=5, pady=10)

        except Exception as e:
            print(f"Erreur chargement devis attente: {e}")

    def confirmer_suppression(self, id_devis, nom_devis):
        reponse = messagebox.askyesno("Confirmation", f"Voulez-vous vraiment supprimer le devis '{nom_devis}' ?\nCette action est irréversible.")
        if reponse:
            try:
                with sqlite3.connect("atelier.db") as conn:
                    cursor = conn.cursor()
                    cursor.execute("DELETE FROM devis_attente WHERE id = ?", (id_devis,))
                    conn.commit()
                
                self.charger_devis_attente()
                self.lbl_msg_commande.configure(text=f"🗑️ Devis '{nom_devis}' supprimé.", text_color=self.error_border)
                self.after(3000, lambda: self.lbl_msg_commande.configure(text=""))
            except Exception as e:
                print(f"Erreur suppression : {e}")

    def envoyer_en_prod(self, id_devis, nom_devis, qte, poids, matiere):
        """Transfère le devis dans les commandes clients (en production) sans laisser de cases vides."""
        try:
            with sqlite3.connect("atelier.db") as conn:
                cursor = conn.cursor()
                
                date_saisie = datetime.now().strftime("%d/%m/%Y %H:%M")
                
                # CORRECTION : On renseigne des valeurs par défaut pour TOUTES les colonnes attendues
                # pour éviter les NULL (None) qui font planter le planning.
                cursor.execute("""
                    INSERT INTO commandes_clients (reference_piece, quantite, temps_unitaire, statut, date_saisie, echeance, consommable_lie, quantite_conso)
                    VALUES (?, ?, 0, 'Créée', ?, '', ?, ?)
                """, (nom_devis, qte, date_saisie, matiere, poids))
                
                cursor.execute("DELETE FROM devis_attente WHERE id = ?", (id_devis,))
                conn.commit()

            self.charger_devis_attente() 
            self.lbl_msg_commande.configure(text=f"🚀 '{nom_devis}' envoyé en production avec succès !", text_color="#10B981")
            self.after(4000, lambda: self.lbl_msg_commande.configure(text=""))

            if self.fonction_rafraichir_global:
                self.fonction_rafraichir_global()

        except Exception as e:
            self.lbl_msg_commande.configure(text=f"❌ Erreur lors de l'envoi en prod: {e}", text_color=self.error_border)