"""멀티모달 출력 유틸리티 - 사이드채널 + 마크다운 이미지 하이브리드.

도구에서 이미지를 등록하면 app.py가 Chainlit cl.Image로 렌더링합니다.

사용법 (도구 안에서):
    from media_utils import add_image
    add_image(path="/tmp/chart.png", caption="CPU 사용률")
    add_image(url="https://example.com/img.png", caption="뉴스 이미지")
"""
import re

_media_queue: list[dict] = []


def add_image(path: str = None, url: str = None, data: bytes = None, caption: str = ""):
    """이미지를 사이드채널에 등록."""
    _media_queue.append({"type": "image", "path": path, "url": url, "data": data, "caption": caption})


def flush() -> list[dict]:
    """등록된 미디어를 반환하고 큐를 비움."""
    items = list(_media_queue)
    _media_queue.clear()
    return items


_MD_IMG_RE = re.compile(r'!\[([^\]]*)\]\(([^)]+)\)')


def extract_markdown_images(text: str) -> tuple[str, list[dict]]:
    """텍스트에서 마크다운 이미지를 추출. 반환: (정리된 텍스트, 이미지 리스트)."""
    images = [{"type": "image", "url": m[1], "caption": m[0]} for m in _MD_IMG_RE.findall(text)]
    cleaned = _MD_IMG_RE.sub('', text).strip() if images else text
    return cleaned, images
