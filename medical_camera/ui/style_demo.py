from __future__ import annotations

import sys
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon, QPixmap
from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QComboBox,
    QDoubleSpinBox,
    QFrame,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QMainWindow,
    QPushButton,
    QRadioButton,
    QStyle,
    QTabWidget,
    QTableWidget,
    QTableWidgetItem,
    QTextEdit,
    QToolBox,
    QVBoxLayout,
    QWidget,
)

from medical_camera.ui.demo_styles import DEMO_STYLE


class StyleDemoWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Medical UI Style Demo")
        self.resize(1720, 980)
        self.setStyleSheet(DEMO_STYLE)

        central = QWidget()
        self.setCentralWidget(central)
        root = QVBoxLayout(central)
        root.setContentsMargins(18, 18, 18, 18)
        root.setSpacing(16)

        root.addWidget(self._build_top_bar())

        body = QHBoxLayout()
        body.setSpacing(16)
        body.addWidget(self._build_left_column(), 3)
        body.addWidget(self._build_center_column(), 5)
        body.addWidget(self._build_right_column(), 4)
        root.addLayout(body, 1)

    def _build_top_bar(self) -> QWidget:
        bar = QFrame()
        bar.setObjectName("TopBar")
        layout = QHBoxLayout(bar)
        layout.setContentsMargins(18, 14, 18, 14)
        layout.setSpacing(14)

        badge = QFrame()
        badge.setObjectName("BrandBadge")
        badge_layout = QHBoxLayout(badge)
        badge_layout.setContentsMargins(12, 10, 16, 10)
        badge_layout.setSpacing(12)
        logo = QLabel()
        logo.setFixedSize(40, 40)
        logo.setAlignment(Qt.AlignCenter)
        logo.setPixmap(self._load_logo_pixmap())
        badge_layout.addWidget(logo)

        text_layout = QVBoxLayout()
        text_layout.setContentsMargins(0, 0, 0, 0)
        text_layout.setSpacing(2)
        title = QLabel("CIQT 医疗相机")
        title.setObjectName("BrandTitle")
        subtitle = QLabel("STYLE DEMO PANEL")
        subtitle.setObjectName("BrandSubtitle")
        text_layout.addWidget(title)
        text_layout.addWidget(subtitle)
        badge_layout.addLayout(text_layout)
        layout.addWidget(badge)

        layout.addStretch(1)

        info = QFrame()
        info.setObjectName("InfoPill")
        info_layout = QHBoxLayout(info)
        info_layout.setContentsMargins(14, 10, 14, 10)
        info_layout.setSpacing(10)
        info_layout.addWidget(QLabel("设计状态：控件风格校准中"))
        info_layout.addWidget(self._value_badge("浅色专业工作台"))
        layout.addWidget(info)

        top_buttons = (
            ("主题", self.style().standardIcon(QStyle.SP_DialogResetButton)),
            ("语言", self.style().standardIcon(QStyle.SP_FileDialogDetailedView)),
            ("帮助", self.style().standardIcon(QStyle.SP_MessageBoxQuestion)),
        )
        for text, icon in top_buttons:
            button = QPushButton(icon, text)
            button.setObjectName("TopIconButton")
            layout.addWidget(button)

        return bar

    def _build_left_column(self) -> QWidget:
        column = QWidget()
        layout = QVBoxLayout(column)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(16)
        layout.addWidget(self._build_buttons_card())
        layout.addWidget(self._build_fields_card())
        layout.addWidget(self._build_choice_card())
        layout.addStretch(1)
        return column

    def _build_center_column(self) -> QWidget:
        column = QWidget()
        layout = QVBoxLayout(column)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(16)
        layout.addWidget(self._build_tab_card(), 3)
        layout.addWidget(self._build_table_card(), 2)
        return column

    def _build_right_column(self) -> QWidget:
        column = QWidget()
        layout = QVBoxLayout(column)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(16)
        layout.addWidget(self._build_toolbox_card(), 3)
        layout.addWidget(self._build_labels_card(), 2)
        return column

    def _build_buttons_card(self) -> QWidget:
        card = self._card()
        layout = QVBoxLayout(card)
        layout.addWidget(self._section_title("PushButton 样式"))

        grid = QGridLayout()
        buttons = [
            ("Primary", "PrimaryButton", self.style().standardIcon(QStyle.SP_DialogApplyButton)),
            ("Success", "SuccessButton", self.style().standardIcon(QStyle.SP_DialogYesButton)),
            ("Danger", "DangerButton", self.style().standardIcon(QStyle.SP_DialogCancelButton)),
            ("Ghost", "GhostButton", self.style().standardIcon(QStyle.SP_FileDialogInfoView)),
            ("Normal", "", self.style().standardIcon(QStyle.SP_DialogOpenButton)),
            ("Save", "", self.style().standardIcon(QStyle.SP_DialogSaveButton)),
        ]
        for index, (text, object_name, icon) in enumerate(buttons):
            button = QPushButton(icon, text)
            if object_name:
                button.setObjectName(object_name)
            grid.addWidget(button, index // 2, index % 2)

        layout.addLayout(grid)

        compact_row = QHBoxLayout()
        compact_row.addWidget(self._block_title("紧凑按钮"))
        for text in ("−", "+", "i"):
            button = QPushButton(text)
            button.setObjectName("CompactButton")
            compact_row.addWidget(button)
        compact_row.addStretch(1)
        layout.addLayout(compact_row)
        return card

    def _build_fields_card(self) -> QWidget:
        card = self._card()
        layout = QVBoxLayout(card)
        layout.addWidget(self._section_title("LineEdit / ComboBox / 数值输入"))

        form = QGridLayout()
        form.addWidget(self._field_label("QLineEdit"), 0, 0)
        form.addWidget(QLineEdit("海康工业相机"), 0, 1)

        form.addWidget(self._field_label("QComboBox"), 1, 0)
        combo = QComboBox()
        combo.addItems(["1920 x 1080", "3840 x 2160", "1280 x 720"])
        form.addWidget(combo, 1, 1)

        form.addWidget(self._field_label("QDoubleSpinBox"), 2, 0)
        spin = QDoubleSpinBox()
        spin.setDecimals(2)
        spin.setRange(0.0, 9999.0)
        spin.setValue(6.00)
        form.addWidget(spin, 2, 1)
        layout.addLayout(form)
        return card

    def _build_choice_card(self) -> QWidget:
        card = self._card()
        layout = QVBoxLayout(card)
        layout.addWidget(self._section_title("CheckBox / RadioButton / GroupBox"))

        group = QGroupBox("识别方式")
        group_layout = QVBoxLayout(group)

        radio_row = QHBoxLayout()
        radio_a = QRadioButton("单次识别")
        radio_b = QRadioButton("实时识别")
        radio_a.setChecked(True)
        radio_row.addWidget(radio_a)
        radio_row.addWidget(radio_b)
        group_layout.addLayout(radio_row)

        check_items = ("圆视场边界", "70%视场圆", "矩形视场(ROI)", "画面中心米字线")
        for index, text in enumerate(check_items):
            checkbox = QCheckBox(text)
            checkbox.setChecked(index < 2)
            group_layout.addWidget(checkbox)

        layout.addWidget(group)
        return card

    def _build_tab_card(self) -> QWidget:
        card = self._card()
        layout = QVBoxLayout(card)
        layout.addWidget(self._section_title("TabWidget"))

        tabs = QTabWidget()
        tabs.addTab(self._tab_page("设备总览", "这里用于看 tab 的页签、留白和密度。"), "设备总览")
        tabs.addTab(self._tab_page("识别参数", "这里可继续试识别参数卡片和控件排列。"), "识别参数")
        tabs.addTab(self._tab_page("日志输出", "这里可试日志、说明文案、错误提示风格。"), "日志输出")
        layout.addWidget(tabs)
        return card

    def _build_table_card(self) -> QWidget:
        card = self._card()
        layout = QVBoxLayout(card)
        layout.addWidget(self._section_title("TableWidget"))

        table = QTableWidget(4, 3)
        table.setAlternatingRowColors(True)
        table.setHorizontalHeaderLabels(["参数", "当前值", "状态"])
        rows = [
            ("分辨率", "3840 x 2160", "已应用"),
            ("曝光", "8000 us", "手动"),
            ("增益", "6.0 dB", "手动"),
            ("白平衡", "R:1.00 G:1.00 B:1.00", "自动"),
        ]
        for row, values in enumerate(rows):
            for col, value in enumerate(values):
                table.setItem(row, col, QTableWidgetItem(value))
        table.verticalHeader().setVisible(False)
        layout.addWidget(table)
        return card

    def _build_toolbox_card(self) -> QWidget:
        card = self._card()
        layout = QVBoxLayout(card)
        layout.addWidget(self._section_title("ToolBox"))

        toolbox = QToolBox()
        toolbox.addItem(self._toolbox_page("设备与采集"), "设备与采集")
        toolbox.addItem(self._toolbox_page("相机参数"), "相机参数")
        toolbox.addItem(self._toolbox_page("显示叠加"), "显示叠加")
        layout.addWidget(toolbox)
        return card

    def _build_labels_card(self) -> QWidget:
        card = self._card()
        layout = QVBoxLayout(card)
        layout.addWidget(self._section_title("Label / 文本块 / 列表"))

        badge_row = QHBoxLayout()
        badge_row.addWidget(self._field_label("字段标签"))
        badge_row.addWidget(self._value_badge("Value Badge"))
        badge_row.addStretch(1)
        layout.addLayout(badge_row)

        text = QTextEdit()
        text.setPlainText(
            "这块用于看说明文案、段落留白、输入框边框和整体浅色风格是否协调。\n\n"
            "你后面可以直接指出：按钮太重、边框太浅、字号太小、卡片太松、图标不够多。"
        )
        text.setFixedHeight(120)
        layout.addWidget(text)

        list_widget = QListWidget()
        list_widget.addItems(
            [
                "15:32:11 [系统] 样式 Demo 已启动",
                "15:32:12 [设计] 当前主题：浅色专业工作台",
                "15:32:13 [建议] 下一步可继续调整 groupbox 和 tab 样式",
            ]
        )
        layout.addWidget(list_widget)
        return card

    def _tab_page(self, title: str, description: str) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.addWidget(self._block_title(title))
        layout.addWidget(QLabel(description))
        layout.addStretch(1)
        return page

    def _toolbox_page(self, title: str) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.addWidget(self._block_title(title))
        layout.addWidget(QPushButton(self.style().standardIcon(QStyle.SP_DialogYesButton), "主动作"))
        ghost = QPushButton(self.style().standardIcon(QStyle.SP_FileDialogInfoView), "次动作")
        ghost.setObjectName("GhostButton")
        layout.addWidget(ghost)
        line_edit = QLineEdit()
        line_edit.setPlaceholderText(f"{title} 输入示例")
        layout.addWidget(line_edit)
        layout.addWidget(QCheckBox("启用此项"))
        layout.addStretch(1)
        return page

    def _card(self) -> QFrame:
        card = QFrame()
        card.setObjectName("DemoCard")
        layout = QVBoxLayout(card)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(14)
        return card

    def _section_title(self, text: str) -> QLabel:
        label = QLabel(text)
        label.setObjectName("SectionTitle")
        return label

    def _block_title(self, text: str) -> QLabel:
        label = QLabel(text)
        label.setObjectName("BlockTitle")
        return label

    def _field_label(self, text: str) -> QLabel:
        label = QLabel(text)
        label.setObjectName("FieldLabel")
        return label

    def _value_badge(self, text: str) -> QLabel:
        label = QLabel(text)
        label.setObjectName("ValueBadge")
        return label

    def _load_logo_pixmap(self) -> QPixmap:
        branding_dir = Path(__file__).resolve().parent.parent.parent / "assets" / "branding"
        for file_name in ("company_logo.png", "company_logo.svg", "company_logo.jpg"):
            file_path = branding_dir / file_name
            if file_path.exists():
                pixmap = QPixmap(str(file_path))
                if not pixmap.isNull():
                    return pixmap.scaled(34, 34, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        return self.style().standardIcon(QStyle.SP_ComputerIcon).pixmap(30, 30)


def main() -> int:
    app = QApplication(sys.argv)
    icon_path = Path(__file__).resolve().parent.parent.parent / "assets" / "branding" / "app_icon.ico"
    if icon_path.exists():
        app.setWindowIcon(QIcon(str(icon_path)))
    window = StyleDemoWindow()
    window.show()
    return app.exec()
