import customtkinter as ctk
import sqlite3
from tkinter import messagebox
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import threading
from datetime import datetime

class OngletMagasin(ctk.CTkFrame):
    def __init__(self, master, fonction_rafraichir_global=None):
        super().__init__(master, fg_color="transparent")
        self.fonction_rafraichir_global = fonction_rafraichir_global
        
        self.default_border = "#4B5563"
        self.error_border = "#EF4444"

        # Suivi pour éviter les envois multiples le même jour
        self.date_dernier_envoi = None

        # --- MISE À JOUR DE LA BASE DE DONNÉES ---
        self.mettre_a_jour_schema_bdd()

        # --- EN-TÊTE ---
        en_tete = ctk.CTkFrame(self, fg_color="transparent")
        en_tete.pack(fill="x", pady=(0, 10))
        ctk.CTkLabel(en_tete, text="🏪 Magasin & Projections", font=ctk.CTkFont(size=26, weight="bold")).pack(side="left")

        # Boutons e-mail dans l'en-tête
        frame_actions_mail = ctk.CTkFrame(en_tete, fg_color="transparent")
        frame_actions_mail.pack(side="right")

        self.btn_config_mail = ctk.CTkButton(
            frame_actions_mail, 
            text="⚙️ Config Email", 
            width=110,
            command=self.ouvrir_dialogue_config_mail
        )
        self.btn_config_mail.pack(side="right", padx=(5, 10))

        self.btn_alerte_mail = ctk.CTkButton(
            frame_actions_mail, 
            text="📧 Envoyer maintenant", 
            font=ctk.CTkFont(weight="bold"), 
            fg_color="#D97706", 
            hover_color="#B45309",
            command=lambda: self.envoyer_mail_automatique(manuel=True)
        )
        self.btn_alerte_mail.pack(side="right", padx=5)

        # --- ONGLETS INTERNES DU MAGASIN ---
        self.onglets = ctk.CTkTabview(self, command=self.sur_changement_onglet)
        self.onglets.pack(fill="both", expand=True)

        self.onglets.add("🔫 Scan (Entrée Stock)")
        self.onglets.add("📊 État & Projections")
        self.onglets.add("➕ Créer Consommable")
        self.onglets.add("🔧 Pièces Maintenance")

        # ==========================================
        # 1. ONGLET : SCAN DOUCHETTE
        # ==========================================
        frame_scan = ctk.CTkFrame(self.onglets.tab("🔫 Scan (Entrée Stock)"), fg_color="transparent")
        frame_scan.pack(expand=True)

        carte_scan = ctk.CTkFrame(frame_scan, fg_color=("#E0E7FF", "#1E3A8A"), corner_radius=15)
        carte_scan.pack(ipadx=30, ipady=30)
        
        ctk.CTkLabel(carte_scan, text="Scannez ou tapez un code-barres pour entrer le produit en stock", font=ctk.CTkFont(weight="bold", size=18)).pack(pady=(0, 15))
        
        frame_input_scan = ctk.CTkFrame(carte_scan, fg_color="transparent")
        frame_input_scan.pack(pady=10)

        self.entry_douchette = ctk.CTkEntry(frame_input_scan, width=350, height=45, font=ctk.CTkFont(size=18), placeholder_text="Bip ou tapez le code barre ici...")
        self.entry_douchette.pack(side="left", padx=(0, 10))
        self.entry_douchette.bind("<Return>", self.traitement_scan) 
        
        self.btn_valider_scan = ctk.CTkButton(frame_input_scan, text="Valider", height=45, font=ctk.CTkFont(weight="bold"), fg_color="#3B82F6", hover_color="#2563EB", command=self.traitement_scan)
        self.btn_valider_scan.pack(side="left")

        self.lbl_msg_scan = ctk.CTkLabel(carte_scan, text="", font=ctk.CTkFont(weight="bold", size=16))
        self.lbl_msg_scan.pack(pady=10)

        # ==========================================
        # 2. ONGLET : ÉTAT DES STOCKS & PROJECTIONS
        # ==========================================
        self.onglets_stocks = ctk.CTkTabview(self.onglets.tab("📊 État & Projections"))
        self.onglets_stocks.pack(fill="both", expand=True)
        self.onglets_stocks.add("🧱 Stocks 3D")
        self.onglets_stocks.add("💧 Stocks Résine")

        self.scroll_3d = ctk.CTkScrollableFrame(self.onglets_stocks.tab("🧱 Stocks 3D"), fg_color="transparent")
        self.scroll_3d.pack(fill="both", expand=True)
        
        self.scroll_resine = ctk.CTkScrollableFrame(self.onglets_stocks.tab("💧 Stocks Résine"), fg_color="transparent")
        self.scroll_resine.pack(fill="both", expand=True)

        # ==========================================
        # 3. ONGLET : CRÉATION DE CONSOMMABLE
        # ==========================================
        scroll_creation = ctk.CTkScrollableFrame(self.onglets.tab("➕ Créer Consommable"), fg_color="transparent")
        scroll_creation.pack(fill="both", expand=True)

        carte_crea = ctk.CTkFrame(scroll_creation, fg_color=("gray95", "#1F2937"), corner_radius=10)
        carte_crea.pack(fill="x", padx=10, pady=10)
        
        ctk.CTkLabel(carte_crea, text="Nouveau Consommable", font=ctk.CTkFont(weight="bold", size=18)).pack(anchor="w", padx=20, pady=(15, 10))

        grid_form = ctk.CTkFrame(carte_crea, fg_color="transparent")
        grid_form.pack(fill="x", padx=20, pady=(0, 20))

        ctk.CTkLabel(grid_form, text="Pôle de destination :").grid(row=0, column=0, sticky="w", pady=10, padx=5)
        self.var_pole = ctk.StringVar(value="3D")
        radio_frame = ctk.CTkFrame(grid_form, fg_color="transparent")
        radio_frame.grid(row=0, column=1, sticky="w", pady=10, padx=15)
        ctk.CTkRadioButton(radio_frame, text="3D (FDM)", variable=self.var_pole, value="3D").pack(side="left", padx=(0, 10))
        ctk.CTkRadioButton(radio_frame, text="Résine (SLA)", variable=self.var_pole, value="Resine").pack(side="left")

        ctk.CTkLabel(grid_form, text="Nom complet (ex: Bobine PLA Blanc) :").grid(row=1, column=0, sticky="w", pady=10, padx=5)
        self.entry_nom_conso = ctk.CTkEntry(grid_form, width=300, border_color=self.default_border)
        self.entry_nom_conso.grid(row=1, column=1, sticky="w", pady=10, padx=15)

        ctk.CTkLabel(grid_form, text="Matière (ex: PLA, ABS) :").grid(row=2, column=0, sticky="w", pady=10, padx=5)
        self.entry_matiere = ctk.CTkEntry(grid_form, width=150, border_color=self.default_border)
        self.entry_matiere.grid(row=2, column=1, sticky="w", pady=10, padx=15)

        ctk.CTkLabel(grid_form, text="Couleur :").grid(row=3, column=0, sticky="w", pady=10, padx=5)
        self.entry_couleur = ctk.CTkEntry(grid_form, width=150, border_color=self.default_border)
        self.entry_couleur.grid(row=3, column=1, sticky="w", pady=10, padx=15)
        
        ctk.CTkLabel(grid_form, text="Poids unitaire (en g) :").grid(row=4, column=0, sticky="w", pady=10, padx=5)
        self.entry_poids = ctk.CTkEntry(grid_form, width=150, border_color=self.default_border, placeholder_text="ex: 1000")
        self.entry_poids.grid(row=4, column=1, sticky="w", pady=10, padx=15)

        ctk.CTkLabel(grid_form, text="Stock minimum (Alerte en g) :").grid(row=5, column=0, sticky="w", pady=10, padx=5)
        self.entry_stock_min = ctk.CTkEntry(grid_form, width=150, border_color=self.default_border, placeholder_text="ex: 500")
        self.entry_stock_min.grid(row=5, column=1, sticky="w", pady=10, padx=15)

        ctk.CTkLabel(grid_form, text="Code-barres (Scannez-le) :").grid(row=6, column=0, sticky="w", pady=10, padx=5)
        self.entry_code_barre = ctk.CTkEntry(grid_form, width=250, border_color=self.default_border, placeholder_text="Bip le code ici...")
        self.entry_code_barre.grid(row=6, column=1, sticky="w", pady=10, padx=15)
        
        self.entry_code_barre.bind("<Return>", lambda event: self.creer_consommable())

        self.lbl_msg_crea = ctk.CTkLabel(scroll_creation, text="", font=ctk.CTkFont(weight="bold"))
        self.lbl_msg_crea.pack(pady=5)
        
        ctk.CTkButton(scroll_creation, text="💾 Enregistrer au Magasin", font=ctk.CTkFont(size=16, weight="bold"), height=45, fg_color="#10B981", hover_color="#059669", command=self.creer_consommable).pack(fill="x", padx=10, pady=(0, 20))

        # --- CARTE : SUPPRESSION SÉPARÉE (3D vs Résine) ---
        carte_suppr = ctk.CTkFrame(scroll_creation, fg_color=("#FEE2E2", "#451a1a"), corner_radius=10)
        carte_suppr.pack(fill="x", padx=10, pady=(20, 10))
        
        ctk.CTkLabel(carte_suppr, text="🗑️ Supprimer une référence obsolète", font=ctk.CTkFont(weight="bold", size=18), text_color="#EF4444").pack(anchor="w", padx=20, pady=(15, 5))

        grid_suppr = ctk.CTkFrame(carte_suppr, fg_color="transparent")
        grid_suppr.pack(fill="x", padx=20, pady=(0, 10))
        grid_suppr.grid_columnconfigure(0, weight=1)
        grid_suppr.grid_columnconfigure(1, weight=1)

        # Colonne de gauche : 3D
        frame_3d = ctk.CTkFrame(grid_suppr, fg_color="transparent")
        frame_3d.grid(row=0, column=0, padx=10, pady=5, sticky="ew")
        
        ctk.CTkLabel(frame_3d, text="Pôle 3D (FDM) :", font=ctk.CTkFont(weight="bold")).pack(anchor="w")
        
        self.combo_suppr_3d = ctk.CTkComboBox(frame_3d, width=250)
        self.combo_suppr_3d.pack(side="left", pady=5)
        
        ctk.CTkButton(frame_3d, text="Supprimer", width=80, fg_color="#EF4444", hover_color="#B91C1C", 
                      command=lambda: self.supprimer_consommable("3D")).pack(side="left", padx=10)

        # Colonne de droite : Résine
        frame_resine = ctk.CTkFrame(grid_suppr, fg_color="transparent")
        frame_resine.grid(row=0, column=1, padx=10, pady=5, sticky="ew")
        
        ctk.CTkLabel(frame_resine, text="Pôle Résine (SLA) :", font=ctk.CTkFont(weight="bold")).pack(anchor="w")
        
        self.combo_suppr_resine = ctk.CTkComboBox(frame_resine, width=250)
        self.combo_suppr_resine.pack(side="left", pady=5)
        
        ctk.CTkButton(frame_resine, text="Supprimer", width=80, fg_color="#EF4444", hover_color="#B91C1C", 
                      command=lambda: self.supprimer_consommable("Resine")).pack(side="left", padx=10)

        self.lbl_msg_suppr = ctk.CTkLabel(carte_suppr, text="", font=ctk.CTkFont(weight="bold"))
        self.lbl_msg_suppr.pack(pady=(0, 10))

        # ==========================================
        # 4. ONGLET : PIÈCES DE MAINTENANCE
        # ==========================================
        tab_maint = self.onglets.tab("🔧 Pièces Maintenance")
        
        frame_ajout_maint = ctk.CTkFrame(tab_maint, fg_color=("gray95", "#1F2937"), corner_radius=10)
        frame_ajout_maint.pack(fill="x", padx=10, pady=10)
        
        ctk.CTkLabel(frame_ajout_maint, text="Ajouter une nouvelle pièce :", font=ctk.CTkFont(weight="bold")).pack(side="left", padx=10, pady=10)
        
        self.entry_ref_maint = ctk.CTkEntry(frame_ajout_maint, placeholder_text="Référence (ex: BUSE-04)", width=150)
        self.entry_ref_maint.pack(side="left", padx=5, pady=10)
        
        self.entry_des_maint = ctk.CTkEntry(frame_ajout_maint, placeholder_text="Désignation (ex: Buse Laiton 0.4mm)", width=250)
        self.entry_des_maint.pack(side="left", padx=5, pady=10)
        
        btn_add_maint = ctk.CTkButton(frame_ajout_maint, text="Ajouter", width=100, command=self.ajouter_piece_maintenance)
        btn_add_maint.pack(side="left", padx=10, pady=10)

        self.lbl_msg_maint = ctk.CTkLabel(tab_maint, text="", text_color=self.error_border, font=ctk.CTkFont(weight="bold"))
        self.lbl_msg_maint.pack()

        self.scroll_maintenance = ctk.CTkScrollableFrame(tab_maint, fg_color="transparent")
        self.scroll_maintenance.pack(fill="both", expand=True, padx=10, pady=5)

        # Lancement de la vérification automatique des lundis et mercredis
        self.verifier_planification_email()

    # ==========================================
    # BASE DE DONNÉES & CONFIGURATION EMAIL
    # ==========================================
    def mettre_a_jour_schema_bdd(self):
        for db in ["atelier.db", "atelier_resine.db"]:
            try:
                with sqlite3.connect(db) as conn:
                    cursor = conn.cursor()
                    cursor.execute("CREATE TABLE IF NOT EXISTS consommables (nom TEXT)")
                    cursor.execute("PRAGMA table_info(consommables)")
                    colonnes = [col[1] for col in cursor.fetchall()]
                    
                    if "quantite" not in colonnes:
                        cursor.execute("ALTER TABLE consommables ADD COLUMN quantite INTEGER DEFAULT 0")
                    if "code_barre" not in colonnes:
                        cursor.execute("ALTER TABLE consommables ADD COLUMN code_barre TEXT")
                    if "type_matiere" not in colonnes:
                        cursor.execute("ALTER TABLE consommables ADD COLUMN type_matiere TEXT")
                    if "couleur" not in colonnes:
                        cursor.execute("ALTER TABLE consommables ADD COLUMN couleur TEXT")
                    if "poids_unitaire" not in colonnes:
                        cursor.execute("ALTER TABLE consommables ADD COLUMN poids_unitaire REAL DEFAULT 1000")
                    if "stock_min" not in colonnes:
                        cursor.execute("ALTER TABLE consommables ADD COLUMN stock_min REAL DEFAULT 0")
                    conn.commit()
            except Exception as e:
                print(f"Erreur MàJ BDD {db}: {e}")

        try:
            with sqlite3.connect("atelier.db") as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS pieces_maintenance (
                        ref TEXT PRIMARY KEY,
                        designation TEXT,
                        quantite INTEGER DEFAULT 0
                    )
                """)
                # Table de configuration de l'email
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS config_email (
                        id INTEGER PRIMARY KEY,
                        destinataire TEXT,
                        expediteur TEXT,
                        mot_de_passe TEXT,
                        serveur_smtp TEXT DEFAULT 'smtp.gmail.com',
                        port INTEGER DEFAULT 587,
                        heure_envoi TEXT DEFAULT '08:00'
                    )
                """)
                conn.commit()
        except Exception as e:
            print(f"Erreur MàJ BDD Tables atelier.db: {e}")

    def charger_configuration_mail(self):
        try:
            with sqlite3.connect("atelier.db") as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT destinataire, expediteur, mot_de_passe, serveur_smtp, port, heure_envoi FROM config_email WHERE id = 1")
                row = cursor.fetchone()
                if row:
                    return {
                        "destinataire": row[0],
                        "expediteur": row[1],
                        "mot_de_passe": row[2],
                        "serveur_smtp": row[3],
                        "port": row[4],
                        "heure_envoi": row[5] or "08:00"
                    }
        except Exception as e:
            print(f"Erreur lecture config mail: {e}")
        return None

    # ==========================================
    # PLANIFICATION AUTOMATIQUE (LUNDI & MERCREDI)
    # ==========================================
    def verifier_planification_email(self):
        """Vérifie toutes les 60 secondes si on est Lundi ou Mercredi à l'heure prévue"""
        maintenant = datetime.now()
        jour_semaine = maintenant.weekday() # 0 = Lundi, 2 = Mercredi
        date_actuelle = maintenant.strftime("%Y-%m-%d")

        config = self.charger_configuration_mail()
        if config and config.get("destinataire") and config.get("expediteur") and config.get("mot_de_passe"):
            heure_cible = config.get("heure_envoi", "08:00")
            heure_actuelle = maintenant.strftime("%H:%M")

            # Condition : Lundi (0) ou Mercredi (2), bonne heure, et pas déjà envoyé aujourd'hui
            if jour_semaine in [0, 2] and heure_actuelle == heure_cible:
                if self.date_dernier_envoi != date_actuelle:
                    self.date_dernier_envoi = date_actuelle
                    self.envoyer_mail_automatique(manuel=False)

        # Re-vérifier dans 60 secondes (60000 ms)
        self.after(60000, self.verifier_planification_email)

    def envoyer_mail_automatique(self, manuel=False):
        """Déclenche la création et l'envoi du mail avec les alertes"""
        config = self.charger_configuration_mail()
        if not config or not config.get("destinataire") or not config.get("expediteur") or not config.get("mot_de_passe"):
            if manuel:
                messagebox.showwarning("Configuration manquante", "Veuillez d'abord configurer vos paramètres e-mail via le bouton '⚙️ Config Email'.")
                self.ouvrir_dialogue_config_mail()
            return

        alertes = self.recuperer_alertes_stock()
        if not alertes:
            if manuel:
                messagebox.showinfo("Stock OK", "🎉 Aucune référence n'est actuellement en alerte (rouge ou orange).")
            return

        def executer_envoi():
            try:
                dest = config["destinataire"]
                exp = config["expediteur"]
                pwd = config["mot_de_passe"]
                host = config.get("serveur_smtp", "smtp.gmail.com")
                port = int(config.get("port", 587))

                msg = MIMEMultipart("alternative")
                msg["Subject"] = f"🚨 ALERTE STOCKS ({datetime.now().strftime('%d/%m/%Y')}) : {len(alertes)} référence(s) critique(s)"
                msg["From"] = exp
                msg["To"] = dest

                html_lignes = ""
                for item in alertes:
                    html_lignes += f"""
                    <tr style="border-bottom: 1px solid #ddd;">
                        <td style="padding: 10px; font-weight: bold;">{item['pole']}</td>
                        <td style="padding: 10px;">{item['nom']}</td>
                        <td style="padding: 10px; text-align: center; color: {item['couleur_hex']}; font-weight: bold;">
                            {item['projection']:.1f} g
                        </td>
                        <td style="padding: 10px; text-align: center;">{item['stock_min']} g</td>
                        <td style="padding: 10px; color: {item['couleur_hex']}; font-weight: bold;">{item['statut']}</td>
                    </tr>
                    """

                html_body = f"""
                <html>
                <body style="font-family: Arial, sans-serif; color: #333;">
                    <h2 style="color: #B91C1C;">⚠️ Rapport Hebdomadaire des Stocks</h2>
                    <p>Voici la liste des consommables <strong>en rouge (rupture/sous le seuil)</strong> et <strong>en orange (proche du minimum)</strong> :</p>
                    
                    <table style="width: 100%; border-collapse: collapse; margin-top: 15px;">
                        <thead>
                            <tr style="background-color: #374151; color: white;">
                                <th style="padding: 10px; text-align: left;">Pôle</th>
                                <th style="padding: 10px; text-align: left;">Référence</th>
                                <th style="padding: 10px; text-align: center;">Projection actuelle</th>
                                <th style="padding: 10px; text-align: center;">Stock Min</th>
                                <th style="padding: 10px; text-align: left;">Statut</th>
                            </tr>
                        </thead>
                        <tbody>
                            {html_lignes}
                        </tbody>
                    </table>
                    <br>
                    <p style="font-size: 12px; color: #777;">Rapport automatique envoyé les lundis et mercredis depuis l'application Magasin.</p>
                </body>
                </html>
                """

                msg.attach(MIMEText(html_body, "html"))

                with smtplib.SMTP(host, port) as server:
                    server.ehlo()
                    server.starttls()
                    server.login(exp, pwd)
                    server.sendmail(exp, [dest], msg.as_string())

                if manuel:
                    self.after(0, lambda: messagebox.showinfo("Succès", f"✅ Email envoyé avec succès à {dest} !"))

            except Exception as e:
                print(f"Erreur d'envoi d'email : {e}")
                if manuel:
                    self.after(0, lambda err=str(e): messagebox.showerror("Erreur d'envoi", f"Impossible d'envoyer l'email :\n{err}"))

        threading.Thread(target=executer_envoi, daemon=True).start()

    def ouvrir_dialogue_config_mail(self):
        """Fenêtre de configuration sauvegardée en base"""
        fenetre = ctk.CTkToplevel(self)
        fenetre.title("⚙️ Paramètres de notification Email")
        fenetre.geometry("450x520")
        fenetre.grab_set()

        ctk.CTkLabel(fenetre, text="Configuration des alertes automatiques", font=ctk.CTkFont(size=16, weight="bold")).pack(pady=(15, 5))
        ctk.CTkLabel(fenetre, text="📅 Envoi programmé : Tous les Lundis et Mercredis", text_color="#10B981", font=ctk.CTkFont(weight="bold")).pack(pady=(0, 10))

        frame = ctk.CTkFrame(fenetre, fg_color="transparent")
        frame.pack(fill="both", expand=True, padx=25)

        ctk.CTkLabel(frame, text="Adresse Destinataire (qui reçoit l'alerte) :", anchor="w").pack(fill="x", pady=(5, 2))
        entry_dest = ctk.CTkEntry(frame, placeholder_text="destinataire@exemple.com")
        entry_dest.pack(fill="x")

        ctk.CTkLabel(frame, text="Adresse Expéditeur :", anchor="w").pack(fill="x", pady=(10, 2))
        entry_exp = ctk.CTkEntry(frame, placeholder_text="mon_adresse@gmail.com")
        entry_exp.pack(fill="x")

        ctk.CTkLabel(frame, text="Mot de passe d'application (ou mot de passe mail) :", anchor="w").pack(fill="x", pady=(10, 2))
        entry_pwd = ctk.CTkEntry(frame, show="*", placeholder_text="Mot de passe d'application")
        entry_pwd.pack(fill="x")

        f_details = ctk.CTkFrame(frame, fg_color="transparent")
        f_details.pack(fill="x", pady=10)

        ctk.CTkLabel(f_details, text="Heure d'envoi :").grid(row=0, column=0, sticky="w", pady=5)
        entry_heure = ctk.CTkEntry(f_details, width=90, placeholder_text="08:00")
        entry_heure.grid(row=0, column=1, sticky="w", padx=10, pady=5)

        ctk.CTkLabel(f_details, text="Serveur SMTP :").grid(row=1, column=0, sticky="w", pady=5)
        entry_smtp = ctk.CTkEntry(f_details, width=160)
        entry_smtp.grid(row=1, column=1, sticky="w", padx=10, pady=5)

        ctk.CTkLabel(f_details, text="Port :").grid(row=2, column=0, sticky="w", pady=5)
        entry_port = ctk.CTkEntry(f_details, width=90)
        entry_port.grid(row=2, column=1, sticky="w", padx=10, pady=5)

        # Pré-remplir avec la config existante si elle existe
        config = self.charger_configuration_mail()
        if config:
            if config.get("destinataire"): entry_dest.insert(0, config["destinataire"])
            if config.get("expediteur"): entry_exp.insert(0, config["expediteur"])
            if config.get("mot_de_passe"): entry_pwd.insert(0, config["mot_de_passe"])
            entry_heure.insert(0, config.get("heure_envoi", "08:00"))
            entry_smtp.insert(0, config.get("serveur_smtp", "smtp.gmail.com"))
            entry_port.insert(0, str(config.get("port", 587)))
        else:
            entry_heure.insert(0, "08:00")
            entry_smtp.insert(0, "smtp.gmail.com")
            entry_port.insert(0, "587")

        def sauvegarder():
            dest = entry_dest.get().strip()
            exp = entry_exp.get().strip()
            pwd = entry_pwd.get().strip()
            heure = entry_heure.get().strip() or "08:00"
            smtp = entry_smtp.get().strip() or "smtp.gmail.com"
            port = int(entry_port.get().strip()) if entry_port.get().strip().isdigit() else 587

            try:
                with sqlite3.connect("atelier.db") as conn:
                    cursor = conn.cursor()
                    cursor.execute("""
                        INSERT OR REPLACE INTO config_email (id, destinataire, expediteur, mot_de_passe, serveur_smtp, port, heure_envoi)
                        VALUES (1, ?, ?, ?, ?, ?, ?)
                    """, (dest, exp, pwd, smtp, port, heure))
                    conn.commit()
                messagebox.showinfo("Succès", "✅ Configuration enregistrée avec succès !")
                fenetre.destroy()
            except Exception as e:
                messagebox.showerror("Erreur", f"Erreur lors de la sauvegarde : {e}")

        btn_save = ctk.CTkButton(fenetre, text="💾 Enregistrer les paramètres", font=ctk.CTkFont(weight="bold"), 
                                 fg_color="#10B981", hover_color="#059669", height=40, command=sauvegarder)
        btn_save.pack(fill="x", padx=25, pady=(5, 15))

    # ==========================================
    # LOGIQUE DE L'INTERFACE
    # ==========================================
    def sur_changement_onglet(self):
        self.lbl_msg_scan.configure(text="")
        self.lbl_msg_crea.configure(text="")
        self.lbl_msg_suppr.configure(text="")
        self.lbl_msg_maint.configure(text="")
        
        onglet_actuel = self.onglets.get()
        if onglet_actuel == "🔫 Scan (Entrée Stock)":
            self.entry_douchette.focus()
        elif onglet_actuel == "📊 État & Projections":
            self.charger_stocks()
        elif onglet_actuel == "➕ Créer Consommable":
            self.entry_nom_conso.focus()
            self.charger_liste_suppression() 
        elif onglet_actuel == "🔧 Pièces Maintenance":
            self.charger_pieces_maintenance()

    def charger_stocks(self):
        self.afficher_liste_stocks("atelier.db", self.scroll_3d)
        self.afficher_liste_stocks("atelier_resine.db", self.scroll_resine)

    def recuperer_alertes_stock(self):
        """Parcourt les 2 BDD et extrait les références en rouge et orange"""
        alertes = []
        bases = [("atelier.db", "3D"), ("atelier_resine.db", "Résine")]
        marge_orange = 500

        for db_nom, pole in bases:
            try:
                with sqlite3.connect(db_nom) as conn:
                    cursor = conn.cursor()
                    cursor.execute("SELECT nom, quantite, stock_min, type_matiere, couleur FROM consommables")
                    produits = cursor.fetchall()

                    cursor.execute("""
                        SELECT consommable_lie, SUM(quantite * quantite_conso) 
                        FROM references_generees 
                        WHERE statut NOT IN ('Terminée', 'Livrée') AND consommable_lie != ''
                        GROUP BY consommable_lie
                    """)
                    alloc_refs = dict(cursor.fetchall())
                    
                    cursor.execute("""
                        SELECT consommable_lie, SUM(quantite * quantite_conso) 
                        FROM commandes_clients 
                        WHERE statut NOT IN ('Terminée', 'Livrée') AND consommable_lie != ''
                        GROUP BY consommable_lie
                    """)
                    alloc_cmds = dict(cursor.fetchall())

                for nom, qte_physique, stock_min, mat, coul in produits:
                    qte_physique = qte_physique if qte_physique else 0
                    stock_min = stock_min if stock_min else 0
                    qte_allouee = alloc_refs.get(nom, 0) + alloc_cmds.get(nom, 0)
                    projection = qte_physique - qte_allouee

                    detail = nom
                    if mat or coul:
                        detail += f" ({mat or '-'} / {coul or '-'})"

                    if projection < stock_min:
                        alertes.append({
                            "pole": pole,
                            "nom": detail,
                            "projection": projection,
                            "stock_min": stock_min,
                            "statut": "ROUGE (En rupture / Critique)",
                            "couleur_hex": "#EF4444"
                        })
                    elif projection <= stock_min + marge_orange:
                        alertes.append({
                            "pole": pole,
                            "nom": detail,
                            "projection": projection,
                            "stock_min": stock_min,
                            "statut": "ORANGE (Proche du seuil)",
                            "couleur_hex": "#F59E0B"
                        })
            except Exception as e:
                print(f"Erreur lors de la récupération des alertes ({db_nom}): {e}")

        return alertes

    # ==========================================
    # LOGIQUE SUPPRESSION CONSOMMABLE
    # ==========================================
    def charger_liste_suppression(self):
        noms_3d = []
        try:
            with sqlite3.connect("atelier.db") as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT nom FROM consommables ORDER BY nom")
                noms_3d = [row[0] for row in cursor.fetchall()]
        except: pass
        
        if noms_3d:
            self.combo_suppr_3d.configure(values=noms_3d)
            self.combo_suppr_3d.set(noms_3d[0])
        else:
            self.combo_suppr_3d.configure(values=["Aucun consommable"])
            self.combo_suppr_3d.set("Aucun consommable")

        noms_resine = []
        try:
            with sqlite3.connect("atelier_resine.db") as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT nom FROM consommables ORDER BY nom")
                noms_resine = [row[0] for row in cursor.fetchall()]
        except: pass

        if noms_resine:
            self.combo_suppr_resine.configure(values=noms_resine)
            self.combo_suppr_resine.set(noms_resine[0])
        else:
            self.combo_suppr_resine.configure(values=["Aucun consommable"])
            self.combo_suppr_resine.set("Aucun consommable")

    def supprimer_consommable(self, pole):
        if pole == "3D":
            nom = self.combo_suppr_3d.get()
            db_cible = "atelier.db"
        else:
            nom = self.combo_suppr_resine.get()
            db_cible = "atelier_resine.db"
            
        if not nom or nom == "Aucun consommable":
            return
            
        confirmation = messagebox.askyesno("Confirmation", f"Êtes-vous sûr de vouloir supprimer la référence '{nom}' du pôle {pole} ?\n\nCette action est irréversible.")
        
        if not confirmation:
            return
            
        try:
            with sqlite3.connect(db_cible) as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM consommables WHERE nom = ?", (nom,))
                conn.commit()
                    
            self.lbl_msg_suppr.configure(text=f"✅ '{nom}' a été supprimé avec succès.", text_color="#10B981")
            self.after(4000, lambda: self.lbl_msg_suppr.configure(text=""))
            
            self.charger_liste_suppression()
            self.charger_stocks()
            if self.fonction_rafraichir_global:
                self.fonction_rafraichir_global()
                
        except Exception as e:
            self.lbl_msg_suppr.configure(text=f"❌ Erreur lors de la suppression : {e}", text_color=self.error_border)

    # ==========================================
    # 1. LOGIQUE SCAN DOUCHETTE
    # ==========================================
    def traitement_scan(self, event=None):
        code_scanne = self.entry_douchette.get().strip()
        if not code_scanne:
            return

        produit_trouve = False
        
        for db_nom in ["atelier.db", "atelier_resine.db"]:
            if produit_trouve: break
            try:
                with sqlite3.connect(db_nom) as conn:
                    cursor = conn.cursor()
                    cursor.execute("SELECT nom, quantite, poids_unitaire FROM consommables WHERE code_barre = ?", (code_scanne,))
                    result = cursor.fetchone()
                    
                    if result:
                        nom_prod, qte_actuelle, poids_unitaire = result
                        ajout = poids_unitaire if poids_unitaire is not None else 1000.0
                        nouvelle_qte = (qte_actuelle if qte_actuelle else 0) + ajout
                        
                        cursor.execute("UPDATE consommables SET quantite = ? WHERE code_barre = ?", (nouvelle_qte, code_scanne))
                        conn.commit()
                        produit_trouve = True
                        p = "3D" if db_nom == "atelier.db" else "Résine"
                        self.lbl_msg_scan.configure(text=f"✅ +{ajout}g stock pour '{nom_prod}' ({p})", text_color="#10B981")
            except: pass

        if not produit_trouve:
            self.lbl_msg_scan.configure(text=f"❌ Code '{code_scanne}' inconnu au magasin.", text_color=self.error_border)

        self.entry_douchette.delete(0, 'end')
        self.entry_douchette.focus()
        self.after(4000, lambda: self.lbl_msg_scan.configure(text=""))
        
        if self.fonction_rafraichir_global:
            self.fonction_rafraichir_global()

    # ==========================================
    # 2. LOGIQUE PROJECTIONS & STOCKS
    # ==========================================
    def afficher_liste_stocks(self, db_nom, scroll_frame):
        for widget in scroll_frame.winfo_children():
            widget.destroy()

        try:
            with sqlite3.connect(db_nom) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT nom, quantite, type_matiere, couleur, code_barre, stock_min FROM consommables ORDER BY nom")
                produits = cursor.fetchall()

                cursor.execute("""
                    SELECT consommable_lie, SUM(quantite * quantite_conso) 
                    FROM references_generees 
                    WHERE statut NOT IN ('Terminée', 'Livrée') AND consommable_lie != ''
                    GROUP BY consommable_lie
                """)
                alloc_refs = dict(cursor.fetchall())
                
                cursor.execute("""
                    SELECT consommable_lie, SUM(quantite * quantite_conso) 
                    FROM commandes_clients 
                    WHERE statut NOT IN ('Terminée', 'Livrée') AND consommable_lie != ''
                    GROUP BY consommable_lie
                """)
                alloc_cmds = dict(cursor.fetchall())

            if not produits:
                ctk.CTkLabel(scroll_frame, text="📭 Aucun consommable dans ce magasin.", font=ctk.CTkFont(slant="italic")).pack(pady=30)
                return

            en_tete = ctk.CTkFrame(scroll_frame, fg_color="#374151")
            en_tete.pack(fill="x", pady=(0, 5))
            ctk.CTkLabel(en_tete, text="Référence Consommable", font=ctk.CTkFont(weight="bold")).pack(side="left", padx=10, pady=5)
            
            frame_droite = ctk.CTkFrame(en_tete, fg_color="transparent")
            frame_droite.pack(side="right", padx=10)
            ctk.CTkLabel(frame_droite, text="Physique", width=90, font=ctk.CTkFont(weight="bold")).pack(side="left")
            ctk.CTkLabel(frame_droite, text="Alloué", width=90, font=ctk.CTkFont(weight="bold"), text_color="orange").pack(side="left")
            ctk.CTkLabel(frame_droite, text="Projection", width=90, font=ctk.CTkFont(weight="bold")).pack(side="left")
            ctk.CTkLabel(frame_droite, text="Min", width=90, font=ctk.CTkFont(weight="bold")).pack(side="left")

            for nom, qte_physique, mat, coul, code, stock_min in produits:
                qte_physique = qte_physique if qte_physique else 0
                stock_min = stock_min if stock_min else 0
                qte_allouee = alloc_refs.get(nom, 0) + alloc_cmds.get(nom, 0)
                projection = qte_physique - qte_allouee

                marge_orange = 500
                
                if projection < stock_min:
                    c_proj = "#EF4444" 
                    couleur_fond = "#fee2e2" if ctk.get_appearance_mode() == "Light" else "#451a1a"
                elif projection <= stock_min + marge_orange:
                    c_proj = "#F59E0B"
                    couleur_fond = "#fef08a" if ctk.get_appearance_mode() == "Light" else "#4d3800"
                else:
                    c_proj = "#10B981"
                    couleur_fond = "gray95" if ctk.get_appearance_mode() == "Light" else "#1F2937"
                
                ligne = ctk.CTkFrame(scroll_frame, fg_color=couleur_fond)
                ligne.pack(fill="x", pady=2)

                desc = f"{nom}"
                if mat or coul: desc += f" ({mat or '-'} / {coul or '-'})"
                
                ctk.CTkLabel(ligne, text=desc, font=ctk.CTkFont(size=14, weight="bold")).pack(side="left", padx=10, pady=8)
                
                f_chiffres = ctk.CTkFrame(ligne, fg_color="transparent")
                f_chiffres.pack(side="right", padx=10)
                
                ctk.CTkLabel(f_chiffres, text=f"{qte_physique:.1f}", width=90, font=ctk.CTkFont(size=14)).pack(side="left")
                ctk.CTkLabel(f_chiffres, text=f"{qte_allouee:.1f}", width=90, font=ctk.CTkFont(size=14), text_color="orange").pack(side="left")
                ctk.CTkLabel(f_chiffres, text=f"{projection:.1f}", width=90, font=ctk.CTkFont(size=15, weight="bold"), text_color=c_proj).pack(side="left")

                f_min = ctk.CTkFrame(f_chiffres, fg_color="transparent")
                f_min.pack(side="left", padx=(10, 0))

                entry_min = ctk.CTkEntry(f_min, width=60, height=24, font=ctk.CTkFont(size=12))
                entry_min.insert(0, str(int(stock_min) if stock_min.is_integer() else stock_min))
                entry_min.pack(side="left", padx=(0, 26))

                entry_min.bind("<Return>", lambda event, db=db_nom, n=nom, e=entry_min: self.maj_stock_min(event, db, n, e))
                entry_min.bind("<FocusOut>", lambda event, db=db_nom, n=nom, e=entry_min: self.maj_stock_min(event, db, n, e))

        except Exception as e:
            ctk.CTkLabel(scroll_frame, text=f"⚠️ Erreur BDD : {e}", text_color=self.error_border).pack(pady=20)

    def maj_stock_min(self, event, db_nom, nom_produit, entry_widget):
        if not entry_widget.winfo_exists():
            return

        valeur = entry_widget.get().strip()
        if not valeur:
            valeur = "0"
            
        try:
            nouveau_min = float(valeur.replace(',', '.'))
            
            with sqlite3.connect(db_nom) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT stock_min FROM consommables WHERE nom = ?", (nom_produit,))
                res = cursor.fetchone()
                valeur_actuelle = res[0] if res and res[0] is not None else 0.0
                
                if valeur_actuelle == nouveau_min:
                    if event and event.keysym == "Return":
                        self.focus()
                    return

                cursor.execute("UPDATE consommables SET stock_min = ? WHERE nom = ?", (nouveau_min, nom_produit))
                conn.commit()
            
            self.charger_stocks()
            
            if event and event.keysym == "Return":
                self.focus()
                
        except ValueError:
            if entry_widget.winfo_exists():
                entry_widget.configure(border_color=self.error_border)

    # ==========================================
    # 3. LOGIQUE CRÉATION CONSOMMABLE
    # ==========================================
    def creer_consommable(self):
        db_cible = "atelier.db" if self.var_pole.get() == "3D" else "atelier_resine.db"
        nom = self.entry_nom_conso.get().strip()
        mat = self.entry_matiere.get().strip()
        coul = self.entry_couleur.get().strip()
        code = self.entry_code_barre.get().strip()
        
        poids_txt = self.entry_poids.get().strip()
        poids = float(poids_txt.replace(',', '.')) if poids_txt.replace('.', '', 1).isdigit() else 1000.0

        stock_min_txt = self.entry_stock_min.get().strip()
        stock_min = float(stock_min_txt.replace(',', '.')) if stock_min_txt.replace('.', '', 1).isdigit() else 0.0

        if not nom or not code:
            self.lbl_msg_crea.configure(text="⚠️ Le nom et le code-barres sont obligatoires.", text_color=self.error_border)
            return

        try:
            with sqlite3.connect(db_cible) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO consommables (nom, quantite, type_matiere, couleur, code_barre, poids_unitaire, stock_min) 
                    VALUES (?, 0, ?, ?, ?, ?, ?)
                """, (nom, mat, coul, code, poids, stock_min))
                conn.commit()
            
            self.lbl_msg_crea.configure(text=f"✅ '{nom}' enregistré avec succès ({poids}g) !", text_color="#10B981")
            
            self.entry_nom_conso.delete(0, 'end')
            self.entry_matiere.delete(0, 'end')
            self.entry_couleur.delete(0, 'end')
            self.entry_code_barre.delete(0, 'end')
            self.entry_poids.delete(0, 'end')
            self.entry_stock_min.delete(0, 'end')
            
            self.entry_nom_conso.focus()
            
            self.after(4000, lambda: self.lbl_msg_crea.configure(text=""))
            
            self.charger_liste_suppression()
            self.charger_stocks()
            if self.fonction_rafraichir_global:
                self.fonction_rafraichir_global()

        except sqlite3.IntegrityError:
            self.lbl_msg_crea.configure(text="⚠️ Ce code-barres est déjà utilisé.", text_color=self.error_border)
        except Exception as e:
            self.lbl_msg_crea.configure(text=f"❌ Erreur: {e}", text_color=self.error_border)

    # ==========================================
    # 4. LOGIQUE PIÈCES DE MAINTENANCE
    # ==========================================
    def ajouter_piece_maintenance(self):
        ref = self.entry_ref_maint.get().strip()
        des = self.entry_des_maint.get().strip()
        
        if not ref or not des:
            self.lbl_msg_maint.configure(text="⚠️ La référence et la désignation sont requises.", text_color=self.error_border)
            self.after(3000, lambda: self.lbl_msg_maint.configure(text=""))
            return
            
        try:
            with sqlite3.connect("atelier.db") as conn:
                cursor = conn.cursor()
                cursor.execute("INSERT INTO pieces_maintenance (ref, designation, quantite) VALUES (?, ?, 0)", (ref, des))
                conn.commit()
                
            self.entry_ref_maint.delete(0, 'end')
            self.entry_des_maint.delete(0, 'end')
            self.charger_pieces_maintenance()
            
        except sqlite3.IntegrityError:
            self.lbl_msg_maint.configure(text="⚠️ Cette référence existe déjà.", text_color=self.error_border)
            self.after(3000, lambda: self.lbl_msg_maint.configure(text=""))
        except Exception as e:
            self.lbl_msg_maint.configure(text=f"❌ Erreur: {e}", text_color=self.error_border)
            self.after(3000, lambda: self.lbl_msg_maint.configure(text=""))

    def charger_pieces_maintenance(self):
        for widget in self.scroll_maintenance.winfo_children():
            widget.destroy()

        try:
            with sqlite3.connect("atelier.db") as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT ref, designation, quantite FROM pieces_maintenance ORDER BY ref")
                pieces = cursor.fetchall()

            if not pieces:
                ctk.CTkLabel(self.scroll_maintenance, text="📭 Aucune pièce de maintenance enregistrée.", font=ctk.CTkFont(slant="italic")).pack(pady=30)
                return

            en_tete = ctk.CTkFrame(self.scroll_maintenance, fg_color="#374151")
            en_tete.pack(fill="x", pady=(0, 5))
            ctk.CTkLabel(en_tete, text="Référence - Désignation", font=ctk.CTkFont(weight="bold")).pack(side="left", padx=10, pady=5)
            ctk.CTkLabel(en_tete, text="Actions / Quantité", font=ctk.CTkFont(weight="bold")).pack(side="right", padx=30, pady=5)

            couleur_fond = "gray95" if ctk.get_appearance_mode() == "Light" else "#1F2937"

            for ref, des, qte in pieces:
                ligne = ctk.CTkFrame(self.scroll_maintenance, fg_color=couleur_fond)
                ligne.pack(fill="x", pady=2)

                ctk.CTkLabel(ligne, text=f"{ref} - {des}", font=ctk.CTkFont(size=14, weight="bold")).pack(side="left", padx=10, pady=8)

                f_actions = ctk.CTkFrame(ligne, fg_color="transparent")
                f_actions.pack(side="right", padx=10)

                btn_moins = ctk.CTkButton(f_actions, text="−", width=30, fg_color="#EF4444", hover_color="#B91C1C", 
                                          command=lambda r=ref: self.modifier_quantite_piece(r, -1))
                btn_moins.pack(side="left", padx=5)

                lbl_qte = ctk.CTkLabel(f_actions, text=str(qte), width=40, font=ctk.CTkFont(size=16, weight="bold"))
                lbl_qte.pack(side="left", padx=5)

                btn_plus = ctk.CTkButton(f_actions, text="+", width=30, fg_color="#10B981", hover_color="#059669", 
                                         command=lambda r=ref: self.modifier_quantite_piece(r, 1))
                btn_plus.pack(side="left", padx=5)

        except Exception as e:
            ctk.CTkLabel(self.scroll_maintenance, text=f"⚠️ Erreur BDD : {e}", text_color=self.error_border).pack(pady=20)

    def modifier_quantite_piece(self, ref, delta):
        try:
            with sqlite3.connect("atelier.db") as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT quantite FROM pieces_maintenance WHERE ref = ?", (ref,))
                qte = cursor.fetchone()[0]
                
                nouvelle_qte = max(0, qte + delta)
                
                cursor.execute("UPDATE pieces_maintenance SET quantite = ? WHERE ref = ?", (nouvelle_qte, ref))
                conn.commit()
                
            self.charger_pieces_maintenance() 
            
            if self.fonction_rafraichir_global:
                self.fonction_rafraichir_global()
                
        except Exception as e:
            print(f"Erreur modif quantité maintenance: {e}")