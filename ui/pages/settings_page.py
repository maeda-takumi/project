from __future__ import annotations

from PySide6.QtWidgets import QWidget, QVBoxLayout, QGroupBox, QFormLayout, QLineEdit, QCheckBox, QHBoxLayout, QPushButton, QLabel


class SettingsPage(QWidget):
    def __init__(self):
        super().__init__()

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(14)

        self.api_group = QGroupBox("API設定")
        form = QFormLayout(self.api_group)

        self.api_name = QLineEdit()
        self.api_base_url = QLineEdit()
        self.api_password = QLineEdit()
        self.api_password.setEchoMode(QLineEdit.Password)
        self.api_active = QCheckBox("有効")
        self.api_active.setChecked(True)

        form.addRow("名前", self.api_name)
        form.addRow("Base URL", self.api_base_url)
        form.addRow("APIパスワード", self.api_password)
        form.addRow("", self.api_active)

        btn_row = QHBoxLayout()
        self.btn_api_load = QPushButton("読込")
        self.btn_api_save = QPushButton("保存")
        self.btn_api_save.setObjectName("primary")
        btn_row.addWidget(self.btn_api_load)
        btn_row.addWidget(self.btn_api_save)
        form.addRow(btn_row)

        api_hint = QLabel("※ api_accounts の最新(または有効)レコードを読み書きします")
        api_hint.setObjectName("muted")
        api_hint.setWordWrap(True)
        form.addRow(api_hint)

        layout.addWidget(self.api_group)
        layout.addStretch(1)
