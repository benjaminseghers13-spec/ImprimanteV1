import customtkinter as ctk
import sqlite3
import re
import os
import shutil
import zipfile
import ftplib
import ssl
from datetime import datetime
from tkinter import filedialog

class OngletCreation(ctk.CTkFrame):
    def __init__(self, master, fonction_rafraichir_global=None):
        super().__init__(master, fg_color="transparent")
        self.fonction_rafraichir_global = fonction_rafraichir_global
        
        # Variable pour mémoriser le fichier sélectionné
        self.chemin_fichier_source = None

        # --- EN-TÊTE ---
        en_tete = ctk.CTkFrame(self, fg_color="transparent")
        en_tete.pack(fill="x", pady=(0, 15))
        ctk.CTkLabel(en_tete, text="✨ Création & Paramétrage", font=ctk.CTkFont(size=26, weight="bold")).pack(side="left")

        # --- CONTENEUR DÉROULANT ---
        self.scroll_frame = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.scroll_frame.pack(fill="both", expand=True, padx=0, pady=0)

        # Variables de contrôle
        self.var_type_creation = ctk.StringVar(value="Nouvelle Pièce") 
        self.var_type_outil = ctk.StringVar(value="Interne") 

        self.error_border = "#EF4444" 
        self.default_border = "#4B5563"

        # ==========================================
        # ÉTAPE 1 : TYPE DE CRÉATION
        # ==========================================
        self.frame_etape1 = self.creer_carte("1️⃣ ÉTAPE 1 : Que voulez-vous planifier ?")
        self.frame_etape1.master.pack(fill="x", pady=10, padx=5)

        radio_frame1 = ctk.CTkFrame(self.frame_etape1, fg_color="transparent")
        radio_frame1.pack(anchor="w", pady=(5, 10))
        ctk.CTkRadioButton(radio_frame1, text="Nouvelle Pièce", variable=self.var_type_creation, value="Nouvelle Pièce", command=self.update_ui, font=ctk.CTkFont(weight="bold")).pack(side="left", padx=(0, 15))
        ctk.CTkRadioButton(radio_frame1, text="Nouvelle Version d'une pièce", variable=self.var_type_creation, value="Nouvelle Version", command=self.update_ui, font=ctk.CTkFont(weight="bold")).pack(side="left", padx=10)
        ctk.CTkRadioButton(radio_frame1, text="Relancer une pièce existante", variable=self.var_type_creation, value="Pièce Existante", command=self.update_ui, font=ctk.CTkFont(weight="bold")).pack(side="left", padx=10)

        # Sous-section : Choix base
        self.frame_choix_base = ctk.CTkFrame(self.frame_etape1, fg_color="transparent")
        ctk.CTkLabel(self.frame_choix_base, text="Recherchez ou tapez la base (ex: CDT-001) :", text_color="gray60").pack(anchor="w", pady=(5, 2))
        self.combo_versions = ctk.CTkComboBox(self.frame_choix_base, width=350, border_color=self.default_border, command=self.sur_choix_version)
        self.combo_versions.pack(anchor="w")
        self.combo_versions.bind("<KeyRelease>", lambda e: self.sur_choix_version(self.combo_versions.get()))

        # Sous-section : Choix existante
        self.frame_choix_existante = ctk.CTkFrame(self.frame_etape1, fg_color="transparent")
        ctk.CTkLabel(self.frame_choix_existante, text="Sélectionnez la référence à reproduire :", text_color="gray60").pack(anchor="w", pady=(5, 2))
        self.combo_existante = ctk.CTkComboBox(self.frame_choix_existante, width=350, border_color=self.default_border, command=self.sur_choix_existante)
        self.combo_existante.pack(anchor="w")
        self.combo_existante.bind("<KeyRelease>", lambda e: self.sur_choix_existante(self.combo_existante.get()))

        # ==========================================
        # ÉTAPE 2 : TYPE D'OUTILLAGE
        # ==========================================
        self.frame_etape2 = self.creer_carte("2️⃣ ÉTAPE 2 : Origine de la pièce")

        radio_frame2 = ctk.CTkFrame(self.frame_etape2, fg_color="transparent")
        radio_frame2.pack(anchor="w", pady=(5, 10))
        ctk.CTkRadioButton(radio_frame2, text="Outillage Interne", variable=self.var_type_outil, value="Interne", command=self.update_ui, font=ctk.CTkFont(weight="bold")).pack(side="left", padx=(0, 20))
        ctk.CTkRadioButton(radio_frame2, text="Commande Client", variable=self.var_type_outil, value="Client", command=self.update_ui, font=ctk.CTkFont(weight="bold")).pack(side="left", padx=10)

        self.frame_ref_client = ctk.CTkFrame(self.frame_etape2, fg_color="transparent")
        ctk.CTkLabel(self.frame_ref_client, text="Tapez la référence exacte du client :", text_color="gray60").pack(anchor="w", pady=(5, 2))
        self.entry_client = ctk.CTkEntry(self.frame_ref_client, width=350, placeholder_text="Ex: SUPPORT_CASQUE_CLIENT", border_color=self.default_border)
        self.entry_client.pack(anchor="w")

        # ==========================================
        # ÉTAPE 3 : SECTEUR D'APPLICATION
        # ==========================================
        self.frame_etape3 = self.creer_carte("3️⃣ ÉTAPE 3 : Secteur d'application")

        ctk.CTkLabel(self.frame_etape3, text="Sélectionnez ou tapez le secteur :", text_color="gray60").pack(anchor="w", pady=(5, 2))
        self.combo_secteur = ctk.CTkComboBox(self.frame_etape3, width=350, border_color=self.default_border, command=self.sur_changement_secteur)
        self.combo_secteur.pack(anchor="w")
        self.combo_secteur.bind("<KeyRelease>", lambda e: self.sur_changement_secteur(self.combo_secteur.get()))

        self.frame_nouveau_secteur = ctk.CTkFrame(self.frame_etape3, fg_color=("#E5E7EB", "#111827"), corner_radius=8)
        ctk.CTkLabel(self.frame_nouveau_secteur, text="➕ Créer un nouveau secteur", font=ctk.CTkFont(weight="bold")).grid(row=0, column=0, columnspan=2, sticky="w", pady=10, padx=10)
        ctk.CTkLabel(self.frame_nouveau_secteur, text="Code (ex: PRW) :").grid(row=1, column=0, sticky="w", padx=10, pady=5)
        self.entry_nouveau_prefix = ctk.CTkEntry(self.frame_nouveau_secteur, width=150, border_color=self.default_border)
        self.entry_nouveau_prefix.grid(row=1, column=1, sticky="w", padx=10, pady=5)
        ctk.CTkLabel(self.frame_nouveau_secteur, text="Nom du secteur :").grid(row=2, column=0, sticky="w", padx=10, pady=5)
        self.entry_nouveau_nom = ctk.CTkEntry(self.frame_nouveau_secteur, width=250, border_color=self.default_border)
        self.entry_nouveau_nom.grid(row=2, column=1, sticky="w", padx=10, pady=5)
        ctk.CTkButton(self.frame_nouveau_secteur, text="Enregistrer ce secteur", fg_color="#10B981", hover_color="#059669", command=self.enregistrer_nouveau_secteur).grid(row=3, column=0, columnspan=2, pady=15, padx=10)

        # ==========================================
        # ÉTAPE 4 : TEMPS ET MATIÈRE (Automatisé)
        # ==========================================
        self.frame_etape4 = self.creer_carte("4️⃣ ÉTAPE 4 : Temps & Matière (Automatisé)")
        self.frame_etape4.master.pack(fill="x", pady=10, padx=5)

        # Bouton d'importation de fichier
        cadre_import = ctk.CTkFrame(self.frame_etape4, fg_color=("#E0E7FF", "#1E3A8A"), corner_radius=8)
        cadre_import.pack(fill="x", pady=(0, 15), ipadx=10, ipady=5)
        
        self.lbl_info_import = ctk.CTkLabel(cadre_import, text="💡 Gagnez du temps : importez votre fichier Slicer (.gcode, .3mf)", font=ctk.CTkFont(slant="italic"))
        self.lbl_info_import.pack(side="left", padx=10)
        
        ctk.CTkButton(cadre_import, text="📥 Importer fichier", font=ctk.CTkFont(weight="bold"), fg_color="#3B82F6", hover_color="#2563EB", command=self.importer_fichier_slicer).pack(side="right", padx=10)

        grid_piece = ctk.CTkFrame(self.frame_etape4, fg_color="transparent")
        grid_piece.pack(fill="x")

        ctk.CTkLabel(grid_piece, text="Temps unitaire (min) :").grid(row=0, column=0, sticky="w", padx=5, pady=8)
        self.entry_temps = ctk.CTkEntry(grid_piece, width=120, border_color=self.default_border)
        self.entry_temps.insert(0, "60")
        self.entry_temps.grid(row=0, column=1, sticky="w", padx=15, pady=8)

        ctk.CTkLabel(grid_piece, text="Consommable lié :").grid(row=1, column=0, sticky="w", padx=5, pady=8)
        self.combo_conso = ctk.CTkComboBox(grid_piece, width=220, border_color=self.default_border)
        self.combo_conso.grid(row=1, column=1, sticky="w", padx=15, pady=8)

        ctk.CTkLabel(grid_piece, text="Qté consommée / pièce :").grid(row=2, column=0, sticky="w", padx=5, pady=8)
        self.entry_qte_conso = ctk.CTkEntry(grid_piece, width=120, border_color=self.default_border)
        self.entry_qte_conso.insert(0, "0")
        self.entry_qte_conso.grid(row=2, column=1, sticky="w", padx=15, pady=8)

        # ==========================================
        # ÉTAPE 5 : QUANTITÉ & PRIORITÉ (Manuel)
        # ==========================================
        self.frame_etape5 = self.creer_carte("5️⃣ ÉTAPE 5 : Quantité & Planification")
        self.frame_etape5.master.pack(fill="x", pady=10, padx=5)

        grid_planif = ctk.CTkFrame(self.frame_etape5, fg_color="transparent")
        grid_planif.pack(fill="x")

        ctk.CTkLabel(grid_planif, text="Quantité à produire :").grid(row=0, column=0, sticky="w", padx=5, pady=8)
        self.entry_qte = ctk.CTkEntry(grid_planif, width=120, border_color=self.default_border)
        self.entry_qte.insert(0, "1")
        self.entry_qte.grid(row=0, column=1, sticky="w", padx=15, pady=8)

        ctk.CTkLabel(grid_planif, text="Priorité de production :").grid(row=1, column=0, sticky="w", padx=5, pady=8)
        self.combo_priorite = ctk.CTkOptionMenu(grid_planif, values=["Flux classique", "Prochaine production", "Avant échéance client"], fg_color="#374151", command=self.update_ui)
        self.combo_priorite.grid(row=1, column=1, sticky="w", padx=15, pady=8)

        self.frame_echeance = ctk.CTkFrame(grid_planif, fg_color="transparent")
        ctk.CTkLabel(self.frame_echeance, text="Échéance (JJ/MM) :").pack(side="left", padx=5)
        self.entry_echeance = ctk.CTkEntry(self.frame_echeance, width=100, placeholder_text="ex: 15/10", border_color=self.default_border)
        self.entry_echeance.pack(side="left", padx=5)

        # VALIDATION FINALE
        self.lbl_message = ctk.CTkLabel(self.scroll_frame, text="", font=ctk.CTkFont(size=14, weight="bold"))
        self.lbl_message.pack(pady=10)

        ctk.CTkButton(self.scroll_frame, text="🚀 Valider, Renommer & Planifier", font=ctk.CTkFont(size=16, weight="bold"), height=50, fg_color="#1D4ED8", hover_color="#1E3A8A", command=self.creer_piece).pack(fill="x", padx=5, pady=(0, 20))

        self.charger_secteurs()
        self.charger_references_existantes()
        self.charger_toutes_references()
        self.charger_consommables_menu()
        self.update_ui()

    # ==========================================
    # LOGIQUE D'ANALYSE DE FICHIER (Le "Traducteur")
    # ==========================================
    def importer_fichier_slicer(self):
        fichier = filedialog.askopenfilename(
            title="Sélectionner le fichier d'impression",
            filetypes=(("Fichiers Slicer", "*.gcode *.3mf *.bgcode"), ("Tous les fichiers", "*.*"))
        )
        
        if not fichier: return 
        
        try:
            temps_min = 0
            poids_g = 0.0
            
            if fichier.endswith('.3mf'):
                with zipfile.ZipFile(fichier, 'r') as z:
                    if 'Metadata/slice_info.config' in z.namelist():
                        contenu = z.read('Metadata/slice_info.config').decode('utf-8', errors='ignore')
                        match_temps = re.search(r'<time>(\d+)</time>', contenu)
                        if match_temps: temps_min = int(match_temps.group(1)) // 60
                        match_poids = re.search(r'<weight>([\d.]+)</weight>', contenu)
                        if match_poids: poids_g = float(match_poids.group(1))
            else:
                texte_a_analyser = ""
                with open(fichier, 'rb') as f:
                    texte_a_analyser += f.read(10000).decode('utf-8', errors='ignore')
                    f.seek(0, 2) 
                    taille = f.tell()
                    f.seek(max(taille - 10000, 0))
                    texte_a_analyser += f.read().decode('utf-8', errors='ignore')

                match_t = re.search(r'; estimated printing time.*?=\s*(?:(\d+)d\s*)?(?:(\d+)h\s*)?(?:(\d+)m\s*)?', texte_a_analyser)
                if match_t:
                    temps_min = (int(match_t.group(1) or 0) * 1440) + (int(match_t.group(2) or 0) * 60) + int(match_t.group(3) or 0)
                if temps_min == 0:
                    match_c = re.search(r';TIME:(\d+)', texte_a_analyser)
                    if match_c: temps_min = int(match_c.group(1)) // 60

                match_p = re.search(r'; total filament used \[g\] = ([\d.]+)', texte_a_analyser)
                if match_p: poids_g = float(match_p.group(1))
                if poids_g == 0.0:
                    match_c2 = re.search(r';Filament used:.*, ([\d.]+)g', texte_a_analyser)
                    if match_c2: poids_g = float(match_c2.group(1))

            if temps_min > 0 or poids_g > 0:
                self.entry_temps.delete(0, 'end'); self.entry_temps.insert(0, str(max(1, temps_min)))
                self.entry_qte_conso.delete(0, 'end'); self.entry_qte_conso.insert(0, str(round(poids_g, 2)))
                
                self.chemin_fichier_source = fichier
                nom_court = os.path.basename(fichier)
                self.lbl_info_import.configure(text=f"📎 Fichier prêt : {nom_court}", text_color="#10B981")
            else:
                self.lbl_message.configure(text=f"⚠️ Impossible de trouver les infos dans ce fichier.", text_color="orange")
                
        except Exception as e:
            self.lbl_message.configure(text=f"❌ Erreur de lecture : {e}", text_color=self.error_border)

    # ==========================================
    # MÉTHODES D'INTERFACE EXISTANTES
    # ==========================================
    def creer_carte(self, titre):
        carte = ctk.CTkFrame(self.scroll_frame, fg_color=("gray95", "#1F2937"), corner_radius=10)
        ctk.CTkLabel(carte, text=titre, font=ctk.CTkFont(weight="bold", size=15)).pack(anchor="w", padx=15, pady=(15, 5))
        contenu = ctk.CTkFrame(carte, fg_color="transparent")
        contenu.pack(fill="both", expand=True, padx=15, pady=(0, 15))
        return contenu

    def charger_references_existantes(self):
        try:
            with sqlite3.connect("atelier_resine.db", timeout=30.0) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT DISTINCT reference_complete FROM references_generees ORDER BY id DESC")
                refs = cursor.fetchall()
        except: refs = []
        base_refs = set()
        for (r,) in refs:
            parts = r.split('-')
            if len(parts) >= 2: base_refs.add(f"{parts[0]}-{parts[1]}")
        self.combo_versions.configure(values=sorted(list(base_refs), reverse=True))
        self.combo_versions.set("") 

    def charger_toutes_references(self):
        try:
            with sqlite3.connect("atelier_resine.db", timeout=30.0) as conn:
                cursor = conn.cursor()
                refs = set()
                cursor.execute("SELECT reference_complete FROM references_generees")
                for (r,) in cursor.fetchall(): refs.add(r)
                try:
                    cursor.execute("SELECT reference_piece FROM commandes_clients")
                    for (r,) in cursor.fetchall(): refs.add(r)
                except: pass
                try:
                    cursor.execute("SELECT reference FROM historique_production")
                    for (r,) in cursor.fetchall(): refs.add(r)
                except: pass
            self.combo_existante.configure(values=sorted(list(refs)))
            self.combo_existante.set("")
        except: pass

    def charger_secteurs(self):
        try:
            with sqlite3.connect("atelier_resine.db", timeout=30.0) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT prefix, nom FROM parametres_references ORDER BY prefix")
                secteurs_db = cursor.fetchall()
        except: secteurs_db = []
        valeurs_menu = [f"{prefix} - {nom}" for prefix, nom in secteurs_db]
        valeurs_menu.append("*+ Nouveau secteur...*")
        self.combo_secteur.configure(values=valeurs_menu)
        self.combo_secteur.set("") 

    def charger_consommables_menu(self):
        try:
            with sqlite3.connect("atelier_resine.db", timeout=30.0) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT nom FROM consommables ORDER BY nom")
                rows = cursor.fetchall()
        except: rows = []
        valeurs = ["--- Aucun ---"] + [r[0] for r in rows]
        self.combo_conso.configure(values=valeurs)
        self.combo_conso.set("--- Aucun ---")

    def update_ui(self, *args):
        self.entry_qte.configure(border_color=self.default_border)
        self.entry_temps.configure(border_color=self.default_border)
        self.entry_client.configure(border_color=self.default_border)
        self.entry_echeance.configure(border_color=self.default_border)
        self.combo_versions.configure(border_color=self.default_border)
        self.combo_existante.configure(border_color=self.default_border)
        self.combo_secteur.configure(border_color=self.default_border)
        self.lbl_message.configure(text="")

        type_creation = self.var_type_creation.get()
        type_outil = self.var_type_outil.get()

        if type_creation == "Nouvelle Version":
            self.frame_choix_base.pack(fill="x", pady=5)
            self.frame_choix_existante.pack_forget()
            self.frame_etape2.master.pack_forget() 
            self.frame_etape3.master.pack_forget()
        elif type_creation == "Pièce Existante":
            self.frame_choix_existante.pack(fill="x", pady=5)
            self.frame_choix_base.pack_forget()
            self.frame_etape2.master.pack_forget() 
            self.frame_etape3.master.pack_forget()
        else:
            self.frame_choix_base.pack_forget()
            self.frame_choix_existante.pack_forget()
            self.frame_etape2.master.pack(fill="x", pady=10, padx=5, after=self.frame_etape1.master)
            if type_outil == "Client":
                self.frame_ref_client.pack(fill="x", pady=5)
                self.frame_etape3.master.pack_forget()
            else:
                self.frame_ref_client.pack_forget()
                self.frame_etape3.master.pack(fill="x", pady=10, padx=5, after=self.frame_etape2.master)
                self.sur_changement_secteur(self.combo_secteur.get())

        # Déplacement dynamique de l'échéance dans la grille 5
        if self.combo_priorite.get() == "Avant échéance client":
            self.frame_echeance.grid(row=2, column=0, columnspan=2, sticky="w", pady=5, padx=5)
        else:
            self.frame_echeance.grid_forget()

    def sur_changement_secteur(self, choix):
        if choix == "*+ Nouveau secteur...*": self.frame_nouveau_secteur.pack(fill="x", pady=15)
        else: self.frame_nouveau_secteur.pack_forget()

    def sur_choix_version(self, choix):
        if not choix: return
        parts = choix.split('-')
        base_ref = f"{parts[0]}-{parts[1]}" if len(parts) >= 2 else choix
        try:
            with sqlite3.connect("atelier_resine.db", timeout=30.0) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT quantite, temps_unitaire, consommable_lie, quantite_conso FROM references_generees WHERE reference_complete LIKE ? ORDER BY version DESC LIMIT 1", (f"{base_ref}-%",))
                data = cursor.fetchone()
            if data:
                self.entry_qte.delete(0, 'end'); self.entry_qte.insert(0, str(data[0]))
                self.entry_temps.delete(0, 'end'); self.entry_temps.insert(0, str(data[1]))
                if data[2]: self.combo_conso.set(data[2])
                if data[3]: self.entry_qte_conso.delete(0, 'end'); self.entry_qte_conso.insert(0, str(data[3]))
        except: pass

    def sur_choix_existante(self, choix):
        if not choix: return
        ref_pure = choix.strip()
        try:
            with sqlite3.connect("atelier_resine.db", timeout=30.0) as conn:
                cursor = conn.cursor()
                data = None
                cursor.execute("SELECT temps_unitaire, consommable_lie, quantite_conso FROM references_generees WHERE reference_complete = ? LIMIT 1", (ref_pure,))
                data = cursor.fetchone()
                if not data:
                    try:
                        cursor.execute("SELECT temps_unitaire, consommable_lie, quantite_conso FROM commandes_clients WHERE reference_piece = ? LIMIT 1", (ref_pure,))
                        data = cursor.fetchone()
                    except: pass
                if not data:
                    try:
                        cursor.execute("SELECT temps_unitaire FROM historique_production WHERE reference = ? LIMIT 1", (ref_pure,))
                        hist_data = cursor.fetchone()
                        if hist_data: data = (hist_data[0], "", 0.0)
                    except: pass

            if data:
                self.entry_temps.delete(0, 'end'); self.entry_temps.insert(0, str(data[0]))
                if len(data) > 1 and data[1]: self.combo_conso.set(data[1])
                else: self.combo_conso.set("--- Aucun ---")
                self.entry_qte_conso.delete(0, 'end')
                if len(data) > 2 and data[2] is not None: self.entry_qte_conso.insert(0, str(data[2]))
                else: self.entry_qte_conso.insert(0, "0")
        except: pass

    def enregistrer_nouveau_secteur(self):
        prefix = self.entry_nouveau_prefix.get().strip().upper()
        nom = self.entry_nouveau_nom.get().strip()
        if not prefix or not nom:
            self.lbl_message.configure(text="⚠️ Code et nom du secteur requis.", text_color=self.error_border)
            return
        try:
            with sqlite3.connect("atelier_resine.db", timeout=30.0) as conn:
                cursor = conn.cursor()
                cursor.execute("INSERT OR REPLACE INTO parametres_references (prefix, nom) VALUES (?, ?)", (prefix, nom))
                conn.commit()
            self.entry_nouveau_prefix.delete(0, 'end'); self.entry_nouveau_nom.delete(0, 'end')
            self.frame_nouveau_secteur.pack_forget()
            self.charger_secteurs()
            self.combo_secteur.set(f"{prefix} - {nom}")
            self.update_ui()
        except: pass

    def creer_piece(self):
        self.entry_qte.configure(border_color=self.default_border)
        self.entry_temps.configure(border_color=self.default_border)
        
        try:
            qte = int(self.entry_qte.get())
            temps = int(self.entry_temps.get())
            qte_conso = float(self.entry_qte_conso.get())
        except ValueError:
            self.lbl_message.configure(text="⚠️ Quantité, temps et conso doivent être des nombres.", text_color=self.error_border)
            return

        conso_lie = self.combo_conso.get()
        if conso_lie == "--- Aucun ---": conso_lie = ""
        statut = self.combo_priorite.get()
        echeance = self.entry_echeance.get().strip() if statut == "Avant échéance client" else ""

        date_creation = datetime.now().strftime("%d/%m/%Y %H:%M")
        type_creation = self.var_type_creation.get()
        nouvelle_ref = ""
        
        try:
            with sqlite3.connect("atelier_resine.db", timeout=30.0) as conn:
                cursor = conn.cursor()

                if type_creation == "Nouvelle Version":
                    base_choisie = self.combo_versions.get().strip()
                    parts = base_choisie.split('-')
                    prefix = parts[0] if len(parts) > 0 else "UNK"
                    num_seq = int(parts[1]) if len(parts) >= 2 and parts[1].isdigit() else 1
                    cursor.execute("SELECT version FROM references_generees WHERE reference_complete LIKE ? ORDER BY version DESC LIMIT 1", (f"{prefix}-{num_seq:03d}-%",))
                    res = cursor.fetchone()
                    version_val = res[0] + 1 if res else 2
                    nouvelle_ref = f"{prefix}-{num_seq:03d}-{version_val:02d}"

                    cursor.execute("""
                        INSERT INTO references_generees (prefix, reference_complete, numero_sequentiel, version, quantite, temps_unitaire, statut, date_creation, consommable_lie, quantite_conso)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (prefix, nouvelle_ref, num_seq, version_val, qte, temps, statut, date_creation, conso_lie, qte_conso))

                elif type_creation == "Pièce Existante":
                    nouvelle_ref = self.combo_existante.get().strip()
                    if "-" in nouvelle_ref:
                        parts = nouvelle_ref.split('-')
                        prefix = parts[0] if len(parts) > 0 else "UNK"
                        num_seq = int(parts[1]) if len(parts) > 1 and parts[1].isdigit() else 1
                        version_val = int(parts[2]) if len(parts) > 2 and parts[2].isdigit() else 1
                        cursor.execute("""
                            INSERT INTO references_generees (prefix, reference_complete, numero_sequentiel, version, quantite, temps_unitaire, statut, date_creation, consommable_lie, quantite_conso)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """, (prefix, nouvelle_ref, num_seq, version_val, qte, temps, statut, date_creation, conso_lie, qte_conso))
                    else:
                        cursor.execute("""
                            INSERT INTO commandes_clients (reference_piece, quantite, temps_unitaire, statut, date_saisie, echeance, consommable_lie, quantite_conso)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                        """, (nouvelle_ref, qte, temps, statut, date_creation, echeance, conso_lie, qte_conso))

                else:
                    if self.var_type_outil.get() == "Client":
                        nouvelle_ref = self.entry_client.get().strip()
                        cursor.execute("""
                            INSERT INTO commandes_clients (reference_piece, quantite, temps_unitaire, statut, date_saisie, echeance, consommable_lie, quantite_conso)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                        """, (nouvelle_ref, qte, temps, statut, date_creation, echeance, conso_lie, qte_conso))
                    else:
                        secteur_sel = self.combo_secteur.get().strip()
                        prefix = secteur_sel.split(" - ")[0].upper()
                        cursor.execute("SELECT reference_complete FROM references_generees WHERE prefix=?", (prefix,))
                        refs = cursor.fetchall()
                        max_seq = 0
                        for (r,) in refs:
                            parts = r.split('-')
                            if len(parts) >= 2:
                                try:
                                    seq = int(parts[1])
                                    if seq > max_seq: max_seq = seq
                                except: pass
                        new_seq = max_seq + 1
                        nouvelle_ref = f"{prefix}-{new_seq:03d}-01"
                        version_val = 1
                        cursor.execute("""
                            INSERT INTO references_generees (prefix, reference_complete, numero_sequentiel, version, quantite, temps_unitaire, statut, date_creation, consommable_lie, quantite_conso)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """, (prefix, nouvelle_ref, new_seq, version_val, qte, temps, statut, date_creation, conso_lie, qte_conso))

                conn.commit()

            # ==================================================
            # SAUVEGARDE & RENOMMAGE
            # ==================================================
            texte_succes = f"✅ Pièce '{nouvelle_ref}' planifiée avec succès !"
            
            if self.chemin_fichier_source and os.path.exists(self.chemin_fichier_source):
                dossier_archives = "Fichiers_Production"
                if not os.path.exists(dossier_archives):
                    os.makedirs(dossier_archives)
                
                extension = os.path.splitext(self.chemin_fichier_source)[1]
                nom_fichier_final = f"{nouvelle_ref}{extension}"
                chemin_final = os.path.join(dossier_archives, nom_fichier_final)
                
                shutil.copy2(self.chemin_fichier_source, chemin_final)
                
                texte_succes = f"✅ Pièce '{nouvelle_ref}' planifiée ET fichier sauvegardé !"
                self.chemin_fichier_source = None
                self.lbl_info_import.configure(text="💡 Gagnez du temps : importez votre fichier Slicer", text_color="gray60")

            self.charger_references_existantes()
            self.charger_toutes_references()
            self.var_type_creation.set("Nouvelle Pièce")
            self.update_ui() 

            self.lbl_message.configure(text=texte_succes, text_color="#10B981")
            self.after(5000, lambda: self.lbl_message.configure(text=""))

            if self.fonction_rafraichir_global:
                self.fonction_rafraichir_global()

        except Exception as e:
            self.lbl_message.configure(text=f"❌ Erreur BDD: {e}", text_color=self.error_border)