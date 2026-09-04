import customtkinter as ctk
import sqlite3

class FenetreAjoutMachine(ctk.CTkToplevel):
    def __init__(self, master, callback_succes):
        super().__init__(master)
        self.callback_succes = callback_succes

        self.title("Ajouter une machine")
        self.geometry("450x450")
        self.resizable(False, False)
        self.grab_set()

        ctk.CTkLabel(self, text="➕ Nouvelle Machine", font=ctk.CTkFont(size=18, weight="bold")).pack(pady=15)

        # Nom
        frame_nom = ctk.CTkFrame(self, fg_color="transparent")
        frame_nom.pack(fill="x", padx=20, pady=5)
        ctk.CTkLabel(frame_nom, text="Nom de la machine :").pack(side="left", padx=5)
        self.entry_nom = ctk.CTkEntry(frame_nom, width=220, placeholder_text="Ex: Imprimante 3D - 01")
        self.entry_nom.pack(side="right", padx=5)

        # Secteurs autorisés (Grille de checkboxes)
        ctk.CTkLabel(self, text="Secteurs autorisés :", font=ctk.CTkFont(weight="bold")).pack(anchor="w", padx=25, pady=(15, 5))
        
        self.scroll_chk = ctk.CTkScrollableFrame(self, height=180)
        self.scroll_chk.pack(fill="x", padx=20, pady=5)
        
        self.check_vars = []
        self.charger_checkboxes_secteurs()

        self.lbl_message = ctk.CTkLabel(self, text="", font=ctk.CTkFont(weight="bold"))
        self.lbl_message.pack(pady=5)

        ctk.CTkButton(self, text="Enregistrer", fg_color="#10B981", hover_color="#059669", command=self.enregistrer).pack(pady=15)

    def charger_checkboxes_secteurs(self):
        conn = sqlite3.connect("atelier.db", timeout=5.0)
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT prefix, nom FROM parametres_references ORDER BY prefix")
            secteurs = cursor.fetchall()
        except sqlite3.OperationalError:
            secteurs = []
        finally:
            conn.close()

        var_all = ctk.StringVar(value="ALL")
        chk_all = ctk.CTkCheckBox(self.scroll_chk, text="🟢 TOUT ACCEPTER (ALL)", variable=var_all, onvalue="ALL", offvalue="")
        chk_all.pack(anchor="w", padx=5, pady=5)
        self.check_vars.append(("ALL", var_all))

        for prefix, nom in secteurs:
            var = ctk.StringVar(value="")
            texte = f"{prefix} - {nom}"
            chk = ctk.CTkCheckBox(self.scroll_chk, text=texte, variable=var, onvalue=prefix, offvalue="")
            chk.pack(anchor="w", padx=5, pady=5)
            self.check_vars.append((prefix, var))

    def enregistrer(self):
        nom = self.entry_nom.get().strip()
        if not nom:
            self.lbl_message.configure(text="⚠️ Nom obligatoire.", text_color="orange")
            return

        selection = [var.get() for prefix, var in self.check_vars if var.get() != ""]
        if not selection:
            self.lbl_message.configure(text="⚠️ Cochez au moins un secteur.", text_color="orange")
            return

        prefixes_propres = "ALL" if "ALL" in selection else ",".join(selection)

        conn = sqlite3.connect("atelier.db", timeout=5.0)
        cursor = conn.cursor()
        try:
            cursor.execute("INSERT INTO machines (nom, statut, prefixes_autorises) VALUES (?, ?, ?)", (nom, "ON", prefixes_propres))
            conn.commit()
        except Exception as e:
            self.lbl_message.configure(text=f"❌ Erreur: {e}", text_color="red")
            conn.close()
            return
        finally:
            conn.close()

        if self.callback_succes:
            self.callback_succes()
        self.destroy()

