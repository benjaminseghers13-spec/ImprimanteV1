import customtkinter as ctk
import sqlite3
from datetime import datetime

class FenetreModificationPiece(ctk.CTkToplevel):
    def __init__(self, master, id_piece, type_table, ref_actuelle, qte_actuelle, temps_actuel, statut_actuel, callback_succes):
        super().__init__(master)
        self.id_piece = id_piece
        self.type_table = type_table 
        self.callback_succes = callback_succes

        self.title(f"Modifier : {ref_actuelle}")
        self.geometry("380x350")
        self.resizable(False, False)
        self.grab_set()

        ctk.CTkLabel(self, text=f"✏️ Modification de la pièce", font=ctk.CTkFont(size=16, weight="bold")).pack(pady=15)

        form_frame = ctk.CTkFrame(self, fg_color="transparent")
        form_frame.pack(fill="x", padx=20, pady=5)

        ctk.CTkLabel(form_frame, text="Quantité :").grid(row=0, column=0, sticky="w", pady=8)
        self.entry_qte = ctk.CTkEntry(form_frame, width=150)
        self.entry_qte.insert(0, str(qte_actuelle))
        self.entry_qte.grid(row=0, column=1, sticky="w", pady=8)

        ctk.CTkLabel(form_frame, text="Temps unitaire (min) :").grid(row=1, column=0, sticky="w", pady=8)
        self.entry_temps = ctk.CTkEntry(form_frame, width=150)
        self.entry_temps.insert(0, str(temps_actuel))
        self.entry_temps.grid(row=1, column=1, sticky="w", pady=8)

        if self.type_table == "references_generees":
            ctk.CTkLabel(form_frame, text="Priorité :").grid(row=2, column=0, sticky="w", pady=8)
            self.combo_priorite = ctk.CTkOptionMenu(form_frame, values=["Flux classique", "Prochaine production", "Avant échéance client"], width=180)
            self.combo_priorite.set(statut_actuel if statut_actuel else "Flux classique")
            self.combo_priorite.grid(row=2, column=1, sticky="w", pady=8)
        else:
            self.combo_priorite = None

        self.lbl_msg = ctk.CTkLabel(self, text="", font=ctk.CTkFont(weight="bold"))
        self.lbl_msg.pack(pady=5)

        ctk.CTkButton(self, text="Enregistrer", fg_color="#10B981", hover_color="#059669", command=self.valider).pack(pady=10)

    def valider(self):
        try:
            qte = int(self.entry_qte.get())
            temps = int(self.entry_temps.get())
        except ValueError:
            self.lbl_msg.configure(text="⚠️ Quantité et temps doivent être des nombres.", text_color="orange")
            return

        statut = self.combo_priorite.get() if self.combo_priorite else "Flux classique"

        conn = sqlite3.connect("atelier.db", timeout=30.0)
        cursor = conn.cursor()
        try:
            if self.type_table == "references_generees":
                cursor.execute("""
                    UPDATE references_generees 
                    SET quantite = ?, temps_unitaire = ?, statut = ? 
                    WHERE id = ?
                """, (qte, temps, statut, self.id_piece))
            else:
                cursor.execute("""
                    UPDATE commandes_clients 
                    SET quantite = ?, temps_unitaire = ? 
                    WHERE id = ?
                """, (qte, temps, self.id_piece))
            
            conn.commit()
        except Exception as e:
            self.lbl_msg.configure(text=f"❌ Erreur: {e}", text_color="red")
            conn.close()
            return
        conn.close()

        if self.callback_succes:
            self.callback_succes()
        self.destroy()

class FenetreConfirmationAnnulation(ctk.CTkToplevel):
    def __init__(self, master, ref, callback_confirmer):
        super().__init__(master)
        self.callback_confirmer = callback_confirmer
        self.title("Annulation de production")
        self.geometry("380x180")
        self.resizable(False, False)
        self.grab_set()

        ctk.CTkLabel(self, text="⚠️ Annulation de l'OF", font=ctk.CTkFont(size=16, weight="bold"), text_color="#EF4444").pack(pady=(20, 10))
        message = f"Voulez-vous vraiment annuler la pièce '{ref}' ?"
        ctk.CTkLabel(self, text=message, font=ctk.CTkFont(size=13), justify="center").pack(pady=5)
        
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(fill="x", padx=20, pady=15)
        ctk.CTkButton(btn_frame, text="Retour", fg_color="gray50", hover_color="gray40", width=130, command=self.destroy).pack(side="left", padx=10)
        ctk.CTkButton(btn_frame, text="Oui, annuler", fg_color="#EF4444", hover_color="#DC2626", width=130, command=self.valider).pack(side="right", padx=10)

    def valider(self):
        self.callback_confirmer()
        self.destroy()

