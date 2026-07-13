from __future__ import annotations

import io
from datetime import datetime

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import (
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

RISK_LABELS = {
    0: "Balanced",
    1: "Mildly Elevated",
    2: "Moderately Elevated",
    3: "Needs Attention",
}

RECOMMENDATIONS = {
    0: "Your brain activity is within your normal baseline. Continue maintaining healthy sleep, hydration, and regular daily routines.",
    1: "A mild deviation from your baseline was observed. Consider taking a short break, practicing deep breathing, or relaxing for a few minutes.",
    2: "A moderate deviation from your baseline was observed. Consider reducing mental workload, taking a longer break, and allowing time for recovery.",
    3: "A significant deviation from your baseline was observed. It is recommended to rest, avoid prolonged mental stress, and repeat the assessment later if needed.",
}


def generate_report(session_data: dict) -> bytes:
    """
    Generate a PDF summary for a completed NuroLab session.

    Expected session_data keys:
        timestamp
        context
        alpha_de
        beta_de
        theta_de
        delta_de
        gamma_de
        deviation_score
        risk_tier
        condition_label
        explanations
    """

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
        "Disclaimer",
        parent=styles["Normal"],
        fontSize=8,
        textColor=colors.grey,
        leading=10,
    )

    story = []

    risk_tier = int(session_data.get("risk_tier", 0))
    # ------------------------------------------------------------------
    # Report Header
    # ------------------------------------------------------------------

    story.append(Paragraph("NuroLab Session Report", styles["Title"]))
    story.append(Spacer(1, 0.3 * cm))

    story.append(
        Paragraph(
            f"Generated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}",
            styles["Normal"],
        )
    )

    story.append(
        Paragraph(
            f"Session Time: {session_data.get('timestamp', 'Unknown')}",
            styles["Normal"],
        )
    )

    story.append(
        Paragraph(
            f"Context: {session_data.get('context', 'Unknown').capitalize()}",
            styles["Normal"],
        )
    )

    story.append(Spacer(1, 0.4 * cm))

    # ------------------------------------------------------------------
    # Session Summary
    # ------------------------------------------------------------------

    story.append(Paragraph("Session Summary", styles["Heading2"]))

    summary = (
        "This report summarizes the recorded brain activity for the completed "
        "session. The observations are compared with the user's personal "
        "baseline to identify overall brain activity patterns and provide "
        "wellness-oriented recommendations."
    )

    story.append(Paragraph(summary, styles["Normal"]))
    story.append(Spacer(1, 0.5 * cm))

    # ------------------------------------------------------------------
    # EEG Band Power Summary
    # ------------------------------------------------------------------

    story.append(Paragraph("EEG Band Power Summary", styles["Heading2"]))
    story.append(Spacer(1, 0.2 * cm))

    band_data = [
        ["Band", "DE Value", "Interpretation"],
        ["Delta", f"{session_data.get('delta_de', 0):.3f}", "Deep rest and recovery"],
        ["Theta", f"{session_data.get('theta_de', 0):.3f}", "Relaxation and creativity"],
        ["Alpha", f"{session_data.get('alpha_de', 0):.3f}", "Calm and relaxed focus"],
        ["Beta", f"{session_data.get('beta_de', 0):.3f}", "Attention and active thinking"],
        ["Gamma", f"{session_data.get('gamma_de', 0):.3f}", "Higher cognitive processing"],
    ]

    band_table = Table(
        band_data,
        colWidths=[4 * cm, 4 * cm, 8 * cm],
    )

    band_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#2dd4bf")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("FONTSIZE", (0, 0), (-1, -1), 10),
                (
                    "ROWBACKGROUNDS",
                    (0, 1),
                    (-1, -1),
                    [colors.white, colors.HexColor("#f7f7f7")],
                ),
            ]
        )
    )

    story.append(band_table)
    story.append(Spacer(1, 0.5 * cm))
    # ------------------------------------------------------------------
    # Overall Wellness Status
    # ------------------------------------------------------------------

    story.append(Paragraph("Overall Wellness Status", styles["Heading2"]))

    story.append(
        Paragraph(
            f"Current status: {RISK_LABELS.get(risk_tier, 'Unknown')}",
            styles["Normal"],
        )
    )

    story.append(
        Paragraph(
            f"Deviation score: {session_data.get('deviation_score', 0):.2f}σ from your personal baseline.",
            styles["Normal"],
        )
    )

    story.append(Spacer(1, 0.4 * cm))

    # ------------------------------------------------------------------
    # Positive Observations
    # ------------------------------------------------------------------

    story.append(Paragraph("Positive Observations", styles["Heading2"]))

    positive_points = []

    if abs(session_data.get("alpha_de", 0)) <= 2:
        positive_points.append(
            "Alpha activity remains close to your personal baseline, indicating a stable relaxation pattern."
        )

    if abs(session_data.get("theta_de", 0)) <= 2:
        positive_points.append(
            "Theta activity is within an expected range for this session."
        )

    if abs(session_data.get("delta_de", 0)) <= 2:
        positive_points.append(
            "Delta activity does not show any significant deviation from baseline."
        )

    if not positive_points:
        positive_points.append(
            "Several brain activity measures remain within an acceptable range for this session."
        )

    for point in positive_points:
        story.append(Paragraph(point, styles["Normal"]))

    story.append(Spacer(1, 0.4 * cm))

    # ------------------------------------------------------------------
    # Areas to Monitor
    # ------------------------------------------------------------------

    story.append(Paragraph("Areas to Monitor", styles["Heading2"]))

    if risk_tier == 0:
        monitor_text = (
            "No significant deviations were observed during this session."
        )
    elif risk_tier == 1:
        monitor_text = (
            "A mild deviation from your usual baseline was observed. Continued monitoring across future sessions is recommended."
        )
    elif risk_tier == 2:
        monitor_text = (
            "A moderate deviation from your baseline was observed. Consider monitoring future sessions for consistency."
        )
    else:
        monitor_text = (
            "A higher level of deviation from your baseline was observed. Additional monitoring and adequate rest are recommended."
        )

    story.append(Paragraph(monitor_text, styles["Normal"]))
    story.append(Spacer(1, 0.5 * cm))

    # ------------------------------------------------------------------
    # Research Model Assessment
    # ------------------------------------------------------------------

    story.append(Paragraph("Research Model Assessment", styles["Heading2"]))

    story.append(
        Paragraph(
            f"Model output: {session_data.get('condition_label', 'Unknown').capitalize()}",
            styles["Normal"],
        )
    )

    story.append(Spacer(1, 0.3 * cm))

    explanations = session_data.get("explanations", [])

    if explanations:
        story.append(Paragraph("Contributing Factors", styles["Heading3"]))

        for exp in explanations:
            story.append(
                Paragraph(f"• {exp}", styles["Normal"])
            )

        story.append(Spacer(1, 0.4 * cm))
    # ------------------------------------------------------------------
    # Wellness Recommendations
    # ------------------------------------------------------------------

    story.append(Paragraph("Wellness Recommendations", styles["Heading2"]))

    story.append(
        Paragraph(
            RECOMMENDATIONS.get(risk_tier, RECOMMENDATIONS[0]),
            styles["Normal"],
        )
    )

    story.append(
        Paragraph(
            "Regular monitoring, adequate sleep, hydration, and stress management can help maintain healthy cognitive function over time.",
            styles["Normal"],
        )
    )

    story.append(Spacer(1, 0.5 * cm))

    # ------------------------------------------------------------------
    # Disclaimer
    # ------------------------------------------------------------------

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