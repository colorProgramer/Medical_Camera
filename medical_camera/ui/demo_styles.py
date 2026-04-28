DEMO_STYLE = """
QWidget {
    background: #edf2f7;
    color: #243447;
    font-family: "Microsoft YaHei UI", "Segoe UI";
    font-size: 13px;
}

QMainWindow {
    background: #edf2f7;
}

QLabel {
    background: transparent;
}

QFrame#TopBar,
QFrame#DemoCard,
QFrame#SectionCard {
    background: #f9fbfd;
    border: 1px solid #dbe5f0;
    border-radius: 18px;
}

QFrame#TopBar {
    border-radius: 22px;
}

QFrame#BrandBadge,
QFrame#InfoPill {
    background: #f2f7fc;
    border: 1px solid #d7e3f0;
    border-radius: 14px;
}

QLabel#BrandTitle {
    color: #0b4ea2;
    font-size: 20px;
    font-weight: 700;
}

QLabel#BrandSubtitle {
    color: #72849a;
    font-size: 11px;
    font-weight: 600;
    letter-spacing: 1px;
}

QLabel#SectionTitle {
    color: #18324d;
    font-size: 16px;
    font-weight: 700;
}

QLabel#BlockTitle {
    color: #35506d;
    font-size: 13px;
    font-weight: 700;
}

QLabel#FieldLabel {
    color: #61778f;
    font-weight: 600;
}

QLabel#ValueBadge {
    background: #f2f6fb;
    border: 1px solid #d7e2f0;
    border-radius: 10px;
    padding: 8px 10px;
    color: #17314c;
}

QPushButton {
    background: #ffffff;
    border: 1px solid #d6e0eb;
    border-radius: 12px;
    padding: 10px 16px;
    color: #17314c;
    font-weight: 600;
}

QPushButton:hover {
    background: #f7fbff;
    border-color: #9fb8d5;
}

QPushButton:pressed {
    background: #ecf3fb;
}

QPushButton#PrimaryButton {
    background: #0b5db3;
    color: white;
    border: none;
}

QPushButton#PrimaryButton:hover {
    background: #0a529d;
}

QPushButton#SuccessButton {
    background: #1f9f68;
    color: white;
    border: none;
}

QPushButton#SuccessButton:hover {
    background: #188558;
}

QPushButton#DangerButton {
    background: #d96574;
    color: white;
    border: none;
}

QPushButton#DangerButton:hover {
    background: #c85765;
}

QPushButton#GhostButton {
    background: #f4f8fc;
    color: #29507d;
    border: 1px solid #d5e1ee;
}

QPushButton#GhostButton:hover {
    background: #edf5fc;
}

QPushButton#TopIconButton {
    min-width: 44px;
    min-height: 44px;
    padding: 0 14px;
}

QPushButton#CompactButton {
    min-width: 38px;
    max-width: 38px;
    min-height: 38px;
    max-height: 38px;
    padding: 0;
}

QLineEdit,
QComboBox,
QTextEdit,
QPlainTextEdit,
QSpinBox,
QDoubleSpinBox {
    background: #ffffff;
    border: 1px solid #d6e0eb;
    border-radius: 12px;
    padding: 8px 10px;
    selection-background-color: #0b5db3;
}

QLineEdit:focus,
QComboBox:focus,
QTextEdit:focus,
QPlainTextEdit:focus,
QSpinBox:focus,
QDoubleSpinBox:focus {
    border-color: #7ea9d4;
}

QComboBox::drop-down {
    border: none;
    width: 26px;
}

QComboBox::down-arrow {
    image: none;
    border-left: 5px solid transparent;
    border-right: 5px solid transparent;
    border-top: 6px solid #5d7792;
    width: 0;
    height: 0;
    margin-right: 8px;
}

QRadioButton,
QCheckBox {
    spacing: 10px;
    color: #22384f;
    font-weight: 600;
}

QRadioButton::indicator,
QCheckBox::indicator {
    width: 18px;
    height: 18px;
    background: #ffffff;
    border: 1px solid #bfd0e5;
}

QRadioButton::indicator {
    border-radius: 9px;
}

QCheckBox::indicator {
    border-radius: 6px;
}

QRadioButton::indicator:hover,
QCheckBox::indicator:hover {
    background: #f4f9ff;
    border-color: #7ea9d4;
}

QRadioButton::indicator:checked,
QCheckBox::indicator:checked {
    background: #0b5db3;
    border-color: #0b5db3;
}

QGroupBox {
    background: #f9fbfd;
    border: 1px solid #dbe5f0;
    border-radius: 16px;
    margin-top: 12px;
    padding-top: 16px;
    font-weight: 700;
}

QGroupBox::title {
    subcontrol-origin: margin;
    left: 14px;
    padding: 0 4px;
}

QTabWidget::pane {
    border: 1px solid #dbe5f0;
    border-radius: 16px;
    background: #f9fbfd;
    top: -1px;
}

QTabBar::tab {
    background: transparent;
    color: #60758b;
    border: 1px solid transparent;
    padding: 10px 18px;
    margin-right: 6px;
    border-top-left-radius: 12px;
    border-top-right-radius: 12px;
    font-weight: 700;
}

QTabBar::tab:selected {
    color: #0b5db3;
    background: #f9fbfd;
    border-color: #dbe5f0;
}

QToolBox {
    background: transparent;
    border: none;
}

QToolBox::tab {
    background: #f4f8fc;
    border: 1px solid #dbe5f0;
    border-radius: 12px;
    color: #34516f;
    font-weight: 700;
    padding: 10px 12px;
}

QToolBox::tab:selected {
    background: #ffffff;
    color: #0b5db3;
}

QTableWidget {
    background: #ffffff;
    alternate-background-color: #f7faff;
    border: 1px solid #dbe5f0;
    border-radius: 14px;
    gridline-color: #e7eef6;
}

QHeaderView::section {
    background: #f2f6fb;
    color: #35506d;
    border: none;
    border-bottom: 1px solid #dbe5f0;
    padding: 10px 8px;
    font-weight: 700;
}

QListWidget {
    background: #ffffff;
    border: 1px solid #dbe5f0;
    border-radius: 14px;
    padding: 8px;
}

QScrollBar:vertical {
    background: transparent;
    width: 12px;
    margin: 6px 0 6px 0;
}

QScrollBar::handle:vertical {
    background: #c8d8ea;
    min-height: 28px;
    border-radius: 6px;
}

QScrollBar::add-line:vertical,
QScrollBar::sub-line:vertical,
QScrollBar::add-page:vertical,
QScrollBar::sub-page:vertical {
    background: transparent;
    height: 0;
}
"""