class OngletSuivi(ctk.CTkFrame):
    def __init__(self, master, get_blocs_planifies_func=None, fonction_rafraichir_global=None):
        super().__init__(master, fg_color="transparent")
        self.get_blocs_planifies = get_blocs_planifies_func
        self.fonction_rafraichir_global = fonction_rafraichir_global
        
        self.labels_dynamiques = {}

        ctk.CTkLabel(self, text="🛠️ Suivi de Production en Direct", font=ctk.CTkFont(size=22, weight="bold")).pack(anchor="w", pady=(0, 15))

        self.tab_suivi_view = ctk.CTkTabview(self, fg_color="transparent")
        self.tab_suivi_view.pack(fill="both", expand=True)

        self.tab_encours = self.tab_suivi_view.add("Pièces Planifiées & En Cours")
        self.tab_historique = self.tab_suivi_view.add("Historique & Réalisations")

        barre_filtre_encours = ctk.CTkFrame(self.tab_encours, fg_color="transparent")
        barre_filtre_encours.pack(fill="x", pady=(0, 10))

        ctk.CTkLabel(barre_filtre_encours, text="🔍 Filtrer :").pack(side="left", padx=5)
        self.entry_recherche = ctk.CTkEntry(barre_filtre_encours, width=200, placeholder_text="Tapez une référence...")
        self.entry_recherche.pack(side="left", padx=5)
        self.entry_recherche.bind("<KeyRelease>", lambda e: self.charger_encours())

        self.btn_tri = ctk.CTkButton(barre_filtre_encours, text="📂 Tri : Avancement ⬇", width=140, fg_color="#333333", command=self.changer_tri)
        self.btn_tri.pack(side="left", padx=10)
        self.tri_desc = True

        self.scroll_encours = ctk.CTkScrollableFrame(self.tab_encours, fg_color="transparent")
        self.scroll_encours.pack(fill="both", expand=True)

        self.scroll_historique = ctk.CTkScrollableFrame(self.tab_historique, fg_color="transparent")
        self.scroll_historique.pack(fill="both", expand=True)

        self.charger_suivi()

        if not hasattr(self, 'boucle_direct_active'):
            self.boucle_direct_active = True
            self.actualiser_en_direct()

    def actualiser_en_direct(self):
        if not self.winfo_exists(): return 
        
        if self.get_blocs_planifies:
            try:
                blocs_gantt = self.get_blocs_planifies()
                for ref, labels in self.labels_dynamiques.items():
                    if labels["prog"].winfo_exists():
                        info = blocs_gantt.get(ref, {"fin": "Planifié", "prog": "0%"})
                        labels["prog"].configure(text=info["prog"])
                        labels["fin"].configure(text=info["fin"])
            except Exception:
                pass
                
        self.after(5000, self.actualiser_en_direct)

    def changer_tri(self):
        self.tri_desc = not self.tri_desc
        texte = "📂 Tri : Avancement ⬇" if self.tri_desc else "📂 Tri : Avancement ⬆"
        self.btn_tri.configure(text=texte)
        self.charger_encours()

    def charger_suivi(self):
        self.charger_encours()
        self.charger_historique()

    def charger_encours(self):
        for widget in self.scroll_encours.winfo_children():
            widget.destroy()

        self.labels_dynamiques.clear() 
        filtre_texte = self.entry_recherche.get().strip().upper()
        
        blocs_gantt = {}
        if self.get_blocs_planifies:
            try:
                blocs_gantt = self.get_blocs_planifies()
            except Exception:
                pass

        conn = sqlite3.connect("atelier.db", timeout=30.0)
        cursor = conn.cursor()
        toutes_taches = []
        
        # On ignore directement les pièces 'Terminé' ou 'Annulé' depuis la BDD
        try:
            cursor.execute("SELECT id, reference_complete, quantite, temps_unitaire, statut, consommable_lie, quantite_conso FROM references_generees WHERE statut NOT IN ('Terminé', 'Annulé')")
            for row in cursor.fetchall():
                toutes_taches.append(("references_generees", row))
        except sqlite3.OperationalError:
            cursor.execute("SELECT id, reference_complete, quantite, temps_unitaire, statut FROM references_generees WHERE statut NOT IN ('Terminé', 'Annulé')")
            for row in cursor.fetchall():
                toutes_taches.append(("references_generees", (*row, "", 0.0)))
                
        try:
            cursor.execute("SELECT id, reference_piece, quantite, temps_unitaire, statut, consommable_lie, quantite_conso FROM commandes_clients WHERE statut NOT IN ('Terminé', 'Annulé')")
            for row in cursor.fetchall():
                toutes_taches.append(("commandes_clients", row))
        except sqlite3.OperationalError:
            cursor.execute("SELECT id, reference_piece, quantite, temps_unitaire, statut FROM commandes_clients WHERE statut NOT IN ('Terminé', 'Annulé')")
            for row in cursor.fetchall():
                toutes_taches.append(("commandes_clients", (*row, "", 0.0)))
                
        conn.close()

        if filtre_texte: 
            toutes_taches = [t for t in toutes_taches if filtre_texte in t[1][1].upper()]

        # FILTRE STRICT : On ne conserve QUE les tâches qui ont réussi à être placées sur le Gantt
        # Cela élimine d'office les tâches avec un statut "Créée" qui ne seraient pas encore passées dans l'algo du Gantt
        toutes_taches = [t for t in toutes_taches if t[1][1] in blocs_gantt]

        def obtenir_pourcentage(tache):
            ref = tache[1][1]
            info = blocs_gantt.get(ref, {})
            prog_str = info.get("prog", "0%")
            try:
                return int(prog_str.replace("%", ""))
            except ValueError:
                return 0
        
        toutes_taches.sort(key=obtenir_pourcentage, reverse=self.tri_desc)

        if not toutes_taches:
            ctk.CTkLabel(self.scroll_encours, text="Aucune pièce n'est actuellement programmée en production.", font=ctk.CTkFont(slant="italic")).pack(pady=20)
            return

        header = ctk.CTkFrame(self.scroll_encours, fg_color=("gray80", "gray25"))
        header.pack(fill="x", pady=2)
        ctk.CTkLabel(header, text="Référence", font=ctk.CTkFont(weight="bold"), width=150, anchor="w").pack(side="left", padx=10)
        ctk.CTkLabel(header, text="Qté", font=ctk.CTkFont(weight="bold"), width=40).pack(side="left")
        ctk.CTkLabel(header, text="Temps", font=ctk.CTkFont(weight="bold"), width=50).pack(side="left")
        ctk.CTkLabel(header, text="Matière estimée", font=ctk.CTkFont(weight="bold"), width=130).pack(side="left")
        ctk.CTkLabel(header, text="Priorité / Statut", font=ctk.CTkFont(weight="bold"), width=120).pack(side="left")
        ctk.CTkLabel(header, text="Avancement", font=ctk.CTkFont(weight="bold"), width=90).pack(side="left")
        ctk.CTkLabel(header, text="Fin Prévue", font=ctk.CTkFont(weight="bold"), width=110).pack(side="left")
        ctk.CTkLabel(header, text="Annuler", font=ctk.CTkFont(weight="bold"), width=50).pack(side="right", padx=10)

        for table_type, (p_id, ref, qte, temps, statut, conso_lie, qte_conso) in toutes_taches:
            ligne = ctk.CTkFrame(self.scroll_encours, fg_color=("gray90", "gray15"))
            ligne.pack(fill="x", pady=3, ipadx=5, ipady=5)

            btn_ref = ctk.CTkButton(ligne, text=ref, fg_color="transparent", text_color=("#1D4ED8", "#60A5FA"),
                                    font=ctk.CTkFont(weight="bold", size=12), anchor="w", width=150,
                                    command=lambda id_p=p_id, t=table_type, r=ref, q=qte, tp=temps, s=statut: self.ouvrir_modification(id_p, t, r, q, tp, s))
            btn_ref.pack(side="left", padx=5)

            ctk.CTkLabel(ligne, text=str(qte), width=40).pack(side="left")
            ctk.CTkLabel(ligne, text=f"{temps}m", width=50).pack(side="left")
            
            texte_matiere = "-"
            total_conso = 0
            
            try:
                val_conso = float(qte_conso) if qte_conso is not None and str(qte_conso).strip() != "" else 0.0
            except (ValueError, TypeError):
                val_conso = 0.0

            if conso_lie and val_conso > 0:
                total_conso = qte * val_conso
                texte_matiere = f"{total_conso:.2f} {conso_lie[:10]}.." if len(conso_lie)>10 else f"{total_conso:.2f} {conso_lie}"
            
            ctk.CTkLabel(ligne, text=texte_matiere, width=130, text_color="#F59E0B", font=ctk.CTkFont(size=11, slant="italic")).pack(side="left")
            ctk.CTkLabel(ligne, text=str(statut), width=120).pack(side="left")

            info_g = blocs_gantt.get(ref, {"fin": "Planifié", "prog": "0%"})
            
            lbl_prog = ctk.CTkLabel(ligne, text=info_g["prog"], width=90, text_color="#10B981", font=ctk.CTkFont(weight="bold"))
            lbl_prog.pack(side="left")
            
            lbl_fin = ctk.CTkLabel(ligne, text=info_g["fin"], width=110, text_color="#60A5FA")
            lbl_fin.pack(side="left")
            
            self.labels_dynamiques[ref] = {"prog": lbl_prog, "fin": lbl_fin}

            btn_annuler = ctk.CTkButton(ligne, text="❌", fg_color="#EF4444", hover_color="#DC2626", width=35, height=26,
                                      command=lambda id_p=p_id, t=table_type, r=ref: self.demander_confirmation_annulation(id_p, t, r))
            btn_annuler.pack(side="right", padx=10)

    def ouvrir_modification(self, id_piece, type_table, ref, qte, temps, statut):
        FenetreModificationPiece(self, id_piece, type_table, ref, qte, temps, statut, callback_succes=self.rafraichir_tout_global)

    def demander_confirmation_annulation(self, id_piece, type_table, ref):
        FenetreConfirmationAnnulation(self, ref, callback_confirmer=lambda: self.annuler_piece(id_piece, type_table))

    def annuler_piece(self, id_piece, type_table):
        conn = sqlite3.connect("atelier.db", timeout=30.0)
        cursor = conn.cursor()
        try:
            table_nom = "references_generees" if type_table == "references_generees" else "commandes_clients"
            # On passe simplement le statut en 'Annulé'
            cursor.execute(f"UPDATE {table_nom} SET statut = 'Annulé' WHERE id = ?", (id_piece,))
            conn.commit()
        except Exception as e:
            print(f"Erreur lors de l'annulation: {e}")
        finally:
            conn.close()

        self.rafraichir_tout_global()

    def charger_historique(self):
        for widget in self.scroll_historique.winfo_children():
            widget.destroy()

        conn = sqlite3.connect("atelier.db", timeout=30.0)
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT reference, quantite, temps_unitaire, statut_final, date_realisation FROM historique_production ORDER BY id DESC")
            historique = cursor.fetchall()
        except sqlite3.OperationalError:
            historique = []
        conn.close()

        if not historique:
            ctk.CTkLabel(self.scroll_historique, text="Aucun historique pour le moment.", font=ctk.CTkFont(slant="italic")).pack(pady=20)
            return

        header = ctk.CTkFrame(self.scroll_historique, fg_color=("gray80", "gray25"))
        header.pack(fill="x", pady=2)
        ctk.CTkLabel(header, text="Référence Réalisée", font=ctk.CTkFont(weight="bold"), width=220, anchor="w").pack(side="left", padx=10)
        ctk.CTkLabel(header, text="Qté", font=ctk.CTkFont(weight="bold"), width=60).pack(side="left")
        ctk.CTkLabel(header, text="Temps unit.", font=ctk.CTkFont(weight="bold"), width=90).pack(side="left")
        ctk.CTkLabel(header, text="Statut", font=ctk.CTkFont(weight="bold"), width=140).pack(side="left")
        ctk.CTkLabel(header, text="Date de réalisation", font=ctk.CTkFont(weight="bold"), width=150).pack(side="right", padx=10)

        for ref, qte, temps, statut_final, date_real in historique:
            ligne = ctk.CTkFrame(self.scroll_historique, fg_color=("gray90", "gray15"))
            ligne.pack(fill="x", pady=3, ipadx=5, ipady=5)

            ctk.CTkLabel(ligne, text=ref, font=ctk.CTkFont(weight="bold"), width=220, anchor="w").pack(side="left", padx=10)
            ctk.CTkLabel(ligne, text=str(qte), width=60).pack(side="left")
            ctk.CTkLabel(ligne, text=f"{temps} min", width=90).pack(side="left")
            ctk.CTkLabel(ligne, text=statut_final, text_color="#10B981", width=140).pack(side="left")
            ctk.CTkLabel(ligne, text=date_real, width=150).pack(side="right", padx=10)

    def rafraichir_tout_global(self):
        # 1. On force d'abord le rafraîchissement global (donc du Gantt) pour éliminer les annulés
        if self.fonction_rafraichir_global:
            self.fonction_rafraichir_global()
        # 2. Ensuite on recharge le suivi avec le nouveau Gantt propre
        self.charger_suivi()