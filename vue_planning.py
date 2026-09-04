import tkinter as tk
import customtkinter as ctk
import sqlite3
import re
from datetime import datetime, timedelta, time
import hashlib
import colorsys

# ==========================================
# UTILITAIRES : FÉRIÉS ET HORAIRES
# ==========================================
def est_ferie(dt):
    """ Calcule si un jour est férié en France pour une date donnée """
    annee = dt.year
    jours_fixes = [(1, 1), (1, 5), (8, 5), (14, 7), (15, 8), (1, 11), (11, 11), (25, 12)]
    if (dt.day, dt.month) in jours_fixes:
        return True
    
    a = annee % 19
    b = annee // 100
    c = annee % 100
    d = b // 4
    e = b % 4
    f = (b + 8) // 25
    g = (b - f + 1) // 3
    h = (19 * a + b - d - g + 15) % 30
    i = c // 4
    k = c % 4
    l = (32 + 2 * e + 2 * i - h - k) % 7
    m = (a + 11 * h + 22 * l) // 451
    mois_paques = (h + l - 7 * m + 114) // 31
    jour_paques = ((h + l - 7 * m + 114) % 31) + 1
    
    dimanche_paques = datetime(annee, mois_paques, jour_paques)
    
    if dt.date() in [
        (dimanche_paques + timedelta(days=1)).date(),  
        (dimanche_paques + timedelta(days=39)).date(), 
        (dimanche_paques + timedelta(days=50)).date()  
    ]:
        return True
        
    return False

def est_chome(dt):
    return dt.weekday() >= 5 or est_ferie(dt)

def valider_horaire_lancement(dt, heure_deb, heure_fin):
    """ 
    Trouve le moment où un opérateur est présent pour lancer l'impression.
    Si on dépasse l'heure de fin, on repousse au lendemain matin.
    """
    while True:
        if est_chome(dt):
            dt = datetime.combine(dt.date() + timedelta(days=1), heure_deb)
            continue
        if dt.time() >= heure_fin:
            dt = datetime.combine(dt.date() + timedelta(days=1), heure_deb)
            continue
        if dt.time() < heure_deb:
            dt = datetime.combine(dt.date(), heure_deb)
            continue
        break
    return dt

# ==========================================
# TOOLTIP ET ONGLET GANTT
# ==========================================
class ToolTip:
    def __init__(self, widget, text):
        self.widget = widget
        self.text = text
        self.tw = None
        self.widget.configure(cursor="hand2")
        self.widget.bind("<Enter>", self.enter)
        self.widget.bind("<Leave>", self.leave)

    def enter(self, event=None):
        x = self.widget.winfo_rootx() + 20
        y = self.widget.winfo_rooty() + self.widget.winfo_height() + 10
        self.tw = tk.Toplevel(self.widget)
        self.tw.wm_overrideredirect(True)
        self.tw.wm_geometry(f"+{x}+{y}")
        
        label = tk.Label(
            self.tw, text=self.text, justify='left', 
            background="#111827", foreground="#F9FAFB", 
            relief='flat', highlightbackground="#374151", highlightcolor="#374151", highlightthickness=1,
            font=("Segoe UI", 10, "normal"), padx=12, pady=8
        )
        label.pack()

    def leave(self, event=None):
        if self.tw:
            self.tw.destroy()
            self.tw = None