class OptionMenuMultiple(ctk.CTkFrame):
    def __init__(self, master, tous_les_secteurs, prefixes_actuels, callback_changement):
        super().__init__(master, fg_color="transparent")
        self.tous_les_secteurs = tous_les_secteurs
        
        # --- SÉCURITÉ AJOUTÉE : Gestion des valeurs vides ---
        if not prefixes_actuels:
            self.prefixes_actuels = []
        elif prefixes_actuels == "ALL":
            self.prefixes_actuels = "ALL"
        else:
            self.prefixes_actuels = [p.strip() for p in prefixes_actuels.split(",")]
        
        self.callback_changement = callback_changement

        texte_btn = "🟢 TOUS (ALL)" if self.prefixes_actuels == "ALL" else f"{len(self.prefixes_actuels)} secteur(s)"
        self.btn_menu = ctk.CTkButton(self, text=texte_btn, width=160, height=24, fg_color="#333333", command=self.ouvrir_popup)
        self.btn_menu.pack()

    def ouvrir_popup(self):
        popup = ctk.CTkToplevel(self)
        popup.title("Modifier les secteurs")
        popup.geometry("300x350")
        popup.resizable(False, False)
        popup.grab_set()

        ctk.CTkLabel(popup, text="Sélectionnez les secteurs :", font=ctk.CTkFont(weight="bold")).pack(pady=10)

        scroll = ctk.CTkScrollableFrame(popup, height=220)
        scroll.pack(fill="x", padx=10, pady=5)

        vars_dict = {}
        
        var_all = ctk.StringVar(value="ALL" if self.prefixes_actuels == "ALL" else "")
        chk_all = ctk.CTkCheckBox(scroll, text="🟢 TOUS (ALL)", variable=var_all, onvalue="ALL", offvalue="")
        chk_all.pack(anchor="w", padx=5, pady=5)
        vars_dict["ALL"] = var_all

        for prefix in self.tous_les_secteurs:
            est_coche = prefix in self.prefixes_actuels or self.prefixes_actuels == "ALL"
            var = ctk.StringVar(value=prefix if est_coche else "")
            chk = ctk.CTkCheckBox(scroll, text=prefix, variable=var, onvalue=prefix, offvalue="")
            chk.pack(anchor="w", padx=5, pady=5)
            vars_dict[prefix] = var

        def valider_modif():
            selection = [v.get() for k, v in vars_dict.items() if v.get() != ""]
            if not selection: return
            nouveaux_prefixes = "ALL" if "ALL" in selection else ",".join(selection)
            self.callback_changement(nouveaux_prefixes)
            popup.destroy()

        ctk.CTkButton(popup, text="Valider", fg_color="#10B981", command=valider_modif).pack(pady=10)

