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
        import requests
from urllib.parse import urljoin
import re

class QuizSolver:
    def __init__(self):
        pass  # no browser now

    def close_browser(self):
        print("  ✅ (No browser to close)")

    def visit_and_parse_quiz(self, quiz_url):
        """
        Visit quiz URL and parse the question using requests only.
        Returns: {question, links, submit_url}
        """
        print(f"  🌐 Fetching: {quiz_url}")
        resp = requests.get(quiz_url, timeout=15)
        resp.raise_for_status()
        html = resp.text

        # Very simple “question” = body text
        question_text = html

        # Extract all href links
        links = {}
        for match in re.finditer(r'<a[^>]+href="([^"]+)"[^>]*>(.*?)</a>', html, re.I | re.S):
            href = match.group(1)
            text = re.sub(r"\s+", " ", match.group(2)).strip()
            full_url = urljoin(quiz_url, href)
            links[text or full_url] = full_url

        # Fallback: also parse text for absolute URLs
        url_pattern = r'https?://[^\s)"<]+'
        text_urls = re.findall(url_pattern, html)
        for u in text_urls:
            links.setdefault(u, u)

        # Detect submit URL
        submit_url = None
        for t, u in links.items():
            if "submit" in u.lower():
                submit_url = u
                break
        if submit_url is None:
            # fallback: last URL with "submit" in text
            for u in reversed(text_urls):
                if "submit" in u.lower():
                    submit_url = u
                    break
        if submit_url is None and text_urls:
            submit_url = text_urls[-1]

        print(f"✅ Question (first line): {question_text.splitlines()[0][:80]}...")
        print(f"✅ Links: {links}")
        print(f"✅ Submit URL: {submit_url}")

        return {
            "question": question_text.strip(),
            "links": links,
            "submit_url": submit_url,
        }


    def extract_submit_url_from_text(self, text):
        """Extract submit URL from page content as fallback"""
                # Detect submit URL
        submit_url = None
        for t, u in links.items():
            if "submit" in u.lower():
                submit_url = u
                break

        if submit_url is None:
            # fallback: last URL with "submit" in text
            for u in reversed(text_urls):
                if "submit" in u.lower():
                    submit_url = u
                    break

        # ⭐ Special case: project2 instructions mention fixed submit URL
        if submit_url is None and "/project2" in quiz_url:
            submit_url = "https://tds-llm-analysis.s-anand.net/submit"

        if submit_url is None and text_urls:
            submit_url = text_urls[-1]


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
