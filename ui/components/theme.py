"""
ui/components/theme.py
Generates the application QSS stylesheet for light and dark modes,
built around the UAIMS teal brand palette.
"""

import config


def get_stylesheet(mode: str = "light") -> str:
    if mode == "dark":
        bg = "#121417"
        surface = "#1B1F24"
        surface_alt = "#22272E"
        text = "#E6E8EB"
        text_muted = "#9BA3AE"
        border = "#2E343C"
    else:
        bg = "#F4F7F8"
        surface = "#FFFFFF"
        surface_alt = "#EAF4F5"
        text = "#1B2A2E"
        text_muted = "#5A6B70"
        border = "#D8E2E4"

    primary = config.THEME_PRIMARY
    primary_dark = config.THEME_PRIMARY_DARK
    accent = config.THEME_ACCENT
    danger = config.THEME_DANGER
    success = config.THEME_SUCCESS

    return f"""
    QWidget {{
        background-color: {bg};
        color: {text};
        font-family: 'Segoe UI', 'Cantarell', sans-serif;
        font-size: 13px;
    }}

    QMainWindow, QDialog {{
        background-color: {bg};
    }}

    #Sidebar {{
        background-color: {primary_dark};
        min-width: 230px;
        max-width: 230px;
    }}

    #Sidebar QPushButton {{
        text-align: left;
        padding: 12px 18px;
        border: none;
        color: #E9F4F5;
        border-radius: 0px;
        font-size: 13px;
    }}

    #Sidebar QPushButton:hover {{
        background-color: {primary};
    }}

    #Sidebar QPushButton:checked {{
        background-color: {primary};
        border-left: 4px solid {accent};
        font-weight: 600;
    }}

    #TopBar {{
        background-color: {surface};
        border-bottom: 1px solid {border};
        min-height: 56px;
    }}

    #Card {{
        background-color: {surface};
        border: 1px solid {border};
        border-radius: 10px;
    }}

    #CardAlt {{
        background-color: {surface_alt};
        border: 1px solid {border};
        border-radius: 10px;
    }}

    QLabel#PageTitle {{
        font-size: 20px;
        font-weight: 700;
        color: {primary_dark if mode == "light" else primary};
    }}

    QLabel#StatValue {{
        font-size: 26px;
        font-weight: 700;
    }}

    QLabel#StatLabel {{
        color: {text_muted};
        font-size: 12px;
    }}

    QPushButton {{
        background-color: {primary};
        color: white;
        border: none;
        border-radius: 6px;
        padding: 8px 16px;
        font-weight: 600;
    }}

    QPushButton:hover {{
        background-color: {primary_dark};
    }}

    QPushButton:disabled {{
        background-color: {border};
        color: {text_muted};
    }}

    QPushButton#DangerButton {{
        background-color: {danger};
    }}

    QPushButton#SuccessButton {{
        background-color: {success};
    }}

    QPushButton#SecondaryButton {{
        background-color: {surface_alt};
        color: {text};
        border: 1px solid {border};
    }}

    QLineEdit, QComboBox, QDateEdit, QSpinBox, QDoubleSpinBox, QTextEdit, QPlainTextEdit {{
        background-color: {surface};
        border: 1px solid {border};
        border-radius: 6px;
        padding: 6px 8px;
        color: {text};
    }}

    QLineEdit:focus, QComboBox:focus {{
        border: 1px solid {primary};
    }}

    QTableWidget {{
        background-color: {surface};
        alternate-background-color: {surface_alt};
        gridline-color: {border};
        border: 1px solid {border};
        border-radius: 6px;
    }}

    QHeaderView::section {{
        background-color: {primary_dark};
        color: white;
        padding: 6px;
        border: none;
        font-weight: 600;
    }}

    QTabWidget::pane {{
        border: 1px solid {border};
        border-radius: 6px;
    }}

    QTabBar::tab {{
        background: {surface_alt};
        padding: 8px 16px;
        border-top-left-radius: 6px;
        border-top-right-radius: 6px;
        margin-right: 2px;
    }}

    QTabBar::tab:selected {{
        background: {primary};
        color: white;
    }}

    QScrollBar:vertical {{
        background: {surface};
        width: 10px;
    }}

    QScrollBar::handle:vertical {{
        background: {border};
        border-radius: 5px;
    }}

    QToolTip {{
        background-color: {primary_dark};
        color: white;
        border: none;
        padding: 4px;
    }}
    """
