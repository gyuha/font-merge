# macOS 빌드 및 배포 가이드

Font Merge 애플리케이션을 macOS용으로 빌드하고 DMG 설치 파일을 생성하는 방법입니다.

## 필요 조건

### 시스템 요구사항
- macOS 10.13 이상
- Python 3.8 이상
- Xcode Command Line Tools

### Python 의존성
```bash
pip install PyInstaller fontTools[unicode] PyQt6
```

### 시스템 도구 설치
```bash
xcode-select --install  # Xcode Command Line Tools
```

## 빌드 방법

### 1. 원클릭 빌드 (권장)

전체 빌드 과정을 자동화한 스크립트:

```bash
# Python 스크립트로 실행
python3 build_and_package.py

# 또는 Shell 스크립트로 실행  
./build_and_package.sh
```

### 2. 단계별 빌드

#### 2-1. 앱 번들 빌드
```bash
python3 build_macos.py
```

결과: `dist/FontMerge.app`

#### 2-2. DMG 설치 파일 생성
```bash
python3 create_dmg.py
```

결과: `FontMerge-1.0.0.dmg`

## 빌드 파일 설명

### 핵심 빌드 파일

- **`build_macos.spec`** - PyInstaller 설정 파일
  - 앱 번들 메타데이터 정의
  - 아이콘 및 의존성 설정
  - macOS 특화 설정

- **`build_macos.py`** - 앱 번들 빌드 스크립트
  - PyInstaller 자동 설치
  - 빌드 아티팩트 정리
  - 앱 번들 검증

- **`create_dmg.py`** - DMG 생성 스크립트
  - 전문적인 DMG 레이아웃
  - 배경 이미지 생성
  - Applications 폴더 링크

### 통합 빌드 스크립트

- **`build_and_package.py`** - Python 통합 스크립트
- **`build_and_package.sh`** - Shell 통합 스크립트

## 출력 파일

빌드 완료 후 생성되는 파일들:

```
dist/
├── FontMerge.app/          # macOS 앱 번들
│   ├── Contents/
│   │   ├── Info.plist     # 앱 메타데이터
│   │   ├── MacOS/         # 실행 파일
│   │   └── Resources/     # 아이콘 및 리소스
│   └── ...
└── ...

FontMerge-1.0.0.dmg        # 배포용 DMG 설치 파일
```

## 앱 번들 구조

생성된 `FontMerge.app`의 구조:

```
FontMerge.app/
├── Contents/
│   ├── Info.plist          # 앱 정보 (번들 ID, 버전 등)
│   ├── MacOS/
│   │   └── FontMerge       # 메인 실행 파일
│   ├── Resources/
│   │   ├── icon.icns       # 앱 아이콘
│   │   └── ...             # 기타 리소스
│   └── Frameworks/         # 내장 라이브러리
```

## DMG 설치 파일 특징

- **사용자 친화적 레이아웃**: 드래그 앤 드롭으로 설치
- **커스텀 배경**: Font Merge 브랜딩이 적용된 배경
- **Applications 링크**: 설치 대상 폴더 바로가기
- **압축 최적화**: UDZO 형식으로 최대 압축

## 배포

### 개발자 서명 (선택사항)

프로덕션 배포를 위해서는 Apple Developer 인증서로 서명:

```bash
# 앱 번들 서명
codesign --deep --force --verify --verbose --sign "Developer ID Application: Your Name" dist/FontMerge.app

# DMG 서명  
codesign --force --verify --verbose --sign "Developer ID Application: Your Name" FontMerge-1.0.0.dmg

# 공증 (notarization)
xcrun notarytool submit FontMerge-1.0.0.dmg --keychain-profile "notarytool-profile"
```

### 배포 방법

1. **직접 배포**: DMG 파일을 웹사이트에서 다운로드 제공
2. **GitHub Releases**: 릴리스 페이지에 DMG 첨부
3. **Mac App Store**: 별도의 App Store 빌드 과정 필요

## 문제 해결

### 자주 발생하는 문제

1. **PyInstaller 설치 실패**
   ```bash
   pip install --upgrade pip
   pip install PyInstaller
   ```

2. **아이콘이 표시되지 않음**
   - `icon.icns` 파일이 프로젝트 루트에 있는지 확인

3. **앱이 실행되지 않음**
   - 터미널에서 `dist/FontMerge.app/Contents/MacOS/FontMerge` 직접 실행하여 오류 메시지 확인

4. **DMG 생성 실패**
   - Xcode Command Line Tools 설치 확인
   - 디스크 공간 확인

### 디버깅

빌드 로그 확인:
```bash
python3 build_macos.py 2>&1 | tee build.log
```

앱 번들 검증:
```bash
# 실행 파일 확인
file dist/FontMerge.app/Contents/MacOS/FontMerge

# 의존성 확인  
otool -L dist/FontMerge.app/Contents/MacOS/FontMerge

# 번들 구조 확인
tree dist/FontMerge.app
```

## 버전 관리

Git 태그를 사용하여 버전 관리:

```bash
# 태그 생성
git tag v1.0.1

# 빌드 시 자동으로 버전 감지됨
python3 build_and_package.py
```

## 성능 최적화

빌드 시간과 파일 크기 최적화:

1. **UPX 압축 활성화** (build_macos.spec에서 `upx=True`)
2. **불필요한 모듈 제외** (`excludes` 리스트 활용)
3. **빌드 캐시 활용** (연속 빌드 시 자동 적용)

---

## 빠른 시작

```bash
# 1. 저장소 클론
git clone <repository-url>
cd font-merge

# 2. 의존성 설치
pip install -r requirements.txt

# 3. 빌드 및 패키지
python3 build_and_package.py

# 4. 결과 확인
open dist/
open FontMerge-1.0.0.dmg
```

빌드 완료! 🎉