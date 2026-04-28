from __future__ import annotations


def get_app_style(theme: str) -> str:
    if theme == "dark":
        return _DARK_STYLE
    return _LIGHT_STYLE


_LIGHT_STYLE = """
QWidget {
    background: #f5f7fa;
    color: #303133;
    font-family: "Microsoft YaHei UI", "Segoe UI";
    font-size: 13px;
}

QMainWindow { background: #f5f7fa; }
QLabel { background: transparent; color: #303133; }

QFrame#TopBar, QFrame#StatusBar {
    background: rgba(255, 255, 255, 235);
    border-bottom: 1px solid #e4e7ed;
}

QFrame#StatusBar { border-top: 1px solid #e4e7ed; border-bottom: none; }
QFrame#SidePanel, QFrame#RightPanel, QFrame#CenterPanel { background: #f5f7fa; }

QFrame#Card, QFrame#BrandBadge, QFrame#InfoPill {
    background: rgba(255, 255, 255, 235);
    border: 1px solid #e4e7ed;
    border-radius: 12px;
}

QLabel#BrandTitle { font-size: 18px; font-weight: 700; color: #1559b7; }
QLabel#BrandSubtitle { font-size: 11px; font-weight: 600; color: #909399; letter-spacing: 1px; }
QLabel#SectionTitle { font-size: 15px; font-weight: 700; color: #303133; }
QLabel#Muted { color: #909399; }
QLabel#FieldLabel { color: #606266; font-weight: 600; }
QLabel#ValueBadge {
    background: #ffffff;
    border: 1px solid #e4e7ed;
    border-radius: 10px;
    padding: 7px 10px;
    color: #303133;
}

QPushButton {
    border: none;
    color: white;
    background-color: #3498db;
    border-radius: 10px;
    text-align: center;
    padding: 9px 16px;
    font-weight: 600;
}
QPushButton:hover { background-color: #2980b9; }
QPushButton:pressed { background-color: #2472a4; }
QPushButton:disabled { color: #ffffff; background-color: #a0cfff; }
QPushButton#PrimaryButton { background-color: #409eff; }
QPushButton#PrimaryButton:hover { background-color: #337ecc; }
QPushButton#PrimaryButton:pressed { background-color: #2a64b0; }
QPushButton#SuccessButton { background-color: #22b573; }
QPushButton#SuccessButton:hover { background-color: #1d9a63; }
QPushButton#SuccessButton:pressed { background-color: #188054; }
QPushButton#DangerButton { background-color: #e56b6f; }
QPushButton#DangerButton:hover { background-color: #cf565a; }
QPushButton#DangerButton:pressed { background-color: #b94347; }
QPushButton#GhostButton {
    background-color: #ffffff;
    color: #409eff;
    border: 1px solid #dcdfe6;
}
QPushButton#GhostButton:hover {
    background-color: #ecf5ff;
    border-color: #c6e2ff;
    color: #409eff;
}
QPushButton#TopIconButton {
    min-width: 44px;
    min-height: 44px;
    padding: 0 12px;
    background-color: #ffffff;
    color: #409eff;
    border: 1px solid #dcdfe6;
}
QPushButton#TopIconButton:hover { background-color: #ecf5ff; border-color: #c6e2ff; }
QPushButton#CompactButton {
    min-width: 38px;
    max-width: 38px;
    min-height: 38px;
    max-height: 38px;
    padding: 0;
}
QPushButton#RefreshDeviceButton {
    min-width: 32px;
    max-width: 32px;
    min-height: 32px;
    max-height: 32px;
    padding: 0;
    background-color: #ffffff;
    color: #409eff;
    border: 1px solid #dcdfe6;
}
QPushButton#RefreshDeviceButton:hover { background-color: #ecf5ff; border-color: #c6e2ff; }
QPushButton#RefreshDeviceButton:pressed { background-color: #d9ecff; border-color: #b3d8ff; }

QComboBox, QLineEdit, QTextEdit, QPlainTextEdit, QSpinBox, QDoubleSpinBox {
    background-color: #ffffff;
    border-radius: 10px;
    border: 1px solid #e0e0e0;
    line-height: 1.2em;
    padding: 0 10px;
    min-height: 36px;
    color: #303133;
}
QComboBox:hover, QLineEdit:hover, QTextEdit:hover, QPlainTextEdit:hover, QSpinBox:hover, QDoubleSpinBox:hover {
    border: 2px solid #55aaff;
}
QComboBox:focus, QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus, QSpinBox:focus, QDoubleSpinBox:focus {
    outline: none;
    border: 2px solid #409eff;
}
QComboBox::drop-down { border: none; width: 25px; }
QComboBox::down-arrow {
    image: none;
    border-left: 5px solid transparent;
    border-right: 5px solid transparent;
    border-top: 6px solid #55aaff;
    width: 0px;
    height: 0px;
    margin-right: 8px;
}
QComboBox QAbstractItemView {
    selection-background-color: #55aaff;
    background-color: #ffffff;
    color: #303133;
    border: 1px solid #e0e0e0;
}

QRadioButton, QCheckBox {
    spacing: 10px;
    background-color: transparent;
    color: #303133;
    font-weight: 600;
}
QCheckBox::indicator, QRadioButton::indicator {
    border: 1px solid #e0e0e0;
    width: 15px;
    height: 15px;
    border-radius: 5px;
    background: #ffffff;
}
QCheckBox::indicator:hover, QRadioButton::indicator:hover { background-color: #dfdfdf; border: 2px solid #ffffff; }
QCheckBox::indicator:checked, QRadioButton::indicator:checked { background-color: #55aaff; border: 2px solid #3c78b4; }

QListWidget {
    border-radius: 8px;
    alternate-background-color: #f5f7fa;
    selection-background-color: #f5f7fa;
    background-color: rgba(255, 255, 255, 240);
    color: #606266;
    padding: 10px;
    border: 1px solid #ebeef5;
    outline: none;
}

QGroupBox {
    border: 1px solid #e0e0e0;
    border-radius: 10px;
    margin-top: 8px;
    padding-top: 8px;
    background-color: rgba(255, 255, 255, 220);
    font-weight: 700;
}
QGroupBox::title {
    subcontrol-origin: margin;
    left: 8px;
    padding: 0 3px;
    color: rgb(52, 152, 219);
}

QScrollBar:horizontal { background: #ffffff; height: 8px; margin: 0px 21px 0 21px; }
QScrollBar::handle:horizontal { background: #55aaff; min-width: 25px; border-radius: 4px; }
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal, QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { background: #dfdfdf; }
QScrollBar:vertical { background-color: #ffffff; width: 8px; margin: 21px 0 21px 0; }
QScrollBar::handle:vertical { background: #55aaff; min-height: 25px; border-radius: 4px; }
"""


