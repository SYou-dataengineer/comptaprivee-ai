"""Contrôle embarqué du prototype : uniquement profil fictif explicitement isolé."""
import json
import os
from pathlib import Path
import time


def run():
    try:
        _run()
    except Exception:
        # Trace détaillée réservée au profil marqué fictif, jamais au démarrage normal.
        from src.comptaprivee import app_paths
        if (os.environ.get('COMPTAPRIVEE_PROTOTYPE_CHECK') == '1'
                and (app_paths.user_data_dir() / 'prototype-only.marker').exists()):
            import traceback
            app_paths.logs_dir().mkdir(parents=True, exist_ok=True)
            (app_paths.logs_dir() / 'prototype-error.log').write_text(traceback.format_exc(), encoding='utf-8')
        raise


def _run():
    if os.environ.get('COMPTAPRIVEE_PROTOTYPE_CHECK') != '1':
        raise RuntimeError('Le contrôle nécessite un profil fictif explicitement isolé.')
    from src.comptaprivee import app_paths as paths
    root = paths.user_data_dir()
    marker = root / 'prototype-only.marker'
    if root.exists() and any(root.iterdir()) and not marker.exists():
        raise RuntimeError('Le profil existe déjà : contrôle refusé pour préserver les données.')
    root.mkdir(parents=True, exist_ok=True)
    marker.write_text('Profil exclusivement fictif POST-V1-C', encoding='utf-8')
    from decimal import Decimal as D
    import sys
    import shutil
    import subprocess
    import tempfile
    import fitz
    import docx
    import openpyxl
    import lxml.etree
    from PIL import Image
    import win32com.client
    import pythoncom
    import pywintypes
    from src.comptaprivee.gui import ApplicationComptaPrivee
    from src.comptaprivee.tax_field_validation import DonneeFiscaleValidee
    from src.comptaprivee.tax_validated_case import DossierFiscalValide
    from src.comptaprivee.tax_case_storage import sauvegarder_dossier_fiscal, charger_dossier_fiscal
    from src.comptaprivee.tax_estimation_2025 import calculer_estimation_fiscale_2025
    from src.comptaprivee.tax_report_pdf_2025 import exporter_rapport_fiscal_pdf_2025
    from src.comptaprivee.settings import ParametresApplication, enregistrer_parametres, lire_parametres
    from src.comptaprivee.database import initialiser_base
    from src.comptaprivee.backup_manager import creer_sauvegarde, restaurer_sauvegarde
    from src.comptaprivee.csv_exporter import exporter_facture_csv
    from src.comptaprivee.facture_parser import DonneesFacture
    from src.comptaprivee.pdf_extractor import extraire_texte_pdf
    from src.comptaprivee.ocr_extractor import extraire_texte_image
    from src.comptaprivee.tax_case import annees_fiscales_disponibles

    started = time.perf_counter()
    app = ApplicationComptaPrivee()
    try:
        app.withdraw()
        app.ouvrir_agent_fiscal()
        app.update()
        gui_seconds = time.perf_counter() - started
        assert annees_fiscales_disponibles() == (2025,)
        initialiser_base()
        settings = ParametresApplication(devise='CAD')
        enregistrer_parametres(settings)
        assert lire_parametres() == settings
        exports = paths.exports_dir(); exports.mkdir(parents=True, exist_ok=True)
        # Vrais PDF synthétiques, aucune pièce provenant de tests ou de clients.
        for name in ('T4 fictif.pdf', 'RL1 fictif.pdf'):
            with fitz.open() as pdf:
                page = pdf.new_page()
                page.insert_text((50,70), 'DOCUMENT FICTIF POST V1 C - 2025')
                pdf.save(exports / name)
        valeurs = []
        for typ, name, cases in (
            ('T4','T4 fictif.pdf', {'14':'52000','17':'3104','18':'681.20','22':'7500',
                                   '24':'52000','26':'52000','55':'256.88','56':'52000'}),
            ('RL-1','RL1 fictif.pdf', {'A':'52000','B.A':'3104','C':'681.20','E':'6200',
                                      'G':'52000','H':'256.88','I':'52000'})):
            for case, montant in cases.items():
                valeurs.append(DonneeFiscaleValidee(exports/name, typ, case, case,
                    D(montant), D(montant), False, 'Validé par le comptable'))
        saved = paths.tax_cases_dir() / 'prototype-fictif.json'
        previous_id = charger_dossier_fiscal(saved).dossier.case_id if saved.exists() else None
        kw = {'case_id':previous_id} if previous_id else {}
        dossier = DossierFiscalValide('Client fictif prototype',2025,'Québec',
            tuple(exports / n for n in ('T4 fictif.pdf','RL1 fictif.pdf')), tuple(valeurs), **kw)
        estimation = calculer_estimation_fiscale_2025(dossier)
        sauvegarder_dossier_fiscal(dossier, destination=saved)
        assert charger_dossier_fiscal(saved).dossier.case_id == dossier.case_id
        app.dossier_fiscal_courant = dossier
        app.dossier_fiscal_valide_courant = charger_dossier_fiscal(saved).dossier
        report = exporter_rapport_fiscal_pdf_2025(estimation, exports/'rapport fictif.pdf')
        with fitz.open(report) as pdf:
            texte = '\n'.join(page.get_text() for page in pdf)
            assert 'Client fictif prototype' in texte
            assert '5 611,05' in texte.replace('\xa0',' ')
        csv = exporter_facture_csv(DonneesFacture('FICTIF',None,'Exemple fictif',None,
                                  D('12.50'),None,None,D('12.50')),exports/'fictif.csv')
        assert csv.exists()
        docx.Document().save(exports/'fictif.docx')  # template natif python-docx
        wb = openpyxl.Workbook(); wb.save(exports/'fictif.xlsx'); wb.close()
        from src.comptaprivee.document_converter import word_vers_pdf, excel_vers_pdf, ErreurConversion
        dispatch = win32com.client.DispatchEx
        def absent(*args, **kwargs): raise RuntimeError('Office absent simulé')
        win32com.client.DispatchEx = absent
        try:
            for conversion, source, produit in ((word_vers_pdf, exports/'fictif.docx', 'Word'),
                                                 (excel_vers_pdf, exports/'fictif.xlsx', 'Excel')):
                try: conversion(source, exports / ('office-' + produit + '.pdf'))
                except ErreurConversion as exc: assert 'Microsoft ' + produit + ' installé' in str(exc)
                else: raise AssertionError('Absence Office non signalée')
        finally:
            win32com.client.DispatchEx = dispatch
        original = saved.read_bytes()
        archive = creer_sauvegarde(root/'prototype.zip')
        restaurer_sauvegarde(archive)
        assert saved.read_bytes() == original
        assert 'DOCUMENT FICTIF' in extraire_texte_pdf(exports/'T4 fictif.pdf')
        with tempfile.TemporaryDirectory(dir=paths.temp_dir()) as td:
            image = Path(td)/'ocr fictif.png'
            with fitz.open() as pdf:
                p=pdf.new_page();p.insert_text((50,100),'FACTURE FICTIVE TOTAL 123.45',fontsize=22)
                p.get_pixmap(dpi=180).save(image)
            with Image.open(image) as im: assert im.width > 0
            tess = shutil.which('tesseract')
            ocr = 'absent_message_clair'
            if tess:
                langues=subprocess.run([tess,'--list-langs'],capture_output=True,text=True,check=True).stdout
                assert 'fra' in langues and 'eng' in langues
                assert '123.45' in extraire_texte_image(image)
                ocr='fra+eng_OK'
            else:
                try: extraire_texte_image(image)
                except RuntimeError as exc: assert 'introuvable' in str(exc)
                else: raise AssertionError('Absence OCR non signalée')
        result = dict(ok=True, frozen=bool(getattr(sys,'frozen',False)),
                      executable=sys.executable, prefix=sys.prefix,
                      resource_dir=str(paths.RESOURCE_DIR), resource_exists=paths.resource_path('.').is_dir(),
                      user_data_dir=str(root), gui_seconds=round(gui_seconds,3),
                      persisted_from_previous_run=previous_id is not None,
                      case_id=dossier.case_id, ocr=ocr, office_started=False,
                      office_absence_simulated=True,
                      modules={m.__name__:str(m.__file__) for m in (fitz, docx, openpyxl, lxml.etree, Image, pythoncom, pywintypes)})
        paths.logs_dir().mkdir(parents=True,exist_ok=True)
        (paths.logs_dir()/'prototype-check.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
    finally:
        app.destroy()
