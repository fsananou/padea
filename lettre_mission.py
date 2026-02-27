#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Générateur de Lettres de Mission
Génère un PDF professionnel à partir de paramètres saisis en ligne de commande.
"""

import os
import sys
from datetime import datetime

try:
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import cm
    from reportlab.lib import colors
    from reportlab.platypus import (
        SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
        HRFlowable, KeepTogether
    )
    from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT, TA_JUSTIFY
except ImportError:
    print("\n[ERREUR] La librairie 'reportlab' n'est pas installée.")
    print("  Lancez : pip install reportlab")
    input("\nAppuyez sur Entrée pour quitter...")
    sys.exit(1)

# ─────────────────────────────────────────────────────────────────────────────
# Couleurs et styles
# ─────────────────────────────────────────────────────────────────────────────

PRIMARY     = colors.HexColor("#1a3a5c")   # Bleu marine
SECONDARY   = colors.HexColor("#2e86ab")   # Bleu clair
ACCENT      = colors.HexColor("#e8f4fd")   # Bleu très clair (fond)
LIGHT_GRAY  = colors.HexColor("#f5f5f5")
TEXT_DARK   = colors.HexColor("#222222")
TEXT_MEDIUM = colors.HexColor("#555555")
TEXT_LIGHT  = colors.HexColor("#888888")
WHITE       = colors.white

# ─────────────────────────────────────────────────────────────────────────────
# Interface terminal
# ─────────────────────────────────────────────────────────────────────────────

def cls():
    os.system("cls" if os.name == "nt" else "clear")

def banner():
    print()
    print("  ╔══════════════════════════════════════════════════════════╗")
    print("  ║         GÉNÉRATEUR DE LETTRES DE MISSION                 ║")
    print("  ║                 Sortie : PDF professionnel               ║")
    print("  ╚══════════════════════════════════════════════════════════╝")
    print()

def section_header(titre):
    print()
    print(f"  ┌─ {titre} {'─' * max(0, 52 - len(titre))}┐")

def ask(question, default=None, required=True):
    """Pose une question et retourne la réponse."""
    if default:
        prompt = f"  │  {question} [{default}] : "
    else:
        prompt = f"  │  {question} : "
    while True:
        try:
            rep = input(prompt).strip()
        except (KeyboardInterrupt, EOFError):
            print("\n\n  Annulé.")
            sys.exit(0)
        if rep:
            return rep
        if default is not None:
            return default
        if not required:
            return ""
        print("  │  ⚠  Ce champ est requis.")

def ask_liste(label_item, min_items=0):
    """Saisie d'une liste (un item par ligne, ligne vide pour terminer)."""
    items = []
    i = 1
    while True:
        val = input(f"  │    {label_item} {i} (vide pour terminer) : ").strip()
        if not val:
            if len(items) >= min_items:
                break
            print(f"  │  ⚠  Saisissez au moins {min_items} élément(s).")
            continue
        items.append(val)
        i += 1
    return items

def ask_yesno(question, default="oui"):
    rep = ask(question, default=default, required=False).lower()
    return rep in ("o", "oui", "y", "yes", "1")

# ─────────────────────────────────────────────────────────────────────────────
# Collecte des données
# ─────────────────────────────────────────────────────────────────────────────

