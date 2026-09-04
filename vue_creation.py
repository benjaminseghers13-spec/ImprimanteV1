import customtkinter as ctk
import sqlite3
from tkinter import messagebox

class OngletCreation(ctk.CTkFrame):
    def __init__(self, master, fonction_rafraichir_global=None):
        super().__init__(master, fg_color="transparent")
        self.fonction_rafraichir_global = fonction_rafraichir_global
        self.default_border = "#4B5563"
        self.error_border = "#EF4444"

        # --- INITIALISATION BDD ---
        self.initialiser_bdd()

        # Variables de contrôle
        self.var_type_creation = ctk.StringVar(value="piece")
        self.base_selectionnee = None
        self.designation_selectionnee = ""
        self.ajout_zone_visible = False

        # --- EN-TÊTE ---
        en_tete = ctk.CTkFrame(self, fg_color="transparent")
        en_tete.pack(fill="x", pady=(0, 15))
        ctk.CTkLabel(en_tete, text="✨ Création de Référence Codifiée", font=ctk.CTkFont(size=26, weight="bold")).pack(side="left")

        self.scroll_frame = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.scroll_frame.pack(fill="both", expand=True)

        # ==========================================
        # ÉTAPE 1 : NOUVELLE PIÈCE OU NOUVELLE VERSION
        # ==========================================
        self.frame_etape1 = self.creer_carte("1️⃣ ÉTAPE 1 : Type de création")
        self.frame_etape1.master.pack(fill="x", pady=10, padx=5)
        
        radio_frame = ctk.CTkFrame(self.frame_etape1, fg_color="transparent")
        radio_frame.pack(anchor="w", pady=(5, 5))
        
        ctk.CTkRadioButton(radio_frame, text="Nouvelle pièce", variable=self.var_type_creation, value="piece", command=self.sur_changement_type, font=ctk.CTkFont(weight="bold")).pack(side="left", padx=(0, 30))
        ctk.CTkRadioButton(radio_frame, text="Nouvelle version", variable=self.var_type_creation, value="version", command=self.sur_changement_type, font=ctk.CTkFont(weight="bold")).pack(side="left")

        # ==========================================
        # CONTENEUR DYNAMIQUE (Change selon l'étape 1)
        # ==========================================
        self.conteneur_dynamique = ctk.CTkFrame(self.scroll_frame, fg_color="transparent")
        self.conteneur_dynamique.pack(fill="both", expand=True)

        # -----------------------------------------------------
        # VUE A : NOUVELLE PIÈCE (Étape 2 et 3)
        # -----------------------------------------------------
        self.frame_mode_piece = ctk.CTkFrame(self.conteneur_dynamique, fg_color="transparent")

        # ÉTAPE 2 : ZONE DE TRAVAIL
        self.frame_etape2 = self.creer_carte_interne(self.frame_mode_piece, "2️⃣ ÉTAPE 2 : Zone de travail (Détermine le préfixe)")
        self.frame_etape2.master.pack(fill="x", pady=10, padx=5)
        
        self.frame_choix_zone = ctk.CTkFrame(self.frame_etape2, fg_color="transparent")
        self.frame_choix_zone.pack(fill="x")
        
        # Ligne de sélection
        ligne_select = ctk.CTkFrame(self.frame_choix_zone, fg_color="transparent")
        ligne_select.pack(anchor="w")
        
        self.combo_zone = ctk.CTkComboBox(ligne_select, width=350, border_color=self.default_border, command=self.actualiser_apercu)
        self.combo_zone.pack(side="left", padx=(0, 10))
        
        self.btn_toggle_zone = ctk.CTkButton(ligne_select, text="➕ Nouvelle Zone", width=140, fg_color="#3B82F6", hover_color="#2563EB", command=self.toggle_ajout_zone)
        self.btn_toggle_zone.pack(side="left")

        # Ligne d'ajout manuel (Masquée par défaut)
        self.frame_ajout_zone = ctk.CTkFrame(self.frame_choix_zone, fg_color="#374151", corner_radius=8)
        
        ctk.CTkLabel(self.frame_ajout_zone, text="Préfixe (3 lettres) :", font=ctk.CTkFont(weight="bold")).grid(row=0, column=0, padx=(15, 5), pady=15)
        self.entry_new_prefix = ctk.CTkEntry(self.frame_ajout_zone, width=80, placeholder_text="Ex: ABC")
        self.entry_new_prefix.grid(row=0, column=1, padx=5, pady=15)
        
        ctk.CTkLabel(self.frame_ajout_zone, text="Désignation :", font=ctk.CTkFont(weight="bold")).grid(row=0, column=2, padx=(15, 5), pady=15)
        self.entry_new_nom = ctk.CTkEntry(self.frame_ajout_zone, width=250, placeholder_text="Ex: Nouvelle Cellule")
        self.entry_new_nom.grid(row=0, column=3, padx=5, pady=15)
        
        ctk.CTkButton(self.frame_ajout_zone, text="✅ Enregistrer Zone", width=120, fg_color="#10B981", hover_color="#059669", command=self.ajouter_zone).grid(row=0, column=4, padx=15, pady=15)

        # ÉTAPE 3 : DÉSIGNATION
        self.frame_etape3 = self.creer_carte_interne(self.frame_mode_piece, "3️⃣ ÉTAPE 3 : Désignation de la pièce")
        self.frame_etape3.master.pack(fill="x", pady=10, padx=5)
        self.entry_designation = ctk.CTkEntry(self.frame_etape3, width=450, border_color=self.default_border, placeholder_text="Ex: Guide chirurgical Supérieur")
        self.entry_designation.pack(anchor="w")
        self.entry_designation.bind("<KeyRelease>", self.actualiser_apercu)

        # -----------------------------------------------------
        # VUE B : NOUVELLE VERSION (Tableau par colonnes et Recherche)
        # -----------------------------------------------------
        self.frame_mode_version = self.creer_carte_interne(self.conteneur_dynamique, "🔄 SÉLECTION : Cliquez sur la pièce à versionner")
        
        # BARRE DE RECHERCHE
        frame_recherche = ctk.CTkFrame(self.frame_mode_version, fg_color="transparent")
        frame_recherche.pack(fill="x", pady=(0, 15))
        
        ctk.CTkLabel(frame_recherche, text="🔍 Rechercher :", font=ctk.CTkFont(weight="bold")).pack(side="left", padx=(0, 10))
        self.entry_recherche = ctk.CTkEntry(frame_recherche, width=350, placeholder_text="Ex: TRI-001 ou Guide...")
        self.entry_recherche.pack(side="left")
        self.entry_recherche.bind("<KeyRelease>", self.filtrer_versions)

        self.lbl_selection_active = ctk.CTkLabel(self.frame_mode_version, text="Sélection : Aucune pièce choisie", font=ctk.CTkFont(weight="bold", size=15), text_color="#F59E0B")
        self.lbl_selection_active.pack(anchor="w", pady=(0, 10))

        # Conteneur pour le tableau
        self.tableau_versions = ctk.CTkScrollableFrame(self.frame_mode_version, height=350, fg_color="transparent")
        self.tableau_versions.pack(fill="both", expand=True)

        # ==========================================
        # RÉSULTAT ET VALIDATION
        # ==========================================
        self.frame_resultat = ctk.CTkFrame(self.scroll_frame, fg_color="#374151", corner_radius=10)
        self.frame_resultat.pack(fill="x", pady=20, padx=5)
        
        ctk.CTkLabel(self.frame_resultat, text="Code Référence Généré :", font=ctk.CTkFont(size=14)).pack(pady=(15, 5))
        self.lbl_apercu = ctk.CTkLabel(self.frame_resultat, text="XXX-000-00", font=ctk.CTkFont(size=32, weight="bold"), text_color="#10B981")
        self.lbl_apercu.pack(pady=(0, 15))

        self.lbl_msg = ctk.CTkLabel(self.scroll_frame, text="", font=ctk.CTkFont(weight="bold"))
        self.lbl_msg.pack(pady=5)

        ctk.CTkButton(self.scroll_frame, text="💾 Générer, Sauvegarder et Copier", font=ctk.CTkFont(size=16, weight="bold"), height=50, fg_color="#10B981", hover_color="#059669", command=self.sauvegarder_reference).pack(fill="x", padx=5, pady=(0, 20))

        # --- Initialisation UI ---
        self.charger_zones()
        self.sur_changement_type()

    # ==========================================
    # LOGIQUE BASE DE DONNÉES ET VUES
    # ==========================================
    def initialiser_bdd(self):
        try:
            with sqlite3.connect("atelier.db") as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS zones_travail (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        nom TEXT UNIQUE,
                        prefixe TEXT UNIQUE
                    )
                """)
                
                cursor.execute("SELECT COUNT(*) FROM zones_travail")
                if cursor.fetchone()[0] == 0:
                    zones_initiales = [
                        ("Cellule de thermoformage", "CDT"),
                        ("Cellule de découpe", "CDD"),
                        ("Cellule de nettoyage / ensachage", "CDN"),
                        ("Lavage manuel", "LMA"),
                        ("Triosmile", "TRI"),
                        ("Puce de suivi à intégrer - Baracoda", "BAR"),
                        ("Finisher / Finition", "FIN"),
                        ("Projet brosse à dents personnalisée", "BAD"),
                        ("Prodways LD20 / D100", "PRW"),
                        ("Rapidshape", "RSH"),
                        ("Outilages", "OUT"),
                        ("Thermoformage", "THE")
                    ]
                    cursor.executemany("INSERT OR IGNORE INTO zones_travail (nom, prefixe) VALUES (?, ?)", zones_initiales)
                
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS references_generees (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        reference_complete TEXT UNIQUE,
                        statut TEXT,
                        quantite INTEGER DEFAULT 0,
                        temps_unitaire INTEGER DEFAULT 0,
                        quantite_conso REAL DEFAULT 0,
                        consommable_lie TEXT DEFAULT '',
                        designation TEXT DEFAULT ''
                    )
                """)
                
                cursor.execute("PRAGMA table_info(references_generees)")
                cols = [col[1] for col in cursor.fetchall()]
                if "designation" not in cols:
                    cursor.execute("ALTER TABLE references_generees ADD COLUMN designation TEXT DEFAULT ''")
                    
                conn.commit()
        except Exception as e:
            print(f"Erreur init bdd: {e}")

    def creer_carte(self, titre):
        carte = ctk.CTkFrame(self.scroll_frame, fg_color=("gray95", "#1F2937"), corner_radius=10)
        ctk.CTkLabel(carte, text=titre, font=ctk.CTkFont(weight="bold", size=15)).pack(anchor="w", padx=15, pady=(15, 5))
        contenu = ctk.CTkFrame(carte, fg_color="transparent")
        contenu.pack(fill="both", expand=True, padx=15, pady=(0, 15))
        return contenu

    def creer_carte_interne(self, parent, titre):
        carte = ctk.CTkFrame(parent, fg_color=("gray95", "#1F2937"), corner_radius=10)
        ctk.CTkLabel(carte, text=titre, font=ctk.CTkFont(weight="bold", size=15)).pack(anchor="w", padx=15, pady=(15, 5))
        contenu = ctk.CTkFrame(carte, fg_color="transparent")
        contenu.pack(fill="both", expand=True, padx=15, pady=(0, 15))
        return contenu

    def charger_zones(self):
        try:
            with sqlite3.connect("atelier.db") as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT nom, prefixe FROM zones_travail ORDER BY nom")
                zones = cursor.fetchall()
                
                valeurs = [f"{nom} ({prefixe})" for nom, prefixe in zones] if zones else ["--- Aucune zone ---"]
                self.combo_zone.configure(values=valeurs)
                if valeurs: self.combo_zone.set(valeurs[0])
        except Exception as e:
            print("Erreur zones:", e)

    def toggle_ajout_zone(self):
        self.ajout_zone_visible = not self.ajout_zone_visible
        if self.ajout_zone_visible:
            self.frame_ajout_zone.pack(anchor="w", pady=(10, 0), fill="x")
            self.btn_toggle_zone.configure(text="➖ Fermer", fg_color="#6B7280", hover_color="#4B5563")
        else:
            self.frame_ajout_zone.pack_forget()
            self.btn_toggle_zone.configure(text="➕ Nouvelle Zone", fg_color="#3B82F6", hover_color="#2563EB")
            self.entry_new_prefix.delete(0, 'end')
            self.entry_new_nom.delete(0, 'end')

    def ajouter_zone(self):
        code = self.entry_new_prefix.get().strip().upper()
        nom = self.entry_new_nom.get().strip()
        
        if not code or not nom:
            messagebox.showerror("Erreur", "Veuillez remplir le préfixe ET la désignation.")
            return
            
        if len(code) != 3:
            messagebox.showerror("Erreur", "Le préfixe doit comporter exactement 3 lettres !")
            return
            
        try:
            with sqlite3.connect("atelier.db") as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT nom FROM zones_travail WHERE prefixe = ?", (code,))
                existant = cursor.fetchone()
                if existant:
                    messagebox.showerror("Bloqué !", f"Le préfixe '{code}' est déjà utilisé par :\n{existant[0]}\n\nVeuillez en choisir un autre.")
                    return
                    
                cursor.execute("INSERT INTO zones_travail (nom, prefixe) VALUES (?, ?)", (nom, code))
                conn.commit()
            
            self.charger_zones()
            self.combo_zone.set(f"{nom} ({code})")
            
            if self.var_type_creation.get() == "version":
                self.charger_tableau_versions()
                
            self.actualiser_apercu()
            self.toggle_ajout_zone()
            
        except sqlite3.IntegrityError:
            messagebox.showerror("Erreur", "Ce nom de zone existe déjà.")
        except Exception as e:
            messagebox.showerror("Erreur", f"Erreur base de données : {e}")

    def sur_changement_type(self):
        if self.var_type_creation.get() == "piece":
            self.frame_mode_version.master.pack_forget()
            self.frame_mode_piece.pack(fill="x", expand=True)
            self.base_selectionnee = None
        else:
            self.frame_mode_piece.pack_forget()
            self.frame_mode_version.master.pack(fill="x", expand=True, pady=10, padx=5)
            self.entry_recherche.delete(0, 'end') # Vide la recherche au basculement
            self.charger_tableau_versions()
            
        self.actualiser_apercu()

    def filtrer_versions(self, event=None):
        """Déclenchée à chaque touche tapée dans la barre de recherche."""
        texte_recherche = self.entry_recherche.get()
        self.charger_tableau_versions(filtre=texte_recherche)

    def charger_tableau_versions(self, filtre=""):
        for widget in self.tableau_versions.winfo_children():
            widget.destroy()

        filtre = filtre.lower().strip()
        prefix_to_nom = {}
        groupes = {} 
        
        try:
            with sqlite3.connect("atelier.db") as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT prefixe, nom FROM zones_travail ORDER BY nom")
                for pre, nom in cursor.fetchall():
                    prefix_to_nom[pre] = nom
                    groupes[pre] = {} 
                    
                cursor.execute("SELECT reference_complete, designation FROM references_generees")
                for row in cursor.fetchall():
                    ref = row[0]
                    desig = row[1] if row[1] else "Sans nom"
                    
                    # --- FILTRAGE DE RECHERCHE ---
                    if filtre:
                        if filtre not in ref.lower() and filtre not in desig.lower():
                            continue # Ignore cette pièce si elle ne matche pas
                    
                    parts = ref.split('-')
                    if len(parts) == 3:
                        prefix = parts[0]
                        base = f"{parts[0]}-{parts[1]}"
                        
                        try:
                            version = int(parts[2])
                            if prefix not in groupes:
                                groupes[prefix] = {}
                                prefix_to_nom[prefix] = "Zone inconnue"
                                
                            if base not in groupes[prefix] or version > groupes[prefix][base]['version']:
                                groupes[prefix][base] = {'version': version, 'designation': desig}
                        except ValueError: 
                            pass
        except Exception as e:
            print(f"Erreur chargement versions: {e}")

        # Vérifier s'il y a des résultats globaux
        resultats_trouves = False

        conteneur_grille = ctk.CTkFrame(self.tableau_versions, fg_color="transparent")
        conteneur_grille.pack(anchor="nw", fill="x")

        row_idx = 0
        col_idx = 0

        for prefix, dict_bases in sorted(groupes.items(), key=lambda x: prefix_to_nom.get(x[0], x[0])):
            # Si on fait une recherche, on masque complètement les colonnes (zones) vides
            if filtre and not dict_bases:
                continue

            resultats_trouves = True
            nom_zone = prefix_to_nom.get(prefix, prefix)
            
            col_frame = ctk.CTkFrame(conteneur_grille, fg_color="gray95" if ctk.get_appearance_mode() == "Light" else "#1F2937", corner_radius=5)
            col_frame.grid(row=row_idx, column=col_idx, sticky="n", padx=10, pady=10, ipadx=10, ipady=10)
            
            ctk.CTkLabel(col_frame, text=nom_zone, font=ctk.CTkFont(weight="bold", size=14)).pack(pady=(0,2))
            ctk.CTkLabel(col_frame, text=prefix, font=ctk.CTkFont(size=12, weight="bold"), text_color="#3B82F6").pack(pady=(0,10))
            
            if not dict_bases:
                ctk.CTkLabel(col_frame, text="Aucune pièce", font=ctk.CTkFont(slant="italic", size=12), text_color="gray").pack(pady=10)
            else:
                for base, data in sorted(dict_bases.items()):
                    ref_a_afficher = f"{base}-{data['version']:02d}"
                    btn = ctk.CTkButton(
                        col_frame, 
                        text=ref_a_afficher, 
                        width=130,
                        fg_color="#374151",
                        hover_color="#10B981",
                        command=lambda b=base, d=data['designation']: self.selectionner_base(b, d)
                    )
                    btn.pack(pady=3)
                
            col_idx += 1
            if col_idx > 4: 
                col_idx = 0
                row_idx += 1

        if not resultats_trouves:
            if filtre:
                ctk.CTkLabel(self.tableau_versions, text=f"📭 Aucun résultat pour '{filtre}'", font=ctk.CTkFont(slant="italic")).pack(pady=20)
            else:
                ctk.CTkLabel(self.tableau_versions, text="📭 Aucune zone de travail trouvée.", font=ctk.CTkFont(slant="italic")).pack(pady=20)

    def selectionner_base(self, base, designation):
        self.base_selectionnee = base
        self.designation_selectionnee = designation
        self.lbl_selection_active.configure(text=f"✅ Sélection : {base} ({designation})", text_color="#10B981")
        self.actualiser_apercu()

    def actualiser_apercu(self, event=None):
        mode = self.var_type_creation.get()
        ref_calculee = "ERREUR"

        if mode == "piece":
            texte_zone = self.combo_zone.get()
            if "(" in texte_zone and ")" in texte_zone:
                prefixe = texte_zone.split("(")[1].replace(")", "")
                
                max_num = 0
                try:
                    with sqlite3.connect("atelier.db") as conn:
                        cursor = conn.cursor()
                        cursor.execute("SELECT reference_complete FROM references_generees WHERE reference_complete LIKE ?", (f"{prefixe}-___-__",))
                        for row in cursor.fetchall():
                            try:
                                num = int(row[0].split('-')[1])
                                if num > max_num: max_num = num
                            except ValueError: 
                                pass
                except Exception: 
                    pass
                
                nouveau_num = max_num + 1
                ref_calculee = f"{prefixe}-{nouveau_num:03d}-01"
            else:
                ref_calculee = "XXX-000-01"
                
        elif mode == "version":
            if not self.base_selectionnee:
                ref_calculee = "SÉLECTIONNEZ UNE PIÈCE ⬆️"
            else:
                max_ver = 0
                try:
                    with sqlite3.connect("atelier.db") as conn:
                        cursor = conn.cursor()
                        cursor.execute("SELECT reference_complete FROM references_generees WHERE reference_complete LIKE ?", (f"{self.base_selectionnee}-__",))
                        for row in cursor.fetchall():
                            try:
                                ver = int(row[0].split('-')[2])
                                if ver > max_ver: max_ver = ver
                            except ValueError: 
                                pass
                except Exception: 
                    pass
                
                nouvelle_ver = max_ver + 1
                ref_calculee = f"{self.base_selectionnee}-{nouvelle_ver:02d}"

        self.lbl_apercu.configure(text=ref_calculee)

    def sauvegarder_reference(self):
        ref_complete = self.lbl_apercu.cget("text")
        
        if "ERREUR" in ref_complete or "SÉLECTIONNEZ" in ref_complete or "XXX" in ref_complete:
            self.lbl_msg.configure(text="⚠️ Aperçu invalide. Remplissez tous les champs.", text_color=self.error_border)
            return

        mode = self.var_type_creation.get()
        if mode == "piece":
            designation = self.entry_designation.get().strip()
            if not designation:
                self.lbl_msg.configure(text="⚠️ La désignation est obligatoire pour une nouvelle pièce.", text_color=self.error_border)
                return
        else:
            designation = self.designation_selectionnee 

        try:
            with sqlite3.connect("atelier.db") as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO references_generees (reference_complete, designation, statut)
                    VALUES (?, ?, 'Créée')
                """, (ref_complete, designation))
                conn.commit()

            # --- COPIE DANS LE PRESSE-PAPIER ---
            self.clipboard_clear()
            self.clipboard_append(ref_complete)
            self.update()

            self.lbl_msg.configure(text=f"✅ '{ref_complete}' sauvegardée et copiée dans le presse-papier !", text_color="#10B981")
            
            # Nettoyage
            if mode == "piece":
                self.entry_designation.delete(0, 'end')
            elif mode == "version":
                self.charger_tableau_versions() 
                
            self.actualiser_apercu()
            self.after(4000, lambda: self.lbl_msg.configure(text=""))
            
            if self.fonction_rafraichir_global:
                self.fonction_rafraichir_global()
                
        except sqlite3.IntegrityError:
            self.lbl_msg.configure(text=f"⚠️ La référence '{ref_complete}' existe déjà.", text_color=self.error_border)
        except Exception as e:
            self.lbl_msg.configure(text=f"❌ Erreur BDD: {e}", text_color=self.error_border)

    def charger_bases_existantes(self):
        self.charger_zones()
        if self.var_type_creation.get() == "version":
            self.charger_tableau_versions()