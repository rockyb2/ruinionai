from __future__ import annotations
import os
import json
from pathlib import Path
from docx import Document
from docx.shared import Pt, Inches, Cm, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_ALIGN_VERTICAL
from docx.oxml.ns import qn
from docx.oxml import OxmlElement
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    Image,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)
from xml.sax.saxutils import escape
import json
from smolagents import Tool


def get_reports_dir() -> Path:
    reports_dir = Path(os.getenv("REPORTS_DIR", "/app/storage/reports"))
    reports_dir.mkdir(parents=True, exist_ok=True)
    return reports_dir


class BuildWord(Tool):
    name = "BuildWord"
    description = (
        "Crée un document Word professionnel (.docx) avec support avancé des tableaux. "
        "Peut générer des lettres, CV, rapports avec tableaux simples ou complexes. "
        "Supporte la fusion de cellules, styles personnalisés, et mise en page avancée."
    )

    inputs = {
        "title": {"type": "string", "description": "Titre principal du document"},
        "recipient": {
            "type": "string",
            "description": "Destinataire (optionnel, multiligne)",
            "nullable": True,
        },
        "sender": {
            "type": "string",
            "description": "Expéditeur (optionnel, multiligne)",
            "nullable": True,
        },
        "date": {"type": "string", "description": "Date (optionnel)", "nullable": True},
        "subject": {
            "type": "string",
            "description": "Objet (optionnel)",
            "nullable": True,
        },
        "body": {
            "type": "string",
            "description": "Corps du document. Supporte :\\n- Paragraphes (séparés par \\n\\n)\\n- Listes (lignes commençant par '- ')\\n- Tableaux (JSON: [TABLE]json_data[/TABLE])",
            "nullable": True,
        },
        "tables": {
            "type": "string",
            "description": "JSON array de tableaux complexes (optionnel). Format: [{headers:[...], rows:[[...]], merge_cells:[...], styles:{...}}]",
            "nullable": True,
        },
        "filename": {
            "type": "string",
            "description": "Nom du fichier sans extension,",
            "nullable": True,
        },
        "style_config": {
            "type": "string",
            "description": "JSON de config style (optionnel): {font:'Arial', font_size:11, margins:2.5, line_spacing:1.15}",
            "nullable": True,
        },
    }

    output_type = "string"

    def _set_cell_border(self, cell, **kwargs):
        """Ajoute des bordures personnalisées à une cellule"""
        tc = cell._tc
        tcPr = tc.get_or_add_tcPr()
        tcBorders = OxmlElement("w:tcBorders")

        for edge in ("top", "left", "bottom", "right"):
            if edge in kwargs:
                edge_data = kwargs[edge]
                edge_el = OxmlElement(f"w:{edge}")
                edge_el.set(qn("w:val"), edge_data.get("val", "single"))
                edge_el.set(qn("w:sz"), str(edge_data.get("sz", 4)))
                edge_el.set(qn("w:space"), str(edge_data.get("space", 0)))
                edge_el.set(qn("w:color"), edge_data.get("color", "000000"))
                tcBorders.append(edge_el)

        tcPr.append(tcBorders)

    def _apply_cell_style(self, cell, style_config):
        """Applique un style à une cellule"""
        if "background" in style_config:
            shading_elm = OxmlElement("w:shd")
            shading_elm.set(qn("w:fill"), style_config["background"])
            cell._tc.get_or_add_tcPr().append(shading_elm)

        if (
            "bold" in style_config
            or "font_size" in style_config
            or "color" in style_config
        ):
            for paragraph in cell.paragraphs:
                for run in paragraph.runs:
                    if style_config.get("bold"):
                        run.font.bold = True
                    if "font_size" in style_config:
                        run.font.size = Pt(style_config["font_size"])
                    if "color" in style_config:
                        color = style_config["color"]
                        run.font.color.rgb = RGBColor(
                            int(color[0:2], 16),
                            int(color[2:4], 16),
                            int(color[4:6], 16),
                        )

        if "alignment" in style_config:
            for paragraph in cell.paragraphs:
                alignment_map = {
                    "center": WD_ALIGN_PARAGRAPH.CENTER,
                    "right": WD_ALIGN_PARAGRAPH.RIGHT,
                    "left": WD_ALIGN_PARAGRAPH.LEFT,
                    "justify": WD_ALIGN_PARAGRAPH.JUSTIFY,
                }
                paragraph.alignment = alignment_map.get(
                    style_config["alignment"], WD_ALIGN_PARAGRAPH.LEFT
                )

        if "vertical_alignment" in style_config:
            valign_map = {
                "center": WD_ALIGN_VERTICAL.CENTER,
                "top": WD_ALIGN_VERTICAL.TOP,
                "bottom": WD_ALIGN_VERTICAL.BOTTOM,
            }
            cell.vertical_alignment = valign_map.get(
                style_config["vertical_alignment"], WD_ALIGN_VERTICAL.TOP
            )

    def _create_table(self, doc, table_config):
        """Crée un tableau avec configuration avancée"""
        headers = table_config.get("headers", [])
        rows = table_config.get("rows", [])
        merge_cells = table_config.get("merge_cells", [])
        styles = table_config.get("styles", {})

        # Créer le tableau
        num_cols = len(headers) if headers else (len(rows[0]) if rows else 1)
        num_rows = len(rows) + (1 if headers else 0)
        table = doc.add_table(rows=num_rows, cols=num_cols)

        # Style général du tableau
        table.style = styles.get("table_style", "Light Grid Accent 1")
        table.alignment = WD_TABLE_ALIGNMENT.CENTER

        # En-têtes
        if headers:
            header_cells = table.rows[0].cells
            for i, header in enumerate(headers):
                header_cells[i].text = str(header)
                # Style header par défaut
                header_style = styles.get(
                    "header_style",
                    {
                        "bold": True,
                        "background": "D9E2F3",
                        "alignment": "center",
                        "vertical_alignment": "center",
                    },
                )
                self._apply_cell_style(header_cells[i], header_style)

        # Données
        start_row = 1 if headers else 0
        for i, row_data in enumerate(rows):
            row_cells = table.rows[start_row + i].cells
            for j, cell_data in enumerate(row_data):
                row_cells[j].text = str(cell_data)

                # Style des cellules de données
                if "cell_styles" in styles and f"{i},{j}" in styles["cell_styles"]:
                    self._apply_cell_style(
                        row_cells[j], styles["cell_styles"][f"{i},{j}"]
                    )
                elif "data_style" in styles:
                    self._apply_cell_style(row_cells[j], styles["data_style"])

        # Fusion de cellules
        for merge in merge_cells:
            start_row = merge.get("start_row", 0)
            start_col = merge.get("start_col", 0)
            end_row = merge.get("end_row", start_row)
            end_col = merge.get("end_col", start_col)

            if start_row != end_row or start_col != end_col:
                start_cell = table.rows[start_row].cells[start_col]
                end_cell = table.rows[end_row].cells[end_col]
                start_cell.merge(end_cell)

        # Largeur des colonnes
        if "column_widths" in styles:
            for i, width in enumerate(styles["column_widths"]):
                for row in table.rows:
                    row.cells[i].width = Inches(width)

        return table

    def _parse_body_with_tables(self, doc, body_text):
        """Parse le corps du texte et insère les tableaux inline"""
        import re

        # Chercher les tableaux dans le texte
        table_pattern = r"\[TABLE\](.*?)\[/TABLE\]"
        parts = re.split(table_pattern, body_text, flags=re.DOTALL)

        for i, part in enumerate(parts):
            if i % 2 == 0:  # Texte normal
                self._add_text_content(doc, part)
            else:  # Tableau JSON
                try:
                    table_config = json.loads(part.strip())
                    self._create_table(doc, table_config)
                except json.JSONDecodeError as e:
                    doc.add_paragraph(f"[Erreur tableau: {str(e)}]")

    def _add_text_content(self, doc, text):
        """Ajoute du contenu texte (paragraphes et listes)"""
        if not text.strip():
            return

        paragraphs = text.split("\n\n")
        for para_text in paragraphs:
            para_text = para_text.strip()
            if not para_text:
                continue

            # Liste à puces
            if "- " in para_text and para_text.split("\n")[0].strip().startswith("- "):
                lines = para_text.split("\n")
                for line in lines:
                    line = line.strip()
                    if line.startswith("- "):
                        doc.add_paragraph(line[2:].strip(), style="List Bullet")
                    elif line:
                        doc.add_paragraph(line)
            else:
                doc.add_paragraph(para_text)

    def forward(
        self,
        title: str,
        recipient: str = "",
        sender: str = "",
        date: str = "",
        subject: str = "",
        body: str = "",
        tables: str = "",
        filename: str = "document",
        style_config: str = "",
    ):
        try:
            doc = Document()

            # === Configuration du style ===
            config = {}
            if style_config:
                try:
                    config = json.loads(style_config)
                except:
                    pass

            font_name = config.get("font", "Arial")
            font_size = config.get("font_size", 11)
            margins = config.get("margins", 2.5)
            line_spacing = config.get("line_spacing", 1.15)

            # Marges
            section = doc.sections[0]
            section.top_margin = Cm(margins)
            section.bottom_margin = Cm(margins)
            section.left_margin = Cm(margins)
            section.right_margin = Cm(margins)

            # Style global
            style = doc.styles["Normal"]
            style.font.name = font_name
            style.font.size = Pt(font_size)

            # Interligne
            paragraph_format = style.paragraph_format
            paragraph_format.line_spacing = line_spacing

            # === En-tête lettre (optionnel) ===
            if sender:
                p = doc.add_paragraph(sender)
                p.alignment = WD_ALIGN_PARAGRAPH.RIGHT

            if recipient:
                doc.add_paragraph(recipient)

            if date:
                doc.add_paragraph(date)

            if subject:
                p = doc.add_paragraph()
                p.add_run("Objet : ").bold = True
                p.add_run(subject)
                doc.add_paragraph()

            # === Titre ===
            if title:
                title_p = doc.add_paragraph(title)
                title_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
                title_run = title_p.runs[0]
                title_run.font.size = Pt(16)
                title_run.bold = True
                doc.add_paragraph()

            # === Corps avec tableaux inline ===
            if body:
                self._parse_body_with_tables(doc, body)

            # === Tableaux externes (en fin de document) ===
            if tables:
                try:
                    tables_array = json.loads(tables)
                    for table_config in tables_array:
                        doc.add_paragraph()
                        if "title" in table_config:
                            p = doc.add_paragraph(table_config["title"])
                            p.runs[0].bold = True
                        self._create_table(doc, table_config)
                        doc.add_paragraph()
                except json.JSONDecodeError:
                    pass

            # === Formule de politesse (si format lettre) ===
            if recipient and sender:
                doc.add_paragraph()
                doc.add_paragraph(
                    "Je vous prie d'agréer, Madame, Monsieur, l'expression de mes salutations distinguées."
                )
                doc.add_paragraph()
                doc.add_paragraph(sender.split("\n")[0])  # Premier ligne = nom

            # === Sauvegarde ===
            reports_dir = get_reports_dir()
            safe_filename = (
                "".join(
                    c for c in filename if c.isalnum() or c in (" ", "-", "_")
                ).rstrip()
                or "document"
            )
            file_path = reports_dir / f"{safe_filename}.docx"
            doc.save(file_path)

            abs_path = file_path.resolve()
            return f"Document Word créé avec succès : {abs_path}||{abs_path}"

        except Exception as e:
            return f"✗ Erreur lors de la création du document : {str(e)}"