_DARK_STYLE = """
QWidget {
    background: #131a23;
    color: #dbe7f4;
    font-family: "Microsoft YaHei UI", "Segoe UI";
    font-size: 13px;
}

QMainWindow { background: #131a23; }
QLabel { background: transparent; color: #dbe7f4; }

QFrame#TopBar, QFrame#StatusBar {
    background: rgba(22, 30, 40, 245);
    border-bottom: 1px solid #2c3948;
}

QFrame#StatusBar { border-top: 1px solid #2c3948; border-bottom: none; }
QFrame#SidePanel, QFrame#RightPanel, QFrame#CenterPanel { background: #131a23; }

QFrame#Card, QFrame#BrandBadge, QFrame#InfoPill {
    background: rgba(22, 30, 40, 235);
    border: 1px solid #334354;
    border-radius: 12px;
}

QLabel#BrandTitle { font-size: 18px; font-weight: 700; color: #8bc0ff; }
QLabel#BrandSubtitle { font-size: 11px; font-weight: 600; color: #8a9bb0; letter-spacing: 1px; }
QLabel#SectionTitle { font-size: 15px; font-weight: 700; color: #eef5fd; }
QLabel#Muted { color: #95a7bb; }
QLabel#FieldLabel { color: #a6b7c9; font-weight: 600; }
QLabel#ValueBadge {
    background: #1b2430;
    border: 1px solid #344557;
    border-radius: 10px;
    padding: 7px 10px;
    color: #e8f1fb;
}

QPushButton {
    border: none;
    color: white;
    background-color: #2b79d0;
    border-radius: 10px;
    text-align: center;
    padding: 9px 16px;
    font-weight: 600;
}
QPushButton:hover { background-color: #2368b4; }
QPushButton:pressed { background-color: #1d5899; }
QPushButton:disabled { color: #d1d9e3; background-color: #506579; }
QPushButton#PrimaryButton { background-color: #409eff; }
QPushButton#PrimaryButton:hover { background-color: #337ecc; }
QPushButton#PrimaryButton:pressed { background-color: #2a64b0; }
QPushButton#SuccessButton { background-color: #27ae78; }
QPushButton#SuccessButton:hover { background-color: #219966; }
QPushButton#SuccessButton:pressed { background-color: #1b8055; }
QPushButton#DangerButton { background-color: #d16b75; }
QPushButton#DangerButton:hover { background-color: #bf5a64; }
QPushButton#DangerButton:pressed { background-color: #a94a53; }
QPushButton#GhostButton {
    background-color: #1b2430;
    color: #8bc0ff;
    border: 1px solid #344557;
}
QPushButton#GhostButton:hover {
    background-color: #223041;
    border-color: #4b6a89;
    color: #a9d0ff;
}
QPushButton#TopIconButton {
    min-width: 44px;
    min-height: 44px;
    padding: 0 12px;
    background-color: #1b2430;
    color: #8bc0ff;
    border: 1px solid #344557;
}
QPushButton#TopIconButton:hover { background-color: #223041; border-color: #4b6a89; }
QPushButton#CompactButton {
    min-width: 38px;
    max-width: 38px;
    min-height: 38px;
    max-height: 38px;
    padding: 0;
}
QPushButton#RefreshDeviceButton {
    min-width: 32px;
    max-width: 32px;
    min-height: 32px;
    max-height: 32px;
    padding: 0;
    background-color: #1b2430;
    color: #8bc0ff;
    border: 1px solid #344557;
}
QPushButton#RefreshDeviceButton:hover { background-color: #223041; border-color: #4b6a89; }
QPushButton#RefreshDeviceButton:pressed { background-color: #2a3a50; border-color: #5a7a99; }

QComboBox, QLineEdit, QTextEdit, QPlainTextEdit, QSpinBox, QDoubleSpinBox {
    background-color: #1b2430;
    border-radius: 10px;
    border: 1px solid #344557;
    line-height: 1.2em;
    padding: 0 10px;
    min-height: 36px;
    color: #e8f1fb;
}
QComboBox:hover, QLineEdit:hover, QTextEdit:hover, QPlainTextEdit:hover, QSpinBox:hover, QDoubleSpinBox:hover {
    border: 2px solid #4e9fff;
}
QComboBox:focus, QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus, QSpinBox:focus, QDoubleSpinBox:focus {
    outline: none;
    border: 2px solid #76b7ff;
}
QComboBox::drop-down { border: none; width: 25px; }
QComboBox::down-arrow {
    image: none;
    border-left: 5px solid transparent;
    border-right: 5px solid transparent;
    border-top: 6px solid #8bc0ff;
    width: 0px;
    height: 0px;
    margin-right: 8px;
}
QComboBox QAbstractItemView {
    selection-background-color: #2b79d0;
    background-color: #1b2430;
    color: #e8f1fb;
    border: 1px solid #344557;
}

QRadioButton, QCheckBox {
    spacing: 10px;
    background-color: transparent;
    color: #dbe7f4;
    font-weight: 600;
}
QCheckBox::indicator, QRadioButton::indicator {
    border: 1px solid #546577;
    width: 15px;
    height: 15px;
    border-radius: 5px;
    background: #1b2430;
}
QCheckBox::indicator:hover, QRadioButton::indicator:hover { background-color: #233141; border: 2px solid #334354; }
QCheckBox::indicator:checked, QRadioButton::indicator:checked { background-color: #409eff; border: 2px solid #76b7ff; }

QListWidget {
    border-radius: 8px;
    alternate-background-color: #1a2430;
    selection-background-color: #1a2430;
    background-color: rgba(27, 36, 48, 240);
    color: #a9bbcf;
    padding: 10px;
    border: 1px solid #344557;
    outline: none;
}

QGroupBox {
    border: 1px solid #344557;
    border-radius: 10px;
    margin-top: 8px;
    padding-top: 8px;
    background-color: rgba(22, 30, 40, 220);
    font-weight: 700;
}
QGroupBox::title {
    subcontrol-origin: margin;
    left: 8px;
    padding: 0 3px;
    color: #8bc0ff;
}

QScrollBar:horizontal { background: #1b2430; height: 8px; margin: 0px 21px 0 21px; }
QScrollBar::handle:horizontal { background: #409eff; min-width: 25px; border-radius: 4px; }
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal, QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { background: #233141; }
QScrollBar:vertical { background-color: #1b2430; width: 8px; margin: 21px 0 21px 0; }
QScrollBar::handle:vertical { background: #409eff; min-height: 25px; border-radius: 4px; }
"""
