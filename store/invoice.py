from django.http import HttpResponse, HttpResponseServerError
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from datetime import datetime
import os
from django.conf import settings


def generate_invoice_pdf(order):
    """Génère une facture PDF pour une commande"""
    
    try:
        # Créer la réponse HTTP avec le type MIME PDF
        response = HttpResponse(content_type='application/pdf')
        filename = 'facture_{}_{}.pdf'.format(order.id, order.order_date.strftime("%Y%m%d"))
        response['Content-Disposition'] = 'inline; filename="{}"'.format(filename)
        
        # Créer le document PDF
        doc = SimpleDocTemplate(response, pagesize=A4,
                              rightMargin=2*cm, leftMargin=2*cm,
                              topMargin=2*cm, bottomMargin=2*cm)
        
        # Container pour les éléments du PDF
        elements = []
        
        # Styles
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor('#872D37'),
            spaceAfter=30,
            alignment=1  # Center
        )
        
        heading_style = ParagraphStyle(
            'CustomHeading',
            parent=styles['Heading2'],
            fontSize=14,
            textColor=colors.HexColor('#872D37'),
            spaceAfter=12,
        )
        
        normal_style = ParagraphStyle(
            'CustomNormal',
            parent=styles['Normal'],
            fontSize=10,
            textColor=colors.black,
        )
        
        # En-tête avec logo (si disponible)
        logo_path = os.path.join(settings.BASE_DIR, 'MedinaChic', 'static', 'img', 'logo-rouge.jpg')
        if os.path.exists(logo_path):
            logo = Image(logo_path, width=3*cm, height=3*cm)
            elements.append(logo)
            elements.append(Spacer(1, 0.5*cm))
        
        # Titre
        elements.append(Paragraph("FACTURE", title_style))
        elements.append(Spacer(1, 0.5*cm))
        
        # Informations de l'entreprise et du client
        order_date_str = order.order_date.strftime('%d/%m/%Y')
        client_email = order.user_email or 'Client'
        info_data = [
            [Paragraph("<b>MedinaChic</b><br/>Boutique d'artisanat marocain<br/>Belgique", normal_style),
             Paragraph("<b>Facture N°:</b> {}<br/><b>Date:</b> {}<br/><b>Client:</b> {}".format(order.id, order_date_str, client_email), normal_style)]
        ]
        
        info_table = Table(info_data, colWidths=[9*cm, 9*cm])
        info_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
        ]))
        
        elements.append(info_table)
        elements.append(Spacer(1, 1*cm))
        
        # Titre de la section articles
        elements.append(Paragraph("Détail des articles", heading_style))
        elements.append(Spacer(1, 0.3*cm))
        
        # Tableau des articles
        table_data = [
            ['Article', 'Prix unitaire', 'Quantité', 'Sous-total']
        ]
        
        for item in order.items.all():
            table_data.append([
                item.product_name,
                "{:.2f} €".format(float(item.product_price)),
                str(item.quantity),
                "{:.2f} €".format(float(item.subtotal()))
            ])
        
        # Calculer les montants
        total_ttc = float(order.total_amount)
        tva_rate = 0.21  # 21% TVA
        total_ht = total_ttc / (1 + tva_rate)
        tva_amount = total_ttc - total_ht
        
        # Ajouter les lignes de totaux
        table_data.append(['', '', '', ''])  # Ligne vide
        table_data.append(['', '', 'Total HT:', "{:.2f} €".format(total_ht)])
        table_data.append(['', '', 'TVA (21%):', "{:.2f} €".format(tva_amount)])
        table_data.append(['', '', 'Total TTC:', "{:.2f} €".format(total_ttc)])
        
        # Créer le tableau
        items_table = Table(table_data, colWidths=[8*cm, 3*cm, 3*cm, 3*cm])
        items_table.setStyle(TableStyle([
            # En-tête
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#872D37')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 11),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            
            # Corps du tableau (articles)
            ('ALIGN', (1, 1), (-1, -5), 'RIGHT'),
            ('ALIGN', (0, 1), (0, -5), 'LEFT'),
            ('FONTNAME', (0, 1), (-1, -5), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -5), 10),
            ('ROWBACKGROUNDS', (0, 1), (-1, -5), [colors.white, colors.HexColor('#f8f9fa')]),
            ('GRID', (0, 0), (-1, -5), 0.5, colors.grey),
            
            # Lignes de totaux
            ('ALIGN', (2, -4), (-1, -1), 'RIGHT'),
            ('FONTNAME', (2, -3), (-1, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (2, -3), (-1, -1), 10),
            ('LINEABOVE', (2, -3), (-1, -3), 1, colors.HexColor('#872D37')),
            ('LINEABOVE', (2, -1), (-1, -1), 2, colors.HexColor('#872D37')),
            ('BACKGROUND', (2, -1), (-1, -1), colors.HexColor('#FFF8DC')),
        ]))
        
        elements.append(items_table)
        elements.append(Spacer(1, 1.5*cm))
        
        # Notes de pied de page
        footer_text = """
        <b>Conditions de paiement:</b> Paiement effectué par carte bancaire via Stripe.<br/>
        <b>TVA:</b> TVA belge de 21% incluse dans le prix total.<br/>
        <b>Merci pour votre confiance!</b> MedinaChic - L'artisanat marocain authentique.
        """
        elements.append(Paragraph(footer_text, normal_style))
        
        # Construire le PDF
        doc.build(elements)
        
        return response
    
    except Exception as e:
        # En cas d'erreur, retourner une réponse d'erreur
        return HttpResponseServerError(f"Erreur lors de la génération de la facture: {str(e)}")
