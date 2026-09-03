"""Interface graphique locale de ComptaPrivée AI."""

import tkinter as tk
from decimal import Decimal, InvalidOperation
import os
import subprocess
import sys
from pathlib import Path
from tkinter import colorchooser, filedialog, messagebox, simpledialog, ttk
from tkinter.scrolledtext import ScrolledText

from .anomalies import detecter_anomalies
from .audit_log import (
    journaliser_sans_bloquer,
    lister_evenements,
    rechercher_evenements,
)
from .batch_processor import traiter_et_exporter_documents
from .backup_manager import (
    creer_sauvegarde,
    restaurer_sauvegarde,
)
from .csv_exporter import exporter_facture_csv
from .document_converter import (
    CONVERSIONS_SUPPORTEES,
    ErreurConversion,
    convertir_document,
    images_vers_pdf,
    fusionner_pdfs,
    pdf_vers_images,
)
from .company_profile import (
    ProfilSociete,
    copier_logo_societe,
    enregistrer_profil_societe,
    lire_profil_societe,
)
from .pdf_exporter import exporter_facture_pdf
from .dashboard import (
    calculer_taxes_mensuelles,
    calculer_totaux_mensuels,
    calculer_resume,
    filtrer_factures_fournisseur,
    filtrer_factures_periode,
    preparer_totaux_fournisseurs_graphique,
)
from .dashboard_exporter import (
    exporter_tableau_bord_csv,
    exporter_tableau_bord_pdf,
)
from .database import (
    enregistrer_facture,
    lister_factures,
    lister_factures_corbeille,
    mettre_facture_corbeille,
    restaurer_facture,
    supprimer_facture_corbeille,
)

