from flask import Flask, request, render_template, send_file
from scraper.linkedin_scraper import scrape_profile_and_company
from scraper.gpt import get_gpt_insights
from dotenv import load_dotenv
from io import BytesIO
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, ListFlowable, ListItem, Table, TableStyle
from reportlab.lib.enums import TA_LEFT
from reportlab.lib import colors
from reportlab.lib.units import inch
import os
import re
import json

load_dotenv()
app = Flask(__name__)

@app.route("/", methods=["GET"])
def home():
    return render_template("index.html")

@app.route("/generate", methods=["POST"])
def generate():
    email = request.form.get("email")
    password = request.form.get("password")
    profile_url = request.form.get("profile")
    company_url = request.form.get("company")

    if not all([email, password, profile_url]):
        return render_template("index.html", error="Preencha os campos obrigatórios.")

    try:
        result = scrape_profile_and_company(email, password, profile_url, company_url)

        if isinstance(result, tuple) and len(result) == 3:
            profile_text, nome_pessoa, nome_empresa = result
        else:
            raise Exception("A função scrape_profile_and_company não retornou exatamente três valores.")

        nome_pessoa = nome_pessoa or "Pessoa"
        nome_empresa = nome_empresa or "Não informada"

        raw_insights = get_gpt_insights(profile_text, model="gpt-4o")
        insights = format_insights(raw_insights)

        if not insights:
            return render_template("index.html", error="Não foi possível gerar insights estruturados. Verifique o conteúdo ou tente novamente.")

        return render_template("index.html", insights=insights, nome_pessoa=nome_pessoa, nome_empresa=nome_empresa)
    except Exception as e:
        return render_template("index.html", error=str(e))

@app.route("/baixar-pdf", methods=["POST"])
def baixar_pdf():
    data = json.loads(request.form.get("data"))
    pdf_buffer = gerar_pdf(data)
    nome = request.form.get("nome", "Pessoa").strip() or "Pessoa"
    nome_formatado = re.sub(r'[^a-zA-Z0-9_-]', '_', nome)
    return send_file(pdf_buffer, as_attachment=True, download_name=f"insights_{nome_formatado}.pdf", mimetype='application/pdf')

def format_insights(text: str):
    sections = []
    current_title = ""
    current_body = []

    for line in text.splitlines():
        line = line.strip()

        if line and any(line.startswith(f"{i}.") for i in range(1, 10)):
            if current_title:
                sections.append((current_title, current_body))
                current_body = []
            current_title = line[line.find('.') + 1:].strip(" *")
        elif line:
            line = re.sub(r"\\*\\*(.*?)\\*\\*", r"<strong>\\1</strong>", line)
            line = re.sub(r"^\\\\1[:\\s]*", "", line)  # remove '\1' ou '\1: '
            current_body.append(line)

    if current_title:
        sections.append((current_title, current_body))

    return sections

def gerar_pdf(insights):
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, leftMargin=50, rightMargin=50, topMargin=72, bottomMargin=72)
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name='InsightTitle', fontName='Helvetica-Bold', fontSize=13, textColor=colors.HexColor("#0d47a1"), spaceAfter=6))
    styles.add(ParagraphStyle(name='InsightBody', fontName='Helvetica', fontSize=10.5, textColor=colors.black, spaceAfter=4, leftIndent=10))

    content = []

    for titulo, corpo in insights:
        box_content = []
        box_content.append(Paragraph(titulo, styles['InsightTitle']))
        bullets = []
        for linha in corpo:
            clean_text = re.sub(r"<[^>]+>", "", linha)
            if clean_text.startswith("- "):
                bullets.append(ListItem(Paragraph(clean_text[2:], styles['InsightBody'])))
            else:
                if bullets:
                    box_content.append(ListFlowable(bullets, bulletType='bullet', leftIndent=15))
                    bullets = []
                box_content.append(Paragraph(clean_text, styles['InsightBody']))
        if bullets:
            box_content.append(ListFlowable(bullets, bulletType='bullet', leftIndent=15))

        box_table = Table([[box_content]], colWidths=[doc.width])
        box_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#e3f2fd")),
            ('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor("#1565c0")),
            ('LEFTPADDING', (0, 0), (-1, -1), 12),
            ('RIGHTPADDING', (0, 0), (-1, -1), 12),
            ('TOPPADDING', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
        ]))
        content.append(box_table)
        content.append(Spacer(1, 0.3 * inch))

    doc.build(content)
    buffer.seek(0)
    return buffer

if __name__ == "__main__":
    app.run(debug=True)