import os
import re
import sys

# Qt 디버그 로그 억제
os.environ["QT_LOGGING_RULES"] = "*=false"

from fontTools.ttLib import TTFont
from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import (
    QApplication,
    QButtonGroup,
    QFileDialog,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QRadioButton,
    QVBoxLayout,
    QWidget,
)

# PyInstaller에서도 작동하는 안전한 import
try:
    # 상대 import 시도
    from .font_merger import FontMerger
    from .font_selector import FontSelector
except (ImportError, ValueError):
    # 절대 import 시도 (PyInstaller 환경)
    from font_merge.font_merger import FontMerger
    from font_merge.font_selector import FontSelector


class FontMergeApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("Font Merge - 폰트 합치기")
        self.setGeometry(100, 100, 1000, 700)

        # 아이콘 설정
        icon_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)), "..", "..", "icon.png"
        )
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))

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

        # 폰트 변경 시 UPM 차이 확인을 위한 연결
        self.left_font.font_changed.connect(self.check_upm_difference)
        self.right_font.font_changed.connect(self.check_upm_difference)

        main_layout.addLayout(font_layout)

        # 옵션 영역 (가로로 배치)
        options_group = QGroupBox("옵션")
        options_main_layout = QHBoxLayout()

        # 왼쪽: 폰트 이름 설정
        font_name_group = QGroupBox("폰트 이름 설정")
        font_name_layout = QVBoxLayout()

        self.font_name_option_group = QButtonGroup()

        self.name_option_default = QRadioButton("기본 폰트 이름 사용")
        self.name_option_custom = QRadioButton("폰트 이름 입력")

        self.name_option_default.setChecked(True)

        self.font_name_option_group.addButton(self.name_option_default, 0)
        self.font_name_option_group.addButton(self.name_option_custom, 1)

        font_name_layout.addWidget(self.name_option_default)
        font_name_layout.addWidget(self.name_option_custom)

        # 폰트 이름 입력 필드
        self.font_name_input = QLineEdit()
        self.font_name_input.setPlaceholderText("사용자 정의 폰트 이름을 입력하세요")
        self.font_name_input.setEnabled(False)
        font_name_layout.addWidget(self.font_name_input)

        # 라디오 버튼 상태에 따라 입력 필드 활성화/비활성화
        self.name_option_custom.toggled.connect(self.font_name_input.setEnabled)

        font_name_group.setLayout(font_name_layout)

        # 오른쪽: 병합 옵션
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

        # 가로 레이아웃에 추가 (1:1 비율)
        options_main_layout.addWidget(font_name_group, 1)
        options_main_layout.addWidget(merge_options_group, 1)

        options_group.setLayout(options_main_layout)
        main_layout.addWidget(options_group)

        # UPM 차이 경고 라벨
        self.upm_warning_label = QLabel("")
        self.upm_warning_label.setStyleSheet(
            "color: #d32f2f; background-color: #fff3e0; "
            "border: 1px solid #ffb74d; border-radius: 4px; "
            "padding: 8px; font-size: 12px; font-weight: bold;"
        )
        self.upm_warning_label.setWordWrap(True)
        self.upm_warning_label.setVisible(False)
        main_layout.addWidget(self.upm_warning_label)

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

        # 폰트 이름 옵션 확인 (저장 파일명 결정용)
        default_filename = "merged_font.ttf"
        if self.font_name_option_group.checkedId() == 1:  # 사용자 정의 이름
            custom_name = self.font_name_input.text().strip()
            if custom_name:
                # 파일명에 사용할 수 없는 문자 제거
                safe_name = self._sanitize_filename(custom_name)
                default_filename = f"{safe_name}.ttf"
        else:
            # 기본 폰트 이름 사용
            base_font_path = (
                self.left_font.get_font_path()
                if self.left_font.is_base_font()
                else self.right_font.get_font_path()
            )
            base_font_name = self._extract_font_name(base_font_path)
            if base_font_name:
                safe_name = self._sanitize_filename(base_font_name)
                default_filename = f"{safe_name}.ttf"

        # 저장 경로 선택
        save_path, _ = QFileDialog.getSaveFileName(
            self, "합쳐진 폰트 저장", default_filename, "TrueType Font (*.ttf)"
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

                # 폰트 이름 옵션 가져오기
                font_name = None
                if self.font_name_option_group.checkedId() == 1:  # 사용자 정의 이름
                    custom_name = self.font_name_input.text().strip()
                    if custom_name:
                        font_name = custom_name

                # 기본 폰트 설정에 따라 순서 결정 (사용자 선택 존중)
                if self.left_font.is_base_font():
                    base_font_path = self.left_font.get_font_path()
                    base_charsets = left_charsets
                    secondary_font_path = self.right_font.get_font_path()
                    secondary_charsets = right_charsets
                    print("✓ 왼쪽 폰트를 기본 폰트로 사용합니다 (합자 포함)")
                else:
                    base_font_path = self.right_font.get_font_path()
                    base_charsets = right_charsets
                    secondary_font_path = self.left_font.get_font_path()
                    secondary_charsets = left_charsets
                    print("✓ 오른쪽 폰트를 기본 폰트로 사용합니다 (합자 포함)")

                # 폰트 병합 실행
                success = merger.merge_fonts(
                    base_font_path,
                    base_charsets,
                    secondary_font_path,
                    secondary_charsets,
                    save_path,
                    merge_option,
                    font_name,
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
                    f"폰트 합치기 중 오류가 발생했습니다:\n\n{str(e)}\n\n{suggestion}",
                )

    def _get_merge_option_suggestion(self, current_option, error_message):
        """현재 옵션과 오류 메시지에 따라 적절한 제안 제공"""

        # Units per em 관련 오류 감지
        if "Expected all items to be equal" in error_message and "[" in error_message:
            if current_option == 0:  # 기존 설정 사용
                return (
                    "💡 해결책: 두 폰트의 Units per em 값이 다릅니다.\n"
                    "병합 옵션에서 'Units per em 통일'을 선택해보세요."
                )
            elif current_option == 1:  # UPM 통일
                return (
                    "💡 해결책: UPM 통일로도 해결되지 않았습니다.\n"
                    "'관대한 병합 옵션'을 시도해보세요."
                )

        # 일반적인 호환성 문제
        if "merge" in error_message.lower() or "table" in error_message.lower():
            if current_option == 0:  # 기존 설정 사용
                return (
                    "💡 해결책: 폰트 호환성 문제가 발생했습니다.\n"
                    "병합 옵션에서 'Units per em 통일' 또는 '관대한 병합 옵션'을 "
                    "시도해보세요."
                )
            elif current_option == 1:  # UPM 통일
                return (
                    "💡 해결책: '관대한 병합 옵션'을 시도해보세요.\n"
                    "이 옵션은 호환성 문제를 우회하여 강제로 병합합니다."
                )

        # 파일 경로 또는 권한 관련 오류
        if "permission" in error_message.lower() or "access" in error_message.lower():
            return (
                "💡 해결책: 파일 접근 권한 문제입니다.\n"
                "다른 위치에 저장하거나 파일이 사용 중이 아닌지 확인해보세요."
            )

        # 파일 형식 오류
        if "format" in error_message.lower() or "invalid" in error_message.lower():
            return (
                "💡 해결책: 폰트 파일 형식에 문제가 있을 수 있습니다.\n"
                "다른 폰트 파일을 시도하거나 파일이 손상되지 않았는지 확인해보세요."
            )

        # 기본 제안
        if current_option == 0:
            return (
                "💡 해결책: 다른 병합 옵션을 시도해보세요:\n"
                "• Units per em 통일: 폰트 크기 단위를 맞춤\n"
                "• 관대한 병합 옵션: 호환성 문제를 우회하여 강제 병합"
            )
        elif current_option == 1:
            return (
                "💡 해결책: '관대한 병합 옵션'을 시도해보세요.\n"
                "이 옵션은 더 강력한 호환성 처리를 제공합니다."
            )
        else:  # 관대한 옵션도 실패
            return (
                "💡 해결책: 모든 병합 옵션이 실패했습니다.\n"
                "• 다른 폰트 파일을 시도해보세요\n"
                "• 선택한 문자셋을 줄여보세요\n"
                "• 폰트 파일이 손상되지 않았는지 확인해보세요"
            )

    def _sanitize_filename(self, filename):
        """파일명에 사용할 수 없는 문자를 제거"""
        # 파일명에 사용할 수 없는 문자들을 제거하거나 대체
        illegal_chars = r'[<>:"/\\|?*]'
        safe_filename = re.sub(illegal_chars, "_", filename)

        # 연속된 공백을 하나로 줄이고 앞뒤 공백 제거
        safe_filename = re.sub(r"\s+", " ", safe_filename.strip())

        # 최대 길이 제한 (확장자 제외하고 100자)
        if len(safe_filename) > 100:
            safe_filename = safe_filename[:100]

        return safe_filename if safe_filename else "merged_font"

    def _extract_font_name(self, font_path):
        """폰트 파일에서 폰트 이름 추출"""
        try:
            font = TTFont(font_path)

            if "name" not in font:
                return None

            name_table = font["name"]

            # 폰트 Family 이름 찾기 (nameID 1)
            for record in name_table.names:
                if record.nameID == 1:  # Font Family name
                    # Windows Unicode 우선
                    if record.platformID == 3 and record.platEncID == 1:
                        return record.toUnicode()
                    # Mac Roman도 시도
                    elif record.platformID == 1 and record.platEncID == 0:
                        return record.toUnicode()

            # Full name도 시도 (nameID 4)
            for record in name_table.names:
                if record.nameID == 4:  # Full font name
                    if record.platformID == 3 and record.platEncID == 1:
                        return record.toUnicode()
                    elif record.platformID == 1 and record.platEncID == 0:
                        return record.toUnicode()

            return None

        except Exception:
            return None

    def check_upm_difference(self):
        """두 폰트의 UPM 차이를 확인하고 경고 표시"""
        try:
            # 두 폰트가 모두 선택되었는지 확인
            if (
                not self.left_font.has_font_selected()
                or not self.right_font.has_font_selected()
            ):
                self.upm_warning_label.setVisible(False)
                return

            # 두 폰트의 UPM 값 추출
            left_upm = self._get_font_upm(self.left_font.get_font_path())
            right_upm = self._get_font_upm(self.right_font.get_font_path())

            if left_upm is None or right_upm is None:
                self.upm_warning_label.setVisible(False)
                return

            # UPM 차이 계산 (2배 이상 차이가 나는지 확인)
            ratio = max(left_upm, right_upm) / min(left_upm, right_upm)

            if ratio >= 2.0:
                warning_text = (
                    f"⚠️ UPM 차이 경고: {left_upm} vs {right_upm} "
                    f"(약 {ratio:.1f}배 차이)\n"
                    "폰트 크기 차이가 커서 병합된 폰트에서 글자 크기가 "
                    "불균등하게 보일 수 있습니다. "
                    "'Units per em 통일' 옵션을 사용하시기 바랍니다."
                )
                self.upm_warning_label.setText(warning_text)
                self.upm_warning_label.setVisible(True)
            else:
                self.upm_warning_label.setVisible(False)

        except Exception:
            self.upm_warning_label.setVisible(False)

    def _get_font_upm(self, font_path):
        """폰트 파일에서 UPM 값 추출"""
        try:
            font = TTFont(font_path)
            if "head" in font:
                return font["head"].unitsPerEm
            return None
        except Exception:
            return None


def main():
    app = QApplication(sys.argv)

    # 애플리케이션 아이콘 설정
    icon_path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "..", "..", "icon.png"
    )
    if os.path.exists(icon_path):
        app.setWindowIcon(QIcon(icon_path))

    window = FontMergeApp()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
