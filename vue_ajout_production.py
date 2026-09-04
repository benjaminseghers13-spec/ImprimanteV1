import customtkinter as ctk
import sqlite3

class OngletAjoutProduction(ctk.CTkFrame):
    def __init__(self, master, fonction_rafraichir_global=None):
        super().__init__(master, fg_color="transparent")
        self.fonction_rafraichir_global = fonction_rafraichir_global

        # --- EN-TÊTE ---
        en_tete = ctk.CTkFrame(self, fg_color="transparent")
        en_tete.pack(fill="x", pady=(0, 15))
        ctk.CTkLabel(en_tete, text="⚙️ Ajout de Production", font=ctk.CTkFont(size=26, weight="bold")).pack(side="left")

        # --- CONTENEUR DÉROULANT ---
        self.scroll_frame = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.scroll_frame.pack(fill="both", expand=True, padx=0, pady=0)

        # Variables de contrôle
        self.var_pole = ctk.StringVar(value="3D")
        self.var_source = ctk.StringVar(value="Interne")
        self.var_priorite = ctk.StringVar(value="Dans le flux")
        self.default_border = "#4B5563"
        self.error_border = "#EF4444"

        # ==========================================
        # ÉTAPE 1 : CHOIX DU FLUX (3D ou RÉSINE)
        # ==========================================
        self.frame_etape1 = self.creer_carte("1️⃣ ÉTAPE 1 : De quel côté part la production ?")
        self.frame_etape1.master.pack(fill="x", pady=10, padx=5)

        radio_frame = ctk.CTkFrame(self.frame_etape1, fg_color="transparent")
        radio_frame.pack(anchor="w", pady=(5, 10))
        ctk.CTkRadioButton(radio_frame, text="🧱 Pôle 3D (FDM)", variable=self.var_pole, value="3D", command=self.charger_references, font=ctk.CTkFont(weight="bold")).pack(side="left", padx=(0, 25))
        ctk.CTkRadioButton(radio_frame, text="💧 Pôle Résine (SLA)", variable=self.var_pole, value="Resine", command=self.charger_references, font=ctk.CTkFont(weight="bold")).pack(side="left", padx=10)

        # ==========================================
        # ÉTAPE 2 : CHOIX DE LA RÉFÉRENCE
        # ==========================================
        self.frame_etape2 = self.creer_carte("2️⃣ ÉTAPE 2 : Choisir la pièce à planifier")
        self.frame_etape2.master.pack(fill="x", pady=10, padx=5)

        radio_source = ctk.CTkFrame(self.frame_etape2, fg_color="transparent")
        radio_source.pack(anchor="w", pady=(0, 10))
        ctk.CTkRadioButton(radio_source, text="📁 Références Internes", variable=self.var_source, value="Interne", command=self.sur_changement_source, text_color="#3B82F6", font=ctk.CTkFont(weight="bold")).pack(side="left", padx=(0, 25))
        ctk.CTkRadioButton(radio_source, text="🛒 Commandes Clients", variable=self.var_source, value="Client", command=self.sur_changement_source, text_color="#10B981", font=ctk.CTkFont(weight="bold")).pack(side="left", padx=10)

        ctk.CTkLabel(self.frame_etape2, text="Sélectionnez l'élément :", text_color="gray60").pack(anchor="w", pady=(5, 2))
        self.combo_refs = ctk.CTkComboBox(self.frame_etape2, width=400, border_color=self.default_border, command=self.sur_selection_reference)
        self.combo_refs.pack(anchor="w")

        # ==========================================
        # ÉTAPE 3 : PARAMÈTRES DE PRODUCTION (NOUVEAU)
        # ==========================================
        self.frame_etape3 = self.creer_carte("3️⃣ ÉTAPE 3 : Paramètres de Production (Slicer)")
        self.frame_etape3.master.pack(fill="x", pady=10, padx=5)

        grid_params = ctk.CTkFrame(self.frame_etape3, fg_color="transparent")
        grid_params.pack(fill="x", pady=5)

        # Ligne 1 : Quantité et Temps
        ctk.CTkLabel(grid_params, text="Quantité :", text_color="gray60").grid(row=0, column=0, sticky="w", padx=5, pady=10)
        self.entry_qte = ctk.CTkEntry(grid_params, width=100, border_color=self.default_border)
        self.entry_qte.insert(0, "1")
        self.entry_qte.grid(row=0, column=1, sticky="w", padx=10, pady=10)

        ctk.CTkLabel(grid_params, text="Temps d'impression (min) :", text_color="gray60").grid(row=0, column=2, sticky="w", padx=(25, 5), pady=10)
        self.entry_temps = ctk.CTkEntry(grid_params, width=100, border_color=self.default_border)
        self.entry_temps.insert(0, "0")
        self.entry_temps.grid(row=0, column=3, sticky="w", padx=10, pady=10)

        # Ligne 2 : Poids et Matière liée au Magasin
        ctk.CTkLabel(grid_params, text="Poids unitaire (g) :", text_color="gray60").grid(row=1, column=0, sticky="w", padx=5, pady=10)
        self.entry_poids = ctk.CTkEntry(grid_params, width=100, border_color=self.default_border)
        self.entry_poids.insert(0, "0.0")
        self.entry_poids.grid(row=1, column=1, sticky="w", padx=10, pady=10)

        ctk.CTkLabel(grid_params, text="Matière (Magasin) :", text_color="gray60").grid(row=1, column=2, sticky="w", padx=(25, 5), pady=10)
        self.combo_conso = ctk.CTkComboBox(grid_params, width=220, border_color=self.default_border)
        self.combo_conso.grid(row=1, column=3, sticky="w", padx=10, pady=10)

        # ==========================================
        # ÉTAPE 4 : ORDRE DE PRIORITÉ
        # ==========================================
        self.frame_etape4 = self.creer_carte("4️⃣ ÉTAPE 4 : Ordre de priorité")
        self.frame_etape4.master.pack(fill="x", pady=10, padx=5)

        grid_priorite = ctk.CTkFrame(self.frame_etape4, fg_color="transparent")
        grid_priorite.pack(fill="x", pady=5)

        self.combo_priorite = ctk.CTkOptionMenu(grid_priorite, values=["Dans le flux", "Urgence", "Avant échéance"], variable=self.var_priorite, command=self.sur_changement_priorite, fg_color="#374151")
        self.combo_priorite.grid(row=0, column=0, sticky="w")

        self.frame_echeance = ctk.CTkFrame(grid_priorite, fg_color="transparent")
        ctk.CTkLabel(self.frame_echeance, text="Date (JJ/MM) :").pack(side="left", padx=(15, 5))
        self.entry_echeance = ctk.CTkEntry(self.frame_echeance, width=100, placeholder_text="ex: 15/10", border_color=self.default_border)
        self.entry_echeance.pack(side="left")

        # ==========================================
        # VALIDATION FINALE
        # ==========================================
        self.frame_resultat = ctk.CTkFrame(self.scroll_frame, fg_color="transparent")
        self.frame_resultat.pack(pady=10)

        self.lbl_message = ctk.CTkLabel(self.frame_resultat, text="", font=ctk.CTkFont(size=14, weight="bold"))
        self.lbl_message.pack()

        ctk.CTkButton(self.scroll_frame, text="🚀 Envoyer au Planning", font=ctk.CTkFont(size=16, weight="bold"), height=50, fg_color="#1D4ED8", hover_color="#1E3A8A", command=self.envoyer_production).pack(fill="x", padx=5, pady=(0, 20))

        # Initialisation
        self.charger_references()
        self.sur_changement_priorite(self.var_priorite.get())

    # ==========================================
    # MÉTHODES D'INTERFACE & CHARGEMENT
    # ==========================================
    def creer_carte(self, titre):
        carte = ctk.CTkFrame(self.scroll_frame, fg_color=("gray95", "#1F2937"), corner_radius=10)
        ctk.CTkLabel(carte, text=titre, font=ctk.CTkFont(weight="bold", size=15)).pack(anchor="w", padx=15, pady=(15, 5))
        contenu = ctk.CTkFrame(carte, fg_color="transparent")
        contenu.pack(fill="both", expand=True, padx=15, pady=(0, 15))
        return contenu

    def sur_changement_priorite(self, choix):
        if choix == "Avant échéance":
            self.frame_echeance.grid(row=0, column=1, sticky="w")
        else:
            self.frame_echeance.grid_forget()

    def get_db_name(self):
        return "atelier.db" if self.var_pole.get() == "3D" else "atelier_resine.db"

    def sur_changement_source(self):
        self.charger_references()

    def charger_consommables(self):
        """Récupère les matières exactes disponibles dans le magasin."""
        db_cible = self.get_db_name()
        try:
            with sqlite3.connect(db_cible, timeout=30.0) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT nom FROM consommables ORDER BY nom")
                produits = cursor.fetchall()
                valeurs = [p[0] for p in produits] if produits else ["--- Aucun consommable ---"]
                self.combo_conso.configure(values=valeurs)
                self.combo_conso.set(valeurs[0])
        except:
            self.combo_conso.configure(values=["--- Aucun consommable ---"])
            self.combo_conso.set("--- Aucun consommable ---")

    def charger_references(self):
        # 1. On charge d'abord les consommables dispo selon le pôle sélectionné
        self.charger_consommables()
        
        db_cible = self.get_db_name()
        source = self.var_source.get()
        valeurs = []

        try:
            with sqlite3.connect(db_cible, timeout=30.0) as conn:
                cursor = conn.cursor()
                
                if source == "Interne":
                    cursor.execute("SELECT reference_complete FROM references_generees ORDER BY id DESC")
                    refs = cursor.fetchall()
                    valeurs = [r[0] for r in refs]
                
                elif source == "Client":
                    conn_cmd = sqlite3.connect("atelier.db")
                    cursor_cmd = conn_cmd.cursor()
                    cursor_cmd.execute("SELECT reference_piece, quantite FROM commandes_clients WHERE statut = 'Créée' ORDER BY id DESC")
                    cmds = cursor_cmd.fetchall()
                    valeurs = [f"{nom} (Qté: {qte})" for nom, qte in cmds]
                    conn_cmd.close()
                    
        except Exception as e:
            print(f"Erreur chargement refs: {e}")
        
        if not valeurs:
            valeurs = ["--- Aucune donnée disponible ---"]
            
        self.combo_refs.configure(values=valeurs)
        self.combo_refs.set(valeurs[0])
        
        # On simule un clic sur le premier élément pour charger ses paramètres
        self.sur_selection_reference(valeurs[0])

    def sur_selection_reference(self, choix):
        """Récupère en BDD le temps, le poids et le consommable pour les afficher."""
        if not choix or choix.startswith("---"):
            return
            
        nom_pur = choix.split(" (Qté:")[0].strip()
        db_cible = self.get_db_name()
        source = self.var_source.get()

        try:
            # Récupération selon la source
            if source == "Interne":
                with sqlite3.connect(db_cible) as conn:
                    cursor = conn.cursor()
                    cursor.execute("SELECT quantite, temps_unitaire, quantite_conso, consommable_lie FROM references_generees WHERE reference_complete = ?", (nom_pur,))
                    row = cursor.fetchone()
            else:
                with sqlite3.connect("atelier.db") as conn:
                    cursor = conn.cursor()
                    cursor.execute("SELECT quantite, temps_unitaire, quantite_conso, consommable_lie FROM commandes_clients WHERE reference_piece = ?", (nom_pur,))
                    row = cursor.fetchone()

            if row:
                qte, temps, poids, conso = row
                
                # Remplissage de l'Etape 3
                self.entry_qte.delete(0, 'end')
                self.entry_qte.insert(0, str(qte) if qte else "1")
                
                self.entry_temps.delete(0, 'end')
                self.entry_temps.insert(0, str(temps) if temps else "0")
                
                self.entry_poids.delete(0, 'end')
                self.entry_poids.insert(0, str(poids) if poids else "0.0")
                
                # Si un consommable était déjà lié et existe au magasin, on le sélectionne
                if conso and conso in self.combo_conso.cget("values"):
                    self.combo_conso.set(conso)
        except Exception as e:
            print("Erreur chargement paramètres:", e)

    # ==========================================
    # VALIDATION ET ENVOI
    # ==========================================
    def envoyer_production(self):
        selection = self.combo_refs.get()
        if not selection or selection.startswith("---"):
            self.lbl_message.configure(text="⚠️ Veuillez sélectionner un élément valide.", text_color=self.error_border)
            return
            
        # 1. On récupère les Paramètres de Production (Étape 3)
        qte_texte = self.entry_qte.get().strip()
        qte = int(qte_texte) if qte_texte.isdigit() else 1
        
        temps_texte = self.entry_temps.get().strip()
        temps = int(temps_texte) if temps_texte.isdigit() else 0
        
        poids_texte = self.entry_poids.get().replace(',', '.').strip()
        poids = float(poids_texte) if poids_texte.replace('.', '', 1).isdigit() else 0.0
        
        conso = self.combo_conso.get()
        if conso.startswith("---"):
            conso = ""

        # 2. Priorités (Étape 4)
        statut_priorite = self.var_priorite.get()
        echeance = self.entry_echeance.get().strip() if statut_priorite == "Avant échéance" else ""

        db_cible = self.get_db_name()
        flux_nom = "3D" if self.var_pole.get() == "3D" else "Résine"
        source = self.var_source.get()
        nom_pur = selection.split(" (Qté:")[0].strip()

        try:
            if source == "Interne":
                with sqlite3.connect(db_cible, timeout=30.0) as conn:
                    cursor = conn.cursor()
                    cursor.execute("""
                        UPDATE references_generees 
                        SET statut = ?, quantite = ?, temps_unitaire = ?, quantite_conso = ?, consommable_lie = ? 
                        WHERE reference_complete = ?
                    """, (statut_priorite, qte, temps, poids, conso, nom_pur))
                    conn.commit()
            
            elif source == "Client":
                if self.var_pole.get() == "Resine":
                    # Transfert 3D vers Résine avec les nouvelles données
                    with sqlite3.connect("atelier.db", timeout=30.0) as conn_3d:
                        cursor_3d = conn_3d.cursor()
                        cursor_3d.execute("SELECT date_saisie FROM commandes_clients WHERE reference_piece = ?", (nom_pur,))
                        data = cursor_3d.fetchone()
                        date_saisie = data[0] if data else ""
                        cursor_3d.execute("DELETE FROM commandes_clients WHERE reference_piece = ?", (nom_pur,))
                        conn_3d.commit()
                            
                    with sqlite3.connect("atelier_resine.db", timeout=30.0) as conn_res:
                        cursor_res = conn_res.cursor()
                        cursor_res.execute("""
                            INSERT INTO commandes_clients (reference_piece, quantite, temps_unitaire, statut, date_saisie, echeance, consommable_lie, quantite_conso)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                        """, (nom_pur, qte, temps, statut_priorite, date_saisie, echeance, conso, poids))
                        conn_res.commit()
                else:
                    # Mise à jour classique dans la base 3D
                    with sqlite3.connect("atelier.db", timeout=30.0) as conn:
                        cursor = conn.cursor()
                        cursor.execute("""
                            UPDATE commandes_clients 
                            SET statut = ?, quantite = ?, echeance = ?, temps_unitaire = ?, quantite_conso = ?, consommable_lie = ? 
                            WHERE reference_piece = ?
                        """, (statut_priorite, qte, echeance, temps, poids, conso, nom_pur))
                        conn.commit()

            self.lbl_message.configure(text=f"✅ '{nom_pur}' prêt et envoyé dans {flux_nom} !", text_color="#10B981")
            self.after(4000, lambda: self.lbl_message.configure(text=""))
            
            # Réinitialisation de l'interface
            self.charger_references()
            self.entry_echeance.delete(0, 'end')
            self.var_priorite.set("Dans le flux")
            self.sur_changement_priorite("Dans le flux")

            # Met à jour le planning global ET les stocks projetés du magasin
            if self.fonction_rafraichir_global:
                self.fonction_rafraichir_global()

        except Exception as e:
            self.lbl_message.configure(text=f"❌ Erreur BDD: {e}", text_color=self.error_border)