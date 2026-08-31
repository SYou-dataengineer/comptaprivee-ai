"""Interface graphique locale de ComptaPrivée AI."""

import tkinter as tk
from decimal import Decimal, InvalidOperation
from pathlib import Path
from tkinter import filedialog, messagebox, ttk
from tkinter.scrolledtext import ScrolledText

from .batch_processor import traiter_et_exporter_documents
from .csv_exporter import exporter_facture_csv
from .facture_parser import DonneesFacture, extraire_donnees_facture
from .main import extraire_texte_document


FORMATS_DOCUMENTS = (
    "*.pdf *.docx *.png *.jpg *.jpeg *.tif *.tiff *.bmp"
)


class ApplicationComptaPrivee(tk.Tk):
    """Application graphique locale destinée aux comptables."""

    def __init__(self) -> None:
        super().__init__()

        self.title("ComptaPrivée AI")
        self.geometry("1100x750")
        self.minsize(900, 650)

        self.chemin_document: Path | None = None
        self.chemins_lot: list[Path] = []

        self.variables = {
            "numero": tk.StringVar(),
            "date": tk.StringVar(),
            "fournisseur": tk.StringVar(),
            "client": tk.StringVar(),
            "sous_total": tk.StringVar(),
            "tps": tk.StringVar(),
            "tvq": tk.StringVar(),
            "total": tk.StringVar(),
        }

        self.nom_document = tk.StringVar(
            value="Aucun document sélectionné"
        )
        self.statut = tk.StringVar(
            value="Prêt — traitement entièrement local"
        )

        self.creer_interface()

    def creer_interface(self) -> None:
        """Construit les composants de l'interface."""
        style = ttk.Style(self)
        style.configure(
            "Titre.TLabel",
            font=("Segoe UI", 22, "bold"),
        )
        style.configure(
            "SousTitre.TLabel",
            font=("Segoe UI", 11),
        )
        style.configure(
            "Securite.TLabel",
            foreground="#166534",
        )
        style.configure(
            "Champ.TLabel",
            font=("Segoe UI", 10, "bold"),
        )

        conteneur = ttk.Frame(self, padding=20)
        conteneur.pack(fill="both", expand=True)

        entete = ttk.Frame(conteneur)
        entete.pack(fill="x")

        ttk.Label(
            entete,
            text="ComptaPrivée AI",
            style="Titre.TLabel",
        ).pack(anchor="w")

        ttk.Label(
            entete,
            text=(
                "Extraction et validation locale "
                "de documents comptables"
            ),
            style="SousTitre.TLabel",
        ).pack(anchor="w", pady=(2, 0))

        ttk.Label(
            entete,
            text=(
                "🔒 Traitement 100 % local — "
                "aucune donnée envoyée sur Internet"
            ),
            style="Securite.TLabel",
        ).pack(anchor="w", pady=(8, 15))

        barre_document = ttk.Frame(conteneur)
        barre_document.pack(fill="x", pady=(0, 15))

        ttk.Button(
            barre_document,
            text="Sélectionner un document",
            command=self.selectionner_document,
        ).pack(side="left")

        ttk.Button(
            barre_document,
            text="Traiter plusieurs documents",
            command=self.selectionner_documents_lot,
        ).pack(side="left", padx=(10, 0))

        ttk.Label(
            barre_document,
            textvariable=self.nom_document,
        ).pack(side="left", padx=12)

        zone_principale = ttk.Panedwindow(
            conteneur,
            orient="horizontal",
        )
        zone_principale.pack(fill="both", expand=True)

        panneau_champs = ttk.LabelFrame(
            zone_principale,
            text="Données à vérifier",
            padding=15,
        )
        panneau_texte = ttk.LabelFrame(
            zone_principale,
            text="Texte extrait ou résumé du lot",
            padding=10,
        )

        zone_principale.add(panneau_champs, weight=1)
        zone_principale.add(panneau_texte, weight=2)

        champs = [
            ("Numéro de facture", "numero"),
            ("Date", "date"),
            ("Fournisseur", "fournisseur"),
            ("Client", "client"),
            ("Sous-total", "sous_total"),
            ("TPS", "tps"),
            ("TVQ", "tvq"),
            ("Total", "total"),
        ]

        for ligne, (libelle, cle) in enumerate(champs):
            ttk.Label(
                panneau_champs,
                text=libelle,
                style="Champ.TLabel",
            ).grid(
                row=ligne,
                column=0,
                sticky="w",
                pady=6,
            )

            ttk.Entry(
                panneau_champs,
                textvariable=self.variables[cle],
                width=35,
            ).grid(
                row=ligne,
                column=1,
                sticky="ew",
                padx=(12, 0),
                pady=6,
            )

        panneau_champs.columnconfigure(1, weight=1)

        ttk.Label(
            panneau_champs,
            text=(
                "Vérifiez et corrigez les champs avant "
                "l'exportation d'un document unique."
            ),
            foreground="#92400e",
            wraplength=330,
        ).grid(
            row=len(champs),
            column=0,
            columnspan=2,
            sticky="w",
            pady=(15, 10),
        )

        self.bouton_exporter = ttk.Button(
            panneau_champs,
            text="Exporter le document en CSV",
            command=self.exporter,
            state="disabled",
        )
        self.bouton_exporter.grid(
            row=len(champs) + 1,
            column=0,
            columnspan=2,
            sticky="ew",
            pady=(5, 0),
        )

        self.zone_texte = ScrolledText(
            panneau_texte,
            wrap="word",
            font=("Consolas", 10),
        )
        self.zone_texte.pack(fill="both", expand=True)
        self.zone_texte.configure(state="disabled")

        barre_statut = ttk.Label(
            conteneur,
            textvariable=self.statut,
            relief="sunken",
            anchor="w",
            padding=6,
        )
        barre_statut.pack(fill="x", pady=(15, 0))

    @staticmethod
    def types_fichiers() -> list[tuple[str, str]]:
        """Retourne les formats acceptés par la sélection."""
        return [
            ("Documents acceptés", FORMATS_DOCUMENTS),
            ("PDF", "*.pdf"),
            ("Microsoft Word", "*.docx"),
            (
                "Images",
                "*.png *.jpg *.jpeg *.tif *.tiff *.bmp",
            ),
            ("Tous les fichiers", "*.*"),
        ]

    @staticmethod
    def dossier_exports() -> Path:
        """Retourne et crée le dossier local des exports."""
        chemin = Path.cwd() / "data" / "exports"
        chemin.mkdir(parents=True, exist_ok=True)
        return chemin

    def selectionner_document(self) -> None:
        """Permet de sélectionner et d'analyser un document."""
        chemin = filedialog.askopenfilename(
            title="Sélectionner un document comptable",
            filetypes=self.types_fichiers(),
        )

        if not chemin:
            return

        self.chemins_lot = []
        self.chemin_document = Path(chemin)
        self.nom_document.set(self.chemin_document.name)
        self.analyser_document_selectionne()

    def selectionner_documents_lot(self) -> None:
        """Sélectionne plusieurs documents et lance leur traitement."""
        chemins = filedialog.askopenfilenames(
            title="Sélectionner plusieurs documents comptables",
            filetypes=self.types_fichiers(),
        )

        if not chemins:
            return

        self.chemin_document = None
        self.chemins_lot = [
            Path(chemin)
            for chemin in chemins
        ]

        nombre_documents = len(self.chemins_lot)
        self.nom_document.set(
            f"{nombre_documents} documents sélectionnés"
        )

        self.vider_formulaire()
        self.bouton_exporter.configure(state="disabled")

        chemin_sortie = filedialog.asksaveasfilename(
            title="Enregistrer le CSV regroupé",
            initialdir=str(self.dossier_exports()),
            defaultextension=".csv",
            initialfile="factures_lot.csv",
            filetypes=[("Fichier CSV", "*.csv")],
        )

        if not chemin_sortie:
            self.statut.set(
                "Traitement annulé — "
                "aucun fichier CSV sélectionné"
            )
            return

        self.traiter_lot(Path(chemin_sortie))

    def traiter_lot(self, chemin_sortie: Path) -> None:
        """Analyse les documents et crée un CSV regroupé."""
        self.statut.set(
            f"Traitement local de {len(self.chemins_lot)} documents…"
        )
        self.update_idletasks()

        try:
            resultat = traiter_et_exporter_documents(
                self.chemins_lot,
                chemin_sortie,
            )
        except Exception as erreur:
            self.statut.set("Échec du traitement par lot")
            messagebox.showerror(
                "Erreur du traitement par lot",
                str(erreur),
            )
            return

        lignes_resume = [
            "TRAITEMENT PAR LOT TERMINÉ",
            "=" * 55,
            "",
            f"Documents sélectionnés : {len(self.chemins_lot)}",
            (
                "Documents analysés avec succès : "
                f"{resultat.nombre_documents_reussis}"
            ),
            (
                "Documents en erreur : "
                f"{resultat.nombre_documents_en_erreur}"
            ),
            "",
            f"Fichier CSV créé : {chemin_sortie}",
        ]

        if resultat.factures:
            lignes_resume.extend(
                [
                    "",
                    "FACTURES EXTRAITES",
                    "-" * 55,
                ]
            )

            for position, facture in enumerate(
                resultat.factures,
                start=1,
            ):
                numero = facture.numero or "Numéro non détecté"
                total = self.montant_vers_texte(facture.total)

                if total:
                    total_affiche = f"{total} CAD"
                else:
                    total_affiche = "Total non détecté"

                lignes_resume.append(
                    f"{position}. {numero} — {total_affiche}"
                )

        if resultat.erreurs:
            lignes_resume.extend(
                [
                    "",
                    "ERREURS",
                    "-" * 55,
                ]
            )

            for erreur in resultat.erreurs:
                lignes_resume.append(
                    f"- {erreur.chemin.name} : {erreur.message}"
                )

        self.afficher_texte("\n".join(lignes_resume))

        self.statut.set(
            "Traitement par lot terminé — "
            f"{resultat.nombre_documents_reussis} réussite(s), "
            f"{resultat.nombre_documents_en_erreur} erreur(s)"
        )

        messagebox.showinfo(
            "Traitement terminé",
            (
                "Le traitement local est terminé.\n\n"
                "Documents réussis : "
                f"{resultat.nombre_documents_reussis}\n"
                "Documents en erreur : "
                f"{resultat.nombre_documents_en_erreur}\n\n"
                f"CSV créé :\n{chemin_sortie}"
            ),
        )

    def analyser_document_selectionne(self) -> None:
        """Analyse le document choisi et remplit le formulaire."""
        if self.chemin_document is None:
            return

        self.statut.set("Analyse locale en cours…")
        self.update_idletasks()

        try:
            texte = extraire_texte_document(
                self.chemin_document
            )
            facture = extraire_donnees_facture(texte)
        except Exception as erreur:
            self.statut.set("Échec de l'analyse")
            messagebox.showerror(
                "Erreur d'analyse",
                str(erreur),
            )
            return

        self.afficher_texte(texte)
        self.remplir_formulaire(facture)

        self.bouton_exporter.configure(state="normal")
        self.statut.set(
            "Analyse terminée — "
            "vérifiez les champs avant l'exportation"
        )

    def afficher_texte(self, texte: str) -> None:
        """Affiche du texte dans la zone en lecture seule."""
        self.zone_texte.configure(state="normal")
        self.zone_texte.delete("1.0", "end")
        self.zone_texte.insert("1.0", texte)
        self.zone_texte.configure(state="disabled")

    def vider_formulaire(self) -> None:
        """Efface tous les champs du formulaire."""
        for variable in self.variables.values():
            variable.set("")

    def remplir_formulaire(
        self,
        facture: DonneesFacture,
    ) -> None:
        """Place les données extraites dans le formulaire."""
        self.variables["numero"].set(
            facture.numero or ""
        )
        self.variables["date"].set(
            facture.date or ""
        )
        self.variables["fournisseur"].set(
            facture.fournisseur or ""
        )
        self.variables["client"].set(
            facture.client or ""
        )
        self.variables["sous_total"].set(
            self.montant_vers_texte(facture.sous_total)
        )
        self.variables["tps"].set(
            self.montant_vers_texte(facture.tps)
        )
        self.variables["tvq"].set(
            self.montant_vers_texte(facture.tvq)
        )
        self.variables["total"].set(
            self.montant_vers_texte(facture.total)
        )

    @staticmethod
    def montant_vers_texte(
        montant: Decimal | None,
    ) -> str:
        """Convertit un montant pour son affichage."""
        if montant is None:
            return ""

        return f"{montant:.2f}"

    @staticmethod
    def texte_vers_montant(
        valeur: str,
    ) -> Decimal | None:
        """Convertit un montant corrigé par l'utilisateur."""
        valeur_normalisee = (
            valeur.strip()
            .replace(" ", "")
            .replace(",", ".")
            .replace("$", "")
            .replace("CAD", "")
        )

        if not valeur_normalisee:
            return None

        try:
            return Decimal(valeur_normalisee)
        except InvalidOperation as erreur:
            raise ValueError(
                f"Montant invalide : {valeur}"
            ) from erreur

    def lire_formulaire(self) -> DonneesFacture:
        """Transforme le formulaire en données structurées."""
        return DonneesFacture(
            numero=(
                self.variables["numero"].get().strip()
                or None
            ),
            date=(
                self.variables["date"].get().strip()
                or None
            ),
            fournisseur=(
                self.variables["fournisseur"].get().strip()
                or None
            ),
            client=(
                self.variables["client"].get().strip()
                or None
            ),
            sous_total=self.texte_vers_montant(
                self.variables["sous_total"].get()
            ),
            tps=self.texte_vers_montant(
                self.variables["tps"].get()
            ),
            tvq=self.texte_vers_montant(
                self.variables["tvq"].get()
            ),
            total=self.texte_vers_montant(
                self.variables["total"].get()
            ),
        )

    def exporter(self) -> None:
        """Exporte une facture vérifiée dans un CSV."""
        if self.chemin_document is None:
            return

        nom_initial = f"{self.chemin_document.stem}.csv"

        chemin_sortie = filedialog.asksaveasfilename(
            title="Exporter les données en CSV",
            initialdir=str(self.dossier_exports()),
            defaultextension=".csv",
            initialfile=nom_initial,
            filetypes=[("Fichier CSV", "*.csv")],
        )

        if not chemin_sortie:
            return

        try:
            facture = self.lire_formulaire()
            chemin = exporter_facture_csv(
                facture,
                chemin_sortie,
            )
        except ValueError as erreur:
            messagebox.showerror(
                "Donnée invalide",
                str(erreur),
            )
            return

        self.statut.set(
            f"Export CSV terminé : {chemin.name}"
        )

        messagebox.showinfo(
            "Export terminé",
            (
                "Le fichier CSV a été créé localement :\n"
                f"{chemin}"
            ),
        )


def lancer_interface() -> None:
    """Lance l'interface graphique locale."""
    application = ApplicationComptaPrivee()
    application.mainloop()


if __name__ == "__main__":
    lancer_interface()