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

        self.setLayout(layout)

    def update_font_info(self, font_path):
        """폰트 파일의 정보를 업데이트"""
        if not font_path:
            self.clear_info()
            return

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

        except Exception as e:
            self.size_info_label.setText(f"정보 읽기 실패: {str(e)}")
            self.char_count_label.setText("")

    def _get_font_name(self, font):
        """폰트 이름 추출"""
        try:
            name_table = font["name"]
            # 영어 이름 우선, 한글 이름도 시도
            for name_id in [1, 4, 6]:  # Family name, Full name, PostScript name
                for record in name_table.names:
                    if record.nameID == name_id:
                        if record.platformID == 3 and record.platEncID == 1:  # Windows Unicode
                            return record.toUnicode()
                        elif record.platformID == 1 and record.platEncID == 0:  # Mac Roman
                            return record.toUnicode()
            return "알 수 없는 폰트"
        except:
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
                if hasattr(os2_table, "sTypoAscender") and hasattr(os2_table, "sTypoDescender"):
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
        except:
            return 0

    def clear_info(self):
        """정보 초기화"""
        self.font_name_label.setText("폰트: -")
        self.size_info_label.setText("크기 정보: -")
        self.char_count_label.setText("문자 개수: -")