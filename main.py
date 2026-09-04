import customtkinter as ctk

# ==========================================
# IMPORTS GLOBAUX & 3D
# ==========================================
import database
from vue_creation import OngletCreation
from vue_nomenclature import OngletNomenclature  # <--- NOUVEL IMPORT
from vue_commandes import OngletCommandes          
from vue_ajout_production import OngletAjoutProduction
from vue_planning import OngletPlanning
from vue_suivi import OngletSuivi
from vue_machines import OngletMachines
from vue_magasin import OngletMagasin

# ==========================================
# IMPORTS RÉSINE
# ==========================================
import database_resine
from vue_planning_resine import OngletPlanning as OngletPlanningResine
from vue_suivi_resine import OngletSuivi as OngletSuiviResine
from vue_machines_resine import OngletMachines as OngletMachinesResine


class ApplicationPrincipale(ctk.CTk):
    def __init__(self):
        super().__init__()

        # Initialisation des bases de données respectives
        database.initialiser_base()
        database_resine.initialiser_base()

        self.title("ERP Atelier & Production - Global")
        self.geometry("1400x850")

        # Configuration de la grille principale
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)

        # ==========================================
        # 1. MENU LATÉRAL PRINCIPAL
        # ==========================================
        self.sidebar = ctk.CTkFrame(self, width=260, corner_radius=0)
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        self.sidebar.grid_rowconfigure(8, weight=1) # Ajusté pour le nouveau bouton

        ctk.CTkLabel(self.sidebar, text="🏭 ERP ATELIER", font=ctk.CTkFont(size=22, weight="bold"), text_color="#3B82F6").pack(pady=(35, 30))

        self.btn_creation = ctk.CTkButton(self.sidebar, text="✨ Création de Référence", height=45, font=ctk.CTkFont(weight="bold"), command=lambda: self.changer_rubrique_principale("creation"))
        self.btn_creation.pack(pady=10, padx=20, fill="x")

        # --- NOUVEAU BOUTON NOMENCLATURE ---
        self.btn_nomenclature = ctk.CTkButton(self.sidebar, text="📚 Nomenclature", height=45, font=ctk.CTkFont(weight="bold"), command=lambda: self.changer_rubrique_principale("nomenclature"))
        self.btn_nomenclature.pack(pady=10, padx=20, fill="x")

        self.btn_commandes = ctk.CTkButton(self.sidebar, text="📦 Commande Client", height=45, font=ctk.CTkFont(weight="bold"), command=lambda: self.changer_rubrique_principale("commandes"))
        self.btn_commandes.pack(pady=10, padx=20, fill="x")

        # --- BOUTON RENOMMÉ ---
        self.btn_ajout_prod = ctk.CTkButton(self.sidebar, text="🚀 Lancement d'OF", height=45, font=ctk.CTkFont(weight="bold"), command=lambda: self.changer_rubrique_principale("ajout_prod"))
        self.btn_ajout_prod.pack(pady=10, padx=20, fill="x")

        self.btn_3d = ctk.CTkButton(self.sidebar, text="🧱 Vue Pôle 3D", height=45, font=ctk.CTkFont(weight="bold"), command=lambda: self.changer_rubrique_principale("3d"))
        self.btn_3d.pack(pady=10, padx=20, fill="x")

        self.btn_resine = ctk.CTkButton(self.sidebar, text="💧 Vue Pôle Résine", height=45, font=ctk.CTkFont(weight="bold"), command=lambda: self.changer_rubrique_principale("resine"))
        self.btn_resine.pack(pady=10, padx=20, fill="x")

        self.btn_magasin = ctk.CTkButton(self.sidebar, text="🏪 Magasin & Stocks", height=45, font=ctk.CTkFont(weight="bold"), fg_color="#374151", hover_color="#4B5563", command=lambda: self.changer_rubrique_principale("magasin"))
        self.btn_magasin.pack(pady=10, padx=20, fill="x")

        # ==========================================
        # 2. CONTENEUR CENTRAL PRINCIPAL
        # ==========================================
        self.container_principal = ctk.CTkFrame(self, fg_color="transparent")
        self.container_principal.grid(row=0, column=1, sticky="nsew", padx=20, pady=20)
        self.container_principal.grid_rowconfigure(0, weight=1)
        self.container_principal.grid_columnconfigure(0, weight=1)

        # Construction de TOUTES les vues
        self.construire_cadre_creation()
        self.construire_cadre_nomenclature() # <--- NOUVELLE VUE
        self.construire_cadre_commandes()
        self.construire_cadre_ajout_prod()
        self.construire_cadre_3d()
        self.construire_cadre_resine()
        self.construire_cadre_magasin()

        # Affichage par défaut
        self.changer_rubrique_principale("creation")

    # ==========================================
    # CONSTRUCTION DES VUES
    # ==========================================
    def construire_cadre_creation(self):
        self.cadre_creation = OngletCreation(self.container_principal, fonction_rafraichir_global=self.rafraichir_global)

    def construire_cadre_nomenclature(self):
        self.cadre_nomenclature = OngletNomenclature(self.container_principal)

    def construire_cadre_commandes(self):
        self.cadre_commandes = OngletCommandes(self.container_principal, fonction_rafraichir_global=self.rafraichir_global)

    def construire_cadre_ajout_prod(self):
        self.cadre_ajout_prod = OngletAjoutProduction(self.container_principal, fonction_rafraichir_global=self.rafraichir_global)

    def construire_cadre_3d(self):
        self.cadre_3d = ctk.CTkFrame(self.container_principal, fg_color="transparent")
        self.cadre_3d.grid_rowconfigure(0, weight=1)
        self.cadre_3d.grid_columnconfigure(0, weight=1)

        self.onglets_3d = ctk.CTkTabview(self.cadre_3d, command=self.on_onglet_3d_change)
        self.onglets_3d.grid(row=0, column=0, sticky="nsew")

        noms_onglets = ["📅 Planning", "🛠️ Suivi Prod", "⚙️ Machines"]
        for nom in noms_onglets:
            self.onglets_3d.add(nom)
            self.onglets_3d.tab(nom).grid_rowconfigure(0, weight=1)
            self.onglets_3d.tab(nom).grid_columnconfigure(0, weight=1)

        self.vue_planning_3d = OngletPlanning(self.onglets_3d.tab("📅 Planning"), fonction_rafraichir_global=self.rafraichir_global)
        self.vue_planning_3d.grid(row=0, column=0, sticky="nsew")

        self.vue_suivi_3d = OngletSuivi(self.onglets_3d.tab("🛠️ Suivi Prod"), get_blocs_planifies_func=self.vue_planning_3d.get_blocs_planifies, fonction_rafraichir_global=self.rafraichir_global)
        self.vue_suivi_3d.grid(row=0, column=0, sticky="nsew")

        self.vue_machines_3d = OngletMachines(self.onglets_3d.tab("⚙️ Machines"), fonction_rafraichir_global=self.rafraichir_global)
        self.vue_machines_3d.grid(row=0, column=0, sticky="nsew")

    def construire_cadre_resine(self):
        self.cadre_resine = ctk.CTkFrame(self.container_principal, fg_color="transparent")
        self.cadre_resine.grid_rowconfigure(0, weight=1)
        self.cadre_resine.grid_columnconfigure(0, weight=1)

        self.onglets_resine = ctk.CTkTabview(self.cadre_resine, command=self.on_onglet_resine_change)
        self.onglets_resine.grid(row=0, column=0, sticky="nsew")

        noms_onglets = ["📅 Planning", "🛠️ Suivi Prod", "⚙️ Machines"]
        for nom in noms_onglets:
            self.onglets_resine.add(nom)
            self.onglets_resine.tab(nom).grid_rowconfigure(0, weight=1)
            self.onglets_resine.tab(nom).grid_columnconfigure(0, weight=1)

        self.vue_planning_res = OngletPlanningResine(self.onglets_resine.tab("📅 Planning"), fonction_rafraichir_global=self.rafraichir_global)
        self.vue_planning_res.grid(row=0, column=0, sticky="nsew")

        self.vue_suivi_res = OngletSuiviResine(self.onglets_resine.tab("🛠️ Suivi Prod"), get_blocs_planifies_func=self.vue_planning_res.get_blocs_planifies, fonction_rafraichir_global=self.rafraichir_global)
        self.vue_suivi_res.grid(row=0, column=0, sticky="nsew")

        self.vue_machines_res = OngletMachinesResine(self.onglets_resine.tab("⚙️ Machines"), fonction_rafraichir_global=self.rafraichir_global)
        self.vue_machines_res.grid(row=0, column=0, sticky="nsew")

    def construire_cadre_magasin(self):
        self.cadre_magasin = OngletMagasin(self.container_principal, fonction_rafraichir_global=self.rafraichir_global)

    # ==========================================
    # LOGIQUE DE NAVIGATION PRINCIPALE
    # ==========================================
    def changer_rubrique_principale(self, nom):
        # 1. On cache toutes les vues
        for cadre in (self.cadre_creation, self.cadre_nomenclature, self.cadre_commandes, self.cadre_ajout_prod, self.cadre_3d, self.cadre_resine, self.cadre_magasin):
            cadre.grid_forget()

        # 2. On réinitialise la couleur de tous les boutons
        for btn in (self.btn_creation, self.btn_nomenclature, self.btn_commandes, self.btn_ajout_prod, self.btn_3d, self.btn_resine):
            btn.configure(fg_color=["#3B82F6", "#2563EB"])
        self.btn_magasin.configure(fg_color=["#374151", "#4B5563"])

        # 3. On affiche la bonne vue et on colore le bon bouton
        if nom == "creation":
            self.cadre_creation.grid(row=0, column=0, sticky="nsew")
            self.btn_creation.configure(fg_color="#10B981")
            self.cadre_creation.charger_bases_existantes() 
            
        elif nom == "nomenclature":
            self.cadre_nomenclature.grid(row=0, column=0, sticky="nsew")
            self.btn_nomenclature.configure(fg_color="#10B981")
            self.cadre_nomenclature.charger_donnees() # Charge les données à l'ouverture de l'onglet
            
        elif nom == "commandes":
            self.cadre_commandes.grid(row=0, column=0, sticky="nsew")
            self.btn_commandes.configure(fg_color="#10B981")

        elif nom == "ajout_prod":
            self.cadre_ajout_prod.grid(row=0, column=0, sticky="nsew")
            self.btn_ajout_prod.configure(fg_color="#10B981")
            self.cadre_ajout_prod.charger_references() 
            
        elif nom == "3d":
            self.cadre_3d.grid(row=0, column=0, sticky="nsew")
            self.btn_3d.configure(fg_color="#10B981")
            self.on_onglet_3d_change() 
            
        elif nom == "resine":
            self.cadre_resine.grid(row=0, column=0, sticky="nsew")
            self.btn_resine.configure(fg_color="#10B981")
            self.on_onglet_resine_change() 

        elif nom == "magasin":
            self.cadre_magasin.grid(row=0, column=0, sticky="nsew")
            self.btn_magasin.configure(fg_color="#10B981")
            self.cadre_magasin.charger_stocks()

    # ==========================================
    # RAFRAÎCHISSEMENT DES ONGLETS CTKTabview
    # ==========================================
    def on_onglet_3d_change(self):
        onglet_actuel = self.onglets_3d.get()
        if onglet_actuel == "📅 Planning":
            self.vue_planning_3d.rafraichir_planning()
        elif onglet_actuel == "🛠️ Suivi Prod":
            self.vue_suivi_3d.charger_suivi()
        elif onglet_actuel == "⚙️ Machines":
            self.vue_machines_3d.charger_machines()

    def on_onglet_resine_change(self):
        onglet_actuel = self.onglets_resine.get()
        if onglet_actuel == "📅 Planning":
            self.vue_planning_res.rafraichir_planning()
        elif onglet_actuel == "🛠️ Suivi Prod":
            self.vue_suivi_res.charger_suivi()
        elif onglet_actuel == "⚙️ Machines":
            self.vue_machines_res.charger_machines()

    # ==========================================
    # RAFRAICHISSEMENT GLOBAL
    # ==========================================
    def rafraichir_global(self):
        try:
            self.vue_planning_3d.rafraichir_planning()
            self.vue_suivi_3d.charger_suivi()
            self.vue_machines_3d.charger_machines()
            
            self.vue_planning_res.rafraichir_planning()
            self.vue_suivi_res.charger_suivi()
            self.vue_machines_res.charger_machines()
            
            self.cadre_magasin.charger_stocks()
            self.cadre_creation.charger_bases_existantes()
            
            # --- Mise à jour de la nomenclature si une pièce est ajoutée ---
            if hasattr(self, 'cadre_nomenclature'):
                self.cadre_nomenclature.charger_donnees()
                
        except Exception as e:
            print(f"Erreur lors du rafraîchissement global : {e}")


if __name__ == "__main__":
    app = ApplicationPrincipale()
    app.mainloop()