import os
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

# Assuming the font file is located in a "fonts" directory within your project
font_path = os.path.join(os.path.dirname(__file__), 'fonts', 'Arial Unicode MS Font.ttf')

# Register the Arial Unicode font
pdfmetrics.registerFont(TTFont('ArialUnicode', font_path))
