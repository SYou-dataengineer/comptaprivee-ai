"""Composants locaux pour les formulaires fiscaux redimensionnables."""

import tkinter as tk
from tkinter import ttk


def organiser_boutons(cadre):
    """Répartit les boutons sur autant de lignes que la largeur l'exige."""
    boutons = cadre.winfo_children()
    for bouton in boutons:
        bouton.pack_forget()
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