def collect_data():
    cls()
    banner()
    data = {}

    # ── Prestataire ──────────────────────────────────────────────────────────
    section_header("PRESTATAIRE  (vous / votre cabinet)")
    data["presta_nom"]      = ask("Nom / Raison sociale")
    data["presta_adresse"]  = ask("Adresse (rue)")
    data["presta_cp"]       = ask("Code postal")
    data["presta_ville"]    = ask("Ville")
    data["presta_tel"]      = ask("Téléphone", required=False)
    data["presta_email"]    = ask("Email",      required=False)
    data["presta_siret"]    = ask("SIRET",      required=False)
    data["presta_tva"]      = ask("N° TVA intracommunautaire", required=False)

    # ── Client ───────────────────────────────────────────────────────────────
    section_header("CLIENT")
    data["client_societe"]  = ask("Raison sociale")
    data["client_contact"]  = ask("Nom du contact / responsable")
    data["client_adresse"]  = ask("Adresse (rue)")
    data["client_cp"]       = ask("Code postal")
    data["client_ville"]    = ask("Ville")

    # ── Mission ──────────────────────────────────────────────────────────────
    section_header("MISSION")
    data["mission_titre"]   = ask("Intitulé de la mission")
    data["mission_contexte"]= ask("Contexte / présentation rapide de la mission", required=False)
    data["mission_lieu"]    = ask("Lieu d'exécution", default=data["client_ville"])
    data["mission_debut"]   = ask("Date de début  (ex : 1er mars 2026)")
    data["mission_fin"]     = ask("Date de fin    (ex : 30 juin 2026)")

    # ── Objectifs ────────────────────────────────────────────────────────────
    section_header("OBJECTIFS  (un par ligne, ligne vide pour terminer)")
    data["objectifs"] = ask_liste("Objectif", min_items=1)

    # ── Livrables ────────────────────────────────────────────────────────────
    section_header("LIVRABLES  (un par ligne, ligne vide pour terminer)")
    data["livrables"] = ask_liste("Livrable", min_items=0)
    if not data["livrables"]:
        data["livrables"] = ["À définir conjointement entre les parties"]

    # ── Honoraires ───────────────────────────────────────────────────────────
    section_header("CONDITIONS FINANCIÈRES")
    print("  │  Types : forfait  /  régie  /  TJM")
    data["honor_type"]      = ask("Type d'honoraires", default="forfait")
    data["honor_montant"]   = ask("Montant (ex : 15 000 € HT  ou  850 €/jour HT)")
    data["honor_tva"]       = ask("Taux de TVA", default="20 %")
    data["honor_paiement"]  = ask("Conditions de paiement", default="30 jours fin de mois")
    data["honor_acompte"]   = ask("Acompte à la signature", required=False)

    # ── Clauses ──────────────────────────────────────────────────────────────
    section_header("CLAUSES")
    data["confidentialite"] = ask_yesno("Clause de confidentialité ?", "oui")
    data["propriete_intel"] = ask_yesno("Clause de propriété intellectuelle ?", "oui")
    data["droit"]           = ask("Droit applicable",    default="droit français")
    data["tribunal"]        = ask("Tribunal compétent",  default="Paris")
    data["notes"]           = ask("Clauses supplémentaires / notes libres (facultatif)", required=False)

    # ── Fichier de sortie ────────────────────────────────────────────────────
    section_header("FICHIER DE SORTIE")
    ref_default = f"LM-{datetime.now().strftime('%Y%m%d')}"
    data["ref"]       = ask("Référence de la lettre", default=ref_default)
    data["date_doc"]  = ask("Date de la lettre",      default=datetime.now().strftime("%d/%m/%Y"))

    safe_client = data["client_societe"].replace(" ", "_").replace("/", "-")
    file_default = f"lettre_mission_{safe_client}_{datetime.now().strftime('%Y%m%d')}.pdf"
    output = ask("Nom du fichier PDF", default=file_default)
    if not output.lower().endswith(".pdf"):
        output += ".pdf"
    data["output"] = output

    print()
    print("  └─ Données collectées ✓")
    print()
    return data

# ─────────────────────────────────────────────────────────────────────────────
# Génération PDF
# ─────────────────────────────────────────────────────────────────────────────

