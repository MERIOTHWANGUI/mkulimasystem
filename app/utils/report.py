from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable, PageBreak
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from io import BytesIO
from datetime import datetime

# ── COLORS ──
GREEN_DARK  = colors.HexColor('#1a4d2e')
GREEN_MID   = colors.HexColor('#2d7a4f')
GREEN_LIGHT = colors.HexColor('#4caf7d')
GREEN_PALE  = colors.HexColor('#e8f5ee')
AMBER       = colors.HexColor('#f5a623')
AMBER_PALE  = colors.HexColor('#fef3dc')
GRAY_DARK   = colors.HexColor('#1c2617')
GRAY_MID    = colors.HexColor('#4a5e42')
GRAY_LIGHT  = colors.HexColor('#8a9e82')
WHITE       = colors.white
BORDER      = colors.HexColor('#d4e2ce')

ADVICE = {
    'Maize':        'Plant at long rains March-May or short rains Oct-Dec. Use H614 or DK8031 seeds. Apply DAP at planting, CAN at knee height.',
    'Beans':        'Plant with maize or alone. Use Rosecoco or Mwitemania. Ensure good drainage. Ready in 60-90 days. Store with ash.',
    'Kale':         'Plant anytime with irrigation. Ready in 6 weeks. Harvest outer leaves weekly without uprooting. Watch for aphids.',
    'Irish Potato': 'Plant Shangi or Tigoni March-May or Aug-Oct. Spray copper fungicide every 2 weeks for blight. Ready in 90-120 days.',
    'Tomato':       'Start in nursery, transplant after 4 weeks. Stake at 30cm. Water at base. Spray copper fungicide every 10 days.',
    'Sorghum':      'Best for dry areas. Use Serena variety. Scare birds at grain maturity. Ready in 3-5 months. Stores 2 years.',
    'Groundnut':    'Needs sandy loam soil. Do not over-fertilize. Harvest when leaves yellow. Dry 1 week before storage.',
    'Cowpea':       'Very drought tolerant. Good for dry regions. Eat young leaves. Improves soil for next season.',
    'Wheat':        'Best in cool highlands. Apply nitrogen at tillering stage. Monitor for rust disease.',
    'Millet':       'Drought resistant. Good for dry areas. Bird control needed at harvest time.',
}


def _style(name, **kwargs):
    return ParagraphStyle(name, **kwargs)


