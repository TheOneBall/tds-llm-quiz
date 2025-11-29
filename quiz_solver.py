from playwright.sync_api import sync_playwright
from urllib.parse import urljoin
import re
import requests
from io import BytesIO
from PyPDF2 import PdfReader


class QuizSolver:
    def __init__(self):
        self.browser = None
        self.context = None
        self.playwright = None

    def init_browser(self):
        """Initialize browser - SYNCHRONOUS (no async/await)"""
        try:
            print("  🔧 Starting Playwright...")
            self.playwright = sync_playwright().start()

            print("  🌐 Launching browser...")
            self.browser = self.playwright.chromium.launch(headless=True)

            print("  📄 Creating context...")
            self.context = self.browser.new_context()

            print("  ✅ Browser ready!")
        except Exception as e:
            print(f"  ❌ Browser init failed: {e}")
            raise

    def close_browser(self):
        """Close browser and cleanup"""
        try:
            if self.context:
                self.context.close()
            if self.browser:
                self.browser.close()
            if self.playwright:
                self.playwright.stop()
            print("  ✅ Browser closed")
        except Exception as e:
            print(f"  ⚠️ Close error: {e}")

    def visit_and_parse_quiz(self, quiz_url):
        """
        Visit quiz URL and parse the question.
        Returns: {question, links, submit_url}
        """
        if not self.browser:
            self.init_browser()

        page = None
        try:
            page = self.context.new_page()

            print(f"  📍 Navigating to: {quiz_url}")
            page.goto(quiz_url, wait_until="networkidle", timeout=30000)

            print(f"  ⏳ Waiting for JavaScript to render...")
            page.wait_for_timeout(2000)

            print(f"  📖 Extracting question text...")
            question_text = page.inner_text("body")

            print(f"  🔗 Extracting links...")
            anchors = page.locator("a").all()
            link_urls = {}
            submit_url = None

            for link in anchors:
                href = link.get_attribute("href")
                text = (link.inner_text() or "").strip()
                if not href:
                    continue

                full_url = urljoin(quiz_url, href)
                link_urls[text or full_url] = full_url

                if "/submit" in href and submit_url is None:
                    submit_url = full_url

            print(f"  🎯 Detecting submit URL (fallback if needed)...")
            if submit_url is None:
                submit_url = self.extract_submit_url_from_text(question_text)

            page.close()
            page = None

            print(f"✅ Question: {question_text.splitlines()[0][:80]}...")
            print(f"✅ Links: {link_urls}")
            print(f"✅ Submit URL: {submit_url}")

            return {
                "question": question_text.strip(),
                "links": link_urls,
                "submit_url": submit_url,
            }

        except Exception as e:
            if page:
                page.close()
            raise Exception(f"Error parsing quiz page: {str(e)}")

    def extract_submit_url_from_text(self, text):
        """Extract submit URL from page content as fallback"""
        url_pattern = r'https?://[^\s\)\"<]+'
        urls = re.findall(url_pattern, text)

        for url in reversed(urls):
            if "submit" in url.lower():
                return url

        return urls[-1] if urls else None

    # Optional helpers used in main.py
    def download_file(self, url):
        """Download a file and return bytes or text"""
        try:
            resp = requests.get(url, timeout=15)
            resp.raise_for_status()
            content_type = resp.headers.get("content-type", "").lower()
            if "pdf" in content_type:
                return resp.content
            return resp.text
        except Exception as e:
            print(f"⚠️ Download failed for {url}: {e}")
            return None

    def extract_text_from_pdf(self, pdf_bytes):
        """Extract text from PDF bytes"""
        try:
            reader = PdfReader(BytesIO(pdf_bytes))
            text = ""
            for page in reader.pages:
                text += page.extract_text() or ""
            return text
        except Exception as e:
            print(f"⚠️ PDF extract failed: {e}")
            return ""
