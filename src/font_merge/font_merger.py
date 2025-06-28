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

    def determine_optimal_font_order(self, font1_path, font2_path):
        """
        합자 보존을 위한 최적의 폰트 순서 결정

        Args:
            font1_path: 첫 번째 폰트 경로
            font2_path: 두 번째 폰트 경로

        Returns:
            tuple: (base_font_path, secondary_font_path, should_swap)
            should_swap이 True면 원래 순서를 바꿔야 함
        """
        try:
            font1 = TTFont(font1_path)
            font2 = TTFont(font2_path)

            # 각 폰트의 합자 점수 계산
            score1 = self._calculate_ligature_score(font1)
            score2 = self._calculate_ligature_score(font2)

            print(f"합자 점수 - 폰트1: {score1}, 폰트2: {score2}")

            # 점수가 높은 폰트를 기본 폰트로 설정
            if score2 > score1:
                print("⚠ 합자 보존을 위해 폰트 순서를 변경합니다")
                return font2_path, font1_path, True
            else:
                return font1_path, font2_path, False

        except Exception as e:
            print(f"폰트 순서 최적화 중 오류: {str(e)}")
            return font1_path, font2_path, False

    def _calculate_ligature_score(self, font):
        """
        폰트의 합자 기능 점수 계산

        Returns:
            int: 합자 점수 (높을수록 더 많은 합자 기능)
        """
        score = 0

        try:
            if "GSUB" not in font:
                return 0

            gsub_table = font["GSUB"]
            if not (
                hasattr(gsub_table.table, "FeatureList")
                and gsub_table.table.FeatureList
            ):
                return 0

            # 피처별 점수 부여
            for feature_record in gsub_table.table.FeatureList.FeatureRecord:
                feature_tag = feature_record.FeatureTag

                if feature_tag == "liga":  # Standard Ligatures
                    score += 100
                elif feature_tag == "dlig":  # Discretionary Ligatures
                    score += 50
                elif feature_tag == "clig":  # Contextual Ligatures
                    score += 50
                elif feature_tag == "rlig":  # Required Ligatures
                    score += 30
                elif feature_tag == "calt":  # Contextual Alternates
                    score += 20
                elif feature_tag in ["kern", "curs"]:  # Kerning, Cursive
                    score += 10
                elif feature_tag in [
                    "ss01",
                    "ss02",
                    "ss03",
                    "ss04",
                    "ss05",
                    "ss06",
                    "ss07",
                    "ss08",
                    "ss09",
                    "ss10",
                ]:  # Stylistic Sets
                    score += 5

            # 글리프 이름에서 합자 패턴 확인
            if hasattr(font, "getGlyphSet"):
                glyph_set = font.getGlyphSet()
                ligature_glyphs = 0

                for glyph_name in glyph_set.keys():
                    if any(
                        pattern in glyph_name.lower()
                        for pattern in [
                            "liga",
                            "_",
                            "arrow",
                            "equal",
                            "greater",
                            "less",
                            "ampersand",
                            "at",
                            "dollar",
                            "percent",
                        ]
                    ):
                        ligature_glyphs += 1

                # 합자 글리프가 많으면 추가 점수
                if ligature_glyphs > 50:
                    score += 25
                elif ligature_glyphs > 20:
                    score += 15
                elif ligature_glyphs > 10:
                    score += 10

        except Exception:
            pass

        return score

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

                # 합자 지원 복원 (기본 폰트 설정 보존)
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
            subsetter.options.layout_scripts = ["*"]  # 모든 스크립트 유지
            subsetter.options.glyph_names = True  # 글리프 이름 유지
            subsetter.options.legacy_kern = True  # 커닝 정보 유지
            subsetter.options.hinting = True  # 힌팅 정보 유지

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
        if "name" not in font:
            return

        name_table = font["name"]

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
            (1, 0, 0),  # Macintosh, Roman, English
        ]

        for platform_id, encoding_id, language_id in platforms:
            # Font Family name (ID 1)
            name_table.setName(font_name, 1, platform_id, encoding_id, language_id)

            # Full font name (ID 4)
            name_table.setName(font_name, 4, platform_id, encoding_id, language_id)

            # PostScript name (ID 6) - 공백 제거하고 특수문자 처리
            ps_name = font_name.replace(" ", "").replace("-", "")
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
        if "OS/2" in font:
            os2_table = font["OS/2"]

            # Unicode Range 설정 (한글 지원 추가 - 기존 값 보존)
            # Bit 28: Hangul Jamo (U+1100-U+11FF)
            # Bit 29: Hangul Syllables (U+AC00-U+D7AF)
            # Bit 30: Hangul Compatibility Jamo (U+3130-U+318F)
            if hasattr(os2_table, "ulUnicodeRange1"):
                # 기존 값에 한글 범위만 추가 (OR 연산으로 기존 비트 보존)
                korean_ranges = (1 << 28) | (1 << 29) | (1 << 30)
                os2_table.ulUnicodeRange1 |= korean_ranges

            # Unicode Range 2, 3, 4도 보존 (다른 언어 및 특수 문자 지원)
            # 이 값들을 건드리지 않아야 합자 등이 유지됨

            # Code Page Range 설정 (한국어 지원 추가 - 기존 값 보존)
            # Bit 19: Korean (Wansung) - 949
            if hasattr(os2_table, "ulCodePageRange1"):
                os2_table.ulCodePageRange1 |= 1 << 19

            # Weight과 Width 설정 (VSCode 호환성)
            if hasattr(os2_table, "usWeightClass"):
                if os2_table.usWeightClass == 0:
                    os2_table.usWeightClass = 400  # Normal weight

            if hasattr(os2_table, "usWidthClass"):
                if os2_table.usWidthClass == 0:
                    os2_table.usWidthClass = 5  # Medium width

        # cmap 테이블 확인 및 보강
        if "cmap" in font:
            cmap_table = font["cmap"]

            # Unicode BMP 서브테이블이 있는지 확인
            has_unicode_bmp = False
            for subtable in cmap_table.tables:
                if (subtable.platformID == 3 and subtable.platEncID == 1) or (
                    subtable.platformID == 0 and subtable.platEncID == 3
                ):
                    has_unicode_bmp = True
                    break

            # Unicode BMP 서브테이블이 없으면 경고 (하지만 기존 것을 유지)
            if not has_unicode_bmp:
                print(
                    "경고: Unicode BMP cmap 서브테이블을 찾을 수 없습니다. 한글 표시에 문제가 있을 수 있습니다."
                )

        # head 테이블 확인
        if "head" in font:
            head_table = font["head"]
            # macStyle 설정 (Regular 폰트로 표시)
            if hasattr(head_table, "macStyle"):
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
        if "GSUB" in font:
            print("✓ GSUB 테이블 존재")
            gsub_table = font["GSUB"]

            # 피처 리스트 확인
            if (
                hasattr(gsub_table.table, "FeatureList")
                and gsub_table.table.FeatureList
            ):
                feature_tags = []
                for feature_record in gsub_table.table.FeatureList.FeatureRecord:
                    feature_tags.append(feature_record.FeatureTag)

                print(f"  피처 목록: {', '.join(feature_tags)}")

                # 일반적인 합자 피처 확인
                ligature_features = ["liga", "dlig", "clig", "rlig"]
                found_ligatures = [
                    tag for tag in feature_tags if tag in ligature_features
                ]

                if found_ligatures:
                    print(f"✓ 합자 피처 발견: {', '.join(found_ligatures)}")
                else:
                    print("⚠ 표준 합자 피처(liga, dlig, clig, rlig)를 찾을 수 없습니다")
            else:
                print("⚠ GSUB 테이블에 FeatureList가 없습니다")
        else:
            print("⚠ GSUB 테이블이 없습니다 - 합자가 지원되지 않을 수 있습니다")

        # GPOS 테이블 확인 (위치 조정)
        if "GPOS" in font:
            print("✓ GPOS 테이블 존재")
        else:
            print("⚠ GPOS 테이블이 없습니다")

        # cmap 테이블에서 일반적인 합자 글리프 확인
        if "cmap" in font:
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
                    print(
                        f"✓ 합자 관련 유니코드 문자 발견: {', '.join(found_ligature_chars)}"
                    )

        print("======================\n")

    def _restore_ligature_support(
        self, merged_font, base_font_path, secondary_font_path
    ):
        """
        병합된 폰트에서 합자 지원을 복원

        Args:
            merged_font: 병합된 TTFont 객체
            font1_path: 첫 번째 폰트 경로 (기본 폰트)
            font2_path: 두 번째 폰트 경로 (보조 폰트)
        """
        print("=== 합자 지원 복원 시작 ===")

        # 원본 폰트들 로드
        base_font = TTFont(base_font_path)
        secondary_font = TTFont(secondary_font_path)

        # 기본 폰트의 합자 기능 확인 (사용자 선택 우선)
        base_ligature_score = self._calculate_ligature_score_from_font(base_font)
        print(f"기본 폰트 합자 점수: {base_ligature_score}")

        if base_ligature_score > 0:
            # 기본 폰트에 합자가 있으면 그것을 사용
            ligature_source = base_font
            source_name = "기본 폰트"
        else:
            # 기본 폰트에 합자가 없으면 보조 폰트 확인
            secondary_ligature_score = self._calculate_ligature_score_from_font(
                secondary_font
            )
            print(f"보조 폰트 합자 점수: {secondary_ligature_score}")

            if secondary_ligature_score > 0:
                ligature_source = secondary_font
                source_name = "보조 폰트"
            else:
                ligature_source = None
                source_name = None

        if not ligature_source:
            print("⚠ 합자 기능을 가진 폰트를 찾을 수 없습니다")
            return

        print(f"✓ {source_name}의 합자 기능을 사용합니다")

        # 병합된 폰트의 OpenType 테이블 강화
        self._preserve_ligature_features(merged_font, ligature_source)

        print("=== 합자 지원 복원 완료 ===\n")

    def _calculate_ligature_score_from_font(self, font):
        """TTFont 객체에서 직접 합자 점수 계산"""
        score = 0

        try:
            if "GSUB" in font:
                gsub_table = font["GSUB"]
                if (
                    hasattr(gsub_table.table, "FeatureList")
                    and gsub_table.table.FeatureList
                ):
                    ligature_features = ["liga", "dlig", "clig", "rlig", "hlig"]
                    for feature_record in gsub_table.table.FeatureList.FeatureRecord:
                        if feature_record.FeatureTag in ligature_features:
                            score += 10

            if "GPOS" in font:
                score += 5

        except Exception:
            pass

        return score

    def _preserve_ligature_features(self, merged_font, source_font):
        """소스 폰트의 합자 기능을 병합된 폰트에 보존"""
        try:
            # GSUB 테이블 보존
            if "GSUB" in source_font:
                if "GSUB" not in merged_font:
                    merged_font["GSUB"] = source_font["GSUB"]
                    print("✓ GSUB 테이블 전체 복사")
                else:
                    self._merge_ligature_features(
                        merged_font["GSUB"], source_font["GSUB"]
                    )

            # GPOS 테이블 보존
            if "GPOS" in source_font:
                if "GPOS" not in merged_font:
                    merged_font["GPOS"] = source_font["GPOS"]
                    print("✓ GPOS 테이블 전체 복사")

        except Exception as e:
            print(f"⚠ 합자 기능 보존 중 오류: {str(e)}")

    def _merge_ligature_features(self, target_gsub, source_gsub):
        """합자 관련 피처들을 우선적으로 병합"""
        try:
            if not (
                hasattr(source_gsub.table, "FeatureList")
                and source_gsub.table.FeatureList
            ):
                return

            if not (
                hasattr(target_gsub.table, "FeatureList")
                and target_gsub.table.FeatureList
            ):
                target_gsub.table.FeatureList = source_gsub.table.FeatureList
                print("✓ FeatureList 전체 복사")
                return

            # 합자 관련 피처들만 추가
            ligature_features = ["liga", "dlig", "clig", "rlig", "hlig", "calt"]
            existing_features = {
                fr.FeatureTag for fr in target_gsub.table.FeatureList.FeatureRecord
            }

            source_features = source_gsub.table.FeatureList
            added_count = 0

            for i, feature_record in enumerate(source_features.FeatureRecord):
                if (
                    feature_record.FeatureTag in ligature_features
                    and feature_record.FeatureTag not in existing_features
                ):
                    target_gsub.table.FeatureList.FeatureRecord.append(feature_record)
                    target_gsub.table.FeatureList.Feature.append(
                        source_features.Feature[i]
                    )
                    added_count += 1
                    print(f"✓ {feature_record.FeatureTag} 피처 추가")

            if added_count > 0:
                target_gsub.table.FeatureList.FeatureCount = len(
                    target_gsub.table.FeatureList.FeatureRecord
                )
                print(f"✓ {added_count}개의 합자 피처를 추가했습니다")
            else:
                print("✓ 모든 합자 피처가 이미 존재합니다")

        except Exception as e:
            print(f"⚠ 합자 피처 병합 중 오류: {str(e)}")

    def _find_best_ligature_source(self, font1, font2):
        """
        두 폰트 중 합자 기능이 더 풍부한 폰트 찾기

        Returns:
            tuple: (font, name, features) 또는 None
        """
        candidates = [(font1, "기본 폰트 (첫 번째)"), (font2, "보조 폰트 (두 번째)")]

        best_candidate = None
        best_score = 0

        for font, name in candidates:
            if "GSUB" not in font:
                continue

            gsub_table = font["GSUB"]
            if not (
                hasattr(gsub_table.table, "FeatureList")
                and gsub_table.table.FeatureList
            ):
                continue

            # 합자 관련 피처들 찾기
            ligature_features = []
            feature_score = 0

            for feature_record in gsub_table.table.FeatureList.FeatureRecord:
                feature_tag = feature_record.FeatureTag

                # 합자 관련 피처들과 점수
                if feature_tag == "liga":  # Standard Ligatures
                    ligature_features.append(feature_tag)
                    feature_score += 10
                elif feature_tag == "dlig":  # Discretionary Ligatures
                    ligature_features.append(feature_tag)
                    feature_score += 5
                elif feature_tag == "clig":  # Contextual Ligatures
                    ligature_features.append(feature_tag)
                    feature_score += 5
                elif feature_tag == "rlig":  # Required Ligatures
                    ligature_features.append(feature_tag)
                    feature_score += 3
                elif feature_tag in ["calt", "curs", "kern"]:  # 관련 피처들
                    ligature_features.append(feature_tag)
                    feature_score += 1

            if feature_score > best_score:
                best_score = feature_score
                best_candidate = (font, name, ligature_features)

        return best_candidate

    def _enhance_opentype_features(self, merged_font, source_font, source_features):
        """
        원본 폰트의 OpenType 기능을 병합된 폰트에 강화/복원
        """
        if "GSUB" not in source_font or "GSUB" not in merged_font:
            print("⚠ GSUB 테이블이 없어서 OpenType 기능을 복원할 수 없습니다")
            return

        source_gsub = source_font["GSUB"]
        merged_gsub = merged_font["GSUB"]

        try:
            # 병합된 폰트에 누락된 중요한 피처들 복사
            self._copy_missing_features(merged_gsub, source_gsub, source_features)

            # GPOS 테이블도 복사 (위치 조정)
            if "GPOS" in source_font and "GPOS" not in merged_font:
                print("✓ GPOS 테이블 복사 중...")
                merged_font["GPOS"] = source_font["GPOS"]
            elif "GPOS" in source_font and "GPOS" in merged_font:
                print("✓ GPOS 테이블 기능 강화 중...")
                self._enhance_gpos_features(merged_font["GPOS"], source_font["GPOS"])

        except Exception as e:
            print(f"⚠ OpenType 기능 강화 중 오류: {str(e)}")
            # 실패해도 기본 병합은 유지

    def _copy_missing_features(self, target_gsub, source_gsub, important_features):
        """
        중요한 피처들을 원본에서 대상으로 복사
        """
        if not (
            hasattr(source_gsub.table, "FeatureList") and source_gsub.table.FeatureList
        ):
            return

        if not (
            hasattr(target_gsub.table, "FeatureList") and target_gsub.table.FeatureList
        ):
            return

        # 대상 폰트의 기존 피처 태그들
        existing_features = {
            record.FeatureTag for record in target_gsub.table.FeatureList.FeatureRecord
        }

        # 원본에서 누락된 중요 피처들 찾기
        missing_features = []
        for i, feature_record in enumerate(source_gsub.table.FeatureList.FeatureRecord):
            if (
                feature_record.FeatureTag in important_features
                and feature_record.FeatureTag not in existing_features
            ):
                missing_features.append(
                    (i, feature_record, source_gsub.table.FeatureList.Feature[i])
                )

        if not missing_features:
            print("✓ 모든 중요 피처가 이미 존재합니다")
            return

        # 누락된 피처들 추가
        feature_list = target_gsub.table.FeatureList

        for _, feature_record, feature in missing_features:
            try:
                # 새로운 FeatureRecord 생성
                from fontTools.ttLib.tables.otTables import FeatureRecord

                new_record = FeatureRecord()
                new_record.FeatureTag = feature_record.FeatureTag

                # 피처 추가
                feature_list.FeatureRecord.append(new_record)
                feature_list.Feature.append(feature)

                print(f"✓ '{feature_record.FeatureTag}' 피처를 추가했습니다")

            except Exception as e:
                print(f"⚠ '{feature_record.FeatureTag}' 피처 추가 실패: {str(e)}")

        # 개수 업데이트
        feature_list.FeatureCount = len(feature_list.FeatureRecord)

        # 중복 제거
        self._deduplicate_features(target_gsub)

    def _enhance_gpos_features(self, target_gpos, source_gpos):
        """
        GPOS 테이블의 기능을 강화 (위치 조정, 커닝 등)
        """
        try:
            # 간단한 전략: 원본의 더 풍부한 기능이 있으면 우선
            if (
                hasattr(source_gpos.table, "FeatureList")
                and source_gpos.table.FeatureList
                and hasattr(target_gpos.table, "FeatureList")
            ):
                source_feature_count = len(source_gpos.table.FeatureList.FeatureRecord)
                target_feature_count = len(target_gpos.table.FeatureList.FeatureRecord)

                if source_feature_count > target_feature_count:
                    print(
                        f"✓ GPOS 기능을 원본으로 교체 ({target_feature_count} -> {source_feature_count} 피처)"
                    )
                    target_gpos.table = source_gpos.table
                else:
                    print(f"✓ 기존 GPOS 기능 유지 ({target_feature_count} 피처)")

        except Exception as e:
            print(f"⚠ GPOS 강화 중 오류: {str(e)}")

    def _deduplicate_features(self, gsub_table):
        """
        GSUB 테이블에서 중복된 피처 제거
        """
        if not (
            hasattr(gsub_table.table, "FeatureList") and gsub_table.table.FeatureList
        ):
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
        print(
            f"✓ {removed_count}개의 중복 피처를 제거했습니다 ({original_count} -> {len(new_feature_records)})"
        )
