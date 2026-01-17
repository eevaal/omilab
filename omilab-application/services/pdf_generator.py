import os
from fpdf import FPDF
from datetime import datetime


class PDFService(FPDF):
    def __init__(self, author: str, title: str):
        super().__init__()
        self.author_mark = author
        self.doc_title = title
        self.set_auto_page_break(auto=True, margin=20)

        # --- НАСТРОЙКИ ЦВЕТОВ (RGB) ---
        self.color_primary = (30, 58, 138)  # Глубокий синий (как на скрине)
        self.color_text = (33, 33, 33)  # Почти черный для текста
        self.color_watermark = (240, 240, 240)  # Очень бледный серый
        self.color_accent = (100, 116, 139)  # Серый для колонтитулов

        # --- ШРИФТЫ ---
        font_path = os.path.join("static", "fonts", "font.ttf")
        # Для жирного используем тот же файл, если нет отдельного,
        # но лучше скачать font_bold.ttf
        try:
            self.add_font("CustomFont", "", font_path)
            self.add_font("CustomFont", "B", font_path)
        except RuntimeError:
            print("❌ ОШИБКА: Нет шрифта. Кириллица не заработает.")

    def header(self):
        # 1. ВОДЯНОЙ ЗНАК (Автор лекции)
        # Проверяем, есть ли автор, чтобы не упало
        watermark_text = self.author_mark.upper() if hasattr(self, 'author_mark') else "OMILAB"

        self.set_font("CustomFont", "B", 50)  # Можно поиграть с размером шрифта
        self.set_text_color(*self.color_watermark)

        # Магия поворота: Центр страницы
        # x=105, y=148 — это центр А4
        with self.rotation(45, x=105, y=148):
            # Пишем имя автора.
            # align="C" выровняет текст по центру относительно точки координат
            self.text(30, 180, watermark_text)

        # 2. КОЛОНТИТУЛ (На всех страницах кроме первой)
        if self.page_no() > 1:
            self.set_font("CustomFont", "", 9)
            self.set_text_color(*self.color_accent)

            # Текст справа: "Название лекции • Автор"
            header_text = f"{self.doc_title} • {self.author_mark}"
            self.cell(0, 10, header_text, align="R")

            # Линия
            self.set_draw_color(*self.color_accent)
            self.line(10, 20, 200, 20)
            self.ln(15)

    def footer(self):
        # Номер страницы внизу
        self.set_y(-15)
        self.set_font("CustomFont", "", 8)
        self.set_text_color(128)
        self.cell(0, 10, f'{self.page_no()}', align="L")  # Слева, как в книге

    def create_cover_page(self):
        """Создает красивую титульную страницу"""
        self.add_page()

        # 1. ЛОГОТИП (Слева сверху)
        logo_path = os.path.join("static", "images", "logo.png")
        if os.path.exists(logo_path):
            # x=10, y=10, w=30 (ширина 30мм)
            self.image(logo_path, 10, 10, 30)
            self.ln(40)  # Отступ вниз после логотипа
        else:
            self.ln(40)  # Если лого нет, просто отступаем

        # 2. НАЗВАНИЕ УНИВЕРА (Если лого нет, можно текстом)
        # self.set_font("CustomFont", "B", 12)
        # self.set_text_color(*self.color_primary)
        # self.cell(0, 10, "ОМИЛАБ УНИВЕРСИТЕТ", ln=True)

        self.ln(40)  # Спускаемся к центру

        # 3. ЗАГОЛОВОК ЛЕКЦИИ (Огромный)
        self.set_font("CustomFont", "B", 36)
        self.set_text_color(0, 0, 0)  # Черный
        # multi_cell позволяет переносить текст, если он длинный
        self.multi_cell(0, 15, self.doc_title)

        self.ln(10)

        # 4. ПОДЗАГОЛОВОК (Типа "Лекция №...")
        self.set_font("CustomFont", "", 16)
        self.set_text_color(50, 50, 50)
        self.cell(0, 10, "Конспект лекции", ln=True)

        # 5. НИЖНИЙ БЛОК (Автор и Дата)
        # Сдвигаемся в самый низ страницы
        self.set_y(-50)

        self.set_draw_color(*self.color_primary)
        self.set_line_width(0.5)
        self.line(10, self.get_y(), 80, self.get_y())  # Короткая линия над именем
        self.ln(5)

        self.set_font("CustomFont", "B", 12)
        self.set_text_color(0, 0, 0)
        self.cell(0, 8, self.author_mark, ln=True)

        self.set_font("CustomFont", "", 10)
        self.set_text_color(100, 100, 100)
        today = datetime.now().strftime("%d.%m.%Y")
        self.cell(0, 8, today, ln=True)

    def generate(self, content: str, filename: str) -> str:
        # 1. Генерируем Титульник
        self.create_cover_page()

        # 2. Генерируем Страницы контента
        self.add_page()  # Вторая страница

        # Заголовок раздела "Введение" (или просто начало текста)
        self.set_font("CustomFont", "B", 18)
        self.set_text_color(*self.color_primary)
        self.cell(0, 10, "1. Основной материал", ln=True)
        self.ln(5)

        # Основной текст
        self.set_font("CustomFont", "", 12)
        self.set_text_color(*self.color_text)
        self.multi_cell(0, 8, content)

        # Сохранение
        output_path = os.path.join("static", "lectures", filename)
        self.output(output_path)
        return output_path