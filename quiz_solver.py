import requests
from urllib.parse import urljoin
import re
from io import BytesIO

class QuizSolver:
    def __init__(self):
        pass  # no browser

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

        question_text = html

        # Extract all href links
        links = {}
        for match in re.finditer(r'<a[^>]+href="([^"]+)"[^>]*>(.*?)</a>', html, re.I | re.S):
            href = match.group(1)
            text = re.sub(r"\s+", " ", match.group(2)).strip()
            full_url = urljoin(quiz_url, href)
            links[text or full_url] = full_url

        # Also extract absolute URLs from text
        url_pattern = r'https?://[^\s)"<]+'
        text_urls = re.findall(url_pattern, html)
        for u in text_urls:
            if u not in links.values():
                links[u] = u

        # Detect submit URL
        submit_url = None
        
        # Look in links for "submit"
        for t, u in links.items():
            if "submit" in u.lower():
                submit_url = u
                break
        
        # If not found, look in raw text URLs
        if submit_url is None:
            for u in text_urls:
                if "submit" in u.lower():
                    submit_url = u
                    break
        
        # Hard-code for project2 entry
        if submit_url is None and "/project2" in quiz_url:
            submit_url = "https://tds-llm-analysis.s-anand.net/submit"

        print(f"✅ Question (first line): {question_text.splitlines()[0][:80]}...")
        print(f"✅ Links found: {len(links)} link(s)")
        print(f"✅ Submit URL: {submit_url}")

        return {
            "question": question_text.strip(),
            "links": links,
            "submit_url": submit_url,
        }

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
            from PyPDF2 import PdfReader
            reader = PdfReader(BytesIO(pdf_bytes))
            text = ""
            for page in reader.pages:
                text += page.extract_text() or ""
            return text
        except Exception as e:
            print(f"⚠️ PDF extract failed: {e}")
            return ""