from .duplicate_detector import (
    NiveauDoublon,
    detecter_doublon,
)
from .facture_parser import DonneesFacture, extraire_donnees_facture
from .summary_report import (
    construire_resume_comptable,
    exporter_resume_comptable_pdf,
)
from .report_naming import nom_fichier_rapport
from .review_queue import (
    NiveauVerification,
    analyser_factures_a_verifier,
)
from .ocr_review_queue import (
    lister_alertes_ocr_a_verifier,
    synchroniser_export_ocr_a_verifier,
)
from .export_history import (
    compter_types,
    exporter_historique_csv,
    filtrer_exports,
    formater_taille,
    lister_exports,
    trier_exports,
)
from .invoice_validator import (
    ResultatValidation,
    StatutValidation,
    valider_facture,
)
from .main import extraire_texte_document
from .tax_validator import appliquer_validation_fiscale
from .settings import (
    DEVISES,
    FORMATS_DATE,
    LANGUES_RAPPORTS,
    ParametresApplication,
    enregistrer_parametres,
    lire_parametres,
    normaliser_couleur_hex,
)


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

        conteneur = ttk.Frame(
            self,
            padding=20,
        )
        conteneur.pack(
            fill="both",
            expand=True,
        )

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
        ).pack(
            anchor="w",
            pady=(2, 0),
        )

        ttk.Label(
            entete,
            text=(
                "🔒 Traitement 100 % local — "
                "aucune donnée envoyée sur Internet"
            ),
            style="Securite.TLabel",
        ).pack(
            anchor="w",
            pady=(8, 15),
        )

        barre_document = ttk.Frame(conteneur)
        barre_document.pack(
            fill="x",
            pady=(0, 15),
        )

        ttk.Button(
            barre_document,
            text="Sélectionner un document",
            command=self.selectionner_document,
        ).pack(side="left")

        ttk.Button(
            barre_document,
            text="Traiter plusieurs documents",
            command=self.selectionner_documents_lot,
        ).pack(
            side="left",
            padx=(10, 0),
        )

        menu_conversion = tk.Menu(
            barre_document,
            tearoff=False,
        )

        for type_conversion in CONVERSIONS_SUPPORTEES:
            menu_conversion.add_command(
                label=type_conversion,
                command=lambda conversion=type_conversion: (
                    self.convertir_depuis_interface(conversion)
                ),
            )

        bouton_conversion = ttk.Menubutton(
            barre_document,
            text="Convertir ▼",
            menu=menu_conversion,
        )
        bouton_conversion.pack(
            side="left",
            padx=(10, 0),
        )

        ttk.Button(
            barre_document,
            text="Consulter l'historique",
            command=self.ouvrir_historique,
        ).pack(
            side="left",
            padx=(10, 0),
        )

        ttk.Button(
            barre_document,
            text="Tableau de bord",
            command=self.ouvrir_tableau_bord,
        ).pack(
            side="left",
            padx=(10, 0),
        )

        ttk.Button(
            barre_document,
            text="Ouvrir le dossier des exports",
            command=self.ouvrir_dossier_exports,
        ).pack(
            side="left",
            padx=(10, 0),
        )

        ttk.Button(
            barre_document,
            text="Historique exports",
            command=self.ouvrir_historique_exports,
        ).pack(
            side="left",
            padx=(10, 0),
        )

        ttk.Button(
            barre_document,
            text="À vérifier",
            command=self.ouvrir_a_verifier,
        ).pack(
            side="left",
            padx=(10, 0),
        )

        ttk.Button(
            barre_document,
            text="Journal d'audit",
            command=self.ouvrir_journal_audit,
        ).pack(
            side="left",
            padx=(10, 0),
        )

        ttk.Button(
            barre_document,
            text="Paramètres",
            command=self.ouvrir_parametres,
        ).pack(
            side="left",
            padx=(10, 0),
        )


        ttk.Label(
            barre_document,
            textvariable=self.nom_document,
        ).pack(
            side="left",
            padx=12,
        )

        zone_principale = ttk.Panedwindow(
            conteneur,
            orient="horizontal",
        )
        zone_principale.pack(
            fill="both",
            expand=True,
        )

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
            text="Enregistrer dans l'historique",
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


    def convertir_images_depuis_interface(self) -> None:
        """Sélectionne autant d'images que nécessaire et crée un seul PDF."""
        chemins: list[Path] = []

        while True:
            sources = filedialog.askopenfilenames(
                parent=self,
                title=(
                    "Choisir une ou plusieurs images "
                    f"(actuellement : {len(chemins)})"
                ),
                filetypes=[
                    (
                        "Images",
                        "*.png *.jpg *.jpeg *.bmp *.tif *.tiff",
                    ),
                    ("Tous les fichiers", "*.*"),
                ],
            )

            if sources:
                for source in sources:
                    chemin = Path(source)

                    if chemin not in chemins:
                        chemins.append(chemin)

            if not chemins:
                return

            ajouter = messagebox.askyesno(
                "Ajouter d'autres images ?",
                (
                    f"{len(chemins)} image(s) sélectionnée(s).\n\n"
                    "Voulez-vous ouvrir de nouveau la fenêtre "
                    "pour ajouter d'autres images ?"
                ),
                parent=self,
            )

            if not ajouter:
                break

        destination = filedialog.asksaveasfilename(
            parent=self,
            title="Enregistrer le PDF regroupé",
            defaultextension=".pdf",
            initialfile=f"{chemins[0].stem}_images.pdf",
            filetypes=[("PDF", "*.pdf")],
        )

        if not destination:
            return

        self.statut.set(
            f"Conversion de {len(chemins)} image(s) en PDF..."
        )
        self.update_idletasks()

        try:
            resultat = images_vers_pdf(
                chemins,
                destination,
            )

        except (ErreurConversion, ValueError, FileNotFoundError) as erreur:
            self.statut.set(
                "Échec de conversion : Images → PDF"
            )
            messagebox.showerror(
                "Conversion impossible",
                str(erreur),
                parent=self,
            )
            return

        except Exception as erreur:
            self.statut.set(
                "Échec de conversion : Images → PDF"
            )
            messagebox.showerror(
                "Conversion impossible",
                f"Erreur inattendue : {erreur}",
                parent=self,
            )
            return

        journaliser_sans_bloquer(
            "Document converti",
            "conversion",
            details=(
                f"Images → PDF | "
                f"{len(chemins)} image(s)"
            ),
            reference=resultat.destination.name,
        )

        self.statut.set(
            f"Conversion terminée : {resultat.destination.name}"
        )

        messagebox.showinfo(
            "Conversion terminée",
            (
                f"{len(chemins)} image(s) ont été regroupées "
                f"dans un seul PDF.\n\n"
                f"Fichier : {resultat.destination}"
            ),
            parent=self,
        )

    def fusionner_pdfs_depuis_interface(self) -> None:
        """Sélectionne plusieurs PDF et les fusionne dans un seul fichier."""
        chemins: list[Path] = []

        while True:
            sources = filedialog.askopenfilenames(
                parent=self,
                title=(
                    "Choisir un ou plusieurs PDF "
                    f"(actuellement : {len(chemins)})"
                ),
                filetypes=[
                    ("Documents PDF", "*.pdf"),
                    ("Tous les fichiers", "*.*"),
                ],
            )

            if sources:
                for source in sources:
                    chemin = Path(source)
                    if chemin not in chemins:
                        chemins.append(chemin)

            if not chemins:
                return

            ajouter = messagebox.askyesno(
                "Ajouter d'autres PDF ?",
                (
                    f"{len(chemins)} PDF sélectionné(s).\n\n"
                    "Voulez-vous ouvrir de nouveau la fenêtre "
                    "pour ajouter d'autres PDF ?"
                ),
                parent=self,
            )

            if not ajouter:
                break

        destination = filedialog.asksaveasfilename(
            parent=self,
            title="Enregistrer le PDF fusionné",
            defaultextension=".pdf",
            initialfile=f"{chemins[0].stem}_fusion.pdf",
            filetypes=[("PDF", "*.pdf")],
        )

        if not destination:
            return

        self.statut.set(
            f"Fusion de {len(chemins)} PDF..."
        )
        self.update_idletasks()

        try:
            resultat = fusionner_pdfs(
                chemins,
                destination,
            )

        except (ErreurConversion, ValueError, FileNotFoundError) as erreur:
            self.statut.set(
                "Échec de conversion : PDFs → PDF"
            )
            messagebox.showerror(
                "Fusion impossible",
                str(erreur),
                parent=self,
            )
            return

        except Exception as erreur:
            self.statut.set(
                "Échec de conversion : PDFs → PDF"
            )
            messagebox.showerror(
                "Fusion impossible",
                f"Erreur inattendue : {erreur}",
                parent=self,
            )
            return

        journaliser_sans_bloquer(
            "Document converti",
            "conversion",
            details=(
                f"PDFs → PDF | "
                f"{len(chemins)} PDF"
            ),
            reference=resultat.destination.name,
        )

        self.statut.set(
            f"Fusion terminée : {resultat.destination.name}"
        )

        messagebox.showinfo(
            "Fusion terminée",
            (
                f"{len(chemins)} PDF ont été fusionnés "
                f"dans un seul fichier.\n\n"
                f"Fichier : {resultat.destination}"
            ),
            parent=self,
        )

    def convertir_pdf_vers_images_depuis_interface(
        self,
        format_image: str,
    ) -> None:
        """Convertit les pages choisies d'un PDF en images PNG ou JPG."""
        source = filedialog.askopenfilename(
            parent=self,
            title="Choisir un PDF à convertir en images",
            filetypes=[
                ("Documents PDF", "*.pdf"),
                ("Tous les fichiers", "*.*"),
            ],
        )

        if not source:
            return

        pages = simpledialog.askstring(
            "Pages à convertir",
            (
                "Quelles pages voulez-vous convertir ?\n\n"
                "Exemples : 1 | 2-5 | 1,3,5 | 1,3-5,8\n"
                "Laissez vide pour convertir toutes les pages."
            ),
            parent=self,
        )

        if pages is None:
            return

        dossier = filedialog.askdirectory(
            parent=self,
            title="Choisir le dossier de destination des images",
        )

        if not dossier:
            return

        dpi = simpledialog.askinteger(
            "Qualité des images",
            (
                "Résolution DPI (72 à 600).\n"
                "150 = qualité standard, 300 = haute qualité."
            ),
            parent=self,
            initialvalue=150,
            minvalue=72,
            maxvalue=600,
        )

        if dpi is None:
            return

        type_conversion = (
            "PDF → Images (PNG)"
            if format_image.lower() == "png"
            else "PDF → Images (JPG)"
        )

        self.statut.set(
            f"Conversion en cours : {type_conversion}"
        )
        self.update_idletasks()

        try:
            sorties = pdf_vers_images(
                source,
                dossier,
                format_image=format_image,
                dpi=dpi,
                pages=pages,
            )

        except (ErreurConversion, ValueError, FileNotFoundError) as erreur:
            self.statut.set(
                f"Échec de conversion : {type_conversion}"
            )
            messagebox.showerror(
                "Conversion impossible",
                str(erreur),
                parent=self,
            )
            return

        except Exception as erreur:
            self.statut.set(
                f"Échec de conversion : {type_conversion}"
            )
            messagebox.showerror(
                "Conversion impossible",
                f"Erreur inattendue : {erreur}",
                parent=self,
            )
            return

        journaliser_sans_bloquer(
            "Document converti",
            "conversion",
            details=(
                f"{type_conversion} | "
                f"{len(sorties)} image(s) | "
                f"{dpi} DPI | "
                f"pages={pages.strip() or 'toutes'}"
            ),
            reference=Path(source).name,
        )

        self.statut.set(
            f"Conversion terminée : {len(sorties)} image(s) créées"
        )

        messagebox.showinfo(
            "Conversion terminée",
            (
                f"{len(sorties)} image(s) ont été créées.\n\n"
                f"Pages : {pages.strip() or 'toutes'}\n"
                f"Dossier : {Path(dossier)}"
            ),
            parent=self,
        )

    def convertir_depuis_interface(
        self,
        type_conversion: str,
    ) -> None:
        """Sélectionne un fichier puis lance une conversion locale."""
        if type_conversion == "Images → PDF":
            self.convertir_images_depuis_interface()
            return

        if type_conversion == "PDFs → PDF":
            self.fusionner_pdfs_depuis_interface()
            return

        if type_conversion == "PDF → Images (PNG)":
            self.convertir_pdf_vers_images_depuis_interface("png")
            return

        if type_conversion == "PDF → Images (JPG)":
            self.convertir_pdf_vers_images_depuis_interface("jpg")
            return

        configurations = {
            "Word → PDF": {
                "types": [("Documents Word", "*.doc *.docx")],
                "extension": ".pdf",
                "type_sortie": ("PDF", "*.pdf"),
            },
            "Excel → PDF": {
                "types": [("Fichiers Excel", "*.xls *.xlsx *.xlsm")],
                "extension": ".pdf",
                "type_sortie": ("PDF", "*.pdf"),
            },
            "Excel → CSV": {
                "types": [("Fichiers Excel", "*.xls *.xlsx *.xlsm")],
                "extension": ".csv",
                "type_sortie": ("CSV", "*.csv"),
            },
            "Image → PDF": {
                "types": [
                    ("Images", "*.png *.jpg *.jpeg *.bmp *.tif *.tiff"),
                ],
                "extension": ".pdf",
                "type_sortie": ("PDF", "*.pdf"),
            },
            "CSV → Excel": {
                "types": [
                    ("Fichiers CSV", "*.csv"),
                ],
                "extension": ".xlsx",
                "type_sortie": ("Excel", "*.xlsx"),
            },
            "PDF → CSV": {
                "types": [
                    ("Documents PDF", "*.pdf"),
                ],
                "extension": ".csv",
                "type_sortie": ("CSV", "*.csv"),
            },
            "PDF → Excel": {
                "types": [
                    ("Documents PDF", "*.pdf"),
                ],
                "extension": ".xlsx",
                "type_sortie": ("Excel", "*.xlsx"),
            },
            "PDF → Word": {
                "types": [
                    ("Documents PDF", "*.pdf"),
                ],
                "extension": ".docx",
                "type_sortie": ("Word", "*.docx"),
            },
        }

        configuration = configurations.get(type_conversion)

        if configuration is None:
            messagebox.showerror(
                "Conversion non prise en charge",
                f"Conversion inconnue : {type_conversion}",
                parent=self,
            )
            return

        source = filedialog.askopenfilename(
            parent=self,
            title=f"Choisir le fichier — {type_conversion}",
            filetypes=[
                *configuration["types"],
                ("Tous les fichiers", "*.*"),
            ],
        )

        if not source:
            return

        source_path = Path(source)
        dossier_exports = self.dossier_exports()
        nom_propose = (
            source_path.stem
            + "_converti"
            + configuration["extension"]
        )

        destination = filedialog.asksaveasfilename(
            parent=self,
            title=f"Enregistrer — {type_conversion}",
            initialdir=dossier_exports,
            initialfile=nom_propose,
            defaultextension=configuration["extension"],
            filetypes=[configuration["type_sortie"]],
        )

        if not destination:
            return

        self.statut.set(
            f"Conversion en cours : {type_conversion}..."
        )
        self.update_idletasks()

        try:
            resultat = convertir_document(
                type_conversion,
                source_path,
                destination,
            )

            if type_conversion in {
                "PDF → CSV",
                "PDF → Excel",
            }:
                try:
                    synchroniser_export_ocr_a_verifier(
                        resultat.source,
                        resultat.destination,
                        type_conversion,
                    )
                except (
                    OSError,
                    ValueError,
                    RuntimeError,
                ) as erreur_file_ocr:
                    messagebox.showwarning(
                        "File À vérifier",
                        (
                            "La conversion a réussi, mais la file "
                            "À vérifier n'a pas pu être synchronisée.\n\n"
                            f"Détail : {erreur_file_ocr}"
                        ),
                        parent=self,
                    )
        except (
            ErreurConversion,
            FileNotFoundError,
            ValueError,
            OSError,
        ) as erreur:
            self.statut.set(
                f"Échec de conversion : {type_conversion}"
            )
            messagebox.showerror(
                "Conversion impossible",
                str(erreur),
                parent=self,
            )
            return

        journaliser_sans_bloquer(
            "Document converti",
            "conversion",
            details=(
                f"{type_conversion}; "
                f"source={resultat.source.name}; "
                f"destination={resultat.destination.name}"
            ),
            reference=resultat.destination.name,
        )

        self.statut.set(
            f"Conversion terminée : {resultat.destination.name}"
        )

        ouvrir = messagebox.askyesno(
            "Conversion terminée",
            (
                f"{type_conversion} terminé avec succès.\n\n"
                f"Fichier créé :\n{resultat.destination}\n\n"
                "Voulez-vous ouvrir le fichier ?"
            ),
            parent=self,
        )

        if ouvrir:
            try:
                os.startfile(resultat.destination)
            except OSError as erreur:
                messagebox.showwarning(
                    "Ouverture impossible",
                    str(erreur),
                    parent=self,
                )

    def ouvrir_journal_audit(self) -> None:
        """Affiche le journal d'audit local."""
        fenetre = tk.Toplevel(self)
        fenetre.title("Journal d'audit — ComptaPrivée AI")
        fenetre.geometry("1000x600")
        fenetre.minsize(850, 500)
        fenetre.transient(self)

        conteneur = ttk.Frame(fenetre, padding=18)
        conteneur.pack(fill="both", expand=True)

        ttk.Label(
            conteneur,
            text="Journal d'audit local",
            font=("Segoe UI", 19, "bold"),
        ).pack(anchor="w")

        ttk.Label(
            conteneur,
            text=(
                "Historique local des actions importantes. "
                "Aucune donnée n'est envoyée sur Internet."
            ),
            foreground="#166534",
        ).pack(anchor="w", pady=(3, 12))

        zone_recherche = ttk.Frame(conteneur)
        zone_recherche.pack(fill="x", pady=(0, 12))

        ttk.Label(
            zone_recherche,
            text="Rechercher :",
        ).pack(side="left")

        variable_recherche = tk.StringVar()

        champ_recherche = ttk.Entry(
            zone_recherche,
            textvariable=variable_recherche,
            width=45,
        )
        champ_recherche.pack(side="left", padx=(8, 8))

        compteur = tk.StringVar(value="")
        ttk.Label(
            zone_recherche,
            textvariable=compteur,
            foreground="#475569",
        ).pack(side="right")

        colonnes = (
            "date",
            "categorie",
            "action",
            "reference",
            "details",
        )

        tableau = ttk.Treeview(
            conteneur,
            columns=colonnes,
            show="headings",
        )

        titres = {
            "date": "Date / heure",
            "categorie": "Catégorie",
            "action": "Action",
            "reference": "Référence",
            "details": "Détails",
        }

        for colonne in colonnes:
            tableau.heading(
                colonne,
                text=titres[colonne],
            )

        tableau.column("date", width=150, anchor="w")
        tableau.column("categorie", width=110, anchor="w")
        tableau.column("action", width=190, anchor="w")
        tableau.column("reference", width=150, anchor="w")
        tableau.column("details", width=320, anchor="w")

        tableau.pack(fill="both", expand=True)

        evenements_par_iid = {}

        def charger() -> None:
            recherche = variable_recherche.get().strip()

            if recherche:
                evenements = rechercher_evenements(recherche)
            else:
                evenements = lister_evenements(limite=500)

            for iid in tableau.get_children():
                tableau.delete(iid)

            evenements_par_iid.clear()

            for index, evenement in enumerate(evenements):
                iid = f"audit-{index}"
                evenements_par_iid[iid] = evenement

                tableau.insert(
                    "",
                    "end",
                    iid=iid,
                    values=(
                        evenement.date_creation,
                        evenement.categorie,
                        evenement.action,
                        evenement.reference or "-",
                        evenement.details or "-",
                    ),
                )

            compteur.set(
                f"{len(evenements)} événement(s) affiché(s)"
            )

        tableau.bind(
            "<<TreeviewSelect>>",
            lambda _event: None,
        )

        zone_boutons = ttk.Frame(conteneur)
        zone_boutons.pack(fill="x", pady=(10, 0))

        ttk.Button(
            zone_boutons,
            text="Actualiser",
            command=charger,
        ).pack(side="left")

        def effacer_recherche() -> None:
            variable_recherche.set("")
            charger()

        ttk.Button(
            zone_boutons,
            text="Effacer recherche",
            command=effacer_recherche,
        ).pack(side="left", padx=(8, 0))

        ttk.Button(
            zone_boutons,
            text="Fermer",
            command=fenetre.destroy,
        ).pack(side="right")

        champ_recherche.bind(
            "<Return>",
            lambda _event: charger(),
        )

        charger()
        champ_recherche.focus_set()

    def ouvrir_a_verifier(self) -> None:
        """Affiche les factures qui nécessitent une vérification humaine."""
        fenetre = tk.Toplevel(self)
        fenetre.title("À vérifier — ComptaPrivée AI")
        fenetre.geometry("1050x620")
        fenetre.minsize(850, 500)
        fenetre.transient(self)

        conteneur = ttk.Frame(fenetre, padding=18)
        conteneur.pack(fill="both", expand=True)

        ttk.Label(
            conteneur,
            text="Factures à vérifier",
            font=("Segoe UI", 19, "bold"),
        ).pack(anchor="w")

        compteur = tk.StringVar(value="")
        ttk.Label(
            conteneur,
            textvariable=compteur,
            foreground="#92400e",
        ).pack(anchor="w", pady=(3, 12))

        colonnes = (
            "niveau",
            "numero",
            "fournisseur",
            "date",
            "total",
            "raisons",
        )

        tableau = ttk.Treeview(
            conteneur,
            columns=colonnes,
            show="headings",
        )

        titres = {
            "niveau": "Priorité",
            "numero": "N° facture",
            "fournisseur": "Fournisseur",
            "date": "Date",
            "total": "Total",
            "raisons": "Motif principal",
        }

        largeurs = {
            "niveau": 95,
            "numero": 125,
            "fournisseur": 210,
            "date": 105,
            "total": 100,
            "raisons": 330,
        }

        for colonne in colonnes:
            tableau.heading(
                colonne,
                text=titres[colonne],
            )
            tableau.column(
                colonne,
                width=largeurs[colonne],
                anchor="w",
            )

        barre = ttk.Scrollbar(
            conteneur,
            orient="vertical",
            command=tableau.yview,
        )
        tableau.configure(yscrollcommand=barre.set)

        tableau.pack(
            side="left",
            fill="both",
            expand=True,
        )
        barre.pack(
            side="left",
            fill="y",
        )

        panneau_droit = ttk.Frame(
            conteneur,
            padding=(15, 0, 0, 0),
        )
        panneau_droit.pack(
            side="right",
            fill="y",
        )

        ttk.Label(
            panneau_droit,
            text="Détails",
            font=("Segoe UI", 11, "bold"),
        ).pack(anchor="w")

        details = ScrolledText(
            panneau_droit,
            width=38,
            height=23,
            wrap="word",
            font=("Segoe UI", 9),
        )
        details.pack(
            fill="both",
            expand=True,
            pady=(6, 10),
        )
        details.configure(state="disabled")

        elements_par_iid = {}

        def actualiser() -> None:
            for iid in tableau.get_children():
                tableau.delete(iid)

            elements = [
                *analyser_factures_a_verifier(
                    lister_factures()
                ),
                *lister_alertes_ocr_a_verifier(),
            ]

            for index, element in enumerate(elements):
                facture = element.facture
                iid = f"verification-{index}"
                elements_par_iid[iid] = element

                priorite = (
                    "ERREUR"
                    if element.niveau is NiveauVerification.ERREUR
                    else "À VÉRIFIER"
                )

                motif = (
                    element.raisons[0]
                    if element.raisons
                    else ""
                )

                tableau.insert(
                    "",
                    "end",
                    iid=iid,
                    values=(
                        priorite,
                        facture.numero or "-",
                        facture.fournisseur or "-",
                        facture.date or "-",
                        (
                            f"{facture.total:.2f}"
                            if facture.total is not None
                            else "-"
                        ),
                        motif,
                    ),
                )

            compteur.set(
                f"{len(elements)} facture(s) nécessitent une vérification."
            )

            details.configure(state="normal")
            details.delete("1.0", "end")
            details.insert(
                "1.0",
                "Sélectionnez une facture pour afficher tous les motifs.",
            )
            details.configure(state="disabled")

        def afficher_details(_event=None) -> None:
            selection = tableau.selection()

            if not selection:
                return

            element = elements_par_iid.get(selection[0])
            if element is None:
                return

            facture = element.facture
            lignes = [
                f"Facture : {facture.numero or '-'}",
                f"Fournisseur : {facture.fournisseur or '-'}",
                f"Date : {facture.date or '-'}",
                (
                    f"Total : {facture.total:.2f}"
                    if facture.total is not None
                    else "Total : -"
                ),
                "",
                "Motifs :",
            ]

            lignes.extend(
                f"• {raison}"
                for raison in element.raisons
            )

            details.configure(state="normal")
            details.delete("1.0", "end")
            details.insert(
                "1.0",
                "\n".join(lignes),
            )
            details.configure(state="disabled")

        tableau.bind(
            "<<TreeviewSelect>>",
            afficher_details,
        )

        zone_boutons = ttk.Frame(panneau_droit)
        zone_boutons.pack(fill="x")

        ttk.Button(
            zone_boutons,
            text="Actualiser",
            command=actualiser,
        ).pack(side="left")

        ttk.Button(
            zone_boutons,
            text="Fermer",
            command=fenetre.destroy,
        ).pack(side="right")

        actualiser()

    def ouvrir_historique_exports(self) -> None:
        """Affiche les fichiers PDF/CSV présents dans data/exports."""
        fenetre = tk.Toplevel(self)
        fenetre.title("Historique des exports — ComptaPrivée AI")
        fenetre.geometry("920x560")
        fenetre.minsize(760, 460)
        fenetre.transient(self)

        conteneur = ttk.Frame(fenetre, padding=18)
        conteneur.pack(fill="both", expand=True)

        ttk.Label(
            conteneur,
            text="Historique des exports",
            font=("Segoe UI", 19, "bold"),
        ).pack(anchor="w")

        ttk.Label(
            conteneur,
            text=(
                "Liste calculée directement à partir du dossier "
                "local data/exports."
            ),
            foreground="#166534",
        ).pack(anchor="w", pady=(3, 14))

        zone_filtres = ttk.LabelFrame(
            conteneur,
            text="Recherche et filtres",
            padding=10,
        )
        zone_filtres.pack(
            fill="x",
            pady=(0, 12),
        )

        recherche_export = tk.StringVar()
        type_export_selectionne = tk.StringVar(
            value="Tous"
        )
        compteur_exports = tk.StringVar(
            value=""
        )

        ttk.Label(
            zone_filtres,
            text="Rechercher :",
        ).grid(
            row=0,
            column=0,
            sticky="w",
        )

        champ_recherche = ttk.Entry(
            zone_filtres,
            textvariable=recherche_export,
            width=38,
        )
        champ_recherche.grid(
            row=0,
            column=1,
            sticky="ew",
            padx=(8, 16),
        )

        ttk.Label(
            zone_filtres,
            text="Type :",
        ).grid(
            row=0,
            column=2,
            sticky="w",
        )

        ttk.Combobox(
            zone_filtres,
            textvariable=type_export_selectionne,
            values=("Tous", "PDF", "CSV"),
            state="readonly",
            width=10,
        ).grid(
            row=0,
            column=3,
            sticky="w",
            padx=(8, 16),
        )

        ttk.Label(
            zone_filtres,
            textvariable=compteur_exports,
            foreground="#475569",
        ).grid(
            row=0,
            column=4,
            sticky="e",
        )

        date_export_debut = tk.StringVar()
        date_export_fin = tk.StringVar()

        ttk.Label(
            zone_filtres,
            text="Du :",
        ).grid(
            row=1,
            column=0,
            sticky="w",
            pady=(10, 0),
        )

        champ_date_debut = ttk.Entry(
            zone_filtres,
            textvariable=date_export_debut,
            width=14,
        )
        champ_date_debut.grid(
            row=1,
            column=1,
            sticky="w",
            padx=(8, 16),
            pady=(10, 0),
        )

        ttk.Label(
            zone_filtres,
            text="Au :",
        ).grid(
            row=1,
            column=2,
            sticky="w",
            pady=(10, 0),
        )

        champ_date_fin = ttk.Entry(
            zone_filtres,
            textvariable=date_export_fin,
            width=14,
        )
        champ_date_fin.grid(
            row=1,
            column=3,
            sticky="w",
            padx=(8, 16),
            pady=(10, 0),
        )

        ttk.Label(
            zone_filtres,
            text="Format : AAAA-MM-JJ",
            foreground="#64748b",
        ).grid(
            row=1,
            column=4,
            sticky="e",
            pady=(10, 0),
        )

        zone_filtres.columnconfigure(
            1,
            weight=1,
        )

        zone_tableau = ttk.Frame(conteneur)
        zone_tableau.pack(fill="both", expand=True)

        colonne_tri_export = tk.StringVar(value="date")
        tri_decroissant_export = tk.BooleanVar(value=True)

        colonnes = ("nom", "type", "date", "taille")
        tableau = ttk.Treeview(
            zone_tableau,
            columns=colonnes,
            show="headings",
            selectmode="browse",
        )

        tableau.heading("nom", text="Fichier")
        tableau.heading("type", text="Type")
        tableau.heading("date", text="Créé / modifié")
        tableau.heading("taille", text="Taille")

        tableau.column("nom", width=480, anchor="w")
        tableau.column("type", width=80, anchor="center")
        tableau.column("date", width=170, anchor="center")
        tableau.column("taille", width=90, anchor="e")

        barre = ttk.Scrollbar(
            zone_tableau,
            orient="vertical",
            command=tableau.yview,
        )
        tableau.configure(yscrollcommand=barre.set)

        tableau.pack(side="left", fill="both", expand=True)
        barre.pack(side="right", fill="y")

        chemins: dict[str, Path] = {}

        def actualiser() -> None:
            for item in tableau.get_children():
                tableau.delete(item)

            chemins.clear()

            tous_exports = lister_exports(
                self.dossier_exports()
            )
            try:
                exports = filtrer_exports(
                    tous_exports,
                    recherche=recherche_export.get(),
                    type_fichier=type_export_selectionne.get(),
                    date_debut=date_export_debut.get(),
                    date_fin=date_export_fin.get(),
                )
            except ValueError as erreur:
                compteur_exports.set(str(erreur))
                return

            exports = trier_exports(
                exports,
                colonne=colonne_tri_export.get(),
                decroissant=tri_decroissant_export.get(),
            )

            compte = compter_types(tous_exports)
            compteur_exports.set(
                (
                    f"{len(exports)} affiché(s) / "
                    f"{compte['Tous']} total "
                    f"— PDF : {compte['PDF']} "
                    f"— CSV : {compte['CSV']}"
                )
            )

            actualiser_entetes_tri()

            for export in exports:
                identifiant = tableau.insert(
                    "",
                    "end",
                    values=(
                        export.nom,
                        export.type_fichier,
                        export.modifie_le.strftime("%Y-%m-%d %H:%M"),
                        formater_taille(export.taille_octets),
                    ),
                )
                chemins[identifiant] = export.chemin

            if not exports:
                message = (
                    "Aucun export correspondant"
                    if tous_exports
                    else "Aucun export local"
                )
                tableau.insert(
                    "",
                    "end",
                    values=(message, "", "", ""),
                )

        def chemin_selectionne() -> Path | None:
            selection = tableau.selection()
            if not selection:
                return None
            return chemins.get(selection[0])

        def ouvrir_selection() -> None:
            chemin = chemin_selectionne()

            if chemin is None:
                messagebox.showinfo(
                    "Historique des exports",
                    "Sélectionnez d'abord un fichier.",
                    parent=fenetre,
                )
                return

            try:
                os.startfile(chemin)
            except OSError as erreur:
                messagebox.showerror(
                    "Ouverture impossible",
                    str(erreur),
                    parent=fenetre,
                )

        def supprimer_selection() -> None:
            chemin = chemin_selectionne()

            if chemin is None:
                messagebox.showinfo(
                    "Historique des exports",
                    "Sélectionnez d'abord un fichier.",
                    parent=fenetre,
                )
                return

            confirmer = messagebox.askyesno(
                "Supprimer l'export",
                (
                    "Supprimer définitivement ce fichier local ?\n\n"
                    f"{chemin.name}"
                ),
                parent=fenetre,
            )

            if not confirmer:
                return

            try:
                chemin.unlink()
            except OSError as erreur:
                messagebox.showerror(
                    "Suppression impossible",
                    str(erreur),
                    parent=fenetre,
                )
                return

            self.statut.set(
                f"Export supprimé : {chemin.name}"
            )
            actualiser()

        def trier_par(colonne: str) -> None:
            if colonne_tri_export.get() == colonne:
                tri_decroissant_export.set(
                    not tri_decroissant_export.get()
                )
            else:
                colonne_tri_export.set(colonne)
                tri_decroissant_export.set(
                    colonne in {"date", "taille"}
                )

            actualiser()

        def titre_colonne(
            colonne: str,
            libelle: str,
        ) -> str:
            if colonne_tri_export.get() != colonne:
                return libelle

            symbole = (
                "▼"
                if tri_decroissant_export.get()
                else "▲"
            )
            return f"{libelle} {symbole}"

        def actualiser_entetes_tri() -> None:
            tableau.heading(
                "nom",
                text=titre_colonne("nom", "Fichier"),
                command=lambda: trier_par("nom"),
            )
            tableau.heading(
                "type",
                text=titre_colonne("type", "Type"),
                command=lambda: trier_par("type"),
            )
            tableau.heading(
                "date",
                text=titre_colonne(
                    "date",
                    "Créé / modifié",
                ),
                command=lambda: trier_par("date"),
            )
            tableau.heading(
                "taille",
                text=titre_colonne("taille", "Taille"),
                command=lambda: trier_par("taille"),
            )

        def obtenir_exports_affiches() -> list:
            tous_exports = lister_exports(
                self.dossier_exports()
            )

            exports = filtrer_exports(
                tous_exports,
                recherche=recherche_export.get(),
                type_fichier=type_export_selectionne.get(),
                date_debut=date_export_debut.get(),
                date_fin=date_export_fin.get(),
            )

            return trier_exports(
                exports,
                colonne=colonne_tri_export.get(),
                decroissant=tri_decroissant_export.get(),
            )

        def exporter_liste_csv() -> None:
            try:
                exports = obtenir_exports_affiches()
            except ValueError as erreur:
                messagebox.showerror(
                    "Historique des exports",
                    str(erreur),
                    parent=fenetre,
                )
                return

            if not exports:
                messagebox.showinfo(
                    "Historique des exports",
                    "Aucun export correspondant à enregistrer.",
                    parent=fenetre,
                )
                return

            chemin = filedialog.asksaveasfilename(
                parent=fenetre,
                title="Exporter l'historique filtré en CSV",
                initialdir=self.dossier_exports(),
                initialfile="historique_exports_filtre.csv",
                defaultextension=".csv",
                filetypes=[("Fichier CSV", "*.csv")],
            )

            if not chemin:
                return

            try:
                destination = exporter_historique_csv(
                    exports,
                    chemin,
                )
            except (OSError, ValueError) as erreur:
                messagebox.showerror(
                    "Export impossible",
                    str(erreur),
                    parent=fenetre,
                )
                return

            self.statut.set(
                f"Historique exporté : {destination.name}"
            )
            messagebox.showinfo(
                "Historique des exports",
                (
                    "Export CSV créé avec succès.\n\n"
                    f"{destination}"
                ),
                parent=fenetre,
            )

        actions = ttk.Frame(conteneur)
        actions.pack(fill="x", pady=(14, 0))

        ttk.Button(
            actions,
            text="Actualiser",
            command=actualiser,
        ).pack(side="left")

        def effacer_filtres() -> None:
            recherche_export.set("")
            type_export_selectionne.set("Tous")
            date_export_debut.set("")
            date_export_fin.set("")
            actualiser()
            champ_recherche.focus_set()

        ttk.Button(
            actions,
            text="Effacer filtres",
            command=effacer_filtres,
        ).pack(
            side="left",
            padx=(8, 0),
        )

        ttk.Button(
            actions,
            text="Ouvrir le fichier",
            command=ouvrir_selection,
        ).pack(side="left", padx=(8, 0))

        ttk.Button(
            actions,
            text="Supprimer",
            command=supprimer_selection,
        ).pack(side="left", padx=(8, 0))

        ttk.Button(
            actions,
            text="Ouvrir le dossier",
            command=self.ouvrir_dossier_exports,
        ).pack(side="left", padx=(8, 0))

        ttk.Button(
            actions,
            text="Exporter la liste en CSV",
            command=exporter_liste_csv,
        ).pack(
            side="left",
            padx=(8, 0),
        )

        ttk.Button(
            actions,
            text="Fermer",
            command=fenetre.destroy,
        ).pack(side="right")

        tableau.bind(
            "<Double-1>",
            lambda _event: ouvrir_selection(),
        )

        recherche_export.trace_add(
            "write",
            lambda *_args: actualiser(),
        )
        type_export_selectionne.trace_add(
            "write",
            lambda *_args: actualiser(),
        )
        date_export_debut.trace_add(
            "write",
            lambda *_args: actualiser(),
        )
        date_export_fin.trace_add(
            "write",
            lambda *_args: actualiser(),
        )

        champ_recherche.bind(
            "<Escape>",
            lambda _event: effacer_filtres(),
        )

        actualiser()
        champ_recherche.focus_set()

    def ouvrir_parametres(self) -> None:
        """Ouvre les paramètres locaux de l'application."""
        parametres = lire_parametres()
        profil = lire_profil_societe()

        fenetre = tk.Toplevel(self)
        fenetre.title("Paramètres — ComptaPrivée AI")
        fenetre.geometry("720x560")
        fenetre.minsize(650, 520)
        fenetre.transient(self)
        fenetre.grab_set()

        conteneur = ttk.Frame(
            fenetre,
            padding=20,
        )
        conteneur.pack(
            fill="both",
            expand=True,
        )

        ttk.Label(
            conteneur,
            text="Paramètres",
            font=("Segoe UI", 20, "bold"),
        ).pack(
            anchor="w",
            pady=(0, 4),
        )

        ttk.Label(
            conteneur,
            text=(
                "Toutes les préférences sont conservées "
                "uniquement sur cet ordinateur."
            ),
            foreground="#166534",
        ).pack(
            anchor="w",
            pady=(0, 15),
        )

        onglets = ttk.Notebook(conteneur)
        onglets.pack(
            fill="both",
            expand=True,
        )

        onglet_rapports = ttk.Frame(
            onglets,
            padding=20,
        )
        onglet_cabinet = ttk.Frame(
            onglets,
            padding=20,
        )

        onglets.add(
            onglet_rapports,
            text="Rapports",
        )
        onglets.add(
            onglet_cabinet,
            text="Cabinet",
        )


        onglet_sauvegarde = ttk.Frame(
            onglets,
            padding=20,
        )

        onglets.add(
            onglet_sauvegarde,
            text="Sauvegarde",
        )

        ttk.Label(
            onglet_sauvegarde,
            text="Sauvegarde et restauration locales",
            font=("Segoe UI", 12, "bold"),
        ).pack(anchor="w")

        ttk.Label(
            onglet_sauvegarde,
            text=(
                "Créez une copie locale de la base SQLite, "
                "des paramètres et du profil du cabinet."
            ),
            foreground="#166534",
            wraplength=560,
        ).pack(
            anchor="w",
            pady=(6, 18),
        )

        def creer_sauvegarde_depuis_interface() -> None:
            chemin = filedialog.asksaveasfilename(
                parent=fenetre,
                title="Créer une sauvegarde ComptaPrivée AI",
                initialfile="ComptaPrivee_sauvegarde.zip",
                defaultextension=".zip",
                filetypes=[
                    ("Sauvegarde ZIP", "*.zip"),
                ],
            )

            if not chemin:
                return

            try:
                destination = creer_sauvegarde(chemin)
            except (OSError, ValueError) as erreur:
                messagebox.showerror(
                    "Sauvegarde impossible",
                    str(erreur),
                    parent=fenetre,
                )
                return

            self.statut.set(
                f"Sauvegarde créée : {destination.name}"
            )
            messagebox.showinfo(
                "Sauvegarde créée",
                (
                    "La sauvegarde locale a été créée avec succès.\n\n"
                    f"{destination}"
                ),
                parent=fenetre,
            )

        def restaurer_sauvegarde_depuis_interface() -> None:
            chemin = filedialog.askopenfilename(
                parent=fenetre,
                title="Choisir une sauvegarde ComptaPrivée AI",
                filetypes=[
                    ("Sauvegarde ZIP", "*.zip"),
                ],
            )

            if not chemin:
                return

            confirmer = messagebox.askyesno(
                "Restaurer la sauvegarde",
                (
                    "La restauration remplacera les données locales "
                    "présentes par celles de la sauvegarde sélectionnée.\n\n"
                    "Voulez-vous continuer ?"
                ),
                parent=fenetre,
            )

            if not confirmer:
                return

            try:
                fichiers = restaurer_sauvegarde(
                    chemin,
                    racine=Path.cwd(),
                )
            except (OSError, ValueError, FileNotFoundError) as erreur:
                messagebox.showerror(
                    "Restauration impossible",
                    str(erreur),
                    parent=fenetre,
                )
                return

            self.statut.set(
                "Sauvegarde restaurée — redémarrage recommandé"
            )
            messagebox.showinfo(
                "Restauration terminée",
                (
                    f"{len(fichiers)} fichier(s) restauré(s).\n\n"
                    "Fermez puis relancez ComptaPrivée AI afin "
                    "de recharger toutes les données restaurées."
                ),
                parent=fenetre,
            )

        cadre_sauvegarde = ttk.LabelFrame(
            onglet_sauvegarde,
            text="Créer une sauvegarde",
            padding=16,
        )
        cadre_sauvegarde.pack(
            fill="x",
            pady=(0, 14),
        )

        ttk.Label(
            cadre_sauvegarde,
            text=(
                "Enregistre les données essentielles dans "
                "une archive ZIP locale."
            ),
            wraplength=520,
        ).pack(anchor="w")

        ttk.Button(
            cadre_sauvegarde,
            text="Créer une sauvegarde...",
            command=creer_sauvegarde_depuis_interface,
        ).pack(
            anchor="w",
            pady=(12, 0),
        )

        cadre_restauration = ttk.LabelFrame(
            onglet_sauvegarde,
            text="Restaurer une sauvegarde",
            padding=16,
        )
        cadre_restauration.pack(fill="x")

        ttk.Label(
            cadre_restauration,
            text=(
                "Restaure une archive créée par ComptaPrivée AI. "
                "Une confirmation est demandée avant le remplacement."
            ),
            wraplength=520,
        ).pack(anchor="w")

        ttk.Button(
            cadre_restauration,
            text="Restaurer une sauvegarde...",
            command=restaurer_sauvegarde_depuis_interface,
        ).pack(
            anchor="w",
            pady=(12, 0),
        )

        devise = tk.StringVar(
            value=parametres.devise
        )
        langue = tk.StringVar(
            value=parametres.langue_rapports
        )
        format_date = tk.StringVar(
            value=parametres.format_date
        )
        couleur_pdf = tk.StringVar(
            value=parametres.couleur_pdf
        )

        champs_rapports = [
            ("Devise", devise, DEVISES),
            (
                "Langue des rapports",
                langue,
                LANGUES_RAPPORTS,
            ),
            (
                "Format de date",
                format_date,
                FORMATS_DATE,
            ),
        ]

        for ligne, (
            libelle,
            variable,
            valeurs,
        ) in enumerate(champs_rapports):
            ttk.Label(
                onglet_rapports,
                text=libelle,
            ).grid(
                row=ligne,
                column=0,
                sticky="w",
                pady=10,
            )

            ttk.Combobox(
                onglet_rapports,
                textvariable=variable,
                values=valeurs,
                state="readonly",
                width=24,
            ).grid(
                row=ligne,
                column=1,
                sticky="w",
                padx=(20, 0),
                pady=10,
            )

        ttk.Label(
            onglet_rapports,
            text="Couleur principale PDF",
        ).grid(
            row=3,
            column=0,
            sticky="w",
            pady=10,
        )

        zone_couleur = ttk.Frame(
            onglet_rapports,
        )
        zone_couleur.grid(
            row=3,
            column=1,
            sticky="w",
            padx=(20, 0),
            pady=10,
        )

        ttk.Entry(
            zone_couleur,
            textvariable=couleur_pdf,
            width=16,
        ).pack(
            side="left",
        )

        def choisir_couleur_pdf() -> None:
            couleur_actuelle = couleur_pdf.get().strip()

            try:
                couleur_actuelle = normaliser_couleur_hex(
                    couleur_actuelle
                )
            except ValueError:
                couleur_actuelle = "#1A408C"

            resultat = colorchooser.askcolor(
                color=couleur_actuelle,
                title="Choisir la couleur principale du PDF",
                parent=fenetre,
            )

            couleur_hex = resultat[1]

            if couleur_hex:
                couleur_pdf.set(couleur_hex.upper())

        ttk.Button(
            zone_couleur,
            text="Choisir une couleur...",
            command=choisir_couleur_pdf,
        ).pack(
            side="left",
            padx=(8, 0),
        )

        ttk.Label(
            onglet_rapports,
            text="Vous pouvez aussi saisir une couleur au format #RRGGBB.",
            foreground="#64748b",
        ).grid(
            row=4,
            column=1,
            sticky="w",
            padx=(20, 0),
        )

        apercu_couleur_pdf = tk.Canvas(
            onglet_rapports,
            width=170,
            height=38,
            highlightthickness=1,
            highlightbackground="#cbd5e1",
        )
        apercu_couleur_pdf.grid(
            row=5,
            column=1,
            sticky="w",
            padx=(20, 0),
            pady=(10, 0),
        )

        def actualiser_apercu_couleur(*_args) -> None:
            couleur = couleur_pdf.get().strip()
            try:
                couleur = normaliser_couleur_hex(couleur)
            except ValueError:
                couleur = "#E5E7EB"
            apercu_couleur_pdf.configure(background=couleur)

        couleur_pdf.trace_add(
            "write",
            actualiser_apercu_couleur,
        )
        actualiser_apercu_couleur()

        nom_cabinet = (
            profil.nom_societe
            or "Aucun cabinet configuré"
        )

        ttk.Label(
            onglet_cabinet,
            text="Profil du cabinet",
            font=("Segoe UI", 12, "bold"),
        ).pack(
            anchor="w",
            pady=(0, 10),
        )

        ttk.Label(
            onglet_cabinet,
            text=nom_cabinet,
            font=("Segoe UI", 11),
        ).pack(
            anchor="w",
            pady=(0, 5),
        )

        details = [
            profil.adresse,
            ", ".join(
                valeur
                for valeur in (
                    profil.ville,
                    profil.province,
                    profil.code_postal,
                )
                if valeur
            ),
            profil.telephone,
            profil.courriel,
            profil.site_web,
        ]

        for detail in details:
            if detail:
                ttk.Label(
                    onglet_cabinet,
                    text=detail,
                ).pack(
                    anchor="w",
                    pady=2,
                )

        ttk.Button(
            onglet_cabinet,
            text="Modifier le profil du cabinet",
            command=self.configurer_societe_comptable,
        ).pack(
            anchor="w",
            pady=(20, 0),
        )

        ttk.Label(
            onglet_cabinet,
            text=(
                "Le profil, les coordonnées et le logo "
                "restent enregistrés localement."
            ),
            foreground="#166534",
        ).pack(
            anchor="w",
            pady=(15, 0),
        )

        def enregistrer() -> None:
            nouveaux = ParametresApplication(
                devise=devise.get(),
                langue_rapports=langue.get(),
                format_date=format_date.get(),
                couleur_pdf=couleur_pdf.get(),
            )

            try:
                enregistrer_parametres(
                    nouveaux
                )
            except (OSError, ValueError) as erreur:
                messagebox.showerror(
                    "Erreur des paramètres",
                    str(erreur),
                    parent=fenetre,
                )
                return

            self.statut.set(
                "Paramètres enregistrés localement"
            )

            messagebox.showinfo(
                "Paramètres enregistrés",
                (
                    "Les préférences ont été "
                    "enregistrées localement."
                ),
                parent=fenetre,
            )

            fenetre.destroy()

        barre_actions = ttk.Frame(conteneur)
        barre_actions.pack(
            fill="x",
            pady=(18, 0),
        )

        ttk.Button(
            barre_actions,
            text="Annuler",
            command=fenetre.destroy,
        ).pack(
            side="right",
        )

        ttk.Button(
            barre_actions,
            text="Enregistrer",
            command=enregistrer,
        ).pack(
            side="right",
            padx=(0, 8),
        )

    def configurer_societe_comptable(self) -> None:
        """Configure le profil local du cabinet comptable."""
        profil = lire_profil_societe()

        fenetre = tk.Toplevel(self)
        fenetre.title(
            "Profil de la société — ComptaPrivée AI"
        )
        fenetre.geometry("680x720")
        fenetre.minsize(620, 680)
        fenetre.transient(self)
        fenetre.grab_set()

        cadre = ttk.Frame(
            fenetre,
            padding=20,
        )
        cadre.pack(
            fill="both",
            expand=True,
        )

        ttk.Label(
            cadre,
            text="Profil de la société",
            font=("Segoe UI", 18, "bold"),
        ).grid(
            row=0,
            column=0,
            columnspan=2,
            sticky="w",
            pady=(0, 5),
        )

        ttk.Label(
            cadre,
            text=(
                "Ces informations restent locales et seront "
                "ajoutées automatiquement aux rapports."
            ),
            foreground="#166534",
        ).grid(
            row=1,
            column=0,
            columnspan=2,
            sticky="w",
            pady=(0, 15),
        )

        champs = [
            ("Nom de la société *", "nom_societe"),
            ("Adresse", "adresse"),
            ("Ville", "ville"),
            ("Province", "province"),
            ("Code postal", "code_postal"),
            ("Téléphone", "telephone"),
            ("Courriel", "courriel"),
            ("Site Web", "site_web"),
            ("NEQ", "neq"),
            ("N° TPS", "numero_tps"),
            ("N° TVQ", "numero_tvq"),
        ]

        valeurs = {
            cle: tk.StringVar(
                value=getattr(profil, cle)
            )
            for _, cle in champs
        }

        for ligne, (libelle, cle) in enumerate(
            champs,
            start=2,
        ):
            ttk.Label(
                cadre,
                text=libelle,
            ).grid(
                row=ligne,
                column=0,
                sticky="w",
                pady=6,
            )

            ttk.Entry(
                cadre,
                textvariable=valeurs[cle],
                width=42,
            ).grid(
                row=ligne,
                column=1,
                sticky="ew",
                padx=(15, 0),
                pady=6,
            )

        cadre.columnconfigure(
            1,
            weight=1,
        )

        logo_selectionne = tk.StringVar(
            value=profil.logo_path
        )

        ligne_logo = len(champs) + 2

        ttk.Label(
            cadre,
            text="Logo du cabinet",
        ).grid(
            row=ligne_logo,
            column=0,
            sticky="w",
            pady=6,
        )

        zone_logo = ttk.Frame(cadre)
        zone_logo.grid(
            row=ligne_logo,
            column=1,
            sticky="ew",
            padx=(15, 0),
            pady=(10, 14),
        )
        zone_logo.columnconfigure(0, weight=1)

        ttk.Entry(
            zone_logo,
            textvariable=logo_selectionne,
            state="readonly",
            width=34,
        ).grid(
            row=0,
            column=0,
            sticky="ew",
            padx=(0, 8),
        )

        def choisir_logo() -> None:
            chemin = filedialog.askopenfilename(
                title="Choisir le logo du cabinet",
                filetypes=[
                    ("Images", "*.png *.jpg *.jpeg"),
                    ("PNG", "*.png"),
                    ("JPEG", "*.jpg *.jpeg"),
                ],
                parent=fenetre,
            )
            if chemin:
                logo_selectionne.set(chemin)

        def retirer_logo() -> None:
            logo_selectionne.set("")

        boutons_logo = ttk.Frame(zone_logo)
        boutons_logo.grid(
            row=1,
            column=0,
            columnspan=3,
            sticky="w",
            pady=(8, 0),
        )

        ttk.Button(
            boutons_logo,
            text="Choisir un logo...",
            command=choisir_logo,
        ).pack(
            side="left",
        )

        ttk.Button(
            boutons_logo,
            text="Retirer le logo",
            command=retirer_logo,
        ).pack(
            side="left",
            padx=(8, 0),
        )

        def enregistrer() -> None:
            logo_final = logo_selectionne.get().strip()

            if logo_final and logo_final != profil.logo_path:
                try:
                    logo_final = str(copier_logo_societe(logo_final))
                except (OSError, ValueError) as erreur:
                    messagebox.showerror(
                        "Erreur du logo",
                        str(erreur),
                        parent=fenetre,
                    )
                    return

            nouveau = ProfilSociete(
                nom_societe=valeurs[
                    "nom_societe"
                ].get().strip(),
                adresse=valeurs[
                    "adresse"
                ].get().strip(),
                ville=valeurs[
                    "ville"
                ].get().strip(),
                province=valeurs[
                    "province"
                ].get().strip(),
                code_postal=valeurs[
                    "code_postal"
                ].get().strip(),
                telephone=valeurs[
                    "telephone"
                ].get().strip(),
                courriel=valeurs[
                    "courriel"
                ].get().strip(),
                site_web=valeurs[
                    "site_web"
                ].get().strip(),
                logo_path=logo_final,
                neq=valeurs[
                    "neq"
                ].get().strip(),
                numero_tps=valeurs[
                    "numero_tps"
                ].get().strip(),
                numero_tvq=valeurs[
                    "numero_tvq"
                ].get().strip(),
            )

            try:
                enregistrer_profil_societe(
                    nouveau
                )
            except (OSError, ValueError) as erreur:
                messagebox.showerror(
                    "Erreur de configuration",
                    str(erreur),
                    parent=fenetre,
                )
                return

            self.statut.set(
                "Profil société enregistré localement"
            )

            messagebox.showinfo(
                "Profil enregistré",
                (
                    "Les coordonnées de la société ont "
                    "été enregistrées localement."
                ),
                parent=fenetre,
            )

            fenetre.destroy()

        boutons = ttk.Frame(cadre)
        boutons.grid(
            row=len(champs) + 2,
            column=0,
            columnspan=2,
            sticky="e",
            pady=(20, 0),
        )

        ttk.Button(
            boutons,
            text="Annuler",
            command=fenetre.destroy,
        ).pack(
            side="right",
        )

        ttk.Button(
            boutons,
            text="Enregistrer",
            command=enregistrer,
        ).pack(
            side="right",
            padx=(0, 8),
        )

    def ouvrir_tableau_bord(self) -> None:
        """Ouvre un tableau de bord comptable local avec filtres."""
        try:
            factures = lister_factures()
        except Exception as erreur:
            messagebox.showerror(
                "Erreur du tableau de bord",
                str(erreur),
            )
            return

        fenetre = tk.Toplevel(self)
        fenetre.title("Tableau de bord — ComptaPrivée AI")
        fenetre.geometry("1050x720")
        fenetre.minsize(860, 600)

        conteneur = ttk.Frame(
            fenetre,
            padding=20,
        )
        conteneur.pack(
            fill="both",
            expand=True,
        )

        ttk.Label(
            conteneur,
            text="Tableau de bord comptable",
            font=("Segoe UI", 20, "bold"),
        ).pack(
            anchor="w",
            pady=(0, 5),
        )

        ttk.Label(
            conteneur,
            text=(
                "Indicateurs calculés uniquement à partir "
                "de l'historique SQLite local."
            ),
            foreground="#166534",
        ).pack(
            anchor="w",
            pady=(0, 15),
        )

        zone_filtres = ttk.LabelFrame(
            conteneur,
            text="Filtres",
            padding=10,
        )
        zone_filtres.pack(
            fill="x",
            pady=(0, 15),
        )

        date_debut = tk.StringVar()
        date_fin = tk.StringVar()
        fournisseur_selectionne = tk.StringVar(
            value="Tous les fournisseurs"
        )

        ttk.Label(
            zone_filtres,
            text="Du :",
        ).pack(side="left")

        ttk.Entry(
            zone_filtres,
            textvariable=date_debut,
            width=12,
        ).pack(
            side="left",
            padx=(6, 10),
        )

        ttk.Label(
            zone_filtres,
            text="Au :",
        ).pack(side="left")

        ttk.Entry(
            zone_filtres,
            textvariable=date_fin,
            width=12,
        ).pack(
            side="left",
            padx=(6, 10),
        )

        ttk.Label(
            zone_filtres,
            text="Fournisseur :",
        ).pack(
            side="left",
            padx=(5, 0),
        )

        fournisseurs = sorted(
            {
                facture.fournisseur.strip()
                for facture in factures
                if facture.fournisseur
                and facture.fournisseur.strip()
            },
            key=str.casefold,
        )

        liste_fournisseurs = [
            "Tous les fournisseurs",
            *fournisseurs,
        ]

        ttk.Combobox(
            zone_filtres,
            textvariable=fournisseur_selectionne,
            values=liste_fournisseurs,
            state="readonly",
            width=28,
        ).pack(
            side="left",
            padx=(6, 10),
        )

        ttk.Label(
            zone_filtres,
            text="Dates : AAAA-MM-JJ",
            foreground="#475569",
        ).pack(
            side="left",
            padx=(0, 10),
        )

        cartes = ttk.Frame(conteneur)
        cartes.pack(
            fill="x",
            pady=(0, 20),
        )

        variables_indicateurs = {
            "Factures": tk.StringVar(),
            "Sous-total": tk.StringVar(),
            "TPS": tk.StringVar(),
            "TVQ": tk.StringVar(),
            "Total": tk.StringVar(),
        }

        for colonne, (titre, variable) in enumerate(
            variables_indicateurs.items()
        ):
            cadre = ttk.LabelFrame(
                cartes,
                text=titre,
                padding=12,
            )
            cadre.grid(
                row=0,
                column=colonne,
                sticky="nsew",
                padx=(0, 8),
            )

            ttk.Label(
                cadre,
                textvariable=variable,
                font=("Segoe UI", 13, "bold"),
            ).pack()

            cartes.columnconfigure(
                colonne,
                weight=1,
            )

        cadre_fournisseurs = ttk.LabelFrame(
            conteneur,
            text="Totaux par fournisseur",
            padding=10,
        )
        cadre_fournisseurs.pack(
            fill="both",
            expand=True,
        )

        tableau = ttk.Treeview(
            cadre_fournisseurs,
            columns=("fournisseur", "total"),
            show="headings",
        )
        tableau.heading(
            "fournisseur",
            text="Fournisseur",
        )
        tableau.heading(
            "total",
            text="Total",
        )
        tableau.column(
            "fournisseur",
            width=600,
        )
        tableau.column(
            "total",
            width=170,
            anchor="e",
        )
        tableau.pack(
            fill="both",
            expand=True,
        )

        resume_courant = {"resume": None}

        def obtenir_selection():
            selection = filtrer_factures_periode(
                factures,
                date_debut.get().strip() or None,
                date_fin.get().strip() or None,
            )

            fournisseur = fournisseur_selectionne.get().strip()

            if fournisseur == "Tous les fournisseurs":
                fournisseur = None

            selection = filtrer_factures_fournisseur(
                selection,
                fournisseur,
            )

            return selection, fournisseur

        def actualiser_tableau_bord() -> None:
            try:
                selection, _ = obtenir_selection()
                resume = calculer_resume(selection)
            except ValueError as erreur:
                messagebox.showerror(
                    "Filtre invalide",
                    (
                        "Utilisez le format AAAA-MM-JJ "
                        "pour les dates.\n\n"
                        f"{erreur}"
                    ),
                    parent=fenetre,
                )
                return

            resume_courant["resume"] = resume

            variables_indicateurs[
                "Factures"
            ].set(str(resume.nombre_factures))
            variables_indicateurs[
                "Sous-total"
            ].set(f"{resume.sous_total:.2f} CAD")
            variables_indicateurs[
                "TPS"
            ].set(f"{resume.tps:.2f} CAD")
            variables_indicateurs[
                "TVQ"
            ].set(f"{resume.tvq:.2f} CAD")
            variables_indicateurs[
                "Total"
            ].set(f"{resume.total:.2f} CAD")

            for element in tableau.get_children():
                tableau.delete(element)

            for nom_fournisseur, total in (
                resume.total_par_fournisseur
            ):
                tableau.insert(
                    "",
                    "end",
                    values=(
                        nom_fournisseur,
                        f"{total:.2f} CAD",
                    ),
                )

            if not resume.total_par_fournisseur:
                tableau.insert(
                    "",
                    "end",
                    values=(
                        "Aucune facture pour ces filtres",
                        "0.00 CAD",
                    ),
                )

            self.statut.set(
                "Tableau de bord comptable actualisé"
            )

        def effacer_filtres() -> None:
            date_debut.set("")
            date_fin.set("")
            fournisseur_selectionne.set(
                "Tous les fournisseurs"
            )
            actualiser_tableau_bord()

        def exporter_dashboard_csv() -> None:
            try:
                _, fournisseur = obtenir_selection()
                resume = resume_courant["resume"]
                if resume is None:
                    actualiser_tableau_bord()
                    resume = resume_courant["resume"]
                if resume is None:
                    return
            except ValueError as erreur:
                messagebox.showerror(
                    "Filtre invalide",
                    str(erreur),
                    parent=fenetre,
                )
                return

            chemin = filedialog.asksaveasfilename(
                title="Exporter le tableau de bord en CSV",
                initialdir=str(self.dossier_exports()),
                defaultextension=".csv",
                initialfile=nom_fichier_rapport(
                    lire_profil_societe().nom_societe,
                    "Tableau_de_bord",
                    "csv",
                    date_debut=date_debut.get().strip() or None,
                    date_fin=date_fin.get().strip() or None,
                ),
                filetypes=[("Fichier CSV", "*.csv")],
                parent=fenetre,
            )

            if not chemin:
                return

            try:
                sortie = exporter_tableau_bord_csv(
                    resume,
                    chemin,
                    date_debut=date_debut.get().strip() or None,
                    date_fin=date_fin.get().strip() or None,
                    fournisseur=fournisseur,
                )
            except (OSError, ValueError) as erreur:
                messagebox.showerror(
                    "Erreur d'export CSV",
                    str(erreur),
                    parent=fenetre,
                )
                return

            self.statut.set(
                f"Tableau de bord exporté : {sortie.name}"
            )
            messagebox.showinfo(
                "Export CSV terminé",
                f"Rapport créé localement :\n{sortie}",
                parent=fenetre,
            )

        def exporter_dashboard_pdf() -> None:
            try:
                _, fournisseur = obtenir_selection()
                resume = resume_courant["resume"]
                if resume is None:
                    actualiser_tableau_bord()
                    resume = resume_courant["resume"]
                if resume is None:
                    return
            except ValueError as erreur:
                messagebox.showerror(
                    "Filtre invalide",
                    str(erreur),
                    parent=fenetre,
                )
                return

            chemin = filedialog.asksaveasfilename(
                title="Exporter le tableau de bord en PDF",
                initialdir=str(self.dossier_exports()),
                defaultextension=".pdf",
                initialfile=nom_fichier_rapport(
                    lire_profil_societe().nom_societe,
                    "Tableau_de_bord",
                    "pdf",
                    date_debut=date_debut.get().strip() or None,
                    date_fin=date_fin.get().strip() or None,
                ),
                filetypes=[("Fichier PDF", "*.pdf")],
                parent=fenetre,
            )

            if not chemin:
                return

            try:
                sortie = exporter_tableau_bord_pdf(
                    resume,
                    chemin,
                    date_debut=date_debut.get().strip() or None,
                    date_fin=date_fin.get().strip() or None,
                    fournisseur=fournisseur,
                )
            except (OSError, ValueError) as erreur:
                messagebox.showerror(
                    "Erreur d'export PDF",
                    str(erreur),
                    parent=fenetre,
                )
                return

            self.statut.set(
                f"Tableau de bord exporté : {sortie.name}"
            )
            messagebox.showinfo(
                "Export PDF terminé",
                f"Rapport créé localement :\n{sortie}",
                parent=fenetre,
            )

        def afficher_graphique_fournisseurs() -> None:
            resume = resume_courant["resume"]

            if resume is None:
                actualiser_tableau_bord()
                resume = resume_courant["resume"]

            if resume is None:
                return

            donnees = preparer_totaux_fournisseurs_graphique(
                resume,
                limite=8,
            )

            if not donnees:
                messagebox.showinfo(
                    "Graphique",
                    "Aucune donnée à afficher pour ces filtres.",
                    parent=fenetre,
                )
                return

            graphique = tk.Toplevel(fenetre)
            graphique.title(
                "Graphique fournisseurs — ComptaPrivée AI"
            )
            graphique.geometry("900x560")
            graphique.minsize(700, 450)

            cadre = ttk.Frame(
                graphique,
                padding=20,
            )
            cadre.pack(
                fill="both",
                expand=True,
            )

            ttk.Label(
                cadre,
                text="Total par fournisseur",
                font=("Segoe UI", 18, "bold"),
            ).pack(
                anchor="w",
                pady=(0, 5),
            )

            ttk.Label(
                cadre,
                text=(
                    "Graphique calculé à partir des filtres "
                    "actuellement appliqués."
                ),
                foreground="#166534",
            ).pack(
                anchor="w",
                pady=(0, 15),
            )

            toile = tk.Canvas(
                cadre,
                background="white",
                highlightthickness=1,
                highlightbackground="#cbd5e1",
            )
            toile.pack(
                fill="both",
                expand=True,
            )

            def dessiner(_event=None) -> None:
                toile.delete("all")

                largeur = max(toile.winfo_width(), 650)
                hauteur = max(toile.winfo_height(), 330)

                marge_gauche = 220
                marge_droite = 110
                marge_haut = 35
                marge_bas = 35

                largeur_graphique = max(
                    largeur - marge_gauche - marge_droite,
                    100,
                )
                hauteur_graphique = max(
                    hauteur - marge_haut - marge_bas,
                    100,
                )

                maximum = max(
                    float(total)
                    for _, total in donnees
                )

                if maximum <= 0:
                    maximum = 1.0

                nombre = len(donnees)
                espace = hauteur_graphique / nombre
                hauteur_barre = min(34, espace * 0.6)

                for index, (nom, total) in enumerate(donnees):
                    centre_y = (
                        marge_haut
                        + espace * index
                        + espace / 2
                    )
                    y1 = centre_y - hauteur_barre / 2
                    y2 = centre_y + hauteur_barre / 2

                    ratio = float(total) / maximum
                    x1 = marge_gauche
                    x2 = (
                        marge_gauche
                        + largeur_graphique * ratio
                    )

                    nom_affiche = nom
                    if len(nom_affiche) > 28:
                        nom_affiche = (
                            nom_affiche[:25] + "..."
                        )

                    toile.create_text(
                        marge_gauche - 12,
                        centre_y,
                        text=nom_affiche,
                        anchor="e",
                        font=("Segoe UI", 10),
                    )

                    toile.create_rectangle(
                        x1,
                        y1,
                        x2,
                        y2,
                        fill="#2563eb",
                        outline="#1d4ed8",
                    )

                    toile.create_text(
                        min(x2 + 10, largeur - 10),
                        centre_y,
                        text=f"{total:.2f} CAD",
                        anchor="w",
                        font=("Segoe UI", 10, "bold"),
                    )

                toile.create_line(
                    marge_gauche,
                    marge_haut,
                    marge_gauche,
                    hauteur - marge_bas,
                    fill="#64748b",
                )

            toile.bind(
                "<Configure>",
                dessiner,
            )

            ttk.Button(
                cadre,
                text="Fermer",
                command=graphique.destroy,
            ).pack(
                anchor="e",
                pady=(12, 0),
            )

            graphique.after(
                50,
                dessiner,
            )

        def afficher_resume_comptable() -> None:
            try:
                selection, _ = obtenir_selection()
                resume = calculer_resume(selection)
            except ValueError as erreur:
                messagebox.showerror(
                    "Filtre invalide",
                    str(erreur),
                    parent=fenetre,
                )
                return

            resume_imprimable = construire_resume_comptable(
                selection,
                resume,
                date_debut=date_debut.get().strip() or None,
                date_fin=date_fin.get().strip() or None,
            )

            resume_fenetre = tk.Toplevel(fenetre)
            resume_fenetre.title(
                "Résumé comptable — ComptaPrivée AI"
            )
            resume_fenetre.geometry("760x600")
            resume_fenetre.minsize(650, 520)

            cadre = ttk.Frame(
                resume_fenetre,
                padding=20,
            )
            cadre.pack(
                fill="both",
                expand=True,
            )

            ttk.Label(
                cadre,
                text="Résumé comptable",
                font=("Segoe UI", 20, "bold"),
            ).pack(
                anchor="w",
                pady=(0, 5),
            )

            ttk.Label(
                cadre,
                text=(
                    "Vue synthétique calculée localement "
                    "à partir des filtres actifs."
                ),
                foreground="#166534",
            ).pack(
                anchor="w",
                pady=(0, 15),
            )

            informations = [
                ("Période", resume_imprimable.periode),
                (
                    "Nombre de factures",
                    str(resume_imprimable.nombre_factures),
                ),
                (
                    "Sous-total",
                    f"{resume_imprimable.sous_total:.2f} CAD",
                ),
                (
                    "TPS",
                    f"{resume_imprimable.tps:.2f} CAD",
                ),
                (
                    "TVQ",
                    f"{resume_imprimable.tvq:.2f} CAD",
                ),
                (
                    "Total",
                    f"{resume_imprimable.total:.2f} CAD",
                ),
                (
                    "Nombre d'anomalies",
                    str(resume_imprimable.nombre_anomalies),
                ),
                (
                    "Fournisseur principal",
                    resume_imprimable.fournisseur_principal,
                ),
                (
                    "Total fournisseur principal",
                    f"{resume_imprimable.total_fournisseur_principal:.2f} CAD",
                ),
            ]

            zone = ttk.LabelFrame(
                cadre,
                text="Synthèse",
                padding=15,
            )
            zone.pack(
                fill="both",
                expand=True,
            )

            for ligne, (libelle, valeur) in enumerate(
                informations
            ):
                ttk.Label(
                    zone,
                    text=f"{libelle} :",
                    font=("Segoe UI", 10, "bold"),
                ).grid(
                    row=ligne,
                    column=0,
                    sticky="w",
                    padx=(0, 25),
                    pady=8,
                )

                ttk.Label(
                    zone,
                    text=valeur,
                ).grid(
                    row=ligne,
                    column=1,
                    sticky="w",
                    pady=8,
                )

            zone.columnconfigure(
                1,
                weight=1,
            )

            def exporter_resume_pdf() -> None:
                chemin = filedialog.asksaveasfilename(
                    title="Exporter le résumé comptable en PDF",
                    initialdir=str(self.dossier_exports()),
                    defaultextension=".pdf",
                    initialfile=nom_fichier_rapport(
                        lire_profil_societe().nom_societe,
                        "Resume_comptable",
                        "pdf",
                        date_debut=date_debut.get().strip() or None,
                        date_fin=date_fin.get().strip() or None,
                    ),
                    filetypes=[("Fichier PDF", "*.pdf")],
                    parent=resume_fenetre,
                )

                if not chemin:
                    return

                try:
                    sortie = exporter_resume_comptable_pdf(
                        resume_imprimable,
                        chemin,
                    )
                except (OSError, ValueError) as erreur:
                    messagebox.showerror(
                        "Erreur d'export PDF",
                        str(erreur),
                        parent=resume_fenetre,
                    )
                    return

                self.statut.set(
                    f"Résumé comptable exporté : {sortie.name}"
                )
                messagebox.showinfo(
                    "Export terminé",
                    f"Résumé créé localement :\n{sortie}",
                    parent=resume_fenetre,
                )

            boutons = ttk.Frame(cadre)
            boutons.pack(
                fill="x",
                pady=(15, 0),
            )

            ttk.Button(
                boutons,
                text="Fermer",
                command=resume_fenetre.destroy,
            ).pack(
                side="right",
            )

            ttk.Button(
                boutons,
                text="Exporter en PDF",
                command=exporter_resume_pdf,
            ).pack(
                side="right",
                padx=(0, 8),
            )

        def afficher_anomalies() -> None:
            try:
                selection, _ = obtenir_selection()
            except ValueError as erreur:
                messagebox.showerror(
                    "Filtre invalide",
                    str(erreur),
                    parent=fenetre,
                )
                return

            anomalies = detecter_anomalies(
                selection
            )

            controle = tk.Toplevel(fenetre)
            controle.title(
                "Contrôle des anomalies — ComptaPrivée AI"
            )
            controle.geometry("980x580")
            controle.minsize(780, 460)

            cadre = ttk.Frame(
                controle,
                padding=20,
            )
            cadre.pack(
                fill="both",
                expand=True,
            )

            ttk.Label(
                cadre,
                text="Contrôle des anomalies",
                font=("Segoe UI", 18, "bold"),
            ).pack(
                anchor="w",
                pady=(0, 5),
            )

            if anomalies:
                texte_resume = (
                    f"{len(anomalies)} anomalie(s) détectée(s) "
                    f"sur {len(selection)} facture(s)."
                )
                couleur_resume = "#b45309"
            else:
                texte_resume = (
                    "Aucune anomalie détectée dans les "
                    "factures correspondant aux filtres."
                )
                couleur_resume = "#166534"

            ttk.Label(
                cadre,
                text=texte_resume,
                foreground=couleur_resume,
            ).pack(
                anchor="w",
                pady=(0, 15),
            )

            tableau_anomalies = ttk.Treeview(
                cadre,
                columns=(
                    "id",
                    "numero",
                    "niveau",
                    "message",
                ),
                show="headings",
            )

            tableau_anomalies.heading(
                "id",
                text="ID",
            )
            tableau_anomalies.heading(
                "numero",
                text="N° facture",
            )
            tableau_anomalies.heading(
                "niveau",
                text="Niveau",
            )
            tableau_anomalies.heading(
                "message",
                text="Anomalie",
            )

            tableau_anomalies.column(
                "id",
                width=60,
                anchor="center",
            )
            tableau_anomalies.column(
                "numero",
                width=150,
            )
            tableau_anomalies.column(
                "niveau",
                width=110,
                anchor="center",
            )
            tableau_anomalies.column(
                "message",
                width=600,
            )

            tableau_anomalies.pack(
                fill="both",
                expand=True,
            )

            for anomalie in anomalies:
                tableau_anomalies.insert(
                    "",
                    "end",
                    values=(
                        anomalie.identifiant,
                        anomalie.numero,
                        anomalie.niveau,
                        anomalie.message,
                    ),
                )

            if not anomalies:
                tableau_anomalies.insert(
                    "",
                    "end",
                    values=(
                        "",
                        "",
                        "OK",
                        "Aucune anomalie détectée.",
                    ),
                )

            ttk.Button(
                cadre,
                text="Fermer",
                command=controle.destroy,
            ).pack(
                anchor="e",
                pady=(12, 0),
            )

        def afficher_taxes_mensuelles() -> None:
            try:
                selection, _ = obtenir_selection()
            except ValueError as erreur:
                messagebox.showerror(
                    "Filtre invalide",
                    str(erreur),
                    parent=fenetre,
                )
                return

            donnees = calculer_taxes_mensuelles(
                selection
            )

            if not donnees:
                messagebox.showinfo(
                    "Taxes mensuelles",
                    "Aucune donnée de taxes à afficher pour ces filtres.",
                    parent=fenetre,
                )
                return

            graphique = tk.Toplevel(fenetre)
            graphique.title(
                "TPS et TVQ mensuelles — ComptaPrivée AI"
            )
            graphique.geometry("940x580")
            graphique.minsize(740, 460)

            cadre = ttk.Frame(
                graphique,
                padding=20,
            )
            cadre.pack(
                fill="both",
                expand=True,
            )

            ttk.Label(
                cadre,
                text="TPS et TVQ par mois",
                font=("Segoe UI", 18, "bold"),
            ).pack(
                anchor="w",
                pady=(0, 5),
            )

            ttk.Label(
                cadre,
                text=(
                    "Taxes calculées à partir des factures "
                    "correspondant aux filtres actifs."
                ),
                foreground="#166534",
            ).pack(
                anchor="w",
                pady=(0, 15),
            )

            toile = tk.Canvas(
                cadre,
                background="white",
                highlightthickness=1,
                highlightbackground="#cbd5e1",
            )
            toile.pack(
                fill="both",
                expand=True,
            )

            def dessiner_taxes(_event=None) -> None:
                toile.delete("all")

                largeur = max(
                    toile.winfo_width(),
                    700,
                )
                hauteur = max(
                    toile.winfo_height(),
                    340,
                )

                marge_gauche = 80
                marge_droite = 40
                marge_haut = 55
                marge_bas = 80

                largeur_graphique = max(
                    largeur - marge_gauche - marge_droite,
                    100,
                )
                hauteur_graphique = max(
                    hauteur - marge_haut - marge_bas,
                    100,
                )

                maximum = max(
                    max(float(tps), float(tvq))
                    for _, tps, tvq in donnees
                )

                if maximum <= 0:
                    maximum = 1.0

                y_bas = hauteur - marge_bas
                y_haut = marge_haut

                toile.create_line(
                    marge_gauche,
                    y_haut,
                    marge_gauche,
                    y_bas,
                    fill="#64748b",
                )
                toile.create_line(
                    marge_gauche,
                    y_bas,
                    largeur - marge_droite,
                    y_bas,
                    fill="#64748b",
                )

                for division in range(5):
                    valeur = maximum * division / 4
                    y = (
                        y_bas
                        - hauteur_graphique * division / 4
                    )

                    toile.create_line(
                        marge_gauche - 5,
                        y,
                        largeur - marge_droite,
                        y,
                        fill="#e2e8f0",
                    )
                    toile.create_text(
                        marge_gauche - 10,
                        y,
                        text=f"{valeur:.0f}",
                        anchor="e",
                        font=("Segoe UI", 9),
                    )

                nombre = len(donnees)
                largeur_groupe = (
                    largeur_graphique / max(nombre, 1)
                )
                largeur_barre = min(
                    36,
                    largeur_groupe * 0.28,
                )

                for index, (mois, tps, tvq) in enumerate(
                    donnees
                ):
                    centre = (
                        marge_gauche
                        + largeur_groupe * index
                        + largeur_groupe / 2
                    )

                    valeurs = [
                        ("TPS", tps, "#2563eb"),
                        ("TVQ", tvq, "#16a34a"),
                    ]

                    for decalage, (
                        libelle,
                        montant,
                        couleur,
                    ) in enumerate(valeurs):
                        ratio = float(montant) / maximum
                        hauteur_barre = (
                            hauteur_graphique * ratio
                        )

                        x1 = (
                            centre
                            - largeur_barre
                            - 3
                            if decalage == 0
                            else centre + 3
                        )
                        x2 = x1 + largeur_barre
                        y1 = y_bas - hauteur_barre

                        toile.create_rectangle(
                            x1,
                            y1,
                            x2,
                            y_bas,
                            fill=couleur,
                            outline=couleur,
                        )

                        toile.create_text(
                            (x1 + x2) / 2,
                            max(y1 - 8, 12),
                            text=f"{montant:.2f}",
                            anchor="s",
                            font=("Segoe UI", 8, "bold"),
                        )

                    toile.create_text(
                        centre,
                        y_bas + 24,
                        text=mois,
                        anchor="n",
                        font=("Segoe UI", 9),
                    )

                legende_y = 18
                toile.create_rectangle(
                    marge_gauche,
                    legende_y,
                    marge_gauche + 16,
                    legende_y + 12,
                    fill="#2563eb",
                    outline="#2563eb",
                )
                toile.create_text(
                    marge_gauche + 24,
                    legende_y + 6,
                    text="TPS",
                    anchor="w",
                    font=("Segoe UI", 9),
                )

                toile.create_rectangle(
                    marge_gauche + 80,
                    legende_y,
                    marge_gauche + 96,
                    legende_y + 12,
                    fill="#16a34a",
                    outline="#16a34a",
                )
                toile.create_text(
                    marge_gauche + 104,
                    legende_y + 6,
                    text="TVQ",
                    anchor="w",
                    font=("Segoe UI", 9),
                )

            toile.bind(
                "<Configure>",
                dessiner_taxes,
            )

            ttk.Button(
                cadre,
                text="Fermer",
                command=graphique.destroy,
            ).pack(
                anchor="e",
                pady=(12, 0),
            )

            graphique.after(
                50,
                dessiner_taxes,
            )

        def afficher_evolution_mensuelle() -> None:
            try:
                selection, _ = obtenir_selection()
            except ValueError as erreur:
                messagebox.showerror(
                    "Filtre invalide",
                    str(erreur),
                    parent=fenetre,
                )
                return

            donnees = calculer_totaux_mensuels(
                selection
            )

            if not donnees:
                messagebox.showinfo(
                    "Évolution mensuelle",
                    "Aucune donnée mensuelle à afficher pour ces filtres.",
                    parent=fenetre,
                )
                return

            graphique = tk.Toplevel(fenetre)
            graphique.title(
                "Évolution mensuelle — ComptaPrivée AI"
            )
            graphique.geometry("920x560")
            graphique.minsize(720, 450)

            cadre = ttk.Frame(
                graphique,
                padding=20,
            )
            cadre.pack(
                fill="both",
                expand=True,
            )

            ttk.Label(
                cadre,
                text="Évolution mensuelle des montants",
                font=("Segoe UI", 18, "bold"),
            ).pack(
                anchor="w",
                pady=(0, 5),
            )

            ttk.Label(
                cadre,
                text=(
                    "Total facturé par mois selon les filtres "
                    "actuellement appliqués."
                ),
                foreground="#166534",
            ).pack(
                anchor="w",
                pady=(0, 15),
            )

            toile = tk.Canvas(
                cadre,
                background="white",
                highlightthickness=1,
                highlightbackground="#cbd5e1",
            )
            toile.pack(
                fill="both",
                expand=True,
            )

            def dessiner_mensuel(_event=None) -> None:
                toile.delete("all")

                largeur = max(
                    toile.winfo_width(),
                    680,
                )
                hauteur = max(
                    toile.winfo_height(),
                    330,
                )

                marge_gauche = 80
                marge_droite = 40
                marge_haut = 40
                marge_bas = 70

                largeur_graphique = max(
                    largeur - marge_gauche - marge_droite,
                    100,
                )
                hauteur_graphique = max(
                    hauteur - marge_haut - marge_bas,
                    100,
                )

                maximum = max(
                    float(total)
                    for _, total in donnees
                )
                if maximum <= 0:
                    maximum = 1.0

                x_gauche = marge_gauche
                y_bas = hauteur - marge_bas
                y_haut = marge_haut

                toile.create_line(
                    x_gauche,
                    y_haut,
                    x_gauche,
                    y_bas,
                    fill="#64748b",
                )
                toile.create_line(
                    x_gauche,
                    y_bas,
                    largeur - marge_droite,
                    y_bas,
                    fill="#64748b",
                )

                for division in range(5):
                    valeur = maximum * division / 4
                    y = (
                        y_bas
                        - hauteur_graphique * division / 4
                    )

                    toile.create_line(
                        x_gauche - 5,
                        y,
                        largeur - marge_droite,
                        y,
                        fill="#e2e8f0",
                    )
                    toile.create_text(
                        x_gauche - 10,
                        y,
                        text=f"{valeur:.0f}",
                        anchor="e",
                        font=("Segoe UI", 9),
                    )

                nombre = len(donnees)

                if nombre == 1:
                    positions_x = [
                        x_gauche + largeur_graphique / 2
                    ]
                else:
                    positions_x = [
                        (
                            x_gauche
                            + largeur_graphique
                            * index
                            / (nombre - 1)
                        )
                        for index in range(nombre)
                    ]

                points = []

                for index, (mois, total) in enumerate(
                    donnees
                ):
                    x = positions_x[index]
                    ratio = float(total) / maximum
                    y = (
                        y_bas
                        - hauteur_graphique * ratio
                    )

                    points.extend([x, y])

                    toile.create_text(
                        x,
                        y_bas + 22,
                        text=mois,
                        anchor="n",
                        font=("Segoe UI", 9),
                    )

                if len(points) >= 4:
                    toile.create_line(
                        *points,
                        fill="#2563eb",
                        width=3,
                        smooth=False,
                    )

                for index, (mois, total) in enumerate(
                    donnees
                ):
                    x = positions_x[index]
                    ratio = float(total) / maximum
                    y = (
                        y_bas
                        - hauteur_graphique * ratio
                    )

                    toile.create_oval(
                        x - 5,
                        y - 5,
                        x + 5,
                        y + 5,
                        fill="#2563eb",
                        outline="#1d4ed8",
                    )

                    toile.create_text(
                        x,
                        max(y - 12, 12),
                        text=f"{total:.2f} CAD",
                        anchor="s",
                        font=("Segoe UI", 9, "bold"),
                    )

            toile.bind(
                "<Configure>",
                dessiner_mensuel,
            )

            ttk.Button(
                cadre,
                text="Fermer",
                command=graphique.destroy,
            ).pack(
                anchor="e",
                pady=(12, 0),
            )

            graphique.after(
                50,
                dessiner_mensuel,
            )

        ttk.Button(
            zone_filtres,
            text="Appliquer",
            command=actualiser_tableau_bord,
        ).pack(
            side="left",
            padx=(0, 8),
        )

        ttk.Button(
            zone_filtres,
            text="Effacer",
            command=effacer_filtres,
        ).pack(
            side="left",
        )

        ttk.Button(
            zone_filtres,
            text="Résumé comptable",
            command=afficher_resume_comptable,
        ).pack(
            side="left",
            padx=(8, 0),
        )

        zone_bas = ttk.Frame(conteneur)
        zone_bas.pack(
            fill="x",
            pady=(15, 0),
        )

        ttk.Button(
            zone_bas,
            text="Fermer",
            command=fenetre.destroy,
        ).pack(side="right")

        ttk.Button(
            zone_bas,
            text="Exporter en PDF",
            command=exporter_dashboard_pdf,
        ).pack(
            side="right",
            padx=(0, 8),
        )

        ttk.Button(
            zone_bas,
            text="Exporter en CSV",
            command=exporter_dashboard_csv,
        ).pack(
            side="right",
            padx=(0, 8),
        )

        ttk.Button(
            zone_bas,
            text="Voir le graphique",
            command=afficher_graphique_fournisseurs,
        ).pack(
            side="right",
            padx=(0, 8),
        )

        ttk.Button(
            zone_bas,
            text="Évolution mensuelle",
            command=afficher_evolution_mensuelle,
        ).pack(
            side="right",
            padx=(0, 8),
        )

        ttk.Button(
            zone_bas,
            text="TPS / TVQ mensuelles",
            command=afficher_taxes_mensuelles,
        ).pack(
            side="right",
            padx=(0, 8),
        )

        ttk.Button(
            zone_bas,
            text="Contrôle anomalies",
            command=afficher_anomalies,
        ).pack(
            side="right",
            padx=(0, 8),
        )

        actualiser_tableau_bord()

    def ouvrir_dossier_exports(self) -> None:
        """Ouvre le dossier local contenant les exports CSV et PDF."""
        chemin = self.dossier_exports()

        try:
            if sys.platform.startswith("win"):
                os.startfile(chemin)  # type: ignore[attr-defined]
            elif sys.platform == "darwin":
                subprocess.run(
                    ["open", str(chemin)],
                    check=True,
                )
            else:
                subprocess.run(
                    ["xdg-open", str(chemin)],
                    check=True,
                )

        except (OSError, subprocess.SubprocessError) as erreur:
            messagebox.showerror(
                "Impossible d'ouvrir le dossier",
                (
                    "Le dossier des exports existe, mais "
                    "ComptaPrivée AI n'a pas pu l'ouvrir.\n\n"
                    f"Chemin : {chemin}\n"
                    f"Détail : {erreur}"
                ),
            )
            return

        self.statut.set(
            f"Dossier des exports ouvert : {chemin}"
        )

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
        validation = appliquer_validation_fiscale(
            facture,
            validation,
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

        resultat_doublon = detecter_doublon(
            facture
        )

        if resultat_doublon.niveau is NiveauDoublon.CERTAIN:
            existante = resultat_doublon.facture_existante

            details = resultat_doublon.raison

            if existante is not None:
                details += (
                    "\n\nFacture existante :"
                    f"\nNuméro : {existante.numero or '-'}"
                    f"\nFournisseur : {existante.fournisseur or '-'}"
                    f"\nDate : {existante.date or '-'}"
                    f"\nTotal : {existante.total or '-'}"
                )

            messagebox.showwarning(
                "Doublon certain détecté",
                (
                    "Cette facture semble déjà être enregistrée.\n\n"
                    f"{details}\n\n"
                    "L'enregistrement est bloqué pour éviter un doublon."
                ),
                parent=self,
            )

            self.statut.set(
                "Doublon certain détecté — enregistrement bloqué"
            )
            return

        if resultat_doublon.niveau is NiveauDoublon.PROBABLE:
            existante = resultat_doublon.facture_existante

            details = resultat_doublon.raison

            if existante is not None:
                details += (
                    "\n\nFacture similaire :"
                    f"\nNuméro : {existante.numero or '-'}"
                    f"\nFournisseur : {existante.fournisseur or '-'}"
                    f"\nDate : {existante.date or '-'}"
                    f"\nTotal : {existante.total or '-'}"
                )

            continuer = messagebox.askyesno(
                "Doublon probable détecté",
                (
                    "Une facture similaire existe déjà.\n\n"
                    f"{details}\n\n"
                    "Voulez-vous quand même continuer "
                    "l'enregistrement ?"
                ),
                parent=self,
            )

            if not continuer:
                self.statut.set(
                    "Enregistrement annulé — doublon probable"
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
            "l'historique local"
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

    def ouvrir_detail_historique(
        self,
        facture,
        parent: tk.Misc,
    ) -> None:
        """Affiche le détail d'une facture enregistrée."""
        fenetre_detail = tk.Toplevel(parent)

        numero = (
            facture.numero
            or "Sans numéro"
        )

        fenetre_detail.title(
            f"Facture {numero} — ComptaPrivée AI"
        )

        fenetre_detail.geometry(
            "620x560"
        )

        fenetre_detail.minsize(
            520,
            480,
        )

        conteneur = ttk.Frame(
            fenetre_detail,
            padding=20,
        )

        conteneur.pack(
            fill="both",
            expand=True,
        )

        ttk.Label(
            conteneur,
            text="Détail de la facture",
            font=("Segoe UI", 18, "bold"),
        ).pack(
            anchor="w",
            pady=(0, 5),
        )

        ttk.Label(
            conteneur,
            text=(
                "🔒 Données enregistrées dans "
                "la base SQLite locale"
            ),
            foreground="#166534",
        ).pack(
            anchor="w",
            pady=(0, 20),
        )

        cadre = ttk.LabelFrame(
            conteneur,
            text="Informations enregistrées",
            padding=15,
        )

        cadre.pack(
            fill="both",
            expand=True,
        )

        def montant(
            valeur: Decimal | None,
        ) -> str:
            if valeur is None:
                return "Non renseigné"

            return f"{valeur:.2f} CAD"

        valeurs = [
            (
                "Identifiant",
                str(facture.identifiant),
            ),
            (
                "Numéro de facture",
                facture.numero or "Non renseigné",
            ),
            (
                "Date",
                facture.date or "Non renseignée",
            ),
            (
                "Fournisseur",
                facture.fournisseur or "Non renseigné",
            ),
            (
                "Client",
                facture.client or "Non renseigné",
            ),
            (
                "Sous-total",
                montant(facture.sous_total),
            ),
            (
                "TPS",
                montant(facture.tps),
            ),
            (
                "TVQ",
                montant(facture.tvq),
            ),
            (
                "Total",
                montant(facture.total),
            ),
            (
                "Enregistrée le",
                facture.date_creation,
            ),
        ]

        for ligne, (
            libelle,
            valeur,
        ) in enumerate(valeurs):
            ttk.Label(
                cadre,
                text=f"{libelle} :",
                font=("Segoe UI", 10, "bold"),
            ).grid(
                row=ligne,
                column=0,
                sticky="nw",
                padx=(0, 20),
                pady=7,
            )

            ttk.Label(
                cadre,
                text=valeur,
                wraplength=340,
            ).grid(
                row=ligne,
                column=1,
                sticky="nw",
                pady=7,
            )

        cadre.columnconfigure(
            1,
            weight=1,
        )

        ttk.Button(
            conteneur,
            text="Fermer",
            command=fenetre_detail.destroy,
        ).pack(
            anchor="e",
            pady=(15, 0),
        )

    def ouvrir_corbeille(self) -> None:
        """Ouvre la corbeille locale des factures."""
        fenetre = tk.Toplevel(self)
        fenetre.title("Corbeille — ComptaPrivée AI")
        fenetre.geometry("1150x600")
        fenetre.minsize(900, 450)

        conteneur = ttk.Frame(fenetre, padding=15)
        conteneur.pack(fill="both", expand=True)

        ttk.Label(
            conteneur,
            text="Corbeille locale",
            font=("Segoe UI", 18, "bold"),
        ).pack(anchor="w", pady=(0, 5))

        ttk.Label(
            conteneur,
            text=(
                "Les factures placées ici peuvent être restaurées. "
                "La suppression définitive est irréversible."
            ),
            foreground="#92400e",
        ).pack(anchor="w", pady=(0, 12))

        cadre_tableau = ttk.Frame(conteneur)
        cadre_tableau.pack(fill="both", expand=True)

        colonnes = (
            "id", "date", "numero", "fournisseur", "client",
            "total", "date_suppression",
        )
        tableau = ttk.Treeview(
            cadre_tableau, columns=colonnes, show="headings", selectmode="browse"
        )

        titres = {
            "id": "ID",
            "date": "Date",
            "numero": "N° facture",
            "fournisseur": "Fournisseur",
            "client": "Client",
            "total": "Total",
            "date_suppression": "Supprimée le",
        }
        for colonne, titre in titres.items():
            tableau.heading(colonne, text=titre)

        tableau.column("id", width=60, anchor="center", stretch=False)
        tableau.column("date", width=100, anchor="center", stretch=False)
        tableau.column("numero", width=140)
        tableau.column("fournisseur", width=220)
        tableau.column("client", width=220)
        tableau.column("total", width=110, anchor="e", stretch=False)
        tableau.column("date_suppression", width=165, anchor="center")

        barre_verticale = ttk.Scrollbar(
            cadre_tableau, orient="vertical", command=tableau.yview
        )
        barre_horizontale = ttk.Scrollbar(
            cadre_tableau, orient="horizontal", command=tableau.xview
        )
        tableau.configure(
            yscrollcommand=barre_verticale.set,
            xscrollcommand=barre_horizontale.set,
        )
        tableau.grid(row=0, column=0, sticky="nsew")
        barre_verticale.grid(row=0, column=1, sticky="ns")
        barre_horizontale.grid(row=1, column=0, sticky="ew")
        cadre_tableau.rowconfigure(0, weight=1)
        cadre_tableau.columnconfigure(0, weight=1)

        texte_resume = tk.StringVar(value="")
        factures_corbeille = []

        def charger_corbeille() -> None:
            nonlocal factures_corbeille
            for element in tableau.get_children():
                tableau.delete(element)

            try:
                factures_corbeille = lister_factures_corbeille()
            except Exception as erreur:
                messagebox.showerror(
                    "Erreur de la corbeille", str(erreur), parent=fenetre
                )
                return

            for facture in factures_corbeille:
                total_affiche = "" if facture.total is None else f"{facture.total:.2f} CAD"
                tableau.insert(
                    "", "end", iid=str(facture.identifiant),
                    values=(
                        facture.identifiant, facture.date or "", facture.numero or "",
                        facture.fournisseur or "", facture.client or "",
                        total_affiche, facture.date_suppression,
                    ),
                )

            nombre = len(factures_corbeille)
            if nombre == 0:
                texte_resume.set("La corbeille est vide.")
            elif nombre == 1:
                texte_resume.set("1 facture dans la corbeille.")
            else:
                texte_resume.set(f"{nombre} factures dans la corbeille.")

        def facture_selectionnee():
            selection = tableau.selection()
            if not selection:
                return None
            identifiant = int(selection[0])
            for facture in factures_corbeille:
                if facture.identifiant == identifiant:
                    return facture
            return None

        def restaurer_selection() -> None:
            facture = facture_selectionnee()
            if facture is None:
                messagebox.showinfo(
                    "Sélection requise",
                    "Sélectionnez une facture à restaurer.",
                    parent=fenetre,
                )
                return

            numero = facture.numero or "Sans numéro"
            if not messagebox.askyesno(
                "Restaurer la facture",
                f"Restaurer la facture {numero} dans l'historique actif ?",
                parent=fenetre,
            ):
                return

            try:
                restauree = restaurer_facture(facture.identifiant)
            except ValueError as erreur:
                messagebox.showerror(
                    "Restauration impossible", str(erreur), parent=fenetre
                )
                return
            except Exception as erreur:
                messagebox.showerror(
                    "Erreur de restauration", str(erreur), parent=fenetre
                )
                return

            if not restauree:
                messagebox.showwarning(
                    "Facture introuvable",
                    "La facture n'est plus dans la corbeille.",
                    parent=fenetre,
                )
                charger_corbeille()
                return

            charger_corbeille()
            self.statut.set("Facture restaurée depuis la corbeille")
            messagebox.showinfo(
                "Facture restaurée",
                f"La facture {numero} a été restaurée.",
                parent=fenetre,
            )

        def supprimer_definitivement() -> None:
            facture = facture_selectionnee()
            if facture is None:
                messagebox.showinfo(
                    "Sélection requise",
                    "Sélectionnez une facture à supprimer.",
                    parent=fenetre,
                )
                return

            numero = facture.numero or "Sans numéro"
            if not messagebox.askyesno(
                "Suppression définitive",
                (
                    f"Supprimer définitivement la facture {numero} ?\n\n"
                    "Cette opération ne peut pas être annulée."
                ),
                parent=fenetre,
            ):
                return

            if not messagebox.askyesno(
                "Dernière confirmation",
                (
                    "ATTENTION\n\nLa facture sera définitivement effacée "
                    "de la corbeille SQLite locale.\n\nConfirmer ?"
                ),
                parent=fenetre,
            ):
                return

            try:
                supprimee = supprimer_facture_corbeille(facture.identifiant)
            except Exception as erreur:
                messagebox.showerror(
                    "Erreur de suppression", str(erreur), parent=fenetre
                )
                return

            charger_corbeille()
            if supprimee:
                self.statut.set("Facture supprimée définitivement")
                messagebox.showinfo(
                    "Suppression terminée",
                    f"La facture {numero} a été supprimée définitivement.",
                    parent=fenetre,
                )

        zone_bas = ttk.Frame(conteneur)
        zone_bas.pack(fill="x", pady=(12, 0))
        ttk.Label(zone_bas, textvariable=texte_resume).pack(side="left")
        ttk.Button(zone_bas, text="Actualiser", command=charger_corbeille).pack(side="right")
        ttk.Button(zone_bas, text="Fermer", command=fenetre.destroy).pack(side="right", padx=(0, 10))
        ttk.Button(
            zone_bas, text="Supprimer définitivement", command=supprimer_definitivement
        ).pack(side="right", padx=(0, 10))
        ttk.Button(zone_bas, text="Restaurer", command=restaurer_selection).pack(side="right", padx=(0, 10))

        charger_corbeille()

    def ouvrir_historique(self) -> None:
        """Ouvre la fenêtre de consultation de l'historique."""
        fenetre = tk.Toplevel(self)

        fenetre.title(
            "Historique des factures — ComptaPrivée AI"
        )

        fenetre.geometry(
            "1150x600"
        )

        fenetre.minsize(
            900,
            450,
        )

        conteneur = ttk.Frame(
            fenetre,
            padding=15,
        )

        conteneur.pack(
            fill="both",
            expand=True,
        )

        ttk.Label(
            conteneur,
            text="Historique local des factures",
            font=("Segoe UI", 18, "bold"),
        ).pack(
            anchor="w",
            pady=(0, 5),
        )

        ttk.Label(
            conteneur,
            text=(
                "🔒 Les données affichées proviennent "
                "uniquement de la base SQLite locale."
            ),
            foreground="#166534",
        ).pack(
            anchor="w",
            pady=(0, 12),
        )

        zone_recherche = ttk.Frame(
            conteneur
        )

        zone_recherche.pack(
            fill="x",
            pady=(0, 12),
        )

        ttk.Label(
            zone_recherche,
            text="Rechercher :",
            font=("Segoe UI", 10, "bold"),
        ).pack(
            side="left",
        )

        variable_recherche = tk.StringVar()

        champ_recherche = ttk.Entry(
            zone_recherche,
            textvariable=variable_recherche,
            width=45,
        )

        champ_recherche.pack(
            side="left",
            padx=(8, 8),
        )

        cadre_tableau = ttk.Frame(
            conteneur
        )

        cadre_tableau.pack(
            fill="both",
            expand=True,
        )

        colonnes = (
            "id",
            "date",
            "numero",
            "fournisseur",
            "client",
            "total",
            "date_creation",
        )

        tableau = ttk.Treeview(
            cadre_tableau,
            columns=colonnes,
            show="headings",
            selectmode="browse",
        )

        tableau.heading(
            "id",
            text="ID",
        )

        tableau.heading(
            "date",
            text="Date",
        )

        tableau.heading(
            "numero",
            text="N° facture",
        )

        tableau.heading(
            "fournisseur",
            text="Fournisseur",
        )

        tableau.heading(
            "client",
            text="Client",
        )

        tableau.heading(
            "total",
            text="Total",
        )

        tableau.heading(
            "date_creation",
            text="Enregistrée le",
        )

        tableau.column(
            "id",
            width=60,
            anchor="center",
            stretch=False,
        )

        tableau.column(
            "date",
            width=100,
            anchor="center",
            stretch=False,
        )

        tableau.column(
            "numero",
            width=140,
            anchor="w",
        )

        tableau.column(
            "fournisseur",
            width=220,
            anchor="w",
        )

        tableau.column(
            "client",
            width=220,
            anchor="w",
        )

        tableau.column(
            "total",
            width=110,
            anchor="e",
            stretch=False,
        )

        tableau.column(
            "date_creation",
            width=160,
            anchor="center",
        )

        barre_verticale = ttk.Scrollbar(
            cadre_tableau,
            orient="vertical",
            command=tableau.yview,
        )

        barre_horizontale = ttk.Scrollbar(
            cadre_tableau,
            orient="horizontal",
            command=tableau.xview,
        )

        tableau.configure(
            yscrollcommand=barre_verticale.set,
            xscrollcommand=barre_horizontale.set,
        )

        tableau.grid(
            row=0,
            column=0,
            sticky="nsew",
        )

        barre_verticale.grid(
            row=0,
            column=1,
            sticky="ns",
        )

        barre_horizontale.grid(
            row=1,
            column=0,
            sticky="ew",
        )

        cadre_tableau.rowconfigure(
            0,
            weight=1,
        )

        cadre_tableau.columnconfigure(
            0,
            weight=1,
        )

        texte_resume = tk.StringVar(
            value=""
        )

        factures_chargees = []

        def afficher_factures(
            factures,
        ) -> None:
            """Affiche les factures dans le tableau."""
            for element in tableau.get_children():
                tableau.delete(element)

            for facture in factures:
                if facture.total is None:
                    total_affiche = ""
                else:
                    total_affiche = (
                        f"{facture.total:.2f} CAD"
                    )

                tableau.insert(
                    "",
                    "end",
                    iid=str(
                        facture.identifiant
                    ),
                    values=(
                        facture.identifiant,
                        facture.date or "",
                        facture.numero or "",
                        facture.fournisseur or "",
                        facture.client or "",
                        total_affiche,
                        facture.date_creation,
                    ),
                )

            nombre = len(factures)

            if nombre == 0:
                texte_resume.set(
                    "Aucune facture trouvée."
                )

            elif nombre == 1:
                texte_resume.set(
                    "1 facture affichée."
                )

            else:
                texte_resume.set(
                    f"{nombre} factures affichées."
                )

        def rechercher_factures(
            *_,
        ) -> None:
            """Filtre localement les factures affichées."""
            recherche = (
                variable_recherche
                .get()
                .strip()
                .lower()
            )

            if not recherche:
                afficher_factures(
                    factures_chargees
                )
                return

            resultats = []

            for facture in factures_chargees:
                valeurs = (
                    str(facture.identifiant),
                    facture.numero or "",
                    facture.date or "",
                    facture.fournisseur or "",
                    facture.client or "",
                    str(facture.total or ""),
                    facture.date_creation or "",
                )

                texte = " ".join(
                    valeurs
                ).lower()

                if recherche in texte:
                    resultats.append(
                        facture
                    )

            afficher_factures(
                resultats
            )

        def charger_factures() -> None:
            """Recharge toutes les factures depuis SQLite."""
            nonlocal factures_chargees

            try:
                factures_chargees = (
                    lister_factures()
                )

            except Exception as erreur:
                messagebox.showerror(
                    "Erreur de l'historique",
                    str(erreur),
                    parent=fenetre,
                )
                return

            rechercher_factures()

        def effacer_recherche() -> None:
            """Efface le filtre de recherche."""
            variable_recherche.set("")
            champ_recherche.focus_set()

        def obtenir_facture_selectionnee():
            """Retourne la facture sélectionnée."""
            selection = tableau.selection()

            if not selection:
                return None

            try:
                identifiant = int(
                    selection[0]
                )
            except ValueError:
                return None

            for facture in factures_chargees:
                if (
                    facture.identifiant
                    == identifiant
                ):
                    return facture

            return None

        def voir_detail() -> None:
            """Ouvre le détail de la facture sélectionnée."""
            facture = (
                obtenir_facture_selectionnee()
            )

            if facture is None:
                messagebox.showinfo(
                    "Sélection requise",
                    (
                        "Sélectionnez une facture "
                        "dans l'historique."
                    ),
                    parent=fenetre,
                )
                return

            self.ouvrir_detail_historique(
                facture,
                fenetre,
            )

        def exporter_pdf_selection_historique() -> None:
            """Exporte le detail de la facture selectionnee en PDF."""
            facture = obtenir_facture_selectionnee()

            if facture is None:
                messagebox.showinfo(
                    "Selection requise",
                    "Selectionnez une facture a exporter en PDF.",
                    parent=fenetre,
                )
                return

            numero = facture.numero or f"facture_{facture.identifiant}"

            chemin_sortie = filedialog.asksaveasfilename(
                title="Exporter le detail de la facture en PDF",
                initialdir=str(self.dossier_exports()),
                defaultextension=".pdf",
                initialfile=f"{numero}.pdf",
                filetypes=[("Fichier PDF", "*.pdf")],
                parent=fenetre,
            )

            if not chemin_sortie:
                return

            donnees = DonneesFacture(
                numero=facture.numero,
                date=facture.date,
                fournisseur=facture.fournisseur,
                client=facture.client,
                sous_total=facture.sous_total,
                tps=facture.tps,
                tvq=facture.tvq,
                total=facture.total,
            )

            try:
                chemin = exporter_facture_pdf(
                    donnees,
                    chemin_sortie,
                    identifiant=facture.identifiant,
                    date_enregistrement=facture.date_creation,
                )
            except (OSError, ValueError) as erreur:
                messagebox.showerror(
                    "Erreur d'export PDF",
                    str(erreur),
                    parent=fenetre,
                )
                return

            self.statut.set(
                f"Export PDF depuis l'historique : {chemin.name}"
            )

            messagebox.showinfo(
                "Export PDF termine",
                (
                    "Le detail de la facture a ete exporte "
                    "localement en PDF.\n\n"
                    f"Numero : {numero}\n"
                    f"Fichier : {chemin}"
                ),
                parent=fenetre,
            )

        def exporter_selection_historique() -> None:
            """Exporte en CSV la facture sélectionnée dans l'historique."""
            facture = obtenir_facture_selectionnee()

            if facture is None:
                messagebox.showinfo(
                    "Sélection requise",
                    "Sélectionnez une facture à exporter.",
                    parent=fenetre,
                )
                return

            numero = facture.numero or f"facture_{facture.identifiant}"
            nom_initial = f"{numero}.csv"

            chemin_sortie = filedialog.asksaveasfilename(
                title="Exporter la facture de l'historique en CSV",
                initialdir=str(self.dossier_exports()),
                defaultextension=".csv",
                initialfile=nom_initial,
                filetypes=[("Fichier CSV", "*.csv")],
                parent=fenetre,
            )

            if not chemin_sortie:
                return

            donnees = DonneesFacture(
                numero=facture.numero,
                date=facture.date,
                fournisseur=facture.fournisseur,
                client=facture.client,
                sous_total=facture.sous_total,
                tps=facture.tps,
                tvq=facture.tvq,
                total=facture.total,
            )

            try:
                chemin = exporter_facture_csv(
                    donnees,
                    chemin_sortie,
                )
            except (OSError, ValueError) as erreur:
                messagebox.showerror(
                    "Erreur d'export",
                    str(erreur),
                    parent=fenetre,
                )
                return

            self.statut.set(
                f"Export CSV depuis l'historique : {chemin.name}"
            )

            messagebox.showinfo(
                "Export terminé",
                (
                    "La facture a été exportée localement en CSV.\n\n"
                    f"Numéro : {numero}\n"
                    f"Fichier : {chemin}"
                ),
                parent=fenetre,
            )

        def supprimer_selection() -> None:
            """Déplace la facture sélectionnée vers la corbeille."""
            facture = obtenir_facture_selectionnee()

            if facture is None:
                messagebox.showinfo(
                    "Sélection requise",
                    "Sélectionnez d'abord une facture.",
                    parent=fenetre,
                )
                return

            numero = facture.numero or "Sans numéro"
            fournisseur = facture.fournisseur or "Fournisseur non renseigné"

            confirmation = messagebox.askyesno(
                "Mettre à la corbeille",
                (
                    "Déplacer cette facture vers la corbeille ?\n\n"
                    f"Numéro : {numero}\n"
                    f"Fournisseur : {fournisseur}\n"
                    f"ID : {facture.identifiant}\n\n"
                    "La facture pourra être restaurée plus tard."
                ),
                parent=fenetre,
            )

            if not confirmation:
                return

            try:
                deplacee = mettre_facture_corbeille(facture.identifiant)
            except Exception as erreur:
                messagebox.showerror(
                    "Erreur", str(erreur), parent=fenetre
                )
                return

            if not deplacee:
                messagebox.showwarning(
                    "Facture introuvable",
                    "La facture n'existe plus dans l'historique.",
                    parent=fenetre,
                )
                charger_factures()
                return

            charger_factures()
            self.statut.set("Facture déplacée vers la corbeille locale")
            messagebox.showinfo(
                "Facture déplacée",
                (
                    "La facture a été placée dans la corbeille.\n\n"
                    f"Numéro : {numero}\n\n"
                    "Elle peut être restaurée depuis la corbeille."
                ),
                parent=fenetre,
            )

        def double_clic(
            _evenement,
        ) -> None:
            """Ouvre une facture par double-clic."""
            if tableau.selection():
                voir_detail()

        ttk.Button(
            zone_recherche,
            text="Effacer",
            command=effacer_recherche,
        ).pack(
            side="left",
        )

        variable_recherche.trace_add(
            "write",
            rechercher_factures,
        )

        tableau.bind(
            "<Double-1>",
            double_clic,
        )

        zone_bas = ttk.Frame(
            conteneur
        )

        zone_bas.pack(
            fill="x",
            pady=(12, 0),
        )

        ttk.Label(
            zone_bas,
            textvariable=texte_resume,
        ).pack(
            side="left",
        )

        ttk.Button(
            zone_bas,
            text="Actualiser",
            command=charger_factures,
        ).pack(
            side="right",
        )

        ttk.Button(
            zone_bas,
            text="Fermer",
            command=fenetre.destroy,
        ).pack(
            side="right",
            padx=(0, 10),
        )

        ttk.Button(
            zone_bas,
            text="Mettre à la corbeille",
            command=supprimer_selection,
        ).pack(
            side="right",
            padx=(0, 10),
        )

        ttk.Button(
            zone_bas,
            text="Exporter en PDF",
            command=exporter_pdf_selection_historique,
        ).pack(
            side="right",
            padx=(0, 10),
        )

        ttk.Button(
            zone_bas,
            text="Exporter en CSV",
            command=exporter_selection_historique,
        ).pack(
            side="right",
            padx=(0, 10),
        )

        ttk.Button(
            zone_bas,
            text="Corbeille",
            command=self.ouvrir_corbeille,
        ).pack(
            side="right",
            padx=(0, 10),
        )

        ttk.Button(
            zone_bas,
            text="Voir le détail",
            command=voir_detail,
        ).pack(
            side="right",
            padx=(0, 10),
        )

        charger_factures()
        champ_recherche.focus_set()

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