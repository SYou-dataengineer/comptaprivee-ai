"""Interface graphique locale de ComptaPrivée AI."""

import tkinter as tk
from decimal import Decimal, InvalidOperation
from pathlib import Path
from tkinter import filedialog, messagebox, ttk
from tkinter.scrolledtext import ScrolledText

from .batch_processor import traiter_et_exporter_documents
from .csv_exporter import exporter_facture_csv
from .database import enregistrer_facture
from .facture_parser import DonneesFacture, extraire_donnees_facture
from .invoice_validator import (
    ResultatValidation,
    StatutValidation,
    valider_facture,
)
from .main import extraire_texte_document


FORMATS_DOCUMENTS = (
    "*.pdf *.docx *.png *.jpg *.jpeg *.tif *.tiff *.bmp"
)


class ApplicationComptaPrivee(tk.Tk):
    """Application graphique locale destinée aux comptables."""

    def __init__(self) -> None:
        super().__init__()

        self.title("ComptaPrivée AI")
        self.geometry("1100x780")
        self.minsize(900, 680)

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
        self.statut_validation = tk.StringVar(
            value="Validation : aucun document analysé"
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

        zone_principale.add(
            panneau_champs,
            weight=1,
        )
        zone_principale.add(
            panneau_texte,
            weight=2,
        )

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

        panneau_champs.columnconfigure(
            1,
            weight=1,
        )

        self.etiquette_validation = ttk.Label(
            panneau_champs,
            textvariable=self.statut_validation,
            font=("Segoe UI", 10, "bold"),
            foreground="#475569",
        )
        self.etiquette_validation.grid(
            row=len(champs),
            column=0,
            columnspan=2,
            sticky="w",
            pady=(15, 5),
        )

        ttk.Label(
            panneau_champs,
            text=(
                "Vérifiez et corrigez les champs avant "
                "l'exportation d'un document unique."
            ),
            foreground="#92400e",
            wraplength=330,
        ).grid(
            row=len(champs) + 1,
            column=0,
            columnspan=2,
            sticky="w",
            pady=(5, 10),
        )

        self.bouton_valider = ttk.Button(
            panneau_champs,
            text="Valider les données",
            command=self.valider_formulaire,
            state="disabled",
        )
        self.bouton_valider.grid(
            row=len(champs) + 2,
            column=0,
            columnspan=2,
            sticky="ew",
            pady=(5, 0),
        )

        self.bouton_enregistrer = ttk.Button(
            panneau_champs,
            text="Enregistrer dans l’historique",
            command=self.enregistrer_dans_historique,
            state="disabled",
        )
        self.bouton_enregistrer.grid(
            row=len(champs) + 3,
            column=0,
            columnspan=2,
            sticky="ew",
            pady=(8, 0),
        )

        self.bouton_exporter = ttk.Button(
            panneau_champs,
            text="Exporter le document en CSV",
            command=self.exporter,
            state="disabled",
        )
        self.bouton_exporter.grid(
            row=len(champs) + 4,
            column=0,
            columnspan=2,
            sticky="ew",
            pady=(8, 0),
        )

        self.zone_texte = ScrolledText(
            panneau_texte,
            wrap="word",
            font=("Consolas", 10),
        )
        self.zone_texte.pack(
            fill="both",
            expand=True,
        )
        self.zone_texte.configure(
            state="disabled"
        )

        barre_statut = ttk.Label(
            conteneur,
            textvariable=self.statut,
            relief="sunken",
            anchor="w",
            padding=6,
        )
        barre_statut.pack(
            fill="x",
            pady=(15, 0),
        )

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
        chemin.mkdir(
            parents=True,
            exist_ok=True,
        )
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

        self.nom_document.set(
            self.chemin_document.name
        )

        self.analyser_document_selectionne()

    def selectionner_documents_lot(self) -> None:
        """Sélectionne plusieurs documents et lance le traitement."""
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

        nombre_documents = len(
            self.chemins_lot
        )

        self.nom_document.set(
            f"{nombre_documents} documents sélectionnés"
        )

        self.vider_formulaire()

        self.bouton_valider.configure(
            state="disabled"
        )
        self.bouton_exporter.configure(
            state="disabled"
        )

        chemin_sortie = filedialog.asksaveasfilename(
            title="Enregistrer le CSV regroupé",
            initialdir=str(
                self.dossier_exports()
            ),
            defaultextension=".csv",
            initialfile="factures_lot.csv",
            filetypes=[
                ("Fichier CSV", "*.csv")
            ],
        )

        if not chemin_sortie:
            self.statut.set(
                "Traitement annulé — "
                "aucun fichier CSV sélectionné"
            )
            return

        self.traiter_lot(
            Path(chemin_sortie)
        )

    def traiter_lot(
        self,
        chemin_sortie: Path,
    ) -> None:
        """Analyse, valide et exporte plusieurs documents."""
        self.statut.set(
            f"Traitement local de "
            f"{len(self.chemins_lot)} documents…"
        )
        self.update_idletasks()

        try:
            resultat = traiter_et_exporter_documents(
                self.chemins_lot,
                chemin_sortie,
            )
        except Exception as erreur:
            self.statut.set(
                "Échec du traitement par lot"
            )

            messagebox.showerror(
                "Erreur du traitement par lot",
                str(erreur),
            )
            return

        lignes_resume = [
            "TRAITEMENT PAR LOT TERMINÉ",
            "=" * 55,
            "",
            (
                "Documents sélectionnés : "
                f"{len(self.chemins_lot)}"
            ),
            (
                "Documents exportables : "
                f"{resultat.nombre_documents_reussis}"
            ),
            (
                "Factures valides : "
                f"{resultat.nombre_factures_valides}"
            ),
            (
                "Factures à vérifier : "
                f"{resultat.nombre_factures_a_verifier}"
            ),
            (
                "Documents en erreur : "
                f"{resultat.nombre_documents_en_erreur}"
            ),
            "",
            f"Fichier CSV créé : {chemin_sortie}",
        ]

        if resultat.documents_traites:
            lignes_resume.extend(
                [
                    "",
                    "FACTURES EXTRAITES",
                    "-" * 55,
                ]
            )

            for position, document in enumerate(
                resultat.documents_traites,
                start=1,
            ):
                facture = document.facture
                validation = document.validation

                numero = (
                    facture.numero
                    or "Numéro non détecté"
                )

                total = self.montant_vers_texte(
                    facture.total
                )

                if total:
                    total_affiche = (
                        f"{total} CAD"
                    )
                else:
                    total_affiche = (
                        "Total non détecté"
                    )

                lignes_resume.append(
                    f"{position}. "
                    f"{document.chemin.name}"
                )
                lignes_resume.append(
                    f"   Numéro : {numero}"
                )
                lignes_resume.append(
                    f"   Total : {total_affiche}"
                )
                lignes_resume.append(
                    "   Statut : "
                    f"{validation.statut.value}"
                )

                for avertissement in (
                    validation.avertissements
                ):
                    lignes_resume.append(
                        "   Avertissement : "
                        f"{avertissement}"
                    )

        if resultat.erreurs:
            lignes_resume.extend(
                [
                    "",
                    "DOCUMENTS BLOQUÉS",
                    "-" * 55,
                ]
            )

            for erreur in resultat.erreurs:
                lignes_resume.append(
                    f"- {erreur.chemin.name} : "
                    f"{erreur.message}"
                )

        self.afficher_texte(
            "\n".join(lignes_resume)
        )

        if resultat.nombre_documents_en_erreur:
            couleur = "#92400e"
            resume_validation = (
                "Validation du lot : À VÉRIFIER"
            )

        elif resultat.nombre_factures_a_verifier:
            couleur = "#92400e"
            resume_validation = (
                "Validation du lot : À VÉRIFIER"
            )

        else:
            couleur = "#166534"
            resume_validation = (
                "Validation du lot : VALIDE"
            )

        self.statut_validation.set(
            resume_validation
        )

        self.etiquette_validation.configure(
            foreground=couleur
        )

        self.statut.set(
            "Traitement par lot terminé — "
            f"{resultat.nombre_documents_reussis} "
            "exportable(s), "
            f"{resultat.nombre_documents_en_erreur} "
            "bloqué(s)"
        )

        messagebox.showinfo(
            "Traitement terminé",
            (
                "Le traitement local est terminé.\n\n"
                "Factures valides : "
                f"{resultat.nombre_factures_valides}\n"
                "Factures à vérifier : "
                f"{resultat.nombre_factures_a_verifier}\n"
                "Documents bloqués : "
                f"{resultat.nombre_documents_en_erreur}\n\n"
                f"CSV créé :\n{chemin_sortie}"
            ),
        )

    def analyser_document_selectionne(self) -> None:
        """Analyse le document choisi et remplit le formulaire."""
        if self.chemin_document is None:
            return

        self.statut.set(
            "Analyse locale en cours…"
        )
        self.update_idletasks()

        try:
            texte = extraire_texte_document(
                self.chemin_document
            )

            facture = extraire_donnees_facture(
                texte
            )

        except Exception as erreur:
            self.statut.set(
                "Échec de l'analyse"
            )

            messagebox.showerror(
                "Erreur d'analyse",
                str(erreur),
            )
            return

        self.remplir_formulaire(
            facture
        )

        validation = valider_facture(
            facture
        )

        self.appliquer_validation(
            validation
        )

        rapport = self.formater_validation(
            validation
        )

        self.afficher_texte(
            f"{texte.rstrip()}\n\n{rapport}"
        )

        self.bouton_valider.configure(
            state="normal"
        )

        self.statut.set(
            "Analyse terminée — "
            "vérifiez les champs et la validation"
        )

    def afficher_texte(
        self,
        texte: str,
    ) -> None:
        """Affiche du texte dans la zone en lecture seule."""
        self.zone_texte.configure(
            state="normal"
        )

        self.zone_texte.delete(
            "1.0",
            "end",
        )

        self.zone_texte.insert(
            "1.0",
            texte,
        )

        self.zone_texte.configure(
            state="disabled"
        )

    def vider_formulaire(self) -> None:
        """Efface tous les champs du formulaire."""
        for variable in self.variables.values():
            variable.set("")

        self.statut_validation.set(
            "Validation : aucun document analysé"
        )

        self.etiquette_validation.configure(
            foreground="#475569"
        )

        self.bouton_enregistrer.configure(
            state="disabled"
        )

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
            self.montant_vers_texte(
                facture.sous_total
            )
        )

        self.variables["tps"].set(
            self.montant_vers_texte(
                facture.tps
            )
        )

        self.variables["tvq"].set(
            self.montant_vers_texte(
                facture.tvq
            )
        )

        self.variables["total"].set(
            self.montant_vers_texte(
                facture.total
            )
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
            return Decimal(
                valeur_normalisee
            )

        except InvalidOperation as erreur:
            raise ValueError(
                f"Montant invalide : {valeur}"
            ) from erreur

    def lire_formulaire(
        self,
    ) -> DonneesFacture:
        """Transforme le formulaire en données structurées."""
        return DonneesFacture(
            numero=(
                self.variables["numero"]
                .get()
                .strip()
                or None
            ),
            date=(
                self.variables["date"]
                .get()
                .strip()
                or None
            ),
            fournisseur=(
                self.variables["fournisseur"]
                .get()
                .strip()
                or None
            ),
            client=(
                self.variables["client"]
                .get()
                .strip()
                or None
            ),
            sous_total=self.texte_vers_montant(
                self.variables[
                    "sous_total"
                ].get()
            ),
            tps=self.texte_vers_montant(
                self.variables[
                    "tps"
                ].get()
            ),
            tvq=self.texte_vers_montant(
                self.variables[
                    "tvq"
                ].get()
            ),
            total=self.texte_vers_montant(
                self.variables[
                    "total"
                ].get()
            ),
        )

    def appliquer_validation(
        self,
        validation: ResultatValidation,
    ) -> None:
        """Affiche visuellement le statut de validation."""
        couleurs = {
            StatutValidation.VALIDE: "#166534",
            StatutValidation.A_VERIFIER: "#92400e",
            StatutValidation.ERREUR: "#b91c1c",
        }

        self.statut_validation.set(
            f"Validation : "
            f"{validation.statut.value}"
        )

        self.etiquette_validation.configure(
            foreground=couleurs[
                validation.statut
            ]
        )

        if (
            validation.statut
            == StatutValidation.VALIDE
        ):
            self.bouton_enregistrer.configure(
                state="normal"
            )
        else:
            self.bouton_enregistrer.configure(
                state="disabled"
            )

        if validation.autorise_export:
            self.bouton_exporter.configure(
                state="normal"
            )
        else:
            self.bouton_exporter.configure(
                state="disabled"
            )

    @staticmethod
    def formater_validation(
        validation: ResultatValidation,
    ) -> str:
        """Transforme la validation en texte lisible."""
        lignes = [
            "VALIDATION COMPTABLE",
            "=" * 55,
            (
                f"Statut : "
                f"{validation.statut.value}"
            ),
        ]

        if validation.erreurs:
            lignes.extend(
                [
                    "",
                    "Erreurs :",
                ]
            )

            for erreur in validation.erreurs:
                lignes.append(
                    f"- {erreur}"
                )

        if validation.avertissements:
            lignes.extend(
                [
                    "",
                    "Avertissements :",
                ]
            )

            for avertissement in (
                validation.avertissements
            ):
                lignes.append(
                    f"- {avertissement}"
                )

        if (
            not validation.erreurs
            and not validation.avertissements
        ):
            lignes.extend(
                [
                    "",
                    (
                        "Tous les contrôles "
                        "comptables sont réussis."
                    ),
                ]
            )

        return "\n".join(lignes)

    def valider_formulaire(
        self,
        afficher_message: bool = True,
    ) -> ResultatValidation | None:
        """Valide les valeurs présentes dans le formulaire."""
        try:
            facture = self.lire_formulaire()

        except ValueError as erreur:
            messagebox.showerror(
                "Donnée invalide",
                str(erreur),
            )
            return None

        validation = valider_facture(
            facture
        )

        self.appliquer_validation(
            validation
        )

        rapport = self.formater_validation(
            validation
        )

        self.afficher_texte(
            rapport
        )

        if afficher_message:
            if (
                validation.statut
                == StatutValidation.VALIDE
            ):
                messagebox.showinfo(
                    "Validation réussie",
                    (
                        "La facture est complète "
                        "et cohérente."
                    ),
                )

            elif (
                validation.statut
                == StatutValidation.A_VERIFIER
            ):
                messagebox.showwarning(
                    "Facture à vérifier",
                    "\n".join(
                        validation.avertissements
                    ),
                )

            else:
                messagebox.showerror(
                    "Erreur comptable",
                    "\n".join(
                        validation.erreurs
                    ),
                )

        return validation

    def enregistrer_dans_historique(
        self,
    ) -> None:
        """Valide et enregistre la facture dans SQLite."""
        try:
            facture = self.lire_formulaire()

        except ValueError as erreur:
            messagebox.showerror(
                "Donnée invalide",
                str(erreur),
            )
            return

        validation = valider_facture(
            facture
        )

        self.appliquer_validation(
            validation
        )

        if (
            validation.statut
            != StatutValidation.VALIDE
        ):
            messagebox.showerror(
                "Enregistrement bloqué",
                (
                    "La facture doit être complète "
                    "et valide avant son "
                    "enregistrement."
                ),
            )
            return

        try:
            facture_enregistree = (
                enregistrer_facture(
                    facture
                )
            )

        except ValueError as erreur:
            messagebox.showwarning(
                "Facture déjà enregistrée",
                str(erreur),
            )
            return

        except OSError as erreur:
            messagebox.showerror(
                "Erreur de la base de données",
                str(erreur),
            )
            return

        self.bouton_enregistrer.configure(
            state="disabled"
        )

        self.statut.set(
            "Facture enregistrée dans "
            "l’historique local"
        )

        messagebox.showinfo(
            "Facture enregistrée",
            (
                "La facture a été enregistrée "
                "localement.\n\n"
                "Identifiant : "
                f"{facture_enregistree.identifiant}\n"
                "Numéro : "
                f"{facture_enregistree.numero}\n"
                "Fournisseur : "
                f"{facture_enregistree.fournisseur}"
            ),
        )

    def exporter(self) -> None:
        """Valide et exporte une facture dans un CSV."""
        if self.chemin_document is None:
            return

        validation = self.valider_formulaire(
            afficher_message=False
        )

        if validation is None:
            return

        if (
            validation.statut
            == StatutValidation.ERREUR
        ):
            messagebox.showerror(
                "Export bloqué",
                "\n".join(
                    validation.erreurs
                ),
            )
            return

        if (
            validation.statut
            == StatutValidation.A_VERIFIER
        ):
            continuer = messagebox.askyesno(
                "Confirmation requise",
                (
                    "Certains champs nécessitent "
                    "une vérification :\n\n"
                    + "\n".join(
                        validation.avertissements
                    )
                    + (
                        "\n\nVoulez-vous quand même "
                        "exporter la facture?"
                    )
                ),
            )

            if not continuer:
                return

        nom_initial = (
            f"{self.chemin_document.stem}.csv"
        )

        chemin_sortie = (
            filedialog.asksaveasfilename(
                title=(
                    "Exporter les données en CSV"
                ),
                initialdir=str(
                    self.dossier_exports()
                ),
                defaultextension=".csv",
                initialfile=nom_initial,
                filetypes=[
                    ("Fichier CSV", "*.csv")
                ],
            )
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
            f"Export CSV terminé : "
            f"{chemin.name}"
        )

        messagebox.showinfo(
            "Export terminé",
            (
                "Le fichier CSV a été créé "
                "localement :\n"
                f"{chemin}"
            ),
        )


def lancer_interface() -> None:
    """Lance l'interface graphique locale."""
    application = ApplicationComptaPrivee()
    application.mainloop()


if __name__ == "__main__":
    lancer_interface()