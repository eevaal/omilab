import os
from datetime import datetime

from fpdf import FPDF


class PDFService(FPDF):
    def __init__(self, author: str, title: str):
        super().__init__()
        self.author_mark = author
        self.doc_title = title
        self.set_auto_page_break(auto=True, margin=20)

        self.color_primary = (30, 58, 138)
        self.color_text = (33, 33, 33)
        self.color_watermark = (240, 240, 240)
        self.color_accent = (100, 116, 139)

        font_path = os.path.join("static", "fonts", "font.ttf")

        try:
            self.add_font("CustomFont", "", font_path)
            self.add_font("CustomFont", "B", font_path)
        except RuntimeError:
            print("❌ ОШИБКА: Нет шрифта. Кириллица не заработает.")

    def header(self):
        watermark_text = self.author_mark.upper() if hasattr(self, "author_mark") else "OMILAB"

        self.set_font("CustomFont", "B", 50)
        self.set_text_color(*self.color_watermark)

        with self.rotation(45, x=105, y=148):
            self.text(30, 180, watermark_text)

        if self.page_no() > 1:
            self.set_font("CustomFont", "", 9)
            self.set_text_color(*self.color_accent)

            header_text = f"{self.doc_title} • {self.author_mark}"
            self.cell(0, 10, header_text, align="R")

            self.set_draw_color(*self.color_accent)
            self.line(10, 20, 200, 20)
            self.ln(15)

    def footer(self):
        self.set_y(-15)
        self.set_font("CustomFont", "", 8)
        self.set_text_color(128)
        self.cell(0, 10, f"{self.page_no()}", align="L")

    def create_cover_page(self):
        """Создает красивую титульную страницу"""
        self.add_page()

        logo_path = os.path.join("static", "images", "logo.png")
        if os.path.exists(logo_path):
            self.image(logo_path, 10, 10, 30)
            self.ln(40)
        else:
            self.ln(40)

        self.ln(40)

        self.set_font("CustomFont", "B", 36)
        self.set_text_color(0, 0, 0)

        self.multi_cell(0, 15, self.doc_title)

        self.ln(10)

        self.set_font("CustomFont", "", 16)
        self.set_text_color(50, 50, 50)
        self.cell(0, 10, "Конспект лекции", ln=True)

        self.set_y(-50)

        self.set_draw_color(*self.color_primary)
        self.set_line_width(0.5)
        self.line(10, self.get_y(), 80, self.get_y())
        self.ln(5)

        self.set_font("CustomFont", "B", 12)
        self.set_text_color(0, 0, 0)
        self.cell(0, 8, self.author_mark, ln=True)

        self.set_font("CustomFont", "", 10)
        self.set_text_color(100, 100, 100)
        today = datetime.now().strftime("%d.%m.%Y")
        self.cell(0, 8, today, ln=True)

    def generate(self, content: str, filename: str) -> str:
        self.create_cover_page()

        self.add_page()

        self.set_font("CustomFont", "B", 18)
        self.set_text_color(*self.color_primary)
        self.cell(0, 10, "1. Основной материал", ln=True)
        self.ln(5)

        self.set_font("CustomFont", "", 12)
        self.set_text_color(*self.color_text)
        self.multi_cell(0, 8, content)

        output_path = os.path.join("static", "lectures", filename)
        self.output(output_path)
        return output_path
