# File: nurolab/app_backend/report_generator.py

from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
)
from reportlab.lib.units import cm
import io
from datetime import datetime

RISK_LABELS = {
    0: "Normal",
    1: "Mild",
    2: "Moderate",
    3: "High",
}

WELLNESS_STATUS = {
    0: "Balanced",
    1: "Mildly Elevated",
    2: "Needs Attention",
    3: "Needs Rest",
}

RECOMMENDATIONS = {
    0: "Your brain activity looks balanced. Keep up your current routine and maintain healthy sleep and hydration habits.",
    1: "Your brain activity suggests mild mental fatigue. Consider a 5-minute breathing exercise or a short walk to refresh.",
    2: "Your brain activity suggests moderate fatigue. Take a 15-minute break, step away from screens, and hydrate well.",
    3: "Your brain activity suggests significant fatigue. Rest is strongly recommended. Avoid high-stress tasks for now.",
}


def generate_report(session_data: dict) -> bytes:
    buffer = io.BytesIO()

    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=2 * cm,
        leftMargin=2 * cm,
        topMargin=2 * cm,
        bottomMargin=2 * cm,
    )

    styles = getSampleStyleSheet()

    disclaimer_style = ParagraphStyle(
        "disclaimer",
        parent=styles["Normal"],
        fontSize=8,
        textColor=colors.grey,
    )

    positive_style = ParagraphStyle(
        "positive",
        parent=styles["Normal"],
        textColor=colors.HexColor("#065F46"),
        fontSize=11,
    )

    story = []

    # ── Title ──────────────────────────────────────────────────────────
    story.append(Paragraph("NuroLab Session Report", styles["Title"]))
    story.append(Spacer(1, 0.3 * cm))

    # ── Positive opening ───────────────────────────────────────────────
    story.append(
        Paragraph(
            "✓ Your brain monitoring session has been completed successfully.",
            positive_style,
        )
    )
    story.append(Spacer(1, 0.3 * cm))

    # ── Session info ───────────────────────────────────────────────────
    story.append(
        Paragraph(
            f"Generated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}",
            styles["Normal"],
        )
    )
    story.append(
        Paragraph(
            f"Session time: {session_data.get('timestamp', 'Unknown')}",
            styles["Normal"],
        )
    )
    story.append(
        Paragraph(
            f"Context: {session_data.get('context', 'Unknown').capitalize()}",
            styles["Normal"],
        )
    )
    story.append(Spacer(1, 0.5 * cm))

    # ── Wellness status ────────────────────────────────────────────────
    risk_value = session_data.get("risk_tier", "low")

    if isinstance(risk_value, str):
        risk_map = {
            "low": 0,
            "mild": 1,
            "moderate": 2,
            "high": 3,
        }
        risk_tier = risk_map.get(risk_value.lower(), 0)
    else:
        risk_tier = int(risk_value)

    story.append(Paragraph("Overall Wellness Status", styles["Heading2"]))
    story.append(
        Paragraph(
            f"Status: {WELLNESS_STATUS.get(risk_tier, 'Balanced')}  |  "
            f"Deviation score: {session_data.get('deviation_score', 0):.2f}σ from your personal baseline",
            styles["Normal"],
        )
    )
    story.append(Spacer(1, 0.5 * cm))

    # ── EEG Band Power Summary ─────────────────────────────────────────
    story.append(Paragraph("EEG Band Power Summary", styles["Heading2"]))
    story.append(Spacer(1, 0.2 * cm))

    band_data = [
        ["Band", "DE Value", "Interpretation"],
        ["Delta", f"{session_data.get('delta_de', 0):.3f}", "Deep rest / slow wave"],
        ["Theta", f"{session_data.get('theta_de', 0):.3f}", "Drowsiness / creativity"],
        ["Alpha", f"{session_data.get('alpha_de', 0):.3f}", "Relaxed / calm focus"],
        ["Beta",  f"{session_data.get('beta_de',  0):.3f}", "Active thinking / stress"],
        ["Gamma", f"{session_data.get('gamma_de', 0):.3f}", "High cognition"],
    ]

    band_table = Table(band_data, colWidths=[4 * cm, 4 * cm, 8 * cm])
    band_table.setStyle(
        TableStyle([
            ("BACKGROUND",     (0, 0), (-1, 0), colors.HexColor("#2dd4bf")),
            ("TEXTCOLOR",      (0, 0), (-1, 0), colors.white),
            ("FONTNAME",       (0, 0), (-1, 0), "Helvetica-Bold"),
            ("GRID",           (0, 0), (-1, -1), 0.5, colors.grey),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f5f5f5")]),
            ("ALIGN",          (0, 0), (-1, -1), "CENTER"),
            ("VALIGN",         (0, 0), (-1, -1), "MIDDLE"),
            ("FONTSIZE",       (0, 0), (-1, -1), 10),
            ("ROWHEIGHT",      (0, 0), (-1, -1), 0.7 * cm),
        ])
    )

    story.append(band_table)
    story.append(Spacer(1, 0.5 * cm))

    # ── Positive observation ───────────────────────────────────────────
    alpha = session_data.get("alpha_de", 0)
    beta  = session_data.get("beta_de", 0)
    theta = session_data.get("theta_de", 0)

    if alpha > beta:
        positive_obs = "Your alpha activity is higher than beta — a sign of a calm and relaxed mental state."
    elif theta > beta:
        positive_obs = "Your theta activity is elevated — associated with creative thinking and light relaxation."
    else:
        positive_obs = "Your brain is showing active engagement — beta activity indicates focused mental effort."

    story.append(Paragraph("Positive Observation", styles["Heading2"]))
    story.append(Paragraph(f"✓ {positive_obs}", positive_style))
    story.append(Spacer(1, 0.5 * cm))

    # ── Condition Assessment ───────────────────────────────────────────
    story.append(Paragraph("Condition Assessment", styles["Heading2"]))
    story.append(
        Paragraph(
            f"Model output: {session_data.get('condition_label', 'Unknown').capitalize()}",
            styles["Normal"],
        )
    )
    story.append(Spacer(1, 0.3 * cm))

    # ── Contributing Factors ───────────────────────────────────────────
    explanations = session_data.get("explanations", [])
    if explanations:
        story.append(Paragraph("Contributing Factors", styles["Heading2"]))
        for exp in explanations:
            story.append(Paragraph(f"• {exp}", styles["Normal"]))
        story.append(Spacer(1, 0.4 * cm))

    # ── Wellness Recommendations ───────────────────────────────────────
    story.append(Paragraph("Wellness Recommendations", styles["Heading2"]))
    story.append(
        Paragraph(
            RECOMMENDATIONS.get(risk_tier, RECOMMENDATIONS[0]),
            styles["Normal"],
        )
    )
    story.append(
        Paragraph(
            "Regular monitoring, adequate sleep, hydration, and stress management "
            "can help maintain healthy cognitive function over time.",
            styles["Normal"],
        )
    )
    story.append(Spacer(1, 0.5 * cm))

    # ── Disclaimer ─────────────────────────────────────────────────────
    story.append(Paragraph("Disclaimer", styles["Heading2"]))
    story.append(
        Paragraph(
            "NuroLab is a research and wellness monitoring tool. "
            "The observations presented in this report are intended to support "
            "research and personal wellness tracking only. They should not be "
            "considered a clinical diagnosis or used as a substitute for "
            "professional medical advice. Please consult a qualified healthcare "
            "professional for any medical concerns or treatment decisions.",
            disclaimer_style,
        )
    )

    doc.build(story)
    pdf_bytes = buffer.getvalue()
    buffer.close()
    return pdf_bytes