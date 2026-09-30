"""7A : RRQ salarié, douze mois, sans RPC ni cotisation facultative.

Sources : 5005-S8 F (25), partie 2, pages 3–5; TP-1.D.U (2025-12),
partie B, page 3. Les arrondis au cent sont la convention générale du moteur.
Les calculs Québec et fédéral restent distincts.
"""
from dataclasses import dataclass
from decimal import Decimal

from .tax_rules_2025 import arrondir_cent

ZERO = Decimal("0")


@dataclass(frozen=True)
class RrqSalarie2025:
    ligne_30800: Decimal
    ligne_22215: Decimal
    ligne_248: Decimal
    excedent: Decimal
    lignes_annexe_8: tuple[tuple[int, Decimal], ...]


def calculer_rrq_salarie_2025(ba: Decimal, bb: Decimal, gains: Decimal) -> RrqSalarie2025:
    """Montants réels agrégés 17/17A/26, profil standard confirmé ailleurs."""
    for montant in (ba, bb, gains):
        if not isinstance(montant, Decimal) or not montant.is_finite() or montant < ZERO:
            raise ValueError("RRQ salarié : montants Decimal finis et non négatifs requis.")
    l = {}
    l[1] = gains
    l[2] = min(gains, Decimal("81200"))
    l[3] = Decimal("71300")
    l[4] = max(l[2] - l[3], ZERO)
    l[5] = l[2] - l[4]
    l[6] = Decimal("3500")
    l[7] = max(l[5] - l[6], ZERO)
    l[8] = ba
    l[9] = arrondir_cent(ba * Decimal("0.84375"))
    l[10] = ba - l[9]
    l[11] = arrondir_cent(l[7] * Decimal("0.054"))
    l[12] = arrondir_cent(l[7] * Decimal("0.01"))
    l[13] = l[11] + l[12]
    l[14], l[15] = l[9], l[11]
    l[16] = l[14] - l[15]
    l[17], l[18] = l[10], l[12]
    l[19] = l[17] - l[18]
    l[20] = l[16] + l[19]
    l[21] = bb
    l[22] = arrondir_cent(l[4] * Decimal("0.04"))
    l[23] = l[21] - l[22]
    l[24] = l[20] + l[23]
    if l[24] > ZERO:
        l[25], l[26], l[27] = l[15], l[18], l[22]
        l[28] = l[26] + l[27]
        credit, deduction = l[25], l[28]
    else:
        l[29] = min(l[14], l[15])
        l[30] = max(-l[16], ZERO)
        l[31] = min(max(l[19], ZERO), l[30])
        l[32] = l[30] - l[31]
        l[33] = l[29] + l[31]
        l[34] = min(max(l[23], ZERO), l[32])
        l[35] = l[33] + l[34]
        l[36] = min(l[17], l[18])
        l[37] = max(-l[19], ZERO)
        l[38] = min(max(l[16], ZERO), l[37])
        l[39] = l[37] - l[38]
        l[40] = l[36] + l[38]
        l[41] = min(max(l[23] - l[34], ZERO), l[39])
        l[42] = l[40] + l[41]
        l[43] = min(l[21], l[22])
        l[44] = max(-l[23], ZERO)
        l[45] = min(max(l[20], ZERO), l[44])
        l[46] = l[43] + l[45]
        l[47] = l[42] + l[46]
        credit, deduction = l[35], l[47]
    # Annexe U B : lignes 10–16, 17–17.5, 18.5–23.
    u11 = arrondir_cent(min(ba, Decimal("4339.20")) * Decimal("0.156250"))
    u16 = min(u11, l[12])
    u175 = max(ba - arrondir_cent(l[7] * Decimal("0.064")), ZERO) + bb
    u23 = min(u175, l[22]) + u16
    return RrqSalarie2025(credit, deduction, arrondir_cent(u23),
                          max(l[24], ZERO), tuple(l.items()))


def lignes_employeurs_2025(base, source: str) -> tuple[str, ...]:
    if not base.feuillets_emploi:
        return ()
    r = calculer_rrq_salarie_2025(base.rrq_base_premiere_supplementaire,
        base.rrq_deuxieme_supplementaire, base.gains_admissibles_rrq)
    lignes = ["", "EMPLOYEURS MULTIPLES QUÉBEC — 7A", f"Source comptable / employeurs : {source}",
        "Résidence Québec toute l'année; RRQ standard 18–64 ans; sans RPC ni travail autonome.",
        "Feuillets originaux appariés par le comptable; provenance et montants réels conservés."]
    for doc, typ, valeurs in base.feuillets_emploi:
        lignes.append(f"Feuillet {typ} : {doc}")
        lignes.extend(f"  Case {case} : {montant:.2f} $" for case, montant in valeurs)
    lignes.extend([
        f"Agrégats T4 : case 17 = {base.rrq_base_premiere_supplementaire:.2f} $; "
        f"17A = {base.rrq_deuxieme_supplementaire:.2f} $; 26 = {base.gains_admissibles_rrq:.2f} $.",
        "Annexe 8 fédérale 2025, partie 2a/2b (sans cotisation facultative) :",
        f"Ligne 30800 — base admissible RRQ : {r.ligne_30800:.2f} $",
        f"Ligne 22215 — déduction fédérale : {r.ligne_22215:.2f} $",
        f"Annexe U 2025, partie B — déduction Québec 248 : {r.ligne_248:.2f} $",
        f"Excédent RRQ — Québec 452 : {r.excedent:.2f} $; aucun remboursement fédéral 44800.",
        "Arrondis : convention monétaire générale du moteur au cent.",
        "Exclus : RPC/RC381, cotisations facultatives, proratisation, dépenses T2200/T777 multi-employeurs.",
        "Détail annexe 8, partie 2 :",
        *(f"  Ligne {n} : {v:.2f} $" for n, v in r.lignes_annexe_8),
    ])
    return tuple(lignes)
