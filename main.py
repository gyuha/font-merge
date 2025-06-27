import os
import sys

# 현재 디렉토리를 Python 경로에 추가
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from font_merge.main import main as font_merge_main


def main():
    """Font Merge 애플리케이션 실행"""
    font_merge_main()


if __name__ == "__main__":
    main()
