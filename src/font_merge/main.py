import os
import sys

# Qt 디버그 로그 억제
os.environ["QT_LOGGING_RULES"] = "*=false"

from PyQt6.QtWidgets import (
    QApplication,
    QButtonGroup,
    QFileDialog,
    QGroupBox,
    QHBoxLayout,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QRadioButton,
    QVBoxLayout,
    QWidget,
)

from .font_merger import FontMerger
from .font_selector import FontSelector


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

        # 두 FontSelector를 서로 연결
        self.left_font.set_other_selector(self.right_font)
        self.right_font.set_other_selector(self.left_font)

        main_layout.addLayout(font_layout)

        # 병합 옵션 선택 영역
        merge_options_group = QGroupBox("병합 옵션")
        merge_options_layout = QVBoxLayout()

        self.merge_option_group = QButtonGroup()
        
        self.option_default = QRadioButton("기존 설정 사용 (호환되지 않으면 실패)")
        self.option_unify_upm = QRadioButton("Units per em 통일 (더 큰 값으로)")
        self.option_lenient = QRadioButton("관대한 병합 옵션 (강제 병합)")
        
        self.option_default.setChecked(True)  # 기본값
        
        self.merge_option_group.addButton(self.option_default, 0)
        self.merge_option_group.addButton(self.option_unify_upm, 1)
        self.merge_option_group.addButton(self.option_lenient, 2)
        
        merge_options_layout.addWidget(self.option_default)
        merge_options_layout.addWidget(self.option_unify_upm)
        merge_options_layout.addWidget(self.option_lenient)
        
        merge_options_group.setLayout(merge_options_layout)
        main_layout.addWidget(merge_options_group)

        # 하단 합치기 버튼
        self.merge_button = QPushButton("폰트 합치기")
        self.merge_button.setMinimumHeight(50)
        self.merge_button.clicked.connect(self.merge_fonts)
        main_layout.addWidget(self.merge_button)

        central_widget.setLayout(main_layout)

    def merge_fonts(self):
        # 폰트 선택 여부 확인
        if (
            not self.left_font.has_font_selected()
            or not self.right_font.has_font_selected()
        ):
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
            self, "합쳐진 폰트 저장", "merged_font.ttf", "TrueType Font (*.ttf)"
        )

        if save_path:
            try:
                # 폰트 병합 수행
                merger = FontMerger()

                # 폰트 유효성 검사
                is_valid, error_msg = merger.validate_fonts(
                    self.left_font.get_font_path(), self.right_font.get_font_path()
                )

                if not is_valid:
                    QMessageBox.warning(self, "오류", error_msg)
                    return

                # 선택된 병합 옵션 가져오기
                merge_option = self.merge_option_group.checkedId()
                # 폰트 병합 실행
                success = merger.merge_fonts(
                    self.left_font.get_font_path(),
                    left_charsets,
                    self.right_font.get_font_path(),
                    right_charsets,
                    save_path,
                    merge_option,
                )

                if success:
                    QMessageBox.information(
                        self,
                        "완료",
                        f"폰트가 성공적으로 합쳐졌습니다.\n저장 위치: {save_path}",
                    )

            except Exception as e:
                import traceback
                error_details = traceback.format_exc()
                print(f"폰트 합치기 오류 세부사항:\n{error_details}")
                
                # 현재 선택된 옵션에 따라 다른 안내 메시지 제공
                current_option = self.merge_option_group.checkedId()
                suggestion = self._get_merge_option_suggestion(current_option, str(e))
                
                QMessageBox.critical(
                    self, 
                    "폰트 병합 실패", 
                    f"폰트 합치기 중 오류가 발생했습니다:\n\n{str(e)}\n\n{suggestion}"
                )

    def _get_merge_option_suggestion(self, current_option, error_message):
        """현재 옵션과 오류 메시지에 따라 적절한 제안 제공"""
        
        # Units per em 관련 오류 감지
        if "Expected all items to be equal" in error_message and "[" in error_message:
            if current_option == 0:  # 기존 설정 사용
                return ("💡 해결책: 두 폰트의 Units per em 값이 다릅니다.\n"
                       "병합 옵션에서 'Units per em 통일'을 선택해보세요.")
            elif current_option == 1:  # UPM 통일
                return ("💡 해결책: UPM 통일로도 해결되지 않았습니다.\n"
                       "'관대한 병합 옵션'을 시도해보세요.")
        
        # 일반적인 호환성 문제
        if "merge" in error_message.lower() or "table" in error_message.lower():
            if current_option == 0:  # 기존 설정 사용
                return ("💡 해결책: 폰트 호환성 문제가 발생했습니다.\n"
                       "병합 옵션에서 'Units per em 통일' 또는 '관대한 병합 옵션'을 시도해보세요.")
            elif current_option == 1:  # UPM 통일
                return ("💡 해결책: '관대한 병합 옵션'을 시도해보세요.\n"
                       "이 옵션은 호환성 문제를 우회하여 강제로 병합합니다.")
        
        # 파일 경로 또는 권한 관련 오류
        if "permission" in error_message.lower() or "access" in error_message.lower():
            return ("💡 해결책: 파일 접근 권한 문제입니다.\n"
                   "다른 위치에 저장하거나 파일이 사용 중이 아닌지 확인해보세요.")
        
        # 파일 형식 오류
        if "format" in error_message.lower() or "invalid" in error_message.lower():
            return ("💡 해결책: 폰트 파일 형식에 문제가 있을 수 있습니다.\n"
                   "다른 폰트 파일을 시도하거나 파일이 손상되지 않았는지 확인해보세요.")
        
        # 기본 제안
        if current_option == 0:
            return ("💡 해결책: 다른 병합 옵션을 시도해보세요:\n"
                   "• Units per em 통일: 폰트 크기 단위를 맞춤\n"
                   "• 관대한 병합 옵션: 호환성 문제를 우회하여 강제 병합")
        elif current_option == 1:
            return ("💡 해결책: '관대한 병합 옵션'을 시도해보세요.\n"
                   "이 옵션은 더 강력한 호환성 처리를 제공합니다.")
        else:  # 관대한 옵션도 실패
            return ("💡 해결책: 모든 병합 옵션이 실패했습니다.\n"
                   "• 다른 폰트 파일을 시도해보세요\n"
                   "• 선택한 문자셋을 줄여보세요\n"
                   "• 폰트 파일이 손상되지 않았는지 확인해보세요")


def main():
    app = QApplication(sys.argv)
    window = FontMergeApp()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
