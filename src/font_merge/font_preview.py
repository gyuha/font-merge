"""폰트 프리뷰 위젯"""

import os
from PyQt6.QtWidgets import QLabel
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont


class FontPreview(QLabel):
    """폰트 미리보기를 제공하는 위젯"""
    
    def __init__(self, preview_text="가나다라마바사 ABC123"):
        super().__init__()
        self.preview_text = preview_text
        self.init_ui()

    def init_ui(self):
        """UI 초기화"""
        self.setMinimumHeight(80)
        self.setStyleSheet("border: 1px solid gray; background-color: white;")
        self.setText("폰트를 선택하세요")
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)

    def update_preview(self, font_path):
        """폰트 파일로 프리뷰 업데이트"""
        if font_path and os.path.exists(font_path):
            font = QFont()
            font.setFamily(os.path.basename(font_path))
            font.setPointSize(16)
            self.setFont(font)
            self.setText(self.preview_text)
        else:
            self.setText("폰트를 선택하세요")
    
    def set_preview_text(self, text):
        """프리뷰 텍스트 변경"""
        self.preview_text = text
        if self.font().family():
            self.setText(text)