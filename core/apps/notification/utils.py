from io import BytesIO

from django.conf import settings
from django.core.mail import EmailMessage
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer

from apps.supportticket.models import SupportTicket
from apps.tenant.models import MaintenanceRequest


def enrich_notification_data(data):
    data = dict(data)

    if data.get("type") == "SUPPORT_TICKET":
        ticket = SupportTicket.objects.filter(alias=data.get("alias")).first()
        data["is_deleted"] = ticket.is_deleted if ticket else True
    elif data.get("type") == "MAINTENANCE_REQUEST":
        maintenance_request = MaintenanceRequest.objects.filter(alias=data.get("alias")).first()
        data["is_deleted"] = maintenance_request is None
        data.pop("category", None)

    return data


def _styles():
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(
        name="EmergencyBanner",
        fontSize=11,
        textColor=colors.HexColor("#b91c1c"),
        fontName="Helvetica-Bold",
    ))
    return styles


def _build_maintenance_request_pdf(maintenance_request):
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=20 * mm, bottomMargin=20 * mm)
    styles = _styles()
    elements = []

    if maintenance_request.is_emergency:
        elements.append(Paragraph("&#9888; EMERGENCY REQUEST", styles["EmergencyBanner"]))
        elements.append(Spacer(1, 10))

    elements.append(Paragraph("New Maintenance Request", styles["Title"]))
    elements.append(Paragraph(f"Submitted by {maintenance_request.tenant.get_full_name()}", styles["Normal"]))
    elements.append(Spacer(1, 16))

    data = [
        ["Property", str(maintenance_request.property)],
        ["Category", maintenance_request.get_category_display()],
        ["Issue", maintenance_request.issue or "N/A"],
        ["Description", maintenance_request.description or "N/A"],
        ["Emergency", "Yes" if maintenance_request.is_emergency else "No"],
    ]

    table = Table(data, colWidths=[100, 320])
    table.setStyle(TableStyle([
        ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
        ("TEXTCOLOR", (0, 0), (0, -1), colors.HexColor("#6b7280")),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e5e7eb")),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING", (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ("LEFTPADDING", (0, 0), (-1, -1), 10),
    ]))
    elements.append(table)

    doc.build(elements)
    buffer.seek(0)
    return buffer


def _build_maintenance_status_pdf(maintenance_request, status_display):
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=20 * mm, bottomMargin=20 * mm)
    styles = _styles()
    elements = []

    elements.append(Paragraph("Maintenance Request Updated", styles["Title"]))
    elements.append(Paragraph(f"Status changed to: <b>{status_display}</b>", styles["Normal"]))
    elements.append(Spacer(1, 16))

    data = [
        ["Property", str(maintenance_request.property)],
        ["Category", maintenance_request.get_category_display()],
        ["Issue", maintenance_request.issue or "N/A"],
    ]

    table = Table(data, colWidths=[100, 320])
    table.setStyle(TableStyle([
        ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
        ("TEXTCOLOR", (0, 0), (0, -1), colors.HexColor("#6b7280")),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e5e7eb")),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING", (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ("LEFTPADDING", (0, 0), (-1, -1), 10),
    ]))
    elements.append(table)

    doc.build(elements)
    buffer.seek(0)
    return buffer


def send_maintenance_request_created_email(maintenance_request, user):
    pdf_buffer = _build_maintenance_request_pdf(maintenance_request)

    body = (
        f"New maintenance request from {maintenance_request.tenant.get_full_name()} "
        f"for {maintenance_request.property}.\n\n"
        f"See the attached PDF for full details."
    )

    email = EmailMessage(
        subject="New Maintenance Request",
        body=body,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[user.email],
    )
    email.attach(
        f"maintenance-request-{maintenance_request.alias}.pdf",
        pdf_buffer.read(),
        "application/pdf",
    )
    email.send(fail_silently=False)


def send_maintenance_status_changed_email(maintenance_request, tenant):
    status_display = maintenance_request.get_current_status_display()
    pdf_buffer = _build_maintenance_status_pdf(maintenance_request, status_display)

    body = f"Your maintenance request status has been changed to {status_display}.\n\nSee the attached PDF for full details."

    email = EmailMessage(
        subject="Maintenance Request Status Updated",
        body=body,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[tenant.email],
    )
    email.attach(
        f"maintenance-request-{maintenance_request.alias}.pdf",
        pdf_buffer.read(),
        "application/pdf",
    )
    email.send(fail_silently=False)