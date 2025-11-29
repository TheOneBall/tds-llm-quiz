"""
Quiz Solver Module
Handles browser automation and data extraction.
"""

from playwright.sync_api import sync_playwright
from urllib.parse import urljoin
import re
import requests
from io import BytesIO

class QuizSolver:
    def __init__(self):
        """Initialize quiz solver"""
        self.browser = None
        self.context = None
        self.playwright = None
    
    def init_browser(self):
        """
        Initialize headless browser.
        Headless = no GUI, runs in background.
        """
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
        """Cleanup: close browser gracefully"""
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
        Visit quiz page (with JavaScript rendering) and extract:
        - Question text
        - Download links
        - Submit URL
        
        Returns:
            dict: {"question": str, "links": dict, "submit_url": str}
        """
        if not self.browser:
            self.init_browser()
        
        page = None
        try:
            page = self.context.new_page()
            
            print(f"  📍 Navigating to: {quiz_url}")
            # wait_until="networkidle" = wait for page to fully load
            page.goto(quiz_url, wait_until="networkidle", timeout=30000)
            
            print(f"  ⏳ Waiting for JavaScript to render...")
            page.wait_for_timeout(2000)  # Extra wait for any dynamic content
            
            print(f"  📖 Extracting question text...")
            # Get ALL text visible on page
            question_text = page.inner_text("body")
            
            print(f"  🔗 Extracting links...")
            # Find all <a> tags
            anchors = page.locator("a").all()
            link_urls = {}
            submit_url = None
            
            for link in anchors:
                href = link.get_attribute("href")
                text = (link.inner_text() or "").strip()
                
                if not href:
                    continue
                
                # Convert relative URLs to absolute
                # Example: "/submit" becomes "https://example.com/submit"
                full_url = urljoin(quiz_url, href)
                link_urls[text or full_url] = full_url
                
                # If we find a /submit link, that's likely the submit endpoint
                if "/submit" in href.lower() and submit_url is None:
                    submit_url = full_url
            
            # Fallback: extract submit URL from text if not found in links
            if submit_url is None:
                submit_url = self.extract_submit_url(question_text, base_url=quiz_url)
            
            page.close()
            page = None
            
            return {
                "question": question_text.strip(),
                "links": link_urls,
                "submit_url": submit_url,
            }
        
        except Exception as e:
            if page:
                page.close()
            raise Exception(f"❌ Error parsing quiz page: {str(e)}")
    
    def download_file(self, url, file_type="auto"):
        """
        Download a file (PDF, CSV, etc.) from URL.
        
        Args:
            url (str): URL to download from
            file_type (str): "pdf", "csv", "json", etc. or "auto" to detect
        
        Returns:
            str or dict: File content (text for CSV/JSON, bytes for PDF)
        """
        try:
            print(f"  📥 Downloading: {url}")
            response = requests.get(url, timeout=15)
            response.raise_for_status()
            
            # Detect file type if needed
            if file_type == "auto":
                if ".pdf" in url.lower():
                    file_type = "pdf"
                elif ".csv" in url.lower():
                    file_type = "csv"
                elif ".json" in url.lower():
                    file_type = "json"
                else:
                    file_type = "text"
            
            # Handle based on file type
            if file_type == "pdf":
                # For PDF: return raw content
                print(f"    ✅ PDF downloaded ({len(response.content)} bytes)")
                return response.content
            
            elif file_type == "csv":
                # For CSV: return as text
                print(f"    ✅ CSV downloaded")
                return response.text
            
            elif file_type == "json":
                # For JSON: return as dict
                print(f"    ✅ JSON downloaded")
                return response.json()
            
            else:
                # For others: return as text
                print(f"    ✅ File downloaded ({len(response.text)} chars)")
                return response.text
        
        except Exception as e:
            print(f"    ❌ Download failed: {str(e)}")
            return None
    
    def extract_text_from_pdf(self, pdf_content):
        """
        Extract text from PDF binary content.
        
        Args:
            pdf_content (bytes): Raw PDF data
        
        Returns:
            str: Extracted text
        """
        try:
            from PyPDF2 import PdfReader
            
            print(f"  📄 Extracting text from PDF...")
            
            # Convert bytes to file-like object
            pdf_file = BytesIO(pdf_content)
            reader = PdfReader(pdf_file)
            
            text = ""
            for page_num, page in enumerate(reader.pages):
                page_text = page.extract_text()
                text += f"\n--- Page {page_num + 1} ---\n{page_text}"
            
            print(f"    ✅ Extracted {len(reader.pages)} pages, {len(text)} chars")
            return text
        
        except Exception as e:
            print(f"    ❌ PDF extraction failed: {str(e)}")
            return ""
    
    def extract_submit_url(self, text, base_url):
        """
        Extract submit URL from text content.
        Looks for URLs containing "submit".
        
        Args:
            text (str): Text content
            base_url (str): Base URL for relative URL resolution
        
        Returns:
            str: Submit URL or None
        """
        # Find all URLs in text
        url_pattern = r'https?://[^\s\)\"<]+'
        urls = re.findall(url_pattern, text)
        
        if not urls:
            return None
        
        # Prefer URL containing "submit"
        for url in reversed(urls):
            if "submit" in url.lower():
                return url
        
        # Otherwise return last URL
        return urls[-1] if urls else None