def build_styles():
    styles = getSampleStyleSheet()

    def S(name, **kw):
        return ParagraphStyle(name=name, **kw)

    return {
        "presta_name": S("presta_name",
            fontName="Helvetica-Bold", fontSize=16,
            textColor=WHITE, leading=20, spaceAfter=2),
        "presta_info": S("presta_info",
            fontName="Helvetica", fontSize=8,
            textColor=colors.HexColor("#d0e8f8"), leading=11),
        "ref_label": S("ref_label",
            fontName="Helvetica", fontSize=8,
            textColor=TEXT_LIGHT, alignment=TA_RIGHT),
        "ref_value": S("ref_value",
            fontName="Helvetica-Bold", fontSize=9,
            textColor=TEXT_DARK, alignment=TA_RIGHT),
        "client_label": S("client_label",
            fontName="Helvetica-Bold", fontSize=9,
            textColor=SECONDARY, spaceAfter=2),
        "client_info": S("client_info",
            fontName="Helvetica", fontSize=10,
            textColor=TEXT_DARK, leading=14),
        "lieu_date": S("lieu_date",
            fontName="Helvetica", fontSize=10,
            textColor=TEXT_MEDIUM, alignment=TA_RIGHT, spaceAfter=4),
        "objet": S("objet",
            fontName="Helvetica-Bold", fontSize=11,
            textColor=PRIMARY, spaceAfter=6, spaceBefore=8),
        "intro": S("intro",
            fontName="Helvetica", fontSize=10,
            textColor=TEXT_DARK, leading=15, spaceAfter=6, alignment=TA_JUSTIFY),
        "article_title": S("article_title",
            fontName="Helvetica-Bold", fontSize=10,
            textColor=WHITE, leading=14),
        "body": S("body",
            fontName="Helvetica", fontSize=10,
            textColor=TEXT_DARK, leading=15, spaceAfter=4, alignment=TA_JUSTIFY),
        "bullet": S("bullet",
            fontName="Helvetica", fontSize=10,
            textColor=TEXT_DARK, leading=14, leftIndent=12, spaceAfter=2),
        "footer": S("footer",
            fontName="Helvetica", fontSize=8,
            textColor=TEXT_LIGHT, alignment=TA_CENTER),
        "sign_label": S("sign_label",
            fontName="Helvetica-Bold", fontSize=9,
            textColor=TEXT_MEDIUM, alignment=TA_CENTER),
        "sign_name": S("sign_name",
            fontName="Helvetica", fontSize=9,
            textColor=TEXT_DARK, alignment=TA_CENTER),
    }


