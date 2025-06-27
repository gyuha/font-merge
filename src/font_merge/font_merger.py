"""폰트 병합 로직"""

import os
import tempfile

from fontTools.merge import Merger
from fontTools.subset import Subsetter
from fontTools.ttLib import TTFont


class FontMerger:
    """두 폰트를 병합하는 클래스"""

    def __init__(self):
        self.merger = Merger()

    def merge_fonts(
        self,
        font1_path,
        font1_charsets,
        font2_path,
        font2_charsets,
        output_path,
        merge_option=0,
        font_name=None,
    ):
        """
        두 폰트를 선택된 문자셋으로 병합

        Args:
            font1_path: 첫 번째 폰트 파일 경로
            font1_charsets: 첫 번째 폰트에서 선택된 문자셋 딕셔너리
            font2_path: 두 번째 폰트 파일 경로
            font2_charsets: 두 번째 폰트에서 선택된 문자셋 딕셔너리
            output_path: 출력 폰트 파일 경로
            merge_option: 병합 옵션 (0: 기본, 1: UPM 통일, 2: 관대한 옵션)
            font_name: 사용자 정의 폰트 이름 (None이면 기본 폰트 이름 사용)

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

            # 임시 파일로 서브셋 저장
            with tempfile.NamedTemporaryFile(suffix=".ttf", delete=False) as temp1:
                font1_subset.save(temp1.name)
                temp1_path = temp1.name

            with tempfile.NamedTemporaryFile(suffix=".ttf", delete=False) as temp2:
                font2_subset.save(temp2.name)
                temp2_path = temp2.name

            try:
                # 두 폰트 병합 (파일 경로 사용)
                merged_font = self._merge_font_files(
                    temp1_path, temp2_path, merge_option
                )

                # 폰트 이름 설정
                if font_name:
                    self._update_font_name(merged_font, font_name)

                # 결과 저장
                merged_font.save(output_path)
            finally:
                # 임시 파일 정리
                os.unlink(temp1_path)
                os.unlink(temp2_path)

            return True

        except Exception as e:
            raise Exception(f"폰트 병합 중 오류 발생: {str(e)}") from e

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
            for chars in selected_charsets.values():
                all_chars.extend(chars)

            if not all_chars:
                return None

            # 유니코드 코드포인트로 변환 (실제 문자만)
            unicodes = []
            for char in all_chars:
                if len(char) == 1:  # 실제 단일 문자만 처리
                    unicodes.append(ord(char))
                # 글리프 이름은 무시 (lig_0, liga_feature 등)

            if not unicodes:
                return None

            # 서브셋터 생성 및 설정
            subsetter = Subsetter()
            subsetter.options.retain_gids = True
            subsetter.options.notdef_outline = True
            subsetter.options.recommended_glyphs = True
            subsetter.options.name_IDs = ["*"]
            subsetter.options.name_legacy = True
            
            # 합자(ligature) 및 OpenType 피처 보존 설정
            subsetter.options.layout_features = ["*"]  # 모든 레이아웃 피처 유지
            subsetter.options.layout_scripts = ["*"]   # 모든 스크립트 유지
            subsetter.options.glyph_names = True       # 글리프 이름 유지
            subsetter.options.legacy_kern = True       # 커닝 정보 유지
            subsetter.options.hinting = True           # 힌팅 정보 유지

            # 서브셋 생성
            subsetter.populate(unicodes=unicodes)
            subsetter.subset(font)

            return font

        except Exception as e:
            raise Exception(f"폰트 서브셋 생성 중 오류: {str(e)}") from e

    def _merge_font_files(self, font1_path, font2_path, merge_option=0):
        """
        두 폰트 파일을 병합

        Args:
            font1_path: 첫 번째 폰트 파일 경로
            font2_path: 두 번째 폰트 파일 경로
            merge_option: 병합 옵션 (0: 기본, 1: UPM 통일, 2: 관대한 옵션)

        Returns:
            TTFont: 병합된 폰트 객체
        """
        try:
            if merge_option == 1:  # UPM 통일
                return self._merge_with_upm_unification(font1_path, font2_path)
            elif merge_option == 2:  # 관대한 옵션
                return self._merge_with_lenient_options(font1_path, font2_path)
            else:  # 기본 옵션
                return self._merge_with_default_options(font1_path, font2_path)

        except Exception as e:
            import traceback

            print(f"폰트 병합 세부 오류:\n{traceback.format_exc()}")
            raise Exception(f"폰트 병합 중 오류: {str(e)}") from e

    def _merge_with_default_options(self, font1_path, font2_path):
        """기본 옵션으로 폰트 병합"""
        merger = Merger()
        if hasattr(merger, "duplicateGlyphsPerFont"):
            merger.duplicateGlyphsPerFont = True
        
        # OpenType 피처 보존 설정
        merger.options.drop_tables = []  # 테이블 삭제 방지
        
        return merger.merge([font1_path, font2_path])

    def _merge_with_upm_unification(self, font1_path, font2_path):
        """UPM 통일 후 폰트 병합"""
        font1 = TTFont(font1_path)
        font2 = TTFont(font2_path)

        # units per em 통일 (더 큰 값으로)
        if "head" in font1 and "head" in font2:
            upm1 = font1["head"].unitsPerEm
            upm2 = font2["head"].unitsPerEm

            if upm1 != upm2:
                target_upm = max(upm1, upm2)
                print(f"Units per em 조정: {upm1}, {upm2} -> {target_upm}")

                if upm1 != target_upm:
                    font1["head"].unitsPerEm = target_upm
                if upm2 != target_upm:
                    font2["head"].unitsPerEm = target_upm

        # 조정된 폰트를 임시 파일로 저장 후 병합
        with tempfile.NamedTemporaryFile(suffix=".ttf", delete=False) as temp1:
            font1.save(temp1.name)
            adjusted_font1_path = temp1.name

        with tempfile.NamedTemporaryFile(suffix=".ttf", delete=False) as temp2:
            font2.save(temp2.name)
            adjusted_font2_path = temp2.name

        try:
            merger = Merger()
            if hasattr(merger, "duplicateGlyphsPerFont"):
                merger.duplicateGlyphsPerFont = True
            
            # OpenType 피처 보존 설정
            merger.options.drop_tables = []  # 테이블 삭제 방지
            
            return merger.merge([adjusted_font1_path, adjusted_font2_path])
        finally:
            os.unlink(adjusted_font1_path)
            os.unlink(adjusted_font2_path)

    def _merge_with_lenient_options(self, font1_path, font2_path):
        """관대한 옵션으로 폰트 병합"""
        try:
            # 기본 병합 시도
            return self._merge_with_default_options(font1_path, font2_path)
        except Exception:
            # 실패하면 UPM 통일 후 재시도
            try:
                return self._merge_with_upm_unification(font1_path, font2_path)
            except Exception:
                # 그래도 실패하면 더 관대한 설정으로 시도
                font1 = TTFont(font1_path)
                font2 = TTFont(font2_path)

                # 디지털 서명만 제거 (GSUB, GPOS는 합자에 필요하므로 보존)
                for table_name in ["DSIG"]:
                    if table_name in font1:
                        del font1[table_name]
                    if table_name in font2:
                        del font2[table_name]

                # 임시 파일로 저장 후 병합
                with tempfile.NamedTemporaryFile(suffix=".ttf", delete=False) as temp1:
                    font1.save(temp1.name)
                    simplified_font1_path = temp1.name

                with tempfile.NamedTemporaryFile(suffix=".ttf", delete=False) as temp2:
                    font2.save(temp2.name)
                    simplified_font2_path = temp2.name

                try:
                    merger = Merger()
                    # OpenType 피처 보존 설정
                    merger.options.drop_tables = []  # 테이블 삭제 방지
                    return merger.merge([simplified_font1_path, simplified_font2_path])
                finally:
                    os.unlink(simplified_font1_path)
                    os.unlink(simplified_font2_path)

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

    def _update_font_name(self, font, font_name):
        """
        폰트의 이름을 업데이트

        Args:
            font: TTFont 객체
            font_name: 새로운 폰트 이름
        """
        if 'name' not in font:
            return

        name_table = font['name']
        
        # 폰트 이름 관련 name ID들 - 모든 주요 이름 항목 포함
        # 1: Font Family name (패밀리 이름)
        # 2: Font Subfamily name (서브패밀리 이름, Regular 등)
        # 3: Unique font identifier
        # 4: Full font name (전체 이름)
        # 6: PostScript name
        # 16: Typographic Family name (선택적)
        # 17: Typographic Subfamily name (선택적)
        
        # 기본 이름들은 모두 새 이름으로 설정
        primary_name_ids = [1, 4, 6]
        
        # 먼저 모든 기존 이름 레코드를 확인하고 업데이트
        for name_record in name_table.names[:]:  # 복사본으로 순회
            if name_record.nameID in primary_name_ids:
                # 기존 레코드 제거
                name_table.names.remove(name_record)
        
        # 새로운 이름들 추가
        platforms = [
            (3, 1, 0x409),  # Windows, Unicode BMP, English US
            (1, 0, 0),      # Macintosh, Roman, English
        ]
        
        for platform_id, encoding_id, language_id in platforms:
            # Font Family name (ID 1)
            name_table.setName(font_name, 1, platform_id, encoding_id, language_id)
            
            # Full font name (ID 4) 
            name_table.setName(font_name, 4, platform_id, encoding_id, language_id)
            
            # PostScript name (ID 6) - 공백 제거하고 특수문자 처리
            ps_name = font_name.replace(' ', '').replace('-', '')
            name_table.setName(ps_name, 6, platform_id, encoding_id, language_id)
            
            # Unique identifier (ID 3) - 버전 정보 포함
            unique_id = f"{font_name}: 2023"
            name_table.setName(unique_id, 3, platform_id, encoding_id, language_id)
        
        # Typographic names도 설정 (있는 경우)
        for name_record in name_table.names[:]:
            if name_record.nameID == 16:  # Typographic Family name
                name_table.names.remove(name_record)
            elif name_record.nameID == 17:  # Typographic Subfamily name  
                name_table.names.remove(name_record)
        
        # 새로운 Typographic names 추가
        for platform_id, encoding_id, language_id in platforms:
            name_table.setName(font_name, 16, platform_id, encoding_id, language_id)
            name_table.setName("Regular", 17, platform_id, encoding_id, language_id)