class OngletPlanning(ctk.CTkFrame):
    def __init__(self, master, fonction_rafraichir_global=None):
        super().__init__(master, fg_color="transparent")
        self.fonction_rafraichir_global = fonction_rafraichir_global
        self.dernier_gantt = [] 
        self.scroll_droite = None
        self.largeur_canvas = 1
        self.heure_debut_planning = None

        # ==========================================
        # HEADER & CONFIG
        # ==========================================
        header_frame = ctk.CTkFrame(self, fg_color="transparent")
        header_frame.pack(fill="x", pady=(0, 5))

        ctk.CTkLabel(header_frame, text="📅 Planning Gantt de l'Atelier", font=ctk.CTkFont(size=26, weight="bold")).pack(side="left")
        ctk.CTkButton(header_frame, text="🔄 Actualiser", width=120, fg_color="#374151", hover_color="#1F2937", command=self.rafraichir_planning).pack(side="right")

        self.config_frame = ctk.CTkFrame(self, fg_color=("gray90", "#1F2937"), corner_radius=8)
        self.config_frame.pack(fill="x", padx=5, pady=(0, 5), ipadx=10, ipady=5)

        ctk.CTkLabel(self.config_frame, text="⏱️ Horaires opérateur :", font=ctk.CTkFont(weight="bold")).pack(side="left", padx=(10, 5))
        ctk.CTkLabel(self.config_frame, text="Début").pack(side="left", padx=(10, 2))
        self.entry_debut = ctk.CTkEntry(self.config_frame, width=60, height=28)
        self.entry_debut.pack(side="left", padx=5)

        ctk.CTkLabel(self.config_frame, text="Fin lancement").pack(side="left", padx=(15, 2))
        self.entry_fin = ctk.CTkEntry(self.config_frame, width=60, height=28)
        self.entry_fin.pack(side="left", padx=5)

        ctk.CTkButton(self.config_frame, text="Sauvegarder", fg_color="#10B981", hover_color="#059669", height=28, width=100, command=self.sauvegarder_horaires).pack(side="left", padx=20)
        
        self.lbl_msg_horaires = ctk.CTkLabel(self.config_frame, text="", font=ctk.CTkFont(weight="bold"))
        self.lbl_msg_horaires.pack(side="left", padx=10)

        # ==========================================
        # BARRE DE NAVIGATION TEMPORELLE DISCRÈTE
        # ==========================================
        self.nav_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.nav_frame.pack(fill="x", pady=(0, 10))
        
        ctk.CTkButton(self.nav_frame, text="◀", width=36, height=26, fg_color="#374151", hover_color="#1F2937", text_color="#D1D5DB", command=lambda: self.deplacer_vue(-1)).pack(side="left", padx=(5, 2))
        ctk.CTkButton(self.nav_frame, text="Aujourd'hui", width=80, height=26, fg_color="transparent", hover_color="#374151", border_width=1, border_color="#4B5563", text_color="#D1D5DB", command=lambda: self.deplacer_vue(0)).pack(side="left", padx=2)
        ctk.CTkButton(self.nav_frame, text="▶", width=36, height=26, fg_color="#374151", hover_color="#1F2937", text_color="#D1D5DB", command=lambda: self.deplacer_vue(1)).pack(side="left", padx=(2, 10))
        
        ctk.CTkButton(self.nav_frame, text="⏭ Lundi", width=70, height=26, fg_color="transparent", hover_color="#374151", border_width=1, border_color="#6366F1", text_color="#A5B4FC", command=self.passer_weekend).pack(side="left", padx=5)

        # Main view
        self.main_scroll_y = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.main_scroll_y.pack(fill="both", expand=True, padx=0, pady=0)
        
        self.charger_horaires_ui()
        self.rafraichir_planning()

    # ==========================================
    # LOGIQUE DE NAVIGATION
    # ==========================================
    def deplacer_vue(self, jours):
        if not hasattr(self, 'current_view_date'):
            self.current_view_date = datetime.now().date()
            
        if jours == 0:
            self.current_view_date = datetime.now().date()
        else:
            self.current_view_date += timedelta(days=jours)
        self.appliquer_scroll()

    def passer_weekend(self):
        if not hasattr(self, 'current_view_date'):
            self.current_view_date = datetime.now().date()
        
        jours_avancer = 0 - self.current_view_date.weekday() # 0 = Lundi
        if jours_avancer <= 0:
            jours_avancer += 7
        self.current_view_date += timedelta(days=jours_avancer)
        self.appliquer_scroll()

    def appliquer_scroll(self):
        if not self.heure_debut_planning or not self.scroll_droite or not hasattr(self.scroll_droite, '_parent_canvas'):
            return
        
        target_dt = datetime.combine(self.current_view_date, time.min)
        pixels = (target_dt - self.heure_debut_planning).total_seconds() / 60.0 * 2.5 # PIXELS_PAR_MINUTE
        
        fraction = pixels / self.largeur_canvas
        fraction = max(0.0, min(1.0, fraction))
        
        try:
            self.scroll_droite._parent_canvas.xview_moveto(fraction)
        except Exception:
            pass

    # ==========================================
    # GESTION HORAIRES ET DB
    # ==========================================
    def charger_horaires_ui(self):
        conn = sqlite3.connect("atelier.db", timeout=5.0)
        cursor = conn.cursor()
        try:
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS parametres_atelier (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    heure_debut TEXT,
                    heure_fin_lancement TEXT
                )
            """)
            cursor.execute("SELECT heure_debut, heure_fin_lancement FROM parametres_atelier LIMIT 1")
            res = cursor.fetchone()
            if res:
                self.entry_debut.delete(0, 'end')
                self.entry_debut.insert(0, res[0])
                self.entry_fin.delete(0, 'end')
                self.entry_fin.insert(0, res[1])
            else:
                self.entry_debut.insert(0, "07:00")
                self.entry_fin.insert(0, "17:30")
        except Exception:
            pass
        finally:
            conn.close()

    def sauvegarder_horaires(self):
        debut = self.entry_debut.get().strip()
        fin = self.entry_fin.get().strip()
        regex_heure = r"^(0[0-9]|1[0-9]|2[0-3]):[0-5][0-9]$"
        self.entry_debut.configure(border_color="#979DA2")
        self.entry_fin.configure(border_color="#979DA2")

        erreurs = False
        if not re.match(regex_heure, debut):
            self.entry_debut.configure(border_color="#DC2626")
            erreurs = True
        if not re.match(regex_heure, fin):
            self.entry_fin.configure(border_color="#DC2626")
            erreurs = True

        if erreurs:
            self.lbl_msg_horaires.configure(text="⚠️ Format invalide", text_color="#DC2626")
            return

        conn = sqlite3.connect("atelier.db", timeout=5.0)
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT COUNT(*) FROM parametres_atelier")
            if cursor.fetchone()[0] == 0:
                cursor.execute("INSERT INTO parametres_atelier (heure_debut, heure_fin_lancement) VALUES (?, ?)", (debut, fin))
            else:
                cursor.execute("UPDATE parametres_atelier SET heure_debut = ?, heure_fin_lancement = ?", (debut, fin))
            conn.commit()
            self.lbl_msg_horaires.configure(text="✅ Enregistré !", text_color="#10B981")
            self.after(3000, lambda: self.lbl_msg_horaires.configure(text=""))
            self.rafraichir_planning()
        except Exception:
            self.lbl_msg_horaires.configure(text="❌ Erreur", text_color="#DC2626")
        finally:
            conn.close()

    def generer_couleur(self, prefixe, reference, statut=""):
        if not prefixe: prefixe = "AUTRE"
        hash_prefixe = int(hashlib.md5(str(prefixe).encode()).hexdigest(), 16)
        teinte = (hash_prefixe % 360) / 360.0  
        
        luminosite = 0.65 
        saturation = 0.70  
        r, g, b = colorsys.hls_to_rgb(teinte, luminosite, saturation)
        return f"#{int(r*255):02x}{int(g*255):02x}{int(b*255):02x}"

    def recuperer_horaires_atelier(self):
        conn = sqlite3.connect("atelier.db", timeout=30.0)
        c = conn.cursor()
        try:
            c.execute("SELECT heure_debut, heure_fin_lancement FROM parametres_atelier LIMIT 1")
            res = c.fetchone()
            if res:
                h_deb = time(*(map(int, res[0].split(':'))))
                h_fin = time(*(map(int, res[1].split(':'))))
                return h_deb, h_fin
        except Exception:
            pass
        finally:
            conn.close()
        return time(7, 0), time(17, 30)

    def charger_machines(self):
        conn = sqlite3.connect("atelier.db", timeout=30.0)
        cursor = conn.cursor()
        machines = []
        try:
            cursor.execute("SELECT id, nom, prefixes_autorises, statut FROM machines")
            machines = cursor.fetchall()
            if not machines:
                machines = [(0, f"Machine {i+1}", "", "ON") for i in range(8)]
        except sqlite3.OperationalError:
            machines = [(0, f"Machine {i+1}", "", "ON") for i in range(8)]
        finally:
            conn.close()
        return machines

    def charger_taches(self):
        conn = sqlite3.connect("atelier.db", timeout=30.0)
        cursor = conn.cursor()
        taches = []
        try:
            # On ignore les tâches annulées ou terminées (déjà gérées)
            cursor.execute("SELECT prefix, reference_complete, quantite, temps_unitaire, statut, date_creation FROM references_generees WHERE statut NOT IN ('Terminé', 'Annulé')")
            for row in cursor.fetchall():
                try: dc = datetime.strptime(row[5], "%d/%m/%Y %H:%M")
                except: dc = datetime.now()
                pref = str(row[0]).strip() if row[0] is not None else ""
                ref_complete = str(row[1]) if row[1] is not None else "SANS_REF"
                if not pref and "-" in ref_complete:
                    pref = ref_complete.split("-")[0].strip()
                taches.append({
                    "prefix": pref, "ref": ref_complete, "qte": row[2], 
                    "temps": row[3], "statut": row[4] or "Flux classique", 
                    "type": "interne", "date_creation": dc
                })

            cursor.execute("SELECT 'CLIENT', reference_piece, quantite, temps_unitaire, statut, date_saisie FROM commandes_clients WHERE statut NOT IN ('Terminé', 'Annulé')")
            for row in cursor.fetchall():
                try: dc = datetime.strptime(row[5], "%d/%m/%Y %H:%M")
                except: dc = datetime.now()
                taches.append({
                    "prefix": "CLIENT", "ref": str(row[1]) if row[1] is not None else "CLIENT", 
                    "qte": row[2], "temps": row[3], "statut": row[4] or "Flux classique", 
                    "type": "client", "date_creation": dc
                })
            
            # Historique visuel du jour
            date_aujourdhui = datetime.now().strftime("%d/%m/%Y")
            cursor.execute("SELECT reference, quantite, temps_unitaire, statut_final FROM historique_production WHERE date_realisation LIKE ?", (f"{date_aujourdhui}%",))
            for row in cursor.fetchall():
                ref = str(row[0]) if row[0] is not None else "TERMINE"
                prefix = ref.split('-')[0].strip() if '-' in ref else "CLIENT"
                taches.append({
                    "prefix": prefix, "ref": ref, "qte": row[1], 
                    "temps": row[2], "statut": "Terminé", 
                    "type": "interne" if '-' in ref else "client", 
                    "date_creation": datetime.min
                })
        except Exception:
            pass
        finally:
            conn.close()
        return taches

    # ==========================================
    # ALGORITHME DE PLANIFICATION GLOBAL
    # ==========================================
    def rafraichir_planning(self):
        for widget in self.main_scroll_y.winfo_children():
            widget.destroy()

        machines = self.charger_machines()
        taches = self.charger_taches()
        if not taches:
            ctk.CTkLabel(self.main_scroll_y, text="🎉 L'atelier est libre. Aucune pièce en attente.", font=ctk.CTkFont(slant="italic", size=14), text_color="gray50").pack(pady=40)
            return

        heure_deb_atelier, heure_fin_atelier = self.recuperer_horaires_atelier()
        PIXELS_PAR_MINUTE = 2.5       
        HAUTEUR_LIGNE = 60          
        HAUTEUR_ENTETE = 75        
        LARGEUR_PANNEAU_GAUCHE = 220 
        maintenant = datetime.now()
        
        self.heure_debut_planning = datetime.combine(maintenant.date(), heure_deb_atelier)
        if maintenant.time() < heure_deb_atelier:
            self.heure_debut_planning -= timedelta(days=1)

        # 1. Préparation sécurisée des pièces
        pieces_a_planifier = []
        for t in taches:
            try: qte = int(float(t.get("qte", 1)))
            except: qte = 1
                
            statut_str = str(t.get("statut", ""))
            statut_lower = statut_str.lower()
            
            is_termine = (statut_str == "Terminé")
            is_urgence = "urgenc" in statut_lower or "urgent" in statut_lower
            
            date_echeance = None
            match = re.search(r"(\d{2}/\d{2}/\d{4})", statut_str)
            if match:
                try: date_echeance = datetime.strptime(match.group(1), "%d/%m/%Y").replace(hour=12, minute=0)
                except: pass
                
            score = 4
            if is_termine: score = 0
            elif is_urgence: score = 1
            elif date_echeance or "échéance" in statut_lower: score = 2
            elif "prochaine" in statut_lower: score = 3
            
            for piece_index in range(qte):
                try: duree = int(float(t.get("temps", 0)))
                except: continue
                if duree <= 0: continue
                
                p_dict = {
                    "ref": t.get("ref", ""),
                    "num_piece": f"{piece_index + 1}/{qte}",
                    "duree": duree,
                    "date_creation": t["date_creation"],
                    "statut_base": statut_str if statut_str else "Flux classique",
                    "is_urgence": is_urgence,
                    "is_termine": is_termine,
                    "date_echeance": date_echeance,
                    "score": score,
                    "prefix": str(t.get("prefix") or ""),
                    "type": t.get("type", "interne")
                }
                
                # REPLI (FALLBACK) POUR OF : Identifier les machines autorisées
                allowed = []
                for m_idx, mach in enumerate(machines):
                    if mach[3] == "OFF": continue
                    pref_auth = str(mach[2]) if mach[2] else ""
                    # 1ère passe : Compatibilité stricte du préfixe
                    if not pref_auth or (p_dict["prefix"] and p_dict["prefix"] in pref_auth) or p_dict["type"] == "client":
                        allowed.append(m_idx)
                
                # 2ème passe : Si aucune machine n'est trouvée pour ce préfixe, on l'autorise sur toutes
                if not allowed:
                    allowed = [m_idx for m_idx, mach in enumerate(machines) if mach[3] == "ON"]
                if not allowed and machines:
                    allowed = [0]
                    
                p_dict["allowed_machines"] = allowed
                pieces_a_planifier.append(p_dict)

        dispo_machines = [self.heure_debut_planning] * len(machines)
        blocs_a_dessiner = []
        self.dernier_gantt = []

        # 2. Assignation chronologique
        while pieces_a_planifier:
            meilleur_m_idx = -1
            meilleur_piece_idx = -1
            meilleur_start_time = None
            
            for m_idx, mach in enumerate(machines):
                if mach[3] == "OFF": continue
                
                m_dispo = dispo_machines[m_idx]
                candidats = []
                min_start_pour_machine = None
                
                for p_idx, p in enumerate(pieces_a_planifier):
                    if m_idx not in p["allowed_machines"]: 
                        continue
                    
                    start_brute = max(m_dispo, p["date_creation"])
                    start_ajustee = valider_horaire_lancement(start_brute, heure_deb_atelier, heure_fin_atelier)
                    
                    if min_start_pour_machine is None or start_ajustee < min_start_pour_machine:
                        min_start_pour_machine = start_ajustee
                        candidats = [p_idx]
                    elif start_ajustee == min_start_pour_machine:
                        candidats.append(p_idx)
                        
                if not candidats: continue
                    
                is_night_window = False
                try:
                    limit_night = (datetime.combine(min_start_pour_machine.date(), heure_fin_atelier) - timedelta(hours=2)).time()
                    if limit_night <= min_start_pour_machine.time() <= heure_fin_atelier:
                        is_night_window = True
                except: pass
                    
                def sort_key(p_idx):
                    p = pieces_a_planifier[p_idx]
                    if p["is_termine"]: return (-1, 0, 0, 0)
                    urg = 0 if p["is_urgence"] else 1
                    
                    if is_night_window:
                        return (urg, -p["duree"], p["score"], p["date_creation"].timestamp())
                    else:
                        ech_ts = p["date_echeance"].timestamp() if p["date_echeance"] else float('inf')
                        return (urg, ech_ts, p["score"], p["date_creation"].timestamp())
                        
                candidats.sort(key=sort_key)
                best_p_idx = candidats[0]
                
                if meilleur_start_time is None or min_start_pour_machine < meilleur_start_time:
                    meilleur_start_time = min_start_pour_machine
                    meilleur_m_idx = m_idx
                    meilleur_piece_idx = best_p_idx
                    
            if meilleur_m_idx == -1:
                break 
                
            p_choisie = pieces_a_planifier.pop(meilleur_piece_idx)
            debut = meilleur_start_time
            fin = debut + timedelta(minutes=p_choisie["duree"])
            
            is_completed_now = (fin <= maintenant) or p_choisie["is_termine"]
            couleur = "#4B5563" if is_completed_now else self.generer_couleur(p_choisie["prefix"], p_choisie["ref"], p_choisie["statut_base"])
            
            bloc_info = {
                "colonne": meilleur_m_idx,
                "debut": debut,
                "fin": fin,
                "duree": p_choisie["duree"],
                "ref": p_choisie["ref"],
                "qte": 1,
                "num_piece": p_choisie["num_piece"],
                "statut": p_choisie["statut_base"],
                "couleur": couleur,
                "is_termine": is_completed_now,
                "type": p_choisie["type"]
            }
            blocs_a_dessiner.append(bloc_info)
            self.dernier_gantt.append(bloc_info)
            
            dispo_machines[meilleur_m_idx] = fin

        # ==========================================
        # AUTO-ARCHIVAGE DES TÂCHES TERMINÉES
        # ==========================================
        self.auto_archiver_termines(self.dernier_gantt)

        # ==========================================
        # DESSIN DU GRAPHIQUE
        # ==========================================
        valeurs_machines = dispo_machines
        if valeurs_machines:
            fin_max = max(valeurs_machines)
        else:
            fin_max = self.heure_debut_planning + timedelta(hours=12)
            
        duree_totale_minutes = max((fin_max - self.heure_debut_planning).total_seconds() / 60.0, 720.0)
        self.largeur_canvas = int(duree_totale_minutes * PIXELS_PAR_MINUTE) + 400

        split_container = ctk.CTkFrame(self.main_scroll_y, fg_color="transparent")
        split_container.pack(fill="x", expand=True)

        panel_gauche = ctk.CTkFrame(split_container, width=LARGEUR_PANNEAU_GAUCHE, corner_radius=0, fg_color="#1F2937", border_width=0)
        panel_gauche.pack(side="left", fill="y")
        panel_gauche.pack_propagate(False)

        ctk.CTkFrame(panel_gauche, height=HAUTEUR_ENTETE, fg_color="#111827", corner_radius=0).pack(fill="x")

        for i, mach in enumerate(machines):
            statut_machine = mach[3]
            if statut_machine == "OFF":
                bg_color, text_color = "#374151", "#9CA3AF"
                nom_affichage = f"🛑  {mach[1]}\n(HORS SERVICE)"
            else:
                bg_color = "#1F2937" if i % 2 == 0 else "#111827"
                text_color = "#F3F4F6"
                nom_affichage = f"🟢  {mach[1]}"
                
            lbl_cadre = ctk.CTkFrame(panel_gauche, height=HAUTEUR_LIGNE, fg_color=bg_color, corner_radius=0, border_width=0)
            lbl_cadre.pack(fill="x")
            lbl_cadre.pack_propagate(False)
            ctk.CTkLabel(lbl_cadre, text=nom_affichage, text_color=text_color, font=ctk.CTkFont(family="Segoe UI", weight="bold", size=13), anchor="w", justify="left").pack(side="left", padx=15, expand=True, fill="both")

        self.scroll_droite = ctk.CTkScrollableFrame(split_container, orientation="horizontal", corner_radius=0, fg_color="#111827", height=HAUTEUR_ENTETE + (len(machines)*HAUTEUR_LIGNE) + 20)
        self.scroll_droite.pack(side="left", fill="both", expand=True)

        canvas_gantt = ctk.CTkFrame(self.scroll_droite, width=self.largeur_canvas, height=HAUTEUR_ENTETE + (len(machines)*HAUTEUR_LIGNE), fg_color="#111827", corner_radius=0)
        canvas_gantt.pack()
        canvas_gantt.pack_propagate(False)

        def get_x(dt):
            return int((dt - self.heure_debut_planning).total_seconds() / 60.0 * PIXELS_PAR_MINUTE)

        for i, mach in enumerate(machines):
            y_pos = HAUTEUR_ENTETE + (i * HAUTEUR_LIGNE)
            bg_row = "#374151" if mach[3] == "OFF" else ("#1F2937" if i % 2 == 0 else "#111827")
            row_frame = ctk.CTkFrame(canvas_gantt, width=self.largeur_canvas, height=HAUTEUR_LIGNE, fg_color=bg_row, corner_radius=0)
            row_frame.place(x=0, y=y_pos)

        jours_totaux = (fin_max.date() - self.heure_debut_planning.date()).days + 2
        jours_semaine = ["Lun", "Mar", "Mer", "Jeu", "Ven", "Sam", "Dim"]
        mois_noms = ["Jan", "Fév", "Mar", "Avr", "Mai", "Juin", "Juil", "Aoû", "Sep", "Oct", "Nov", "Déc"]

        for i in range(jours_totaux):
            jour_date = self.heure_debut_planning.date() + timedelta(days=i)
            dt_debut_jour = datetime.combine(jour_date, time.min)
            x_jour = get_x(dt_debut_jour)
            if x_jour > self.largeur_canvas: break
            
            txt_date = f"{jours_semaine[jour_date.weekday()]} {jour_date.day} {mois_noms[jour_date.month-1]}"
            ctk.CTkLabel(canvas_gantt, text=txt_date, text_color="#D1D5DB", font=ctk.CTkFont(size=14, weight="bold")).place(x=max(0, x_jour) + 10, y=10)

            for h in range(24):
                dt_h = datetime.combine(jour_date, time(h, 0))
                x_h = get_x(dt_h)
                if 0 <= x_h <= self.largeur_canvas:
                    ctk.CTkLabel(canvas_gantt, text=f"{h:02d}:00", text_color="#9CA3AF", font=ctk.CTkFont(size=11, weight="bold")).place(x=x_h + 5, y=40)
                    ctk.CTkFrame(canvas_gantt, width=1, height=len(machines)*HAUTEUR_LIGNE, fg_color="#374151").place(x=x_h, y=HAUTEUR_ENTETE)

        for i in range(len(machines) + 1):
            y_pos = HAUTEUR_ENTETE + (i * HAUTEUR_LIGNE)
            ctk.CTkFrame(canvas_gantt, width=self.largeur_canvas, height=1, fg_color="#0F172A").place(x=0, y=y_pos - 1)

        for b in blocs_a_dessiner:
            x_deb = get_x(b["debut"])
            x_fin = get_x(b["fin"])
            if x_fin < 0: continue
            
            x_deb = max(0, x_deb)
            largeur_bloc = max(x_fin - x_deb, 4)
            y_pos = HAUTEUR_ENTETE + (b["colonne"] * HAUTEUR_LIGNE)
            
            bloc = ctk.CTkFrame(canvas_gantt, fg_color=b["couleur"], corner_radius=6, border_width=0, width=largeur_bloc, height=HAUTEUR_LIGNE - 14)
            bloc.place(x=x_deb, y=y_pos + 7)
            bloc.pack_propagate(False)

            icone_ok = "✔️ " if b["is_termine"] else ""
            if largeur_bloc > 80: texte = f"{icone_ok}{b['ref']}\n({b['num_piece']})"
            elif largeur_bloc > 40: texte = f"{icone_ok}{b['num_piece']}"
            else: texte = "" 
                
            text_color = "#9CA3AF" if b["is_termine"] else "#111827"
            lbl_texte = ctk.CTkLabel(bloc, text=texte, font=ctk.CTkFont(family="Segoe UI", size=10, weight="bold"), text_color=text_color, justify="center")
            if texte: lbl_texte.pack(expand=True)

            texte_tooltip = f"Référence : {b['ref']} (Pièce {b['num_piece']})\nDébut : {b['debut'].strftime('%d/%m %H:%M')}\nFin : {b['fin'].strftime('%d/%m %H:%M')}\nPriorité : {b['statut']}"
            ToolTip(bloc, texte_tooltip)
            ToolTip(lbl_texte, texte_tooltip)

        if maintenant >= self.heure_debut_planning:
            x_maintenant = get_x(maintenant)
            ctk.CTkFrame(canvas_gantt, width=2, height=len(machines)*HAUTEUR_LIGNE, fg_color="#F43F5E").place(x=x_maintenant, y=HAUTEUR_ENTETE)
            head = ctk.CTkFrame(canvas_gantt, width=12, height=12, fg_color="#F43F5E", corner_radius=6)
            head.place(x=x_maintenant - 5, y=HAUTEUR_ENTETE - 6)
            heure_txt = maintenant.strftime("%H:%M")
            ctk.CTkLabel(canvas_gantt, text=heure_txt, text_color="#F43F5E", font=ctk.CTkFont(size=12, weight="bold")).place(x=x_maintenant - 15, y=HAUTEUR_ENTETE - 25)

    # ==========================================
    # GESTION PRODUCTION : ARCHIVAGE ET SUIVI
    # ==========================================
    def auto_archiver_termines(self, gantt_donnees):
        """ 
        Passe en 'Terminé' et stocke dans l'historique les pièces qui ont atteint 100% de leur temps.
        """
        maintenant = datetime.now()
        groupes = {}
        
        for b in gantt_donnees:
            if b.get("type") != "interne": continue
            ref = b["ref"]
            if ref not in groupes: groupes[ref] = []
            groupes[ref].append(b)
            
        conn = sqlite3.connect("atelier.db")
        cursor = conn.cursor()
        
        for ref, blocs in groupes.items():
            fin_globale = max(b["fin"] for b in blocs)
            
            # Si le lot a atteint 100%
            if maintenant >= fin_globale:
                cursor.execute("SELECT statut FROM references_generees WHERE reference_complete = ?", (ref,))
                resultat = cursor.fetchone()
                
                # S'il n'est pas déjà enregistré comme Terminé
                if resultat and resultat[0] != 'Terminé':
                    cursor.execute("UPDATE references_generees SET statut = 'Terminé' WHERE reference_complete = ?", (ref,))
                    
                    cursor.execute("SELECT quantite, temps_unitaire FROM references_generees WHERE reference_complete = ?", (ref,))
                    info_of = cursor.fetchone()
                    qte = info_of[0] if info_of else 1
                    temps = info_of[1] if info_of else 0
                    date_realisation = fin_globale.strftime("%d/%m/%Y %H:%M")
                    
                    # On crée la table au cas où (sécurité)
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
                        INSERT INTO historique_production (reference, quantite, temps_unitaire, statut_final, date_realisation) 
                        VALUES (?, ?, ?, ?, ?)
                    """, (ref, qte, temps, "Terminé", date_realisation))
                    
        conn.commit()
        conn.close()

    def get_blocs_planifies(self):
        """ 
        Retourne la progression des lots pour alimenter le tableau de Suivi de Prod.
        Affiche toutes les pièces de 0% (en attente) jusqu'à 99% (en cours).
        """
        maintenant = datetime.now()
        res = {}
        groupes = {}
        
        for b in self.dernier_gantt:
            if b.get("type") != "interne": continue
                
            ref = b["ref"]
            if ref not in groupes: groupes[ref] = []
            groupes[ref].append(b)
            
        for ref, blocs in groupes.items():
            total_min = 0
            fait_min = 0
            fin_globale = blocs[0]["fin"]
            
            for b in blocs:
                duree = b["duree"]
                total_min += duree
                if b["fin"] > fin_globale: fin_globale = b["fin"]
                    
                if maintenant >= b["fin"]: 
                    fait_min += duree
                elif b["debut"] <= maintenant < b["fin"]:
                    fait_min += (maintenant - b["debut"]).total_seconds() / 60.0
            
            pct = int((fait_min / total_min) * 100) if total_min > 0 else 0
            pct = min(100, max(0, pct)) 
            
            # Affiche les tâches non terminées (inclut le 0%)
            if pct < 100:
                res[ref] = {
                    "fin": fin_globale.strftime("%d/%m %H:%M"),
                    "prog": f"{pct}%"
                }
        return res

    def annuler_of(self, reference):
        """ 
        Méthode pour annuler une production en cours. 
        À appeler depuis ton interface principale.
        """
        conn = sqlite3.connect("atelier.db")
        cursor = conn.cursor()
        
        # On passe le statut en "Annulé" (ça le sortira du Gantt au prochain refresh)
        cursor.execute("UPDATE references_generees SET statut = 'Annulé' WHERE reference_complete = ?", (reference,))
        
        conn.commit()
        conn.close()
        
        self.rafraichir_planning()
        
        if self.fonction_rafraichir_global:
            self.fonction_rafraichir_global()