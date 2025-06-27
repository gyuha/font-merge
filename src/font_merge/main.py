import sys
from PyQt6.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QFileDialog, QMessageBox

from .font_selector import FontSelector
from .font_merger import FontMerger


class FontMergeApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("Font Merge - 폰트 합치기")
        self.setGeometry(100, 100, 1000, 700)
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 메인 레이아웃
        main_layout = QVBoxLayout()
        
        # 상단 폰트 선택 영역 (좌우 분할)
        font_layout = QHBoxLayout()
        
        # 좌측 폰트 선택기
        self.left_font = FontSelector("첫 번째 폰트")
        font_layout.addWidget(self.left_font)
        
        # 우측 폰트 선택기
        self.right_font = FontSelector("두 번째 폰트")
        font_layout.addWidget(self.right_font)
        
        main_layout.addLayout(font_layout)
        
        # 하단 합치기 버튼
        self.merge_button = QPushButton("폰트 합치기")
        self.merge_button.setMinimumHeight(50)
        self.merge_button.clicked.connect(self.merge_fonts)
        main_layout.addWidget(self.merge_button)
        
        central_widget.setLayout(main_layout)

    def merge_fonts(self):
        # 폰트 선택 여부 확인
        if not self.left_font.has_font_selected() or not self.right_font.has_font_selected():
            QMessageBox.warning(self, "경고", "두 개의 폰트를 모두 선택해주세요.")
            return
        
        # 선택된 문자셋 확인
        left_charsets = self.left_font.get_selected_charsets()
        right_charsets = self.right_font.get_selected_charsets()
        
        if not left_charsets and not right_charsets:
            QMessageBox.warning(self, "경고", "최소 하나의 문자셋을 선택해주세요.")
            return
        
        # 저장 경로 선택
        save_path, _ = QFileDialog.getSaveFileName(
            self,
            "합쳐진 폰트 저장",
            "merged_font.ttf",
            "TrueType Font (*.ttf)"
        )
        
        if save_path:
            try:
                # 폰트 병합 수행
                merger = FontMerger()
                
                # 폰트 유효성 검사
                is_valid, error_msg = merger.validate_fonts(
                    self.left_font.get_font_path(),
                    self.right_font.get_font_path()
                )
                
                if not is_valid:
                    QMessageBox.warning(self, "오류", error_msg)
                    return
                
                # 폰트 병합 실행
                success = merger.merge_fonts(
                    self.left_font.get_font_path(), left_charsets,
                    self.right_font.get_font_path(), right_charsets,
                    save_path
                )
                
                if success:
                    QMessageBox.information(self, "완료", f"폰트가 성공적으로 합쳐졌습니다.\n저장 위치: {save_path}")
                
            except Exception as e:
                QMessageBox.critical(self, "오류", f"폰트 합치기 중 오류가 발생했습니다: {str(e)}")


def main():
    app = QApplication(sys.argv)
    window = FontMergeApp()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()