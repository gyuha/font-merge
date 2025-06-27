"""폰트 병합 로직"""

import os

from fontTools.merge import Merger
from fontTools.subset import Subsetter
from fontTools.ttLib import TTFont


class FontMerger:
    """두 폰트를 병합하는 클래스"""

    def __init__(self):
        self.merger = Merger()

    def merge_fonts(
        self, font1_path, font1_charsets, font2_path, font2_charsets, output_path
    ):
        """
        두 폰트를 선택된 문자셋으로 병합

        Args:
            font1_path: 첫 번째 폰트 파일 경로
            font1_charsets: 첫 번째 폰트에서 선택된 문자셋 딕셔너리
            font2_path: 두 번째 폰트 파일 경로
            font2_charsets: 두 번째 폰트에서 선택된 문자셋 딕셔너리
            output_path: 출력 폰트 파일 경로

        Returns:
            bool: 성공 여부
        """
        try:
            # 첫 번째 폰트에서 선택된 문자들만 추출
            font1_subset = self._create_font_subset(font1_path, font1_charsets)
            if not font1_subset:
                raise Exception("첫 번째 폰트에서 문자셋을 추출할 수 없습니다.")

            # 두 번째 폰트에서 선택된 문자들만 추출
            font2_subset = self._create_font_subset(font2_path, font2_charsets)
            if not font2_subset:
                raise Exception("두 번째 폰트에서 문자셋을 추출할 수 없습니다.")

            # 두 폰트 병합
            merged_font = self._merge_font_subsets(font1_subset, font2_subset)

            # 결과 저장
            merged_font.save(output_path)

            return True

        except Exception as e:
            raise Exception(f"폰트 병합 중 오류 발생: {str(e)}")

    def _create_font_subset(self, font_path, selected_charsets):
        """
        폰트에서 선택된 문자셋만 추출하여 서브셋 생성

        Args:
            font_path: 폰트 파일 경로
            selected_charsets: 선택된 문자셋 딕셔너리

        Returns:
            TTFont: 서브셋된 폰트 객체
        """
        if not selected_charsets:
            return None

        try:
            font = TTFont(font_path)

            # 선택된 모든 문자들을 하나의 리스트로 합치기
            all_chars = []
            for _charset_name, chars in selected_charsets.items():
                all_chars.extend(chars)

            if not all_chars:
                return None

            # 유니코드 코드포인트로 변환
            unicodes = [ord(char) for char in all_chars]

            # 서브셋터 생성 및 설정
            subsetter = Subsetter()
            subsetter.options.retain_gids = True
            subsetter.options.notdef_outline = True
            subsetter.options.recommended_glyphs = True
            subsetter.options.name_IDs = ["*"]
            subsetter.options.name_legacy = True

            # 서브셋 생성
            subsetter.populate(unicodes=unicodes)
            subsetter.subset(font)

            return font

        except Exception as e:
            raise Exception(f"폰트 서브셋 생성 중 오류: {str(e)}")

    def _merge_font_subsets(self, font1, font2):
        """
        두 폰트 서브셋을 병합

        Args:
            font1: 첫 번째 폰트 객체
            font2: 두 번째 폰트 객체

        Returns:
            TTFont: 병합된 폰트 객체
        """
        try:
            # fontTools.merge.Merger를 사용하여 병합
            merger = Merger()

            # 병합 옵션 설정
            merger.duplicateGlyphsPerFont = True

            # 폰트 병합 수행
            merged_font = merger.merge([font1, font2])

            return merged_font

        except Exception as e:
            raise Exception(f"폰트 병합 중 오류: {str(e)}")

    def validate_fonts(self, font1_path, font2_path):
        """
        폰트 파일들의 유효성 검사

        Args:
            font1_path: 첫 번째 폰트 파일 경로
            font2_path: 두 번째 폰트 파일 경로

        Returns:
            tuple: (is_valid, error_message)
        """
        try:
            # 파일 존재 여부 확인
            if not os.path.exists(font1_path):
                return False, f"첫 번째 폰트 파일을 찾을 수 없습니다: {font1_path}"

            if not os.path.exists(font2_path):
                return False, f"두 번째 폰트 파일을 찾을 수 없습니다: {font2_path}"

            # 폰트 파일 로드 테스트
            try:
                font1 = TTFont(font1_path)
                font1.close()
            except Exception as e:
                return False, f"첫 번째 폰트 파일이 유효하지 않습니다: {str(e)}"

            try:
                font2 = TTFont(font2_path)
                font2.close()
            except Exception as e:
                return False, f"두 번째 폰트 파일이 유효하지 않습니다: {str(e)}"

            return True, ""

        except Exception as e:
            return False, f"폰트 유효성 검사 중 오류: {str(e)}"