class OngletMachines(ctk.CTkFrame):
    def __init__(self, master, fonction_rafraichir_global=None):
        super().__init__(master, fg_color="transparent")
        self.fonction_rafraichir_global = fonction_rafraichir_global

        header_frame = ctk.CTkFrame(self, fg_color="transparent")
        header_frame.pack(fill="x", pady=(0, 10))

        ctk.CTkLabel(header_frame, text="⚙️ Gestion du Parc Machines", font=ctk.CTkFont(size=22, weight="bold")).pack(side="left")
        ctk.CTkButton(header_frame, text="➕ Ajouter une machine", fg_color="#10B981", hover_color="#059669", command=self.ouvrir_fenetre_ajout).pack(side="right", padx=5)

        self.scroll_machines = ctk.CTkScrollableFrame(self)
        self.scroll_machines.pack(fill="both", expand=True, padx=5, pady=5)

        self.charger_machines()

    def ouvrir_fenetre_ajout(self):
        FenetreAjoutMachine(self, callback_succes=self.rafraichir_apres_ajout)

    def rafraichir_apres_ajout(self):
        self.charger_machines()
        if self.fonction_rafraichir_global:
            self.fonction_rafraichir_global()

    def toggle_statut(self, machine_id):
        conn = sqlite3.connect("atelier.db", timeout=5.0)
        cursor = conn.cursor()
        cursor.execute("SELECT statut FROM machines WHERE id = ?", (machine_id,))
        res = cursor.fetchone()
        if res:
            nouveau = "OFF" if res[0] == "ON" else "ON"
            cursor.execute("UPDATE machines SET statut = ? WHERE id = ?", (nouveau, machine_id))
            conn.commit()
        conn.close()

        self.charger_machines()
        if self.fonction_rafraichir_global:
            self.fonction_rafraichir_global()

    def supprimer_machine(self, machine_id):
        conn = sqlite3.connect("atelier.db", timeout=5.0)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM machines WHERE id = ?", (machine_id,))
        conn.commit()
        conn.close()

        self.charger_machines()
        if self.fonction_rafraichir_global:
            self.fonction_rafraichir_global()

    def modifier_secteurs_machine(self, machine_id, nouveaux_prefixes):
        conn = sqlite3.connect("atelier.db", timeout=5.0)
        cursor = conn.cursor()
        cursor.execute("UPDATE machines SET prefixes_autorises = ? WHERE id = ?", (nouveaux_prefixes, machine_id))
        conn.commit()
        conn.close()

        self.charger_machines()
        if self.fonction_rafraichir_global:
            self.fonction_rafraichir_global()

    def charger_machines(self):
        for widget in self.scroll_machines.winfo_children():
            widget.destroy()

        conn = sqlite3.connect("atelier.db", timeout=5.0)
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT id, nom, statut, prefixes_autorises FROM machines ORDER BY id")
            machines_db = cursor.fetchall()
            
            # --- FAIL-SAFE : AUTO-CRÉATION DES MACHINES ---
            if not machines_db:
                machines_defaut = [(f"Machine {i+1}", "ON", "ALL") for i in range(8)]
                cursor.executemany("INSERT INTO machines (nom, statut, prefixes_autorises) VALUES (?, ?, ?)", machines_defaut)
                conn.commit()
                # On recharge juste après avoir injecté les machines
                cursor.execute("SELECT id, nom, statut, prefixes_autorises FROM machines ORDER BY id")
                machines_db = cursor.fetchall()
            # ----------------------------------------------

            cursor.execute("SELECT prefix FROM parametres_references ORDER BY prefix")
            tous_les_secteurs = [row[0] for row in cursor.fetchall()]
        except sqlite3.OperationalError:
            machines_db = []
            tous_les_secteurs = []
        finally:
            conn.close()

        if not machines_db:
            ctk.CTkLabel(self.scroll_machines, text="Aucune machine enregistrée.", font=ctk.CTkFont(slant="italic")).pack(pady=20)
            return

        for m_id, nom, statut, prefixes in machines_db:
            ligne = ctk.CTkFrame(self.scroll_machines, fg_color=("gray90", "gray15"))
            ligne.pack(fill="x", pady=5, ipadx=10, ipady=10)

            couleur_statut = "#10B981" if statut == "ON" else "#DC2626"
            pastille = "🟢" if statut == "ON" else "🔴"
            
            info_frame = ctk.CTkFrame(ligne, fg_color="transparent")
            info_frame.pack(side="left", fill="x", expand=True)

            ctk.CTkLabel(info_frame, text=f"{pastille} {nom}", font=ctk.CTkFont(weight="bold", size=15), text_color=couleur_statut).pack(anchor="w", padx=10, pady=(0, 5))
            
            frame_dropdown = ctk.CTkFrame(info_frame, fg_color="transparent")
            frame_dropdown.pack(anchor="w", padx=10)
            ctk.CTkLabel(frame_dropdown, text="Secteurs :", font=ctk.CTkFont(size=12, slant="italic")).pack(side="left", padx=(0, 5))
            
            menu_multi = OptionMenuMultiple(frame_dropdown, tous_les_secteurs, prefixes, lambda nvx, mid=m_id: self.modifier_secteurs_machine(mid, nvx))
            menu_multi.pack(side="left")

            btn_frame = ctk.CTkFrame(ligne, fg_color="transparent")
            btn_frame.pack(side="right", padx=10)

            texte_toggle = "HORS SERVICE" if statut == "ON" else "EN SERVICE"
            couleur_toggle = "#D97706" if statut == "ON" else "#2563EB"
            
            ctk.CTkButton(btn_frame, text=texte_toggle, fg_color=couleur_toggle, width=130, 
                          command=lambda i=m_id: self.toggle_statut(i)).pack(side="left", padx=5)
            
            ctk.CTkButton(btn_frame, text="🗑️", fg_color="#DC2626", hover_color="#991B1B", width=40,
                          command=lambda i=m_id: self.supprimer_machine(i)).pack(side="left", padx=5)