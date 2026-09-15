"""Composants locaux pour les formulaires fiscaux redimensionnables."""

import tkinter as tk
from tkinter import font as tkfont
from tkinter import ttk


def organiser_boutons(cadre):
    """Répartit les boutons sur autant de lignes que la largeur l'exige."""
    boutons = [w for w in cadre.winfo_children() if isinstance(w, (ttk.Button, ttk.Menubutton))]
    autres = [w for w in cadre.winfo_children() if w not in boutons]
    for widget in autres:
        widget.pack_forget()
        widget.grid_forget()
    for bouton in boutons:
        bouton.pack_forget()
        bouton.grid_forget()
        bouton.configure(padding=(10, 6))

    def repartir(event=None):
        largeur = max((b.winfo_reqwidth() for b in boutons), default=1) + 12
        padding = cadre.tk.splitlist(cadre.cget("padding"))
        marge = 2 * int(padding[0]) if padding else 0
        colonnes = min(len(boutons), max(1, (cadre.winfo_width() - marge) // largeur))
        for colonne in range(len(boutons)):
            cadre.columnconfigure(colonne, weight=0, minsize=0, uniform="")
        for colonne in range(colonnes):
            cadre.columnconfigure(colonne, weight=1, uniform="actions")
        for index, bouton in enumerate(boutons):
            bouton.grid(row=index // colonnes, column=index % colonnes,
                        sticky="ew", padx=6, pady=4)
        for index, widget in enumerate(autres):
            if isinstance(widget, ttk.Label):
                widget.configure(wraplength=max(80, cadre.winfo_width() - marge - 12))
            widget.grid(row=(len(boutons) + max(1, colonnes) - 1) // max(1, colonnes) + index,
                        column=0, columnspan=max(1, colonnes), sticky="ew", padx=6)

    cadre.bind("<Configure>", repartir, add="+")
    cadre.after_idle(repartir)


def dimensions_fenetre(largeur, hauteur, ecran_largeur, ecran_hauteur):
    """Réserve une marge pour les bordures et la barre des tâches."""
    if min(largeur, hauteur, ecran_largeur, ecran_hauteur) <= 0:
        raise ValueError("Les dimensions doivent être positives")
    return min(largeur, max(1, ecran_largeur - 48)), min(
        hauteur, max(1, ecran_hauteur - 100)
    )


def dimensionner_fenetre(fenetre, largeur=820, hauteur=700):
    largeur, hauteur = dimensions_fenetre(
        largeur, hauteur, fenetre.winfo_screenwidth(), fenetre.winfo_screenheight()
    )
    fenetre.geometry(f"{largeur}x{hauteur}")
    fenetre.minsize(min(600, largeur), min(360, hauteur))
    fenetre.resizable(True, True)


class FormulaireDefilant(ttk.Frame):
    """Corps défilable avec barre d'actions indépendante toujours visible."""

    def __init__(self, parent):
        super().__init__(parent)
        self.pack(fill="both", expand=True)
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)
        self.canvas = tk.Canvas(self, highlightthickness=0)
        self.canvas.grid(row=0, column=0, sticky="nsew")
        barre = ttk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        barre.grid(row=0, column=1, sticky="ns")
        self.canvas.configure(yscrollcommand=barre.set)
        self.corps = ttk.Frame(self.canvas, padding=16)
        self._item = self.canvas.create_window(0, 0, window=self.corps, anchor="nw")
        self.actions = ttk.Frame(self, padding=(16, 8))
        self.actions.grid(row=1, column=0, columnspan=2, sticky="ew")
        self.corps.bind("<Configure>", self._actualiser)
        self.canvas.bind("<Configure>", self._redimensionner)
        # Le binding appartient à cette fenêtre et ne remplace aucun bind_all.
        self._fenetre = self.winfo_toplevel()
        self._molette = self._fenetre.bind("<MouseWheel>", self._defiler, add="+")
        self._focus = self._fenetre.bind("<FocusIn>", self._montrer_focus, add="+")
        self.bind("<Destroy>", self._nettoyer)

    def _actualiser(self, event=None):
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def _redimensionner(self, event):
        self.canvas.itemconfigure(self._item, width=event.width)
        for widget in self.corps.winfo_children():
            if isinstance(widget, (ttk.Label, tk.Checkbutton)):
                largeur = event.width - 40
                if widget.winfo_manager() == "grid" and int(
                    widget.grid_info().get("columnspan", 1)
                ) == 1:
                    largeur //= 2
                widget.configure(wraplength=max(80, largeur))

    def _defiler(self, event):
        # Les listes et les textes conservent leur propre défilement.
        if isinstance(getattr(event, "widget", None), (tk.Text, ttk.Treeview, ttk.Combobox)):
            return
        if self.canvas.yview() != (0.0, 1.0):
            self.canvas.yview_scroll(-1 if event.delta > 0 else 1, "units")

    def _montrer_focus(self, event):
        widget = event.widget
        if not str(widget).startswith(str(self.corps) + "."):
            return
        haut = widget.winfo_rooty() - self.canvas.winfo_rooty()
        bas = haut + widget.winfo_height()
        if haut < 0 or bas > self.canvas.winfo_height():
            position = self.canvas.canvasy(0) + haut
            self.canvas.yview_moveto(position / max(1, self.corps.winfo_height()))

    def _nettoyer(self, event):
        if event.widget is self:
            self._fenetre.unbind("<MouseWheel>", self._molette)
            self._fenetre.unbind("<FocusIn>", self._focus)


def repartir_controles(cadre):
    """Dispose une barre de filtres en cellules, dans l'ordre de lecture."""
    enfants = [w for w in cadre.winfo_children() if w.winfo_manager() in ("pack", "grid")]
    if not enfants:
        return
    if all(w.winfo_manager() == "grid" for w in enfants):
        enfants.sort(key=lambda w: (int(w.grid_info()["row"]), int(w.grid_info()["column"])))
    for enfant in enfants:
        enfant.pack_forget()
        enfant.grid_forget()
        if isinstance(enfant, (ttk.Button, ttk.Menubutton)):
            enfant.configure(padding=(10, 6))
    colonnes_precedentes = cadre.grid_size()[0]

    def placer(event=None):
        nonlocal colonnes_precedentes
        largeur = max(1, cadre.winfo_width() - 40)
        cellule = max(140, min(240, max(w.winfo_reqwidth() for w in enfants)))
        colonnes = max(1, min(len(enfants), largeur // (cellule + 12)))
        if colonnes > 1 and any(isinstance(w, (ttk.Entry, ttk.Combobox)) for w in enfants):
            colonnes -= colonnes % 2
        for col in range(max(colonnes_precedentes, colonnes)):
            cadre.columnconfigure(col, weight=0, minsize=0, uniform="")
        for col in range(colonnes):
            cadre.columnconfigure(col, weight=1, uniform="controles")
        colonnes_precedentes = colonnes
        if any(isinstance(w, (ttk.Entry, ttk.Combobox)) for w in enfants):
            # Les libellés restent associés à leur champ, même lorsqu'un
            # compteur ou un groupe de boutons interrompt la barre de filtres.
            for col in range(colonnes):
                cadre.columnconfigure(col, weight=0, uniform="")
            cadre.columnconfigure(0, weight=1, uniform="champs")
            cadre.columnconfigure(1, weight=1, uniform="champs")
            colonnes_precedentes = max(colonnes, 2)
            ligne = index = 0
            while index < len(enfants):
                enfant = enfants[index]
                suivant = enfants[index + 1] if index + 1 < len(enfants) else None
                if isinstance(enfant, ttk.Label) and isinstance(suivant, (ttk.Entry, ttk.Combobox)):
                    enfant.configure(wraplength=max(80, largeur // 2 - 12))
                    enfant.grid(row=ligne, column=0, sticky="w", padx=6, pady=4)
                    suivant.grid(row=ligne, column=1, sticky="ew", padx=6, pady=4)
                    index += 2
                else:
                    if isinstance(enfant, ttk.Label):
                        enfant.configure(wraplength=max(80, largeur - 12))
                    enfant.grid(row=ligne, column=0, columnspan=2, sticky="ew", padx=6, pady=4)
                    index += 1
                ligne += 1
            return
        for index, enfant in enumerate(enfants):
            if isinstance(enfant, ttk.Label):
                enfant.configure(wraplength=max(80, largeur // colonnes - 12))
            enfant.grid(row=index // colonnes, column=index % colonnes,
                        sticky="ew", padx=6, pady=4)

    cadre.bind("<Configure>", placer, add="+")
    cadre.after_idle(placer)


class EcranResponsive(FormulaireDefilant):
    """Écran de consultation : contenu défilable et commandes fixes."""

    def finaliser(self):
        """Adapte les groupes après la construction de tous leurs composants."""
        controles = (ttk.Label, ttk.Button, ttk.Menubutton, ttk.Entry,
                     ttk.Combobox, ttk.Checkbutton, tk.Checkbutton)

        def parcourir(parent):
            enfants = parent.winfo_children()
            for enfant in enfants:
                if isinstance(enfant, ttk.Treeview):
                    self._adapter_table(enfant)
                if isinstance(enfant, tk.Canvas) and parent is self.corps:
                    self._adapter_graphique(enfant)
                if isinstance(enfant, tk.Text):
                    enfant.configure(width=40, height=12)
                if isinstance(enfant, (ttk.Frame, ttk.LabelFrame, ttk.Notebook, ttk.Panedwindow)):
                    parcourir(enfant)
            visibles = [w for w in enfants if w.winfo_manager() in ("pack", "grid")]
            if visibles and all(isinstance(w, controles + (ttk.Frame, ttk.LabelFrame)) for w in visibles):
                horizontaux = any(w.winfo_manager() == "pack" and
                                  w.pack_info()["side"] in ("left", "right") for w in visibles)
                colonnes = max((int(w.grid_info().get("column", 0))
                                for w in visibles if w.winfo_manager() == "grid"), default=0)
                if (horizontaux and all(isinstance(w, controles) for w in visibles)) or colonnes > 1:
                    repartir_controles(parent)
            # Les panneaux liste/détails sont empilés : chacun conserve sa largeur.
            panneaux = [w for w in visibles if isinstance(w, ttk.Frame) and
                        w.winfo_manager() == "pack" and
                        w.pack_info()["side"] in ("left", "right")]
            for panneau in panneaux:
                panneau.pack_configure(side="top", fill="both", expand=True)
            for enfant in visibles:
                if isinstance(enfant, ttk.Label):
                    def envelopper(event, widget=enfant):
                        if widget.winfo_exists():
                            widget.configure(wraplength=max(80, event.width - 40))
                    parent.bind("<Configure>", envelopper, add="+")

        parcourir(self.corps)
        organiser_boutons(self.actions)

    @staticmethod
    def _adapter_graphique(toile):
        """Garde les annotations accessibles quand le graphique dépasse la vue."""
        toile.configure(height=360)
        barre = ttk.Scrollbar(toile.master, orient="horizontal", command=toile.xview)
        barre.pack(fill="x", after=toile)
        toile.configure(xscrollcommand=barre.set)

        def actualiser(event=None):
            toile.configure(scrollregion=toile.bbox("all"))

        toile.bind("<Configure>", actualiser, add="+")

    @staticmethod
    def _adapter_table(table):
        table.configure(height=8)
        police = tkfont.nametofont("TkHeadingFont", root=table)
        for colonne in table.cget("columns"):
            minimum = police.measure(table.heading(colonne, "text")) + 24
            table.column(colonne, width=max(minimum, table.column(colonne, "width")),
                         minwidth=minimum, stretch=False)
        parent = table.master
        if not table.cget("xscrollcommand"):
            barre = ttk.Scrollbar(parent, orient="horizontal", command=table.xview)
            table.configure(xscrollcommand=barre.set)
            if table.winfo_manager() == "grid":
                info = table.grid_info()
                barre.grid(row=int(info["row"]) + 1, column=int(info["column"]), sticky="ew")
            else:
                barre.pack(side="bottom", fill="x", before=table)
        if not table.cget("yscrollcommand"):
            barre = ttk.Scrollbar(parent, orient="vertical", command=table.yview)
            table.configure(yscrollcommand=barre.set)
            if table.winfo_manager() == "grid":
                info = table.grid_info()
                barre.grid(row=int(info["row"]), column=int(info["column"]) + 1, sticky="ns")
            else:
                barre.pack(side="right", fill="y", before=table)