class BuildPDF(Tool):
    name = "BuildPDF"
    description = (
        "Génère un PDF professionnel avec titre, contenu, marges et styles optimisés."
    )

    inputs = {
        "name": {"type": "string", "description": "Nom du fichier PDF sans extension"},
        "title": {"type": "string", "description": "Titre du PDF"},
        "content": {"type": "string", "description": "Texte du PDF"},
    }
    output_type = "string"

    def forward(self, name: str, title: str, content: str) -> str:
        try:
            safe_name = (
                "".join(
                    char
                    for char in str(name)
                    if char.isalnum() or char in (" ", "-", "_")
                ).strip()
                or "document"
            )
            reports_dir = get_reports_dir()

            file_path = reports_dir / f"{safe_name}.pdf"
            styles = getSampleStyleSheet()
            style_title = styles["Title"]
            style_body = styles["BodyText"]

            doc = SimpleDocTemplate(
                str(file_path),
                pagesize=A4,
                leftMargin=20,
                rightMargin=20,
                topMargin=20,
                bottomMargin=20
            )

            story = [
                Paragraph(escape(title), style_title),
                Spacer(1, 12),
                Paragraph(escape(content).replace("\n", "<br/>"), style_body),
            ]

            doc.build(story)
            

            return f"PDF '{file_path.name}' genere avec succes.||{file_path.resolve()}"

        except Exception as e:
            return f"Erreur PDF : {str(e)}"
