"""폰트 선택 위젯"""

import os

from fontTools.ttLib import TTFont
from PyQt6.QtWidgets import (
    QCheckBox,
    QFileDialog,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

# PyInstaller에서도 작동하는 안전한 import
try:
    # 상대 import 시도
    from .font_preview import FontPreview
except (ImportError, ValueError):
    # 절대 import 시도 (PyInstaller 환경)
    from font_merge.font_preview import FontPreview


class FontSelector(QGroupBox):
    """폰트 파일 선택 및 문자셋 선택을 제공하는 위젯"""

    def __init__(self, title):
        super().__init__(title)
        self.font_path = None
        self.charset_checkboxes = {}
        self.other_selector = None  # 반대편 FontSelector 참조
        self.init_ui()

    def init_ui(self):
        """UI 초기화"""
        layout = QVBoxLayout()

        # 파일 선택 버튼
        self.select_button = QPushButton("폰트 파일 선택")
        self.select_button.clicked.connect(self.select_font)
        layout.addWidget(self.select_button)

        # 선택된 파일 경로 표시
        self.file_label = QLabel("선택된 파일 없음")
        self.file_label.setWordWrap(True)
        layout.addWidget(self.file_label)

        # 폰트 프리뷰
        self.preview = FontPreview()
        layout.addWidget(self.preview)

        # 기본 폰트 선택 체크박스
        self.base_font_checkbox = QCheckBox("기본 폰트로 사용")
        self.base_font_checkbox.stateChanged.connect(self._on_base_font_changed)
        layout.addWidget(self.base_font_checkbox)

        # 문자셋 선택 영역
        self.charset_group = QGroupBox("문자셋 선택")
        self.charset_group.setMinimumHeight(250)
        self.charset_layout = QVBoxLayout()

        # 전체 선택/해제 버튼 영역
        button_layout = QHBoxLayout()
        self.select_all_button = QPushButton("전체 선택")
        self.deselect_all_button = QPushButton("전체 해제")
        self.select_all_button.clicked.connect(self._select_all_charsets)
        self.deselect_all_button.clicked.connect(self._deselect_all_charsets)
        button_layout.addWidget(self.select_all_button)
        button_layout.addWidget(self.deselect_all_button)

        # 스크롤 영역
        scroll = QScrollArea()
        scroll_widget = QWidget()
        scroll_widget.setLayout(self.charset_layout)
        scroll.setWidget(scroll_widget)
        scroll.setWidgetResizable(True)

        charset_main_layout = QVBoxLayout()
        charset_main_layout.addLayout(button_layout)
        charset_main_layout.addWidget(scroll)
        self.charset_group.setLayout(charset_main_layout)
        layout.addWidget(self.charset_group)

        self.setLayout(layout)

    def select_font(self):
        """폰트 파일 선택"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "폰트 파일 선택", "", "Font Files (*.ttf *.otf *.woff *.woff2)"
        )

        if file_path:
            self.font_path = file_path
            self.file_label.setText(f"선택된 파일: {os.path.basename(file_path)}")
            self.preview.update_preview(file_path)
            self.load_charset_options()

            # 기본 폰트 설정 로직
            if self.other_selector:
                if not self.other_selector.has_font_selected():
                    # 첫 번째로 폰트를 선택한 경우 기본 폰트로 설정
                    self.base_font_checkbox.setChecked(True)
                else:
                    # 두 번째 폰트 선택 시, 둘 다 체크되어 있지 않으면 현재 폰트를 기본으로 설정
                    if (
                        not self.base_font_checkbox.isChecked()
                        and not self.other_selector.base_font_checkbox.isChecked()
                    ):
                        self.base_font_checkbox.setChecked(True)

    def load_charset_options(self):
        """폰트의 문자셋 옵션 로드"""
        # 기존 체크박스 제거
        for i in reversed(range(self.charset_layout.count())):
            widget = self.charset_layout.itemAt(i).widget()
            if widget:
                widget.setParent(None)

        self.charset_checkboxes.clear()

        if not self.font_path:
            return

        try:
            font = TTFont(self.font_path)
            cmap = font.getBestCmap()

            # 합자 정보 확인
            ligature_glyphs = self._find_ligature_glyphs(font)

            # 문자셋 범위별로 분류
            charset_ranges = self._get_charset_ranges()

            for range_name, (start, end) in charset_ranges.items():
                if "합자" in range_name or "Ligature" in range_name:
                    # 합자의 경우 실제 합자 글리프 수 사용
                    if range_name == "표준 합자":
                        available_chars = [
                            chr(code) for code in range(start, end + 1) if code in cmap
                        ]
                        if ligature_glyphs:
                            available_chars.extend(
                                [f"lig_{i}" for i in range(len(ligature_glyphs))]
                            )
                    else:
                        available_chars = [
                            chr(code) for code in range(start, end + 1) if code in cmap
                        ]
                else:
                    available_chars = [
                        chr(code) for code in range(start, end + 1) if code in cmap
                    ]

                checkbox = QCheckBox(f"{range_name} ({len(available_chars)}자)")
                checkbox.setEnabled(len(available_chars) > 0)
                checkbox.setChecked(len(available_chars) > 0)

                self.charset_checkboxes[range_name] = {
                    "checkbox": checkbox,
                    "chars": available_chars,
                    "range": (start, end),
                }

                self.charset_layout.addWidget(checkbox)

        except Exception as e:
            QMessageBox.warning(
                self, "오류", f"폰트 파일을 읽는 중 오류가 발생했습니다: {str(e)}"
            )

    def _get_charset_ranges(self):
        """문자셋 범위 정의"""
        return {
            "영문 대문자": (0x0041, 0x005A),
            "영문 소문자": (0x0061, 0x007A),
            "숫자": (0x0030, 0x0039),
            "한글": (0xAC00, 0xD7AF),
            "한글 자모": (0x1100, 0x11FF),
            "한글 호환 자모": (0x3130, 0x318F),
            "한글 반자모": (0xFFA0, 0xFFDC),
            "기본 기호": (0x0020, 0x007F),
            "라틴 확장 A": (0x0100, 0x017F),
            "라틴 확장 B": (0x0180, 0x024F),
            "일반 구두점": (0x2000, 0x206F),
            "위 첨자/아래 첨자": (0x2070, 0x209F),
            "통화 기호": (0x20A0, 0x20CF),
            "CJK 기호": (0x3000, 0x303F),
            "히라가나": (0x3040, 0x309F),
            "가타카나": (0x30A0, 0x30FF),
            "CJK 통합 한자": (0x4E00, 0x9FFF),
            "CJK 확장 A": (0x3400, 0x4DBF),
            "표준 합자": (0xFB00, 0xFB4F),
            "프로그래밍 합자 1": (0xE000, 0xE0FF),
            "프로그래밍 합자 2": (0xE100, 0xE1FF),
            "확장 합자": (0xF000, 0xF0FF),
            "수학 기호": (0x2200, 0x22FF),
            "화살표": (0x2190, 0x21FF),
            "박스 그리기": (0x2500, 0x257F),
            "블록 요소": (0x2580, 0x259F),
            "기하학적 도형": (0x25A0, 0x25FF),
            "NerdFonts 아이콘": (0xE000, 0xF8FF),
            "Powerline": (0xE0A0, 0xE0A2),
            "Powerline Extra": (0xE0B0, 0xE0B3),
            "Font Awesome": (0xF000, 0xF2E0),
            "Weather Icons": (0xF300, 0xF32F),
            "Seti-UI": (0xE5FA, 0xE62B),
            "Devicons": (0xE700, 0xE7C5),
            "Octicons": (0xF400, 0xF4A9),
            "Material Design": (0xF500, 0xFD46),
            "Codicons": (0xEA60, 0xEBEB),
            "Pomicons": (0xE000, 0xE00D),
        }

    def get_selected_charsets(self):
        """선택된 문자셋 반환"""
        selected = {}
        for range_name, data in self.charset_checkboxes.items():
            if data["checkbox"].isChecked():
                selected[range_name] = data["chars"]
        return selected

    def has_font_selected(self):
        """폰트가 선택되었는지 확인"""
        return self.font_path is not None

    def get_font_path(self):
        """선택된 폰트 파일 경로 반환"""
        return self.font_path

    def set_other_selector(self, other_selector):
        """반대편 FontSelector 설정"""
        self.other_selector = other_selector

    def _on_base_font_changed(self, state):
        """기본 폰트 체크박스 상태 변경 시 호출"""
        if not self.other_selector:
            return

        # 폰트가 2개 모두 선택된 경우에만 라디오 버튼 동작
        if self.has_font_selected() and self.other_selector.has_font_selected():
            if state == 2:  # 체크됨
                # 반대편 체크 해제 (시그널 블록하여 무한 루프 방지)
                self.other_selector.base_font_checkbox.blockSignals(True)
                self.other_selector.base_font_checkbox.setChecked(False)
                self.other_selector.base_font_checkbox.blockSignals(False)
            else:  # 체크 해제 시도
                # 라디오 버튼 동작: 항상 하나는 체크되어야 함
                # 현재 체크박스를 다시 체크 (체크 해제 방지)
                self.base_font_checkbox.blockSignals(True)
                self.base_font_checkbox.setChecked(True)
                self.base_font_checkbox.blockSignals(False)

    def is_base_font(self):
        """기본 폰트로 선택되었는지 확인"""
        return self.base_font_checkbox.isChecked()

    def _select_all_charsets(self):
        """모든 문자셋 선택"""
        for data in self.charset_checkboxes.values():
            checkbox = data["checkbox"]
            if checkbox.isEnabled():
                checkbox.setChecked(True)

    def _deselect_all_charsets(self):
        """모든 문자셋 선택 해제"""
        for data in self.charset_checkboxes.values():
            checkbox = data["checkbox"]
            if checkbox.isEnabled():
                checkbox.setChecked(False)

    def _find_ligature_glyphs(self, font):
        """폰트에서 합자 글리프 찾기"""
        ligature_glyphs = []
        try:
            # GSUB 테이블에서 합자 정보 확인
            if "GSUB" in font:
                gsub = font["GSUB"]
                if hasattr(gsub, "table") and hasattr(gsub.table, "FeatureList"):
                    feature_list = gsub.table.FeatureList
                    if hasattr(feature_list, "FeatureRecord"):
                        for feature_record in feature_list.FeatureRecord:
                            # 'liga' (Standard Ligatures) 기능 찾기
                            if feature_record.FeatureTag == "liga":
                                ligature_glyphs.append("liga_feature")

            # 글리프 이름에서 합자 패턴 찾기
            if hasattr(font, "getGlyphSet"):
                glyph_set = font.getGlyphSet()
                for glyph_name in glyph_set.keys():
                    # 일반적인 합자 글리프 이름 패턴
                    if any(
                        pattern in glyph_name.lower()
                        for pattern in [
                            "liga",
                            "fi",
                            "fl",
                            "ff",
                            "ffi",
                            "ffl",
                            "arrow",
                            "equal",
                        ]
                    ):
                        ligature_glyphs.append(glyph_name)

        except Exception:
            pass  # 오류 시 빈 리스트 반환

        return ligature_glyphs
