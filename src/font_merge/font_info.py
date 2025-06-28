"""폰트 정보 표시 위젯"""

from fontTools.ttLib import TTFont
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QLabel, QVBoxLayout, QWidget


class FontInfo(QWidget):
    """폰트의 기본 정보를 표시하는 위젯"""

    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        """UI 초기화"""
        layout = QVBoxLayout()
        layout.setSpacing(2)
        layout.setContentsMargins(5, 5, 5, 5)

        # 폰트 이름 라벨
        self.font_name_label = QLabel("폰트: -")
        self.font_name_label.setStyleSheet("font-weight: bold; color: #333;")
        layout.addWidget(self.font_name_label)

        # 폰트 크기 정보 라벨
        self.size_info_label = QLabel("크기 정보: -")
        self.size_info_label.setStyleSheet("color: #666; font-size: 11px;")
        layout.addWidget(self.size_info_label)

        # 문자 개수 라벨
        self.char_count_label = QLabel("문자 개수: -")
        self.char_count_label.setStyleSheet("color: #666; font-size: 11px;")
        layout.addWidget(self.char_count_label)

        # 호환성 경고 라벨 (고정 높이 3줄)
        self.warning_label = QLabel("")
        self.warning_label.setStyleSheet(
            "color: #d32f2f; font-size: 11px; font-weight: bold;"
        )
        self.warning_label.setWordWrap(True)
        self.warning_label.setFixedHeight(33)  # 11px * 3줄
        self.warning_label.setAlignment(Qt.AlignmentFlag.AlignTop)
        layout.addWidget(self.warning_label)

        self.setLayout(layout)

    def update_font_info(self, font_path):
        """폰트 파일의 정보를 업데이트"""
        if not font_path:
            self.clear_info()
            return

        self._current_font_path = font_path

        try:
            font = TTFont(font_path)

            # 폰트 이름 추출
            font_name = self._get_font_name(font)
            self.font_name_label.setText(f"폰트: {font_name}")

            # 크기 정보 추출
            size_info = self._get_size_info(font)
            self.size_info_label.setText(f"크기 정보: {size_info}")

            # 문자 개수 추출
            char_count = self._get_character_count(font)
            self.char_count_label.setText(f"문자 개수: {char_count:,}자")

            # 호환성 경고 확인
            warnings = self._check_compatibility_warnings(font)
            self.warning_label.setText(warnings)

        except Exception as e:
            self.size_info_label.setText(f"정보 읽기 실패: {str(e)}")
            self.char_count_label.setText("")
            self.warning_label.setText("")

    def _get_font_name(self, font):
        """폰트 이름 추출"""
        try:
            name_table = font["name"]
            # 영어 이름 우선, 한글 이름도 시도
            for name_id in [1, 4, 6]:  # Family name, Full name, PostScript name
                for record in name_table.names:
                    if record.nameID == name_id:
                        # Windows Unicode
                        if record.platformID == 3 and record.platEncID == 1:
                            return record.toUnicode()
                        # Mac Roman
                        elif record.platformID == 1 and record.platEncID == 0:
                            return record.toUnicode()
            return "알 수 없는 폰트"
        except Exception:
            return "알 수 없는 폰트"

    def _get_size_info(self, font):
        """폰트 크기 정보 추출"""
        try:
            head_table = font["head"]
            units_per_em = head_table.unitsPerEm

            # OS/2 테이블에서 추가 정보
            size_info = f"UPM: {units_per_em}"

            if "OS/2" in font:
                os2_table = font["OS/2"]

                # 타이포그래피 어센더/디센더
                if (
                    hasattr(os2_table, "sTypoAscender")
                    and hasattr(os2_table, "sTypoDescender")
                ):
                    ascender = os2_table.sTypoAscender
                    descender = os2_table.sTypoDescender
                    line_gap = getattr(os2_table, "sTypoLineGap", 0)
                    total_height = ascender - descender + line_gap
                    size_info += f", 높이: {total_height}"

                # 평균 문자 폭
                if hasattr(os2_table, "xAvgCharWidth"):
                    avg_width = os2_table.xAvgCharWidth
                    if avg_width > 0:
                        size_info += f", 평균폭: {avg_width}"

            return size_info

        except Exception as e:
            return f"크기 정보 없음 ({str(e)})"

    def _get_character_count(self, font):
        """폰트에 포함된 문자 개수 계산"""
        try:
            cmap_table = font.getBestCmap()
            if cmap_table:
                return len(cmap_table)
            return 0
        except Exception:
            return 0

    def _check_compatibility_warnings(self, font):
        """폰트 합병 시 문제가 될 수 있는 요소들 확인"""
        warnings = []

        try:
            # UPM 값 확인 (일반적이지 않은 값)
            head_table = font["head"]
            upm = head_table.unitsPerEm
            if upm not in [1000, 2048, 1024, 512, 256]:
                warnings.append(f"비표준 UPM: {upm} (합병 시 크기 문제 가능)")

            # OS/2 테이블 누락 확인
            if "OS/2" not in font:
                warnings.append("OS/2 테이블 누락 (메트릭 문제 가능)")

            # PostScript 이름 확인
            if "post" in font:
                post_table = font["post"]
                if (
                    not hasattr(post_table, "extraNames")
                    and post_table.formatType < 2.0
                ):
                    warnings.append("PostScript 이름 정보 부족")

            # 문자 매핑 테이블 확인
            if "cmap" not in font:
                warnings.append("문자 매핑 테이블 누락")
            else:
                cmap_table = font["cmap"]
                unicode_tables = [t for t in cmap_table.tables if t.isUnicode()]
                if not unicode_tables:
                    warnings.append("유니코드 매핑 테이블 없음")

            # 글리프 이름 중복 가능성 확인
            if "post" in font and "glyf" in font:
                glyf_table = font["glyf"]
                if len(glyf_table.keys()) > 5000:
                    warnings.append(
                        f"글리프 수 많음 ({len(glyf_table.keys())}개, 이름 충돌 가능)"
                    )

            # GSUB/GPOS 테이블 확인 (고급 타이포그래피)
            advanced_features = []
            if "GSUB" in font:
                advanced_features.append("GSUB")
            if "GPOS" in font:
                advanced_features.append("GPOS")
            if advanced_features:
                warnings.append(
                    f"고급 기능: {', '.join(advanced_features)} (합병 시 손실 가능)"
                )

            # 폰트 형식별 특이사항
            if "CFF " in font:
                warnings.append("OpenType CFF 폰트 (TrueType과 합병 시 주의)")
            elif "glyf" in font and "loca" in font:
                # TrueType 폰트
                pass
            else:
                warnings.append("알 수 없는 폰트 형식")

        except Exception as e:
            warnings.append(f"호환성 검사 실패: {str(e)}")

        return "\n".join(warnings) if warnings else ""

    def check_merge_compatibility(self, other_font_path):
        """다른 폰트와의 합병 호환성 확인"""
        if (
            not hasattr(self, "_current_font_path")
            or not self._current_font_path
            or not other_font_path
        ):
            return ""

        try:
            font1 = TTFont(self._current_font_path)
            font2 = TTFont(other_font_path)

            warnings = []

            # UPM 값 비교
            upm1 = font1["head"].unitsPerEm
            upm2 = font2["head"].unitsPerEm
            if upm1 != upm2:
                warnings.append(f"UPM 불일치: {upm1} vs {upm2} (크기 조정 필요)")

            # 문자 중복 확인
            cmap1 = font1.getBestCmap() or {}
            cmap2 = font2.getBestCmap() or {}
            overlap = set(cmap1.keys()) & set(cmap2.keys())
            if overlap:
                overlap_count = len(overlap)
                if overlap_count > 100:
                    warnings.append(
                        f"문자 중복 많음: {overlap_count}개 (덮어쓰기 발생)"
                    )
                elif overlap_count > 10:
                    warnings.append(f"문자 중복: {overlap_count}개")

            # 폰트 형식 호환성
            is_cff1 = "CFF " in font1
            is_cff2 = "CFF " in font2
            if is_cff1 != is_cff2:
                warnings.append("폰트 형식 불일치 (CFF vs TrueType)")

            return "\n".join(warnings)

        except Exception as e:
            return f"호환성 확인 실패: {str(e)}"

    def clear_info(self):
        """정보 초기화"""
        self.font_name_label.setText("폰트: -")
        self.size_info_label.setText("크기 정보: -")
        self.char_count_label.setText("문자 개수: -")
        self.warning_label.setText("")
        self._current_font_path = None

