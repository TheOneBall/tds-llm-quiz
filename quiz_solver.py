"""
Quiz Solver Module

Handles:
1. Visiting quiz pages with browser
2. Parsing HTML to extract questions
3. Downloading linked files and data
4. Extracting submit URLs
"""

from playwright.sync_api import sync_playwright
from urllib.parse import urljoin
import re
import requests
from io import BytesIO

class QuizSolver:
    def __init__(self):
        """Initialize browser state variables"""
        self.browser = None
        self.context = None
        self.playwright = None
    
    def init_browser(self):
        """
        Initialize Playwright browser for JavaScript rendering.
        
        Why: Quiz pages use JavaScript to render content.
        Playwright executes JavaScript and gives us the rendered HTML.
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
        """Close browser and free up resources"""
        try:
            if self.context:
                self.context.close()
            if self.browser:
                self.browser.close()
            if self.playwright:
                self.playwright.stop()
        except Exception as e:
            print(f"  ⚠️ Close error: {e}")
    
    def visit_and_parse_quiz(self, quiz_url):
        """
        Visit quiz page and extract:
        1. The question text
        2. Links to data files
        3. The submit URL where we send answers
        
        Returns:
            Dictionary with:
            - question: The quiz question text
            - links: Dictionary of {text: url} for all links on page
            - submit_url: Where to POST our answer
        """
        if not self.browser:
            self.init_browser()
        
        page = None
        try:
            page = self.context.new_page()
            
            print(f"  📍 Navigating to: {quiz_url}")
            # wait_until="networkidle" means wait until network is idle (all resources loaded)
            page.goto(quiz_url, wait_until="networkidle", timeout=30000)
            
            print(f"  ⏳ Waiting for JavaScript to render...")
            # Give extra time for dynamic content to load
            page.wait_for_timeout(2000)
            
            print(f"  📖 Extracting question text...")
            # Get all visible text from the page
            question_text = page.inner_text("body")
            
            print(f"  🔗 Extracting links...")
            # Find all links on the page
            anchors = page.locator("a").all()
            link_urls = {}
            submit_url = None
            
            for link in anchors:
                href = link.get_attribute("href")
                text = (link.inner_text() or "").strip()
                
                if not href:
                    continue
                
                # Convert relative URLs to absolute URLs
                # Example: "/download" becomes "https://example.com/download"
                full_url = urljoin(quiz_url, href)
                link_urls[text or full_url] = full_url
                
                # If link contains "/submit", this is likely our submit endpoint
                if "/submit" in href and submit_url is None:
                    submit_url = full_url
            
            print(f"  🎯 Extracting submit URL...")
            # If we didn't find submit URL in links, search in text
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
            raise Exception(f"Error parsing quiz page: {str(e)}")
    
    def download_file(self, url):
        """
        Download a file from a URL and return its content.
        
        Args:
            url: The URL to download from
        
        Returns:
            The file content (text or bytes)
        """
        try:
            print(f"    📥 Downloading: {url}")
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            
            # Try to decode as text
            try:
                return response.text
            except:
                # If not text, return as bytes
                return response.content
        
        except Exception as e:
            print(f"    ❌ Download failed: {e}")
            return None
    
    def collect_data_from_links(self, links):
        """
        Download data from all relevant links.
        
        Only downloads files that look like data:
        - .pdf, .csv, .xlsx, .json, .txt, .xml
        
        Returns:
            Dictionary of {filename: content}
        """
        collected_data = {}
        
        data_extensions = ['.pdf', '.csv', '.xlsx', '.json', '.txt', '.xml', '.png', '.jpg']
        
        for link_text, link_url in links.items():
            # Check if URL has a data file extension
            if any(link_url.lower().endswith(ext) for ext in data_extensions):
                print(f"  📊 Collecting data from: {link_text}")
                content = self.download_file(link_url)
                if content:
                    collected_data[link_text] = content
        
        return collected_data
    
    def extract_submit_url(self, text, base_url):
        """
        Extract the submit URL from page text.
        
        Looks for URLs in the text and returns:
        1. URL containing "submit" if found
        2. Otherwise, the last URL found
        """
        url_pattern = r'https?://[^\s\)\"<]+'
        urls = re.findall(url_pattern, text)
        
        # Look for URL containing "submit"
        for url in reversed(urls):
            if "submit" in url.lower():
                return url
        
        # Return last URL if no submit URL found
        return urls[-1] if urls else None

