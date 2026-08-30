"""Interface graphique locale de ComptaPrivée AI."""

import tkinter as tk
from decimal import Decimal, InvalidOperation
from pathlib import Path
from tkinter import filedialog, messagebox, ttk
from tkinter.scrolledtext import ScrolledText

from .csv_exporter import exporter_facture_csv
from .facture_parser import DonneesFacture, extraire_donnees_facture
from .main import extraire_texte_document


class ApplicationComptaPrivee(tk.Tk):
    """Application graphique locale destinée aux comptables."""

    def __init__(self) -> None:
        super().__init__()

        self.title("ComptaPrivée AI")
        self.geometry("1100x750")
        self.minsize(900, 650)

        self.chemin_document: Path | None = None

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
        style.configure("Titre.TLabel", font=("Segoe UI", 22, "bold"))
        style.configure("SousTitre.TLabel", font=("Segoe UI", 11))
        style.configure("Securite.TLabel", foreground="#166534")
        style.configure("Champ.TLabel", font=("Segoe UI", 10, "bold"))

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
                "Extraction et validation locale de documents comptables"
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
            text="Texte extrait",
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
                "Vérifiez et corrigez les champs avant l'exportation."
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
            text="Exporter en CSV",
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

    def selectionner_document(self) -> None:
        """Permet de sélectionner et d'analyser un document."""
        chemin = filedialog.askopenfilename(
            title="Sélectionner un document comptable",
            filetypes=[
                (
                    "Documents acceptés",
                    "*.pdf *.docx *.png *.jpg *.jpeg *.tif *.tiff *.bmp",
                ),
                ("PDF", "*.pdf"),
                ("Microsoft Word", "*.docx"),
                ("Images", "*.png *.jpg *.jpeg *.tif *.tiff *.bmp"),
                ("Tous les fichiers", "*.*"),
            ],
        )

        if not chemin:
            return

        self.chemin_document = Path(chemin)
        self.nom_document.set(self.chemin_document.name)
        self.analyser_document_selectionne()

    def analyser_document_selectionne(self) -> None:
        """Analyse le document choisi et remplit le formulaire."""
        if self.chemin_document is None:
            return

        self.statut.set("Analyse locale en cours…")
        self.update_idletasks()

        try:
            texte = extraire_texte_document(self.chemin_document)
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
            "Analyse terminée — vérifiez les champs avant l'exportation"
        )

    def afficher_texte(self, texte: str) -> None:
        """Affiche le texte extrait en lecture seule."""
        self.zone_texte.configure(state="normal")
        self.zone_texte.delete("1.0", "end")
        self.zone_texte.insert("1.0", texte)
        self.zone_texte.configure(state="disabled")

    def remplir_formulaire(self, facture: DonneesFacture) -> None:
        """Place les données extraites dans les champs modifiables."""
        self.variables["numero"].set(facture.numero or "")
        self.variables["date"].set(facture.date or "")
        self.variables["fournisseur"].set(facture.fournisseur or "")
        self.variables["client"].set(facture.client or "")
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
    def montant_vers_texte(montant: Decimal | None) -> str:
        """Convertit un montant pour l'affichage dans le formulaire."""
        if montant is None:
            return ""

        return f"{montant:.2f}"

    @staticmethod
    def texte_vers_montant(valeur: str) -> Decimal | None:
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
        """Transforme les champs modifiables en données structurées."""
        return DonneesFacture(
            numero=self.variables["numero"].get().strip() or None,
            date=self.variables["date"].get().strip() or None,
            fournisseur=(
                self.variables["fournisseur"].get().strip() or None
            ),
            client=self.variables["client"].get().strip() or None,
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
        """Exporte les données vérifiées dans un fichier CSV."""
        if self.chemin_document is None:
            return

        nom_initial = f"{self.chemin_document.stem}.csv"

        chemin_sortie = filedialog.asksaveasfilename(
            title="Exporter les données en CSV",
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

        self.statut.set(f"Export CSV terminé : {chemin.name}")

        messagebox.showinfo(
            "Export terminé",
            f"Le fichier CSV a été créé localement :\n{chemin}",
        )


def lancer_interface() -> None:
    """Lance l'interface graphique locale."""
    application = ApplicationComptaPrivee()
    application.mainloop()


if __name__ == "__main__":
    lancer_interface()