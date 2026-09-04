import customtkinter as ctk
import sqlite3

class OngletConsommables(ctk.CTkFrame):
    def __init__(self, master, fonction_rafraichir_global=None):
        super().__init__(master, fg_color="transparent")
        self.fonction_rafraichir_global = fonction_rafraichir_global

        # --- MIGRATION AUTOMATIQUE BDD ---
        self.mettre_a_jour_bdd()

        ctk.CTkLabel(self, text="🧪 Gestion des Consommables & Stocks", font=ctk.CTkFont(size=26, weight="bold")).pack(anchor="w", pady=(0, 10))

        # ==========================================
        # SECTION 0 : MODE DOUCHETTE (SCAN RAPIDE)
        # ==========================================
        self.frame_scan = ctk.CTkFrame(self, fg_color="#374151", corner_radius=10, border_width=2, border_color="#10B981")
        self.frame_scan.pack(fill="x", pady=(0, 15), ipadx=10, ipady=10)

        scan_top = ctk.CTkFrame(self.frame_scan, fg_color="transparent")
        scan_top.pack(fill="x")
        
        ctk.CTkLabel(scan_top, text="🔫 MODE DOUCHETTE :", font=ctk.CTkFont(size=16, weight="bold"), text_color="#10B981").pack(side="left", padx=10)
        
        self.var_mode_scan = ctk.StringVar(value="+1")
        ctk.CTkRadioButton(scan_top, text="📥 Entrée", variable=self.var_mode_scan, value="+1", font=ctk.CTkFont(weight="bold")).pack(side="left", padx=(20, 10))
        ctk.CTkRadioButton(scan_top, text="📤 Sortie", variable=self.var_mode_scan, value="-1", font=ctk.CTkFont(weight="bold")).pack(side="left", padx=10)

        # NOUVEAU : Quantité modifiable pour la douchette
        ctk.CTkLabel(scan_top, text="Qté par scan :", font=ctk.CTkFont(weight="bold")).pack(side="left", padx=(30, 5))
        self.entry_qte_scan = ctk.CTkEntry(scan_top, width=70)
        self.entry_qte_scan.insert(0, "1")
        self.entry_qte_scan.pack(side="left")

        scan_bottom = ctk.CTkFrame(self.frame_scan, fg_color="transparent")
        scan_bottom.pack(fill="x", pady=(10, 0))

        ctk.CTkLabel(scan_bottom, text="Scannez ici :", font=ctk.CTkFont(size=14)).pack(side="left", padx=10)
        
        self.entry_scan = ctk.CTkEntry(scan_bottom, width=300, height=40, font=ctk.CTkFont(size=16), placeholder_text="Bip de la douchette...")
        self.entry_scan.pack(side="left", padx=10)
        self.entry_scan.bind("<Return>", self.traiter_scan)
        
        self.lbl_msg_scan = ctk.CTkLabel(scan_bottom, text="", font=ctk.CTkFont(size=14, weight="bold"))
        self.lbl_msg_scan.pack(side="left", padx=20)

        # ==========================================
        # SECTION 1 : AJOUTER UN NOUVEAU CONSOMMABLE
        # ==========================================
        self.frame_ajout = ctk.CTkFrame(self, fg_color=("gray95", "#1F2937"), corner_radius=10)
        self.frame_ajout.pack(fill="x", pady=(0, 15), ipadx=10, ipady=10)

        ctk.CTkLabel(self.frame_ajout, text="➕ Créer une nouvelle référence", font=ctk.CTkFont(size=15, weight="bold")).pack(anchor="w", pady=(0, 5))

        form_grid = ctk.CTkFrame(self.frame_ajout, fg_color="transparent")
        form_grid.pack(fill="x")

        # Ligne 0 : En-têtes du formulaire
        ctk.CTkLabel(form_grid, text="Nom *", text_color="gray60").grid(row=0, column=0, sticky="w", padx=5)
        ctk.CTkLabel(form_grid, text="Catégorie", text_color="gray60").grid(row=0, column=1, sticky="w", padx=5)
        ctk.CTkLabel(form_grid, text="Code-barre", text_color="gray60").grid(row=0, column=2, sticky="w", padx=5)
        ctk.CTkLabel(form_grid, text="Qté", text_color="gray60").grid(row=0, column=3, sticky="w", padx=5)
        ctk.CTkLabel(form_grid, text="Unité *", text_color="gray60").grid(row=0, column=4, sticky="w", padx=5)
        ctk.CTkLabel(form_grid, text="Alerte", text_color="gray60").grid(row=0, column=5, sticky="w", padx=5)

        # Ligne 1 : Champs de saisie
        self.entry_nom = ctk.CTkEntry(form_grid, width=180, placeholder_text="ex: Résine Tough")
        self.entry_nom.grid(row=1, column=0, padx=5, pady=5)
        
        self.entry_cat = ctk.CTkEntry(form_grid, width=120)
        self.entry_cat.grid(row=1, column=1, padx=5, pady=5)

        self.entry_code = ctk.CTkEntry(form_grid, width=150, placeholder_text="Scannez ou tapez")
        self.entry_code.grid(row=1, column=2, padx=5, pady=5)
        
        self.entry_qte = ctk.CTkEntry(form_grid, width=60)
        self.entry_qte.insert(0, "0")
        self.entry_qte.grid(row=1, column=3, padx=5, pady=5)
        
        self.entry_unite = ctk.CTkEntry(form_grid, width=80, placeholder_text="L, pce...")
        self.entry_unite.grid(row=1, column=4, padx=5, pady=5)
        
        self.entry_seuil = ctk.CTkEntry(form_grid, width=60)
        self.entry_seuil.insert(0, "5")
        self.entry_seuil.grid(row=1, column=5, padx=5, pady=5)

        btn_valider = ctk.CTkButton(form_grid, text="Ajouter au stock", fg_color="#10B981", hover_color="#059669", width=120, command=self.ajouter_consommable)
        btn_valider.grid(row=1, column=6, padx=15, pady=5)

        self.lbl_msg_ajout = ctk.CTkLabel(self.frame_ajout, text="", font=ctk.CTkFont(weight="bold"))
        self.lbl_msg_ajout.pack(anchor="w", pady=(2, 0))

        # ==========================================
        # SECTION 2 : GESTION DES STOCKS ACTUELS
        # ==========================================
        self.frame_liste = ctk.CTkFrame(self, fg_color="transparent")
        self.frame_liste.pack(fill="both", expand=True)

        barre_filtre = ctk.CTkFrame(self.frame_liste, fg_color="transparent")
        barre_filtre.pack(fill="x", pady=(0, 10))
        
        ctk.CTkLabel(barre_filtre, text="📋 Vos stocks en direct", font=ctk.CTkFont(size=18, weight="bold")).pack(side="left")
        ctk.CTkLabel(barre_filtre, text="🔍 Filtrer :").pack(side="left", padx=(30, 5))
        
        self.entry_recherche = ctk.CTkEntry(barre_filtre, width=250, placeholder_text="Nom, code-barre...")
        self.entry_recherche.pack(side="left", padx=5)
        self.entry_recherche.bind("<KeyRelease>", lambda e: self.charger_stocks())

        self.scroll_stocks = ctk.CTkScrollableFrame(self.frame_liste, fg_color="transparent")
        self.scroll_stocks.pack(fill="both", expand=True)

        self.charger_stocks()

    def mettre_a_jour_bdd(self):
        try:
            with sqlite3.connect("atelier_resine.db", timeout=30.0) as conn:
                cursor = conn.cursor()
                cursor.execute("ALTER TABLE consommables ADD COLUMN code_barre TEXT")
                conn.commit()
        except sqlite3.OperationalError:
            pass 

    def traiter_scan(self, event):
        code = self.entry_scan.get().strip()
        self.entry_scan.delete(0, 'end') 
        self.entry_qte_scan.configure(border_color="#4B5563")
        
        if not code: return

        # Récupération de la quantité choisie
        try:
            qte_par_scan = float(self.entry_qte_scan.get().strip())
        except ValueError:
            self.entry_qte_scan.configure(border_color="#EF4444")
            self.lbl_msg_scan.configure(text="❌ Quantité par scan invalide.", text_color="#EF4444")
            self.after(3000, lambda: self.lbl_msg_scan.configure(text=""))
            return

        delta = qte_par_scan if self.var_mode_scan.get() == "+1" else -qte_par_scan
        
        try:
            with sqlite3.connect("atelier_resine.db", timeout=30.0) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT id, nom, quantite_stock FROM consommables WHERE code_barre = ? OR code_barre = ?", (code, code.lower()))
                res = cursor.fetchone()
                
                if res:
                    c_id, nom, stock_actuel = res
                    nouveau_stock = max(0.0, stock_actuel + delta)
                    cursor.execute("UPDATE consommables SET quantite_stock = ? WHERE id = ?", (nouveau_stock, c_id))
                    conn.commit()
                    
                    action_txt = "Ajouté" if delta > 0 else "Retiré"
                    couleur = "#10B981" if delta > 0 else "#F59E0B"
                    self.lbl_msg_scan.configure(text=f"✅ {action_txt} : {abs(delta)}x {nom} (Nouveau stock: {nouveau_stock})", text_color=couleur)
                    self.rafraichir_tout_global()
                else:
                    self.lbl_msg_scan.configure(text=f"❌ Code-barre inconnu : {code}", text_color="#EF4444")
            
            self.after(4000, lambda: self.lbl_msg_scan.configure(text=""))
            self.entry_scan.focus_set()
            
        except Exception as e:
            self.lbl_msg_scan.configure(text=f"❌ Erreur: {e}", text_color="#EF4444")

    def ajouter_consommable(self):
        self.entry_nom.configure(border_color="#4B5563")
        self.entry_unite.configure(border_color="#4B5563")

        nom = self.entry_nom.get().strip()
        cat = self.entry_cat.get().strip()
        unite = self.entry_unite.get().strip()
        code_barre = self.entry_code.get().strip()

        try:
            qte = float(self.entry_qte.get())
            seuil = float(self.entry_seuil.get())
        except ValueError:
            self.lbl_msg_ajout.configure(text="⚠️ La quantité et le seuil d'alerte doivent être des chiffres.", text_color="#EF4444")
            return

        if not nom or not unite:
            if not nom: self.entry_nom.configure(border_color="#EF4444")
            if not unite: self.entry_unite.configure(border_color="#EF4444")
            self.lbl_msg_ajout.configure(text="⚠️ Le nom et l'unité sont obligatoires.", text_color="#EF4444")
            return

        try:
            with sqlite3.connect("atelier_resine.db", timeout=30.0) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO consommables (nom, categorie, quantite_stock, unite, seuil_alerte, code_barre)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (nom, cat, qte, unite, seuil, code_barre))
                conn.commit()
            
            self.lbl_msg_ajout.configure(text=f"✅ Le consommable '{nom}' a été ajouté au stock !", text_color="#10B981")
            
            self.entry_nom.delete(0, 'end')
            self.entry_cat.delete(0, 'end')
            self.entry_code.delete(0, 'end')
            self.entry_qte.delete(0, 'end')
            self.entry_qte.insert(0, "0")
            self.entry_unite.delete(0, 'end')
            
            self.rafraichir_tout_global()
            self.after(3000, lambda: self.lbl_msg_ajout.configure(text=""))
            
        except Exception as e:
            self.lbl_msg_ajout.configure(text=f"❌ Erreur BDD: {e}", text_color="#EF4444")

    def ajuster_stock_manuel(self, c_id, entry_widget):
        """ Appelé par le bouton OK pour ajuster librement (+5, -2, 10...) """
        valeur_str = entry_widget.get().strip()
        entry_widget.configure(border_color="#4B5563") # Reset couleur
        
        if not valeur_str: 
            return
            
        try:
            delta = float(valeur_str)
        except ValueError:
            entry_widget.configure(border_color="#EF4444")
            return
            
        self.modifier_quantite(c_id, delta)

    def modifier_quantite(self, c_id, delta):
        try:
            with sqlite3.connect("atelier_resine.db", timeout=30.0) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT quantite_stock FROM consommables WHERE id = ?", (c_id,))
                res = cursor.fetchone()
                if res:
                    nouveau_stock = max(0.0, res[0] + delta)
                    cursor.execute("UPDATE consommables SET quantite_stock = ? WHERE id = ?", (nouveau_stock, c_id))
                    conn.commit()
                    
            self.rafraichir_tout_global()
        except Exception as e:
            print(f"Erreur modification stock : {e}")

    def supprimer_consommable(self, c_id):
        try:
            with sqlite3.connect("atelier_resine.db", timeout=30.0) as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM consommables WHERE id = ?", (c_id,))
                conn.commit()
            self.rafraichir_tout_global()
        except Exception as e:
            print(f"Erreur suppression stock : {e}")

    def charger_stocks(self):
        for widget in self.scroll_stocks.winfo_children():
            widget.destroy()

        filtre = self.entry_recherche.get().strip().upper()

        try:
            with sqlite3.connect("atelier_resine.db", timeout=30.0) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT id, nom, categorie, quantite_stock, unite, seuil_alerte, code_barre FROM consommables ORDER BY categorie, nom")
                stocks = cursor.fetchall()
        except Exception:
            stocks = []

        if filtre:
            stocks = [s for s in stocks if filtre in s[1].upper() or (s[2] and filtre in str(s[2]).upper()) or (s[6] and filtre in str(s[6]).upper())]

        if not stocks:
            ctk.CTkLabel(self.scroll_stocks, text="Aucun consommable n'est enregistré dans l'atelier.", font=ctk.CTkFont(slant="italic")).pack(pady=30)
            return

        # ==========================================
        # TABLEAU STRICT : Alignement forcé
        # ==========================================
        W_NOM = 260
        W_CODE = 130
        W_STOCK = 130
        W_AJUST = 150
        W_ACT = 60

        header = ctk.CTkFrame(self.scroll_stocks, fg_color=("gray80", "gray25"), corner_radius=6)
        header.pack(fill="x", pady=(0, 5), ipadx=5, ipady=5)
        
        ctk.CTkLabel(header, text="Désignation", font=ctk.CTkFont(weight="bold"), width=W_NOM, anchor="w").pack(side="left", padx=(10, 0))
        ctk.CTkLabel(header, text="Code-Barre", font=ctk.CTkFont(weight="bold"), width=W_CODE, anchor="w").pack(side="left")
        ctk.CTkLabel(header, text="Stock Actuel", font=ctk.CTkFont(weight="bold"), width=W_STOCK, anchor="w").pack(side="left")
        ctk.CTkLabel(header, text="Ajustement", font=ctk.CTkFont(weight="bold"), width=W_AJUST, anchor="w").pack(side="left")
        ctk.CTkLabel(header, text="Actions", font=ctk.CTkFont(weight="bold"), width=W_ACT).pack(side="right", padx=10)

        for c_id, nom, cat, stock, unite, seuil, code_barre in stocks:
            alerte = stock <= seuil
            bg_couleur = ("#FEE2E2", "#450A0A") if alerte else ("gray90", "gray15")
            text_couleur = ("#B91C1C", "#FCA5A5") if alerte else ("black", "white")

            ligne = ctk.CTkFrame(self.scroll_stocks, fg_color=bg_couleur, corner_radius=6, height=50)
            ligne.pack(fill="x", pady=4, ipadx=5)
            ligne.pack_propagate(False) # Force la hauteur fixe pour un tableau propre

            prefixe_nom = "⚠️ " if alerte else "📦 "
            
            # Cellule 1 : Désignation
            cell_nom = ctk.CTkFrame(ligne, fg_color="transparent", width=W_NOM)
            cell_nom.pack(side="left", fill="y", padx=(10, 0))
            cell_nom.pack_propagate(False)
            ctk.CTkLabel(cell_nom, text=f"{prefixe_nom}{nom}", font=ctk.CTkFont(weight="bold", size=13), text_color=text_couleur, anchor="w").pack(anchor="w", pady=(2, 0))
            if cat:
                ctk.CTkLabel(cell_nom, text=cat, font=ctk.CTkFont(size=11), text_color="gray50" if not alerte else "#FCA5A5", anchor="w").pack(anchor="w")
            
            # Cellule 2 : Code-Barre
            code_txt = code_barre if code_barre else "-"
            ctk.CTkLabel(ligne, text=code_txt, text_color="gray50" if not alerte else "#FCA5A5", width=W_CODE, anchor="w").pack(side="left")
            
            # Cellule 3 : Stock
            stock_txt = f"{stock:.2f} {unite}"
            ctk.CTkLabel(ligne, text=stock_txt, font=ctk.CTkFont(weight="bold", size=14), text_color="#10B981" if not alerte else "#EF4444", width=W_STOCK, anchor="w").pack(side="left")

            # Cellule 4 : Ajustement Manuel
            cell_ajust = ctk.CTkFrame(ligne, fg_color="transparent", width=W_AJUST)
            cell_ajust.pack(side="left", fill="y", pady=10)
            cell_ajust.pack_propagate(False)
            
            entry_ajust = ctk.CTkEntry(cell_ajust, width=70, placeholder_text="+5 / -2")
            entry_ajust.pack(side="left", padx=(0, 5))
            
            # Bouton OK pour valider la saisie manuelle
            btn_ok = ctk.CTkButton(cell_ajust, text="OK", width=40, fg_color="#3B82F6", hover_color="#2563EB")
            btn_ok.configure(command=lambda cid=c_id, ent=entry_ajust: self.ajuster_stock_manuel(cid, ent))
            btn_ok.pack(side="left")

            # Cellule 5 : Actions (Suppression)
            ctk.CTkButton(ligne, text="🗑️", width=35, fg_color="#DC2626", hover_color="#991B1B", command=lambda cid=c_id: self.supprimer_consommable(cid)).pack(side="right", padx=10)

    def rafraichir_tout_global(self):
        self.charger_stocks()
        if self.fonction_rafraichir_global:
            self.fonction_rafraichir_global()