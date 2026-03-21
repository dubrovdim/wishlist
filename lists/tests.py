from bs4 import BeautifulSoup
from django.test import SimpleTestCase

from .views import _extract_image_url


class ExtractImageUrlTests(SimpleTestCase):
    def test_extracts_og_image_and_normalizes_relative_url(self):
        soup = BeautifulSoup(
            '<meta property="og:image" content="/images/product.webp">',
            'html.parser',
        )

        image_url = _extract_image_url(soup, 'https://comfy.ua/ua/example-product.html')

        self.assertEqual(image_url, 'https://comfy.ua/images/product.webp')

    def test_falls_back_to_twitter_image(self):
        soup = BeautifulSoup(
            '<meta name="twitter:image" content="https://cdn.example.com/product.jpg">',
            'html.parser',
        )

        image_url = _extract_image_url(soup, 'https://prom.ua/p123-test')

        self.assertEqual(image_url, 'https://cdn.example.com/product.jpg')

    def test_extracts_image_from_json_ld(self):
        soup = BeautifulSoup(
            '''
            <script type="application/ld+json">
            {
                "@context": "https://schema.org",
                "@type": "Product",
                "image": {
                    "@type": "ImageObject",
                    "url": "/media/product-main.jpg"
                }
            }
            </script>
            ''',
            'html.parser',
        )

        image_url = _extract_image_url(soup, 'https://prom.ua/p123-test')

        self.assertEqual(image_url, 'https://prom.ua/media/product-main.jpg')
