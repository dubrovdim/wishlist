import json
from io import BytesIO
from urllib.parse import urljoin
import requests
from bs4 import BeautifulSoup
from django.core.files.base import ContentFile
from PIL import Image, UnidentifiedImageError

REQUEST_TIMEOUT = 10


def _build_session():
    session = requests.Session()
    session.headers.update({
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/134.0.0.0 Safari/537.36"
        ),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
        "Accept-Language": "uk-UA,uk;q=0.9,en-US;q=0.8,en;q=0.7",
    })
    return session


def _normalize_image_value(value):
    if isinstance(value, str) and value:
        return value

    if isinstance(value, list):
        for item in value:
            result = _normalize_image_value(item)
            if result:
                return result

    if isinstance(value, dict):
        for key in ("url", "contentUrl"):
            result = _normalize_image_value(value.get(key))
            if result:
                return result

    return None


def _extract_image_from_json_ld(data):
    if isinstance(data, list):
        for item in data:
            result = _extract_image_from_json_ld(item)
            if result:
                return result

    if isinstance(data, dict):
        image_value = _normalize_image_value(data.get("image"))
        if image_value:
            return image_value

        for value in data.values():
            result = _extract_image_from_json_ld(value)
            if result:
                return result

    return None



def _pick_best_from_srcset(srcset):
    best_url = None
    best_width = -1

    for chunk in srcset.split(","):
        parts = chunk.strip().split()
        if not parts:
            continue

        url = parts[0]
        width = 0

        if len(parts) > 1 and parts[1].endswith("w"):
            try:
                width = int(parts[1][:-1])
            except ValueError:
                width = 0

        if width >= best_width:
            best_width = width
            best_url = url

    return best_url


def _extract_image_url(soup, page_url):
    meta_candidates = [
        ("meta", {"property": "og:image"}, "content"),
        ("meta", {"name": "twitter:image"}, "content"),
        ("meta", {"name": "twitter:image:src"}, "content"),
        ("meta", {"itemprop": "image"}, "content"),
        ("link", {"rel": "image_src"}, "href"),
    ]

    for tag_name, attrs, field in meta_candidates:
        tag = soup.find(tag_name, attrs=attrs)
        value = tag.get(field) if tag else None
        if value:
            return urljoin(page_url, value)

    for script in soup.find_all("script", type="application/ld+json"):
        raw_json = script.string or script.get_text()
        if not raw_json or not raw_json.strip():
            continue

        try:
            payload = json.loads(raw_json)
        except json.JSONDecodeError:
            continue

        image_url = _extract_image_from_json_ld(payload)
        if image_url:
            return urljoin(page_url, image_url)

    srcset_candidates = soup.select("img[srcset], img[data-srcset], source[srcset]")
    for tag in srcset_candidates:
        srcset = tag.get("srcset") or tag.get("data-srcset")
        if srcset:
            best = _pick_best_from_srcset(srcset)
            if best:
                return urljoin(page_url, best)

    attr_candidates = [
        ("img", "data-src"),
        ("img", "src"),
    ]
    for selector, attr in attr_candidates:
        for tag in soup.select(selector):
            value = tag.get(attr)
            if value:
                return urljoin(page_url, value)

    return None

def fetch_product_image_file(shop_url):
    session = _build_session()

    try:
        response = session.get(shop_url, timeout=REQUEST_TIMEOUT, allow_redirects=True)
        response.raise_for_status()
    except requests.RequestException:
        return None

    soup = BeautifulSoup(response.text, "html.parser")
    image_url = _extract_image_url(soup, response.url)
    if not image_url:
        return None

    try:
        img_response = session.get(
            image_url,
            headers={
                "Referer": response.url,
                "Accept": "image/webp,image/jpeg,image/png,image/*;q=0.8,*/*;q=0.5",
            },
            timeout=REQUEST_TIMEOUT,
        )
        img_response.raise_for_status()

        content_type = img_response.headers.get("Content-Type", "")
        if content_type and not content_type.startswith("image/"):
            return None

        img = Image.open(BytesIO(img_response.content))

        if img.mode != "RGB":
            img = img.convert("RGB")

        img.thumbnail((600, 600))

        buffer = BytesIO()
        img.save(buffer, format="JPEG", quality=80, optimize=True)

        return ContentFile(buffer.getvalue(), name="product.jpg")

    except (requests.RequestException, UnidentifiedImageError, OSError):
        return None