def generate_history_pdf(farmer, history, crop_counts):
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer, pagesize=A4,
        rightMargin=18*mm, leftMargin=18*mm,
        topMargin=18*mm, bottomMargin=18*mm,
        title='AgroSense Farming Report',
    )
    story = []
    now   = datetime.now()
    W     = 174*mm  # usable width

    # ─── HEADER ───
    hdr = Table([[
        Paragraph('🌿 AgroSense', _style('B', fontName='Helvetica-Bold',
            fontSize=24, textColor=AMBER, alignment=TA_CENTER)),
    ]], colWidths=[W])
    hdr.setStyle(TableStyle([
        ('BACKGROUND',    (0,0),(-1,-1), GREEN_DARK),
        ('TOPPADDING',    (0,0),(-1,-1), 14),
        ('BOTTOMPADDING', (0,0),(-1,-1), 6),
    ]))
    story.append(hdr)

    sub = Table([[
        Paragraph('Personal Farming Report — Crop Recommendation History',
            _style('S', fontName='Helvetica', fontSize=10,
                   textColor=colors.HexColor('#d4edda'), alignment=TA_CENTER)),
    ]], colWidths=[W])
    sub.setStyle(TableStyle([
        ('BACKGROUND',    (0,0),(-1,-1), GREEN_MID),
        ('TOPPADDING',    (0,0),(-1,-1), 6),
        ('BOTTOMPADDING', (0,0),(-1,-1), 10),
    ]))
    story.append(sub)
    story.append(Spacer(1, 12))

    # ─── FARMER INFO ───
    info = Table([
        [
            Paragraph('Farmer Name', _style('L', fontName='Helvetica-Bold', fontSize=9, textColor=GRAY_MID)),
            Paragraph(f'{farmer.first_name} {farmer.last_name}', _style('V', fontName='Helvetica', fontSize=10, textColor=GRAY_DARK)),
            Paragraph('Username', _style('L', fontName='Helvetica-Bold', fontSize=9, textColor=GRAY_MID)),
            Paragraph(farmer.username, _style('V', fontName='Helvetica', fontSize=10, textColor=GRAY_DARK)),
        ],
        [
            Paragraph('Report Date', _style('L', fontName='Helvetica-Bold', fontSize=9, textColor=GRAY_MID)),
            Paragraph(now.strftime('%d %B %Y'), _style('V', fontName='Helvetica', fontSize=10, textColor=GRAY_DARK)),
            Paragraph('Total Records', _style('L', fontName='Helvetica-Bold', fontSize=9, textColor=GRAY_MID)),
            Paragraph(str(len(history)), _style('V', fontName='Helvetica', fontSize=10, textColor=GRAY_DARK)),
        ],
    ], colWidths=[35*mm, 52*mm, 32*mm, 55*mm])
    info.setStyle(TableStyle([
        ('BACKGROUND',    (0,0),(-1,-1), GREEN_PALE),
        ('TOPPADDING',    (0,0),(-1,-1), 7),
        ('BOTTOMPADDING', (0,0),(-1,-1), 7),
        ('LEFTPADDING',   (0,0),(-1,-1), 10),
        ('GRID',          (0,0),(-1,-1), 0.5, BORDER),
    ]))
    story.append(info)
    story.append(Spacer(1, 16))

    # ─── SUMMARY STATS ───
    story.append(Paragraph('Summary Statistics',
        _style('H', fontName='Helvetica-Bold', fontSize=13, textColor=GREEN_DARK, spaceAfter=8)))
    story.append(HRFlowable(width='100%', thickness=1.5, color=GREEN_LIGHT, spaceAfter=10))

    most_rec = max(crop_counts, key=crop_counts.get) if crop_counts else 'N/A'
    if history:
        avg_conf = round(sum(r.top_confidence for r in history) / len(history), 1)
    else:
        avg_conf = 0

    stats_data = [[
        _stat_cell('Total Checks', str(len(history)), 'Your farming sessions'),
        _stat_cell('Top Crop', most_rec, f'{crop_counts.get(most_rec, 0)}x recommended'),
        _stat_cell('Avg Confidence', f'{avg_conf}%', 'Across all sessions'),
        _stat_cell('Latest Crop', history[0].top_crop, history[0].created_at.strftime('%d %b %Y')),
    ]]
    stats_table = Table(stats_data, colWidths=[W/4]*4)
    stats_table.setStyle(TableStyle([
        ('BACKGROUND',    (0,0),(-1,-1), WHITE),
        ('BOX',           (0,0),(-1,-1), 1, BORDER),
        ('INNERGRID',     (0,0),(-1,-1), 0.5, BORDER),
        ('TOPPADDING',    (0,0),(-1,-1), 10),
        ('BOTTOMPADDING', (0,0),(-1,-1), 10),
        ('LEFTPADDING',   (0,0),(-1,-1), 10),
        ('VALIGN',        (0,0),(-1,-1), 'TOP'),
    ]))
    story.append(stats_table)
    story.append(Spacer(1, 16))

    # ─── CROP FREQUENCY ───
    story.append(Paragraph('Crop Recommendation Frequency',
        _style('H', fontName='Helvetica-Bold', fontSize=13, textColor=GREEN_DARK, spaceAfter=8)))
    story.append(HRFlowable(width='100%', thickness=1.5, color=GREEN_LIGHT, spaceAfter=10))

    sorted_crops = sorted(crop_counts.items(), key=lambda x: x[1], reverse=True)
    max_count    = sorted_crops[0][1] if sorted_crops else 1

    freq_data = []
    for crop, count in sorted_crops:
        bar_w    = int((count / max_count) * 90)
        bar_cell = Table([['']], colWidths=[bar_w*mm if bar_w > 0 else 2*mm], rowHeights=[10])
        bar_cell.setStyle(TableStyle([
            ('BACKGROUND',    (0,0),(-1,-1), GREEN_MID),
            ('TOPPADDING',    (0,0),(-1,-1), 0),
            ('BOTTOMPADDING', (0,0),(-1,-1), 0),
            ('LEFTPADDING',   (0,0),(-1,-1), 0),
            ('RIGHTPADDING',  (0,0),(-1,-1), 0),
        ]))
        freq_data.append([
            Paragraph(crop, _style('FC', fontName='Helvetica-Bold', fontSize=9, textColor=GRAY_DARK)),
            bar_cell,
            Paragraph(f'{count}x', _style('FN', fontName='Helvetica', fontSize=9, textColor=GRAY_MID, alignment=TA_RIGHT)),
        ])

    freq_table = Table(freq_data, colWidths=[40*mm, 118*mm, 16*mm])
    freq_table.setStyle(TableStyle([
        ('ROWBACKGROUNDS',  (0,0),(-1,-1), [WHITE, GREEN_PALE]),
        ('TOPPADDING',      (0,0),(-1,-1), 7),
        ('BOTTOMPADDING',   (0,0),(-1,-1), 7),
        ('LEFTPADDING',     (0,0),(-1,-1), 8),
        ('RIGHTPADDING',    (0,0),(-1,-1), 8),
        ('VALIGN',          (0,0),(-1,-1), 'MIDDLE'),
        ('GRID',            (0,0),(-1,-1), 0.5, BORDER),
    ]))
    story.append(freq_table)
    story.append(Spacer(1, 20))

    # ─── FULL HISTORY ───
    story.append(PageBreak())
    story.append(Paragraph('Full Recommendation History',
        _style('H2', fontName='Helvetica-Bold', fontSize=13, textColor=GREEN_DARK,
               spaceBefore=0, spaceAfter=8)))
    story.append(HRFlowable(width='100%', thickness=1.5, color=GREEN_LIGHT, spaceAfter=12))

    for i, rec in enumerate(history):
        results = rec.get_results()
        if isinstance(results, dict):
            results_list = results.get('top_options', [])
        else:
            results_list = results or []
        top     = results_list[0] if results_list else {}
        advice  = ADVICE.get(rec.top_crop, 'Follow standard planting practices for your region.')

        # Record header
        rec_hdr = Table([[
            Paragraph(f'#{i+1}', _style('RN', fontName='Helvetica-Bold', fontSize=12,
                textColor=WHITE, alignment=TA_CENTER)),
            Paragraph(rec.top_crop, _style('RC', fontName='Helvetica-Bold', fontSize=13, textColor=WHITE)),
            Paragraph(f'{rec.top_confidence:.1f}% confidence',
                _style('RCF', fontName='Helvetica', fontSize=10, textColor=AMBER, alignment=TA_RIGHT)),
            Paragraph(rec.created_at.strftime('%d %b %Y'),
                _style('RD', fontName='Helvetica', fontSize=9,
                       textColor=colors.HexColor('#b3d9bf'), alignment=TA_RIGHT)),
        ]], colWidths=[16*mm, 70*mm, 50*mm, 38*mm])
        rec_hdr.setStyle(TableStyle([
            ('BACKGROUND',    (0,0),(-1,-1), GREEN_DARK),
            ('TOPPADDING',    (0,0),(-1,-1), 10),
            ('BOTTOMPADDING', (0,0),(-1,-1), 10),
            ('LEFTPADDING',   (0,0),(-1,-1), 10),
            ('VALIGN',        (0,0),(-1,-1), 'MIDDLE'),
        ]))

        # Conditions
        cond = Table([[
            Paragraph(f'Temp: {rec.temperature}°C', _style('CI', fontName='Helvetica', fontSize=9, textColor=GRAY_MID)),
            Paragraph(f'Rain: {rec.rainfall}mm', _style('CI', fontName='Helvetica', fontSize=9, textColor=GRAY_MID)),
            Paragraph(f'Alt: {rec.altitude}m', _style('CI', fontName='Helvetica', fontSize=9, textColor=GRAY_MID)),
            Paragraph(f'Soil: {rec.soil_type}', _style('CI', fontName='Helvetica', fontSize=9, textColor=GRAY_MID)),
            Paragraph(f'pH: {rec.soil_ph}', _style('CI', fontName='Helvetica', fontSize=9, textColor=GRAY_MID)),
        ]], colWidths=[W/5]*5)
        cond.setStyle(TableStyle([
            ('BACKGROUND',    (0,0),(-1,-1), GREEN_PALE),
            ('TOPPADDING',    (0,0),(-1,-1), 7),
            ('BOTTOMPADDING', (0,0),(-1,-1), 7),
            ('LEFTPADDING',   (0,0),(-1,-1), 8),
            ('INNERGRID',     (0,0),(-1,-1), 0.5, BORDER),
        ]))

        # All crops
        def _score_from_result(result):
            if not isinstance(result, dict):
                return 0.0
            if 'score' in result:
                return float(result.get('score') or 0)
            if 'final_score' in result:
                return float(result.get('final_score') or 0)
            if 'ml_prob' in result:
                return float(result.get('ml_prob') or 0)
            return 0.0

        crops_str = '  |  '.join([
            f"{'#'+str(j+1)} {r.get('crop', 'Unknown')} ({_score_from_result(r):.1f}%)"
            for j, r in enumerate(results_list[:5])
        ])
        crops_row = Table([[
            Paragraph('Recommended Crops:', _style('CRL', fontName='Helvetica-Bold', fontSize=9, textColor=GRAY_MID)),
            Paragraph(crops_str, _style('CRV', fontName='Helvetica', fontSize=9, textColor=GRAY_DARK)),
        ]], colWidths=[38*mm, 136*mm])
        crops_row.setStyle(TableStyle([
            ('BACKGROUND',    (0,0),(-1,-1), WHITE),
            ('TOPPADDING',    (0,0),(-1,-1), 7),
            ('BOTTOMPADDING', (0,0),(-1,-1), 7),
            ('LEFTPADDING',   (0,0),(-1,-1), 8),
            ('VALIGN',        (0,0),(-1,-1), 'TOP'),
        ]))

        # Advice
        adv_row = Table([[
            Paragraph('Planting Advice:', _style('AL', fontName='Helvetica-Bold', fontSize=9, textColor=GRAY_MID)),
            Paragraph(advice, _style('AV', fontName='Helvetica', fontSize=9, textColor=GRAY_DARK, leading=14)),
        ]], colWidths=[38*mm, 136*mm])
        adv_row.setStyle(TableStyle([
            ('BACKGROUND',    (0,0),(-1,-1), AMBER_PALE),
            ('TOPPADDING',    (0,0),(-1,-1), 8),
            ('BOTTOMPADDING', (0,0),(-1,-1), 8),
            ('LEFTPADDING',   (0,0),(-1,-1), 8),
            ('VALIGN',        (0,0),(-1,-1), 'TOP'),
        ]))

        card = Table([[rec_hdr], [cond], [crops_row], [adv_row]], colWidths=[W])
        card.setStyle(TableStyle([
            ('BOX',           (0,0),(-1,-1), 1.5, BORDER),
            ('TOPPADDING',    (0,0),(-1,-1), 0),
            ('BOTTOMPADDING', (0,0),(-1,-1), 0),
            ('LEFTPADDING',   (0,0),(-1,-1), 0),
            ('RIGHTPADDING',  (0,0),(-1,-1), 0),
        ]))
        story.append(card)
        story.append(Spacer(1, 10))

    # ─── FOOTER ───
    story.append(Spacer(1, 10))
    story.append(HRFlowable(width='100%', thickness=1, color=BORDER, spaceAfter=8))
    story.append(Paragraph(
        f'Generated by AgroSense Smart Farming System  •  {now.strftime("%d %B %Y")}  •  agrosense.co.ke',
        _style('F', fontName='Helvetica', fontSize=8, textColor=GRAY_LIGHT, alignment=TA_CENTER)
    ))
    story.append(Paragraph(
        'Recommendations are based on ML analysis of your soil and climate data. Always consult your local agricultural extension officer.',
        _style('D', fontName='Helvetica-Oblique', fontSize=7, textColor=GRAY_LIGHT,
               alignment=TA_CENTER, spaceBefore=4)
    ))

    doc.build(story)
    buffer.seek(0)
    return buffer


def _stat_cell(label, value, sub):
    return Table([[
        Paragraph(value, _style('SV', fontName='Helvetica-Bold', fontSize=18, textColor=GREEN_DARK)),
        Paragraph(label, _style('SL', fontName='Helvetica', fontSize=9, textColor=GRAY_MID)),
        Paragraph(sub,   _style('SS', fontName='Helvetica', fontSize=8, textColor=GREEN_LIGHT)),
    ]], colWidths=[None])