def article_header(titre, numero, S):
    """Retourne un bloc 'Article N – Titre' avec fond coloré."""
    tbl = Table(
        [[Paragraph(f"Article {numero} – {titre}", S["article_title"])]],
        colWidths=[17 * cm]
    )
    tbl.setStyle(TableStyle([
        ("BACKGROUND",  (0, 0), (-1, -1), PRIMARY),
        ("TOPPADDING",  (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LEFTPADDING", (0, 0), (-1, -1), 10),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ("ROWBACKGROUNDS", (0, 0), (-1, -1), [PRIMARY]),
    ]))
    return tbl


def generate_pdf(data):
    """Génère le PDF et retourne le chemin du fichier."""
    output_path = data["output"]
    S = build_styles()
    story = []

    page_w, page_h = A4

    # ── En-tête prestataire ──────────────────────────────────────────────────
    presta_lines = [
        Paragraph(data["presta_nom"], S["presta_name"]),
    ]
    addr = data["presta_adresse"]
    cp_v = f"{data['presta_cp']} {data['presta_ville']}"
    presta_lines.append(Paragraph(f"{addr}  —  {cp_v}", S["presta_info"]))
    if data["presta_tel"] or data["presta_email"]:
        contact_parts = []
        if data["presta_tel"]:   contact_parts.append(f"Tél : {data['presta_tel']}")
        if data["presta_email"]: contact_parts.append(f"Email : {data['presta_email']}")
        presta_lines.append(Paragraph("  ·  ".join(contact_parts), S["presta_info"]))
    if data["presta_siret"]:
        srt = f"SIRET : {data['presta_siret']}"
        if data["presta_tva"]: srt += f"  ·  TVA : {data['presta_tva']}"
        presta_lines.append(Paragraph(srt, S["presta_info"]))

    ref_lines = [
        Spacer(1, 0.5 * cm),
        Paragraph("RÉFÉRENCE", S["ref_label"]),
        Paragraph(data["ref"], S["ref_value"]),
        Spacer(1, 0.3 * cm),
        Paragraph("DATE", S["ref_label"]),
        Paragraph(data["date_doc"], S["ref_value"]),
    ]

    header_tbl = Table(
        [[presta_lines, ref_lines]],
        colWidths=[12.5 * cm, 4.5 * cm]
    )
    header_tbl.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (0, 0), PRIMARY),
        ("BACKGROUND",    (1, 0), (1, 0), ACCENT),
        ("VALIGN",        (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING",   (0, 0), (0, 0), 14),
        ("RIGHTPADDING",  (0, 0), (0, 0), 10),
        ("TOPPADDING",    (0, 0), (-1, -1), 14),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 14),
        ("LEFTPADDING",   (1, 0), (1, 0), 8),
        ("RIGHTPADDING",  (1, 0), (1, 0), 10),
    ]))
    story.append(header_tbl)
    story.append(Spacer(1, 0.6 * cm))

    # ── Adresse client + Lieu / Date ─────────────────────────────────────────
    client_block = [
        Paragraph("À L'ATTENTION DE", S["client_label"]),
        Paragraph(data["client_societe"],  S["client_info"]),
        Paragraph(data["client_contact"],  S["client_info"]),
        Paragraph(data["client_adresse"],  S["client_info"]),
        Paragraph(f"{data['client_cp']} {data['client_ville']}", S["client_info"]),
    ]

    right_block = [
        Spacer(1, 0.3 * cm),
        Paragraph(
            f"{data['presta_ville']}, le {data['date_doc']}",
            S["lieu_date"]
        ),
    ]

    addr_tbl = Table(
        [[client_block, right_block]],
        colWidths=[10 * cm, 7 * cm]
    )
    addr_tbl.setStyle(TableStyle([
        ("VALIGN",        (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING",   (0, 0), (-1, -1), 0),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 0),
        ("TOPPADDING",    (0, 0), (-1, -1), 0),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
    ]))
    story.append(addr_tbl)
    story.append(Spacer(1, 0.7 * cm))

    # ── Objet ────────────────────────────────────────────────────────────────
    story.append(HRFlowable(width="100%", thickness=2, color=SECONDARY,
                             spaceAfter=8, spaceBefore=0))
    story.append(Paragraph(
        f"Objet : Lettre de mission – {data['mission_titre']}",
        S["objet"]
    ))
    story.append(HRFlowable(width="100%", thickness=0.5, color=colors.lightgrey,
                             spaceAfter=10, spaceBefore=0))

    # ── Formule d'introduction ───────────────────────────────────────────────
    intro_txt = (
        f"Madame, Monsieur {data['client_contact']},<br/><br/>"
        f"Nous avons le plaisir de vous adresser la présente lettre de mission "
        f"afin de définir les termes et conditions dans lesquels <b>{data['presta_nom']}</b> "
        f"(ci-après « le Prestataire ») interviendra auprès de "
        f"<b>{data['client_societe']}</b> (ci-après « le Client »)."
    )
    if data.get("mission_contexte"):
        intro_txt += f"<br/><br/>{data['mission_contexte']}"
    story.append(Paragraph(intro_txt, S["intro"]))
    story.append(Spacer(1, 0.4 * cm))

    # ── Article 1 – Objet ────────────────────────────────────────────────────
    story.append(KeepTogether([
        article_header("Objet de la mission", 1, S),
        Spacer(1, 0.25 * cm),
        Paragraph(
            f"Le Prestataire est missionné pour réaliser la mission suivante : "
            f"<b>{data['mission_titre']}</b>.",
            S["body"]
        ),
        Spacer(1, 0.2 * cm),
        Paragraph("Les objectifs de la mission sont les suivants :", S["body"]),
        *[Paragraph(f"• {obj}", S["bullet"]) for obj in data["objectifs"]],
        Spacer(1, 0.2 * cm),
    ]))

    # ── Article 2 – Durée et lieu ────────────────────────────────────────────
    story.append(Spacer(1, 0.3 * cm))
    story.append(KeepTogether([
        article_header("Durée et lieu d'exécution", 2, S),
        Spacer(1, 0.25 * cm),
        Paragraph(
            f"La mission débutera le <b>{data['mission_debut']}</b> "
            f"et est prévue pour se terminer le <b>{data['mission_fin']}</b>.",
            S["body"]
        ),
        Paragraph(
            f"Elle sera principalement exécutée à : <b>{data['mission_lieu']}</b>.",
            S["body"]
        ),
        Spacer(1, 0.2 * cm),
    ]))

    # ── Article 3 – Livrables ────────────────────────────────────────────────
    story.append(Spacer(1, 0.3 * cm))
    story.append(KeepTogether([
        article_header("Livrables", 3, S),
        Spacer(1, 0.25 * cm),
        Paragraph("Au titre de cette mission, le Prestataire remettra au Client :", S["body"]),
        *[Paragraph(f"• {liv}", S["bullet"]) for liv in data["livrables"]],
        Spacer(1, 0.2 * cm),
    ]))

    # ── Article 4 – Honoraires ───────────────────────────────────────────────
    story.append(Spacer(1, 0.3 * cm))
    honor_rows = [
        ["Type",        data["honor_type"].capitalize()],
        ["Montant",     data["honor_montant"]],
        ["TVA",         data["honor_tva"]],
        ["Paiement",    data["honor_paiement"]],
    ]
    if data.get("honor_acompte"):
        honor_rows.append(["Acompte", data["honor_acompte"]])

    honor_tbl = Table(honor_rows, colWidths=[4 * cm, 13 * cm])
    honor_tbl.setStyle(TableStyle([
        ("FONTNAME",     (0, 0), (0, -1), "Helvetica-Bold"),
        ("FONTSIZE",     (0, 0), (-1, -1), 10),
        ("TEXTCOLOR",    (0, 0), (0, -1), PRIMARY),
        ("TEXTCOLOR",    (1, 0), (1, -1), TEXT_DARK),
        ("BACKGROUND",   (0, 0), (-1, 0), ACCENT),
        ("ROWBACKGROUNDS", (0, 0), (-1, -1), [ACCENT, WHITE]),
        ("TOPPADDING",   (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING",(0, 0), (-1, -1), 6),
        ("LEFTPADDING",  (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ("GRID",         (0, 0), (-1, -1), 0.3, colors.lightgrey),
        ("VALIGN",       (0, 0), (-1, -1), "MIDDLE"),
    ]))
    story.append(KeepTogether([
        article_header("Honoraires et conditions financières", 4, S),
        Spacer(1, 0.25 * cm),
        honor_tbl,
        Spacer(1, 0.2 * cm),
    ]))

    # ── Article 5 – Clauses ──────────────────────────────────────────────────
    art_num = 5
    if data["confidentialite"]:
        story.append(Spacer(1, 0.3 * cm))
        story.append(KeepTogether([
            article_header("Confidentialité", art_num, S),
            Spacer(1, 0.25 * cm),
            Paragraph(
                "Le Prestataire s'engage à maintenir strictement confidentiel l'ensemble des "
                "informations, données et documents auxquels il aura accès dans le cadre de la "
                "présente mission, pendant la durée de celle-ci et pendant une période de "
                "<b>5 ans</b> après son terme.",
                S["body"]
            ),
            Spacer(1, 0.2 * cm),
        ]))
        art_num += 1

    if data["propriete_intel"]:
        story.append(Spacer(1, 0.3 * cm))
        story.append(KeepTogether([
            article_header("Propriété intellectuelle", art_num, S),
            Spacer(1, 0.25 * cm),
            Paragraph(
                "Les livrables produits dans le cadre de la présente mission seront la propriété "
                "exclusive du Client dès complet paiement des honoraires correspondants. "
                "Le Prestataire conserve la propriété de ses méthodes, savoir-faire et outils "
                "préexistants.",
                S["body"]
            ),
            Spacer(1, 0.2 * cm),
        ]))
        art_num += 1

    if data.get("notes"):
        story.append(Spacer(1, 0.3 * cm))
        story.append(KeepTogether([
            article_header("Dispositions complémentaires", art_num, S),
            Spacer(1, 0.25 * cm),
            Paragraph(data["notes"], S["body"]),
            Spacer(1, 0.2 * cm),
        ]))
        art_num += 1

    # ── Article N – Droit applicable ─────────────────────────────────────────
    story.append(Spacer(1, 0.3 * cm))
    story.append(KeepTogether([
        article_header("Droit applicable et règlement des litiges", art_num, S),
        Spacer(1, 0.25 * cm),
        Paragraph(
            f"La présente lettre de mission est soumise au <b>{data['droit']}</b>. "
            f"En cas de litige, les parties s'engagent à rechercher une solution amiable "
            f"avant tout recours. À défaut d'accord amiable, le litige sera soumis à la "
            f"compétence exclusive du Tribunal de <b>{data['tribunal']}</b>.",
            S["body"]
        ),
        Spacer(1, 0.2 * cm),
    ]))

    # ── Bloc signature ───────────────────────────────────────────────────────
    story.append(Spacer(1, 0.8 * cm))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.lightgrey,
                             spaceAfter=10, spaceBefore=0))
    story.append(Paragraph(
        "Bon pour accord — Les deux parties reconnaissent avoir pris connaissance "
        "de la présente lettre de mission et en acceptent les termes.",
        S["intro"]
    ))
    story.append(Spacer(1, 0.6 * cm))

    sign_tbl = Table(
        [[
            [
                Paragraph("Fait à _____________ , le _______________", S["sign_name"]),
                Spacer(1, 1.8 * cm),
                Paragraph("Signature du Prestataire", S["sign_label"]),
                Spacer(1, 0.3 * cm),
                Paragraph(data["presta_nom"], S["sign_name"]),
            ],
            [
                Paragraph("Fait à _____________ , le _______________", S["sign_name"]),
                Spacer(1, 1.8 * cm),
                Paragraph("Signature du Client", S["sign_label"]),
                Paragraph("(précédée de la mention « Bon pour accord »)", S["sign_name"]),
                Spacer(1, 0.3 * cm),
                Paragraph(f"{data['client_contact']}", S["sign_name"]),
                Paragraph(f"{data['client_societe']}", S["sign_name"]),
            ],
        ]],
        colWidths=[8.5 * cm, 8.5 * cm]
    )
    sign_tbl.setStyle(TableStyle([
        ("VALIGN",        (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING",    (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ("LEFTPADDING",   (0, 0), (-1, -1), 10),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 10),
        ("BOX",           (0, 0), (0, 0), 0.5, colors.lightgrey),
        ("BOX",           (1, 0), (1, 0), 0.5, colors.lightgrey),
        ("BACKGROUND",    (0, 0), (0, 0), LIGHT_GRAY),
        ("BACKGROUND",    (1, 0), (1, 0), LIGHT_GRAY),
    ]))
    story.append(sign_tbl)

    # ── Pied de page ─────────────────────────────────────────────────────────
    def add_footer(canvas, doc):
        canvas.saveState()
        canvas.setFont("Helvetica", 8)
        canvas.setFillColor(TEXT_LIGHT)
        footer_txt = (
            f"{data['presta_nom']}  ·  {data['presta_cp']} {data['presta_ville']}"
        )
        if data["presta_siret"]:
            footer_txt += f"  ·  SIRET {data['presta_siret']}"
        page_num = f"Page {doc.page}"
        canvas.drawCentredString(page_w / 2, 1.0 * cm, footer_txt)
        canvas.drawRightString(page_w - 2 * cm, 1.0 * cm, page_num)
        canvas.restoreState()

    # ── Compilation ──────────────────────────────────────────────────────────
    doc = SimpleDocTemplate(
        output_path,
        pagesize=A4,
        leftMargin=2 * cm,
        rightMargin=2 * cm,
        topMargin=1.5 * cm,
        bottomMargin=2 * cm,
        title=f"Lettre de mission – {data['mission_titre']}",
        author=data["presta_nom"],
    )
    doc.build(story, onFirstPage=add_footer, onLaterPages=add_footer)
    return output_path

# ─────────────────────────────────────────────────────────────────────────────
# Point d'entrée
# ─────────────────────────────────────────────────────────────────────────────

def main():
    try:
        data = collect_data()
    except KeyboardInterrupt:
        print("\n\n  Annulé par l'utilisateur.")
        sys.exit(0)

    print("  Génération du PDF en cours...")
    try:
        path = generate_pdf(data)
        print()
        print("  ╔══════════════════════════════════════════════════════════╗")
        print(f"  ║  ✓  PDF généré avec succès !                             ║")
        print(f"  ║  📄  {path:<52}  ║")
        print("  ╚══════════════════════════════════════════════════════════╝")
        print()
        if os.name == "nt":
            os.startfile(path)
    except Exception as e:
        print(f"\n  [ERREUR] Impossible de générer le PDF :\n  {e}")
        import traceback
        traceback.print_exc()

    input("\n  Appuyez sur Entrée pour quitter...")

if __name__ == "__main__":
    main()
