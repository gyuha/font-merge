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

                # 합자 지원 복원 (병합 후 처리)
                self._restore_ligature_support(merged_font, temp1_path, temp2_path)

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
        
        # 한글 지원을 위한 추가 메타데이터 설정
        self._update_font_metadata_for_korean(font)

    def _update_font_metadata_for_korean(self, font):
        """
        VSCode에서 한글이 제대로 표시되도록 폰트 메타데이터 업데이트
        
        Args:
            font: TTFont 객체
        """
        # OS/2 테이블 업데이트 (문자 집합 정보)
        if 'OS/2' in font:
            os2_table = font['OS/2']
            
            # Unicode Range 설정 (한글 지원 추가 - 기존 값 보존)
            # Bit 28: Hangul Jamo (U+1100-U+11FF)  
            # Bit 29: Hangul Syllables (U+AC00-U+D7AF)
            # Bit 30: Hangul Compatibility Jamo (U+3130-U+318F)
            if hasattr(os2_table, 'ulUnicodeRange1'):
                # 기존 값에 한글 범위만 추가 (OR 연산으로 기존 비트 보존)
                korean_ranges = (1 << 28) | (1 << 29) | (1 << 30)
                os2_table.ulUnicodeRange1 |= korean_ranges
            
            # Unicode Range 2, 3, 4도 보존 (다른 언어 및 특수 문자 지원)
            # 이 값들을 건드리지 않아야 합자 등이 유지됨
            
            # Code Page Range 설정 (한국어 지원 추가 - 기존 값 보존)  
            # Bit 19: Korean (Wansung) - 949
            if hasattr(os2_table, 'ulCodePageRange1'):
                os2_table.ulCodePageRange1 |= (1 << 19)
            
            # Weight과 Width 설정 (VSCode 호환성)
            if hasattr(os2_table, 'usWeightClass'):
                if os2_table.usWeightClass == 0:
                    os2_table.usWeightClass = 400  # Normal weight
            
            if hasattr(os2_table, 'usWidthClass'):
                if os2_table.usWidthClass == 0:
                    os2_table.usWidthClass = 5  # Medium width
        
        # cmap 테이블 확인 및 보강
        if 'cmap' in font:
            cmap_table = font['cmap']
            
            # Unicode BMP 서브테이블이 있는지 확인
            has_unicode_bmp = False
            for subtable in cmap_table.tables:
                if (subtable.platformID == 3 and subtable.platEncID == 1) or \
                   (subtable.platformID == 0 and subtable.platEncID == 3):
                    has_unicode_bmp = True
                    break
            
            # Unicode BMP 서브테이블이 없으면 경고 (하지만 기존 것을 유지)
            if not has_unicode_bmp:
                print("경고: Unicode BMP cmap 서브테이블을 찾을 수 없습니다. 한글 표시에 문제가 있을 수 있습니다.")
        
        # head 테이블 확인
        if 'head' in font:
            head_table = font['head']
            # macStyle 설정 (Regular 폰트로 표시)
            if hasattr(head_table, 'macStyle'):
                head_table.macStyle = 0  # Regular style
        
        # 합자 지원 확인 및 디버그 정보
        self._verify_ligature_support(font)

    def _verify_ligature_support(self, font):
        """
        폰트의 합자 지원 여부를 확인하고 디버그 정보 출력
        
        Args:
            font: TTFont 객체
        """
        print("=== 폰트 합자 지원 검증 ===")
        
        # GSUB 테이블 확인 (합자의 핵심)
        if 'GSUB' in font:
            print("✓ GSUB 테이블 존재")
            gsub_table = font['GSUB']
            
            # 피처 리스트 확인
            if hasattr(gsub_table.table, 'FeatureList') and gsub_table.table.FeatureList:
                feature_tags = []
                for feature_record in gsub_table.table.FeatureList.FeatureRecord:
                    feature_tags.append(feature_record.FeatureTag)
                
                print(f"  피처 목록: {', '.join(feature_tags)}")
                
                # 일반적인 합자 피처 확인
                ligature_features = ['liga', 'dlig', 'clig', 'rlig']
                found_ligatures = [tag for tag in feature_tags if tag in ligature_features]
                
                if found_ligatures:
                    print(f"✓ 합자 피처 발견: {', '.join(found_ligatures)}")
                else:
                    print("⚠ 표준 합자 피처(liga, dlig, clig, rlig)를 찾을 수 없습니다")
            else:
                print("⚠ GSUB 테이블에 FeatureList가 없습니다")
        else:
            print("⚠ GSUB 테이블이 없습니다 - 합자가 지원되지 않을 수 있습니다")
        
        # GPOS 테이블 확인 (위치 조정)
        if 'GPOS' in font:
            print("✓ GPOS 테이블 존재")
        else:
            print("⚠ GPOS 테이블이 없습니다")
        
        # cmap 테이블에서 일반적인 합자 글리프 확인
        if 'cmap' in font:
            cmap = font.getBestCmap()
            if cmap:
                # 일반적인 합자 문자들 확인
                ligature_chars = [
                    0x2192,  # →
                    0x21D2,  # ⇒  
                    0x2260,  # ≠
                    0x2264,  # ≤
                    0x2265,  # ≥
                ]
                
                found_ligature_chars = []
                for char_code in ligature_chars:
                    if char_code in cmap:
                        found_ligature_chars.append(f"U+{char_code:04X}")
                
                if found_ligature_chars:
                    print(f"✓ 합자 관련 유니코드 문자 발견: {', '.join(found_ligature_chars)}")
        
        print("======================\n")

    def _restore_ligature_support(self, merged_font, font1_path, font2_path):
        """
        병합된 폰트에서 합자 지원을 복원
        
        Args:
            merged_font: 병합된 TTFont 객체
            font1_path: 첫 번째 폰트 경로 (보통 영문 폰트)
            font2_path: 두 번째 폰트 경로 (보통 한글 폰트)
        """
        print("=== 합자 지원 복원 시작 ===")
        
        # 원본 영문 폰트에서 합자 정보 추출
        font1 = TTFont(font1_path)
        font2 = TTFont(font2_path)
        
        # 어느 폰트에 liga 피처가 있는지 확인
        liga_source_font = None
        liga_source_name = None
        
        for font, name in [(font1, "첫 번째 폰트"), (font2, "두 번째 폰트")]:
            if 'GSUB' in font:
                gsub_table = font['GSUB']
                if hasattr(gsub_table.table, 'FeatureList') and gsub_table.table.FeatureList:
                    for feature_record in gsub_table.table.FeatureList.FeatureRecord:
                        if feature_record.FeatureTag == 'liga':
                            liga_source_font = font
                            liga_source_name = name
                            print(f"✓ {name}에서 liga 피처 발견")
                            break
            if liga_source_font:
                break
        
        if not liga_source_font:
            print("⚠ liga 피처를 가진 원본 폰트를 찾을 수 없습니다")
            return
        
        # 병합된 폰트의 GSUB 테이블 수정
        if 'GSUB' not in merged_font:
            print("⚠ 병합된 폰트에 GSUB 테이블이 없습니다")
            return
        
        # liga 피처가 없는 경우 추가
        merged_gsub = merged_font['GSUB']
        source_gsub = liga_source_font['GSUB']
        
        if hasattr(merged_gsub.table, 'FeatureList') and merged_gsub.table.FeatureList:
            # 기존 피처 목록에서 liga 확인
            has_liga = False
            for feature_record in merged_gsub.table.FeatureList.FeatureRecord:
                if feature_record.FeatureTag == 'liga':
                    has_liga = True
                    break
            
            if not has_liga:
                print("liga 피처가 누락됨 - 원본에서 복사 시도")
                self._copy_liga_feature(merged_gsub, source_gsub)
            else:
                print("✓ liga 피처가 이미 존재함")
        
        # 피처 중복 제거
        self._deduplicate_features(merged_gsub)
        
        print("=== 합자 지원 복원 완료 ===\n")

    def _copy_liga_feature(self, target_gsub, source_gsub):
        """
        원본 폰트에서 liga 피처를 대상 폰트로 복사
        """
        try:
            if not (hasattr(source_gsub.table, 'FeatureList') and source_gsub.table.FeatureList):
                return
            
            # 원본에서 liga 피처 찾기
            liga_feature = None
            liga_index = None
            
            for i, feature_record in enumerate(source_gsub.table.FeatureList.FeatureRecord):
                if feature_record.FeatureTag == 'liga':
                    liga_feature = source_gsub.table.FeatureList.Feature[i]
                    liga_index = i
                    break
            
            if liga_feature and hasattr(target_gsub.table, 'FeatureList'):
                # 대상 폰트에 liga 피처 추가
                from fontTools.otlLib.builder import Builder
                from fontTools.feaLib.builder import addOpenTypeFeatures
                
                # 간단한 방법: liga 피처 레코드만 추가
                target_feature_list = target_gsub.table.FeatureList
                
                # FeatureRecord 추가
                from fontTools.ttLib.tables.otTables import FeatureRecord
                new_feature_record = FeatureRecord()
                new_feature_record.FeatureTag = 'liga'
                
                # Feature 리스트에 추가
                target_feature_list.FeatureRecord.append(new_feature_record)
                target_feature_list.Feature.append(liga_feature)
                target_feature_list.FeatureCount += 1
                
                print("✓ liga 피처를 성공적으로 추가했습니다")
                
        except Exception as e:
            print(f"⚠ liga 피처 복사 중 오류: {str(e)}")

    def _deduplicate_features(self, gsub_table):
        """
        GSUB 테이블에서 중복된 피처 제거
        """
        if not (hasattr(gsub_table.table, 'FeatureList') and gsub_table.table.FeatureList):
            return
        
        feature_list = gsub_table.table.FeatureList
        seen_features = set()
        new_feature_records = []
        new_features = []
        
        print("피처 중복 제거 시작...")
        original_count = len(feature_list.FeatureRecord)
        
        for i, feature_record in enumerate(feature_list.FeatureRecord):
            feature_tag = feature_record.FeatureTag
            if feature_tag not in seen_features:
                seen_features.add(feature_tag)
                new_feature_records.append(feature_record)
                new_features.append(feature_list.Feature[i])
        
        # 업데이트
        feature_list.FeatureRecord = new_feature_records
        feature_list.Feature = new_features
        feature_list.FeatureCount = len(new_feature_records)
        
        removed_count = original_count - len(new_feature_records)
        print(f"✓ {removed_count}개의 중복 피처를 제거했습니다 ({original_count} -> {len(new_feature_records)})")
