"""Génère un document Word DOCX fictif pour la démonstration."""

from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile


def creer_word_demo() -> Path:
    """Crée une facture Word fictive sans donnée réelle."""
    chemin_sortie = Path("data/documents/facture_word_demo.docx")
    chemin_sortie.parent.mkdir(parents=True, exist_ok=True)

    types_contenu = """<?xml version="1.0" encoding="UTF-8"?>
    <Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
        <Default Extension="rels"
                 ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
        <Default Extension="xml" ContentType="application/xml"/>
        <Override PartName="/word/document.xml"
                  ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>
    </Types>
    """

    relations = """<?xml version="1.0" encoding="UTF-8"?>
    <Relationships
        xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
        <Relationship
            Id="rId1"
            Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument"
            Target="word/document.xml"/>
    </Relationships>
    """

    document_xml = """<?xml version="1.0" encoding="UTF-8"?>
    <w:document
        xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
        <w:body>
            <w:p><w:r><w:t>FACTURE WORD FICTIVE</w:t></w:r></w:p>
            <w:p><w:r><w:t>Numero : WORD-2026-001</w:t></w:r></w:p>
            <w:p><w:r><w:t>Date : 2026-08-30</w:t></w:r></w:p>
            <w:p><w:r><w:t>Fournisseur : Entreprise Word Exemple Inc.</w:t></w:r></w:p>
            <w:p><w:r><w:t>Client : Client Word Fictif Inc.</w:t></w:r></w:p>
            <w:p><w:r><w:t>Sous-total : 2000.00 CAD</w:t></w:r></w:p>
            <w:p><w:r><w:t>TPS : 100.00 CAD</w:t></w:r></w:p>
            <w:p><w:r><w:t>TVQ : 199.50 CAD</w:t></w:r></w:p>
            <w:p><w:r><w:t>Total : 2299.50 CAD</w:t></w:r></w:p>
        </w:body>
    </w:document>
    """

    with ZipFile(chemin_sortie, "w", ZIP_DEFLATED) as archive:
        archive.writestr("[Content_Types].xml", types_contenu)
        archive.writestr("_rels/.rels", relations)
        archive.writestr("word/document.xml", document_xml)

    return chemin_sortie


if __name__ == "__main__":
    chemin = creer_word_demo()
    print(f"Facture Word fictive créée : {chemin}")