from bs4 import BeautifulSoup
import requests
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from urllib.parse import urlparse

class WebScraper:
    def __init__(self):
        chrome_options = Options()
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        self.driver = webdriver.Chrome(options=chrome_options)

    def scrape_url(self, url):
        try:
            # Initial request to check if JS rendering is needed
            response = requests.get(url, timeout=10)
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Check if content needs JS rendering
            if self._needs_js_rendering(soup):
                content = self._scrape_with_selenium(url)
            else:
                content = self._scrape_with_requests(soup)
                
            # print("Inside scrape_url:", content)

            return {
                'status': 'success',
                'content': content,
                'metadata': self._get_metadata(soup)
            }

        except Exception as e:
            return {
                'status': 'error',
                'error': str(e)
            }

    def _needs_js_rendering(self, soup):
        # Check for signs that JS rendering might be needed
        return (
            len(soup.find_all('script', {'src': True})) > 5 or
            'react' in str(soup).lower() or
            'angular' in str(soup).lower() or
            'vue' in str(soup).lower()
        )

    def _scrape_with_selenium(self, url):
        self.driver.get(url)
        WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )
        
        return self._extract_content(BeautifulSoup(self.driver.page_source, 'html.parser'))

    def _scrape_with_requests(self, soup):
        return self._extract_content(soup)

    def _extract_content(self, soup):
        content = {
            'title': self._get_title(soup),
            'description': self._get_description(soup),
            'name': self._extract_name(soup),
            'about': self._extract_about(soup),
            'source': self._determine_source(soup),
            'industry': self._extract_industry(soup),
            'contact_info': self._extract_contact_info(soup),
            'email': self._extract_email(soup),
            'page_type': self._determine_page_type(soup)
        }
        return content

    def _get_metadata(self, soup):
        return {
            'meta_title': soup.title.string if soup.title else None,
            'meta_description': soup.find('meta', {'name': 'description'})['content'] if soup.find('meta', {'name': 'description'}) else None,
            'og_data': {
                tag['property'][3:]: tag['content']
                for tag in soup.find_all('meta', property=True)
                if tag['property'].startswith('og:')
            }
        }

    # Helper methods for content extraction
    def _get_title(self, soup):
        return soup.title.string if soup.title else None

    def _get_description(self, soup):
        meta_desc = soup.find('meta', {'name': 'description'})
        return meta_desc['content'] if meta_desc else None

    def _extract_name(self, soup):
        # Try common selectors for names
        selectors = [
            'h1', 
            '.profile-name',
            '.name',
            '[itemprop="name"]'
        ]
        for selector in selectors:
            element = soup.select_one(selector)
            if element:
                return element.text.strip()
        return None

    def _extract_about(self, soup):
        # Try common selectors for about sections
        selectors = [
            '.about',
            '#about',
            '[itemprop="description"]',
            '.bio',
            '.description'
        ]
        for selector in selectors:
            element = soup.select_one(selector)
            if element:
                return element.text.strip()
        return None

    def _determine_source(self, soup):
        domain = urlparse(self.driver.current_url).netloc
        if 'linkedin' in domain:
            return 'LinkedIn'
        elif 'facebook' in domain:
            return 'Facebook'
        elif 'twitter' in domain:
            return 'Twitter'
        else:
            return 'Website'

    def _extract_industry(self, soup):
        # Try common selectors for industry information
        selectors = [
            '.industry',
            '[itemprop="industry"]',
            '.business-category'
        ]
        for selector in selectors:
            element = soup.select_one(selector)
            if element:
                return element.text.strip()
        return None

    def _extract_contact_info(self, soup):
        contact_info = {}
        phone_elements = soup.find_all(text=lambda text: text and any(
            char.isdigit() for char in text
        ))
        if phone_elements:
            contact_info['phone'] = phone_elements[0].strip()
        
        address_element = soup.find('address')
        if address_element:
            contact_info['address'] = address_element.text.strip()
            
        return contact_info

    def _extract_email(self, soup):
        email_elements = soup.select('a[href^="mailto:"]')
        if email_elements:
            return email_elements[0]['href'].replace('mailto:', '')
        return None

    def _determine_page_type(self, soup):
        if soup.find('article'):
            return 'Article'
        elif soup.find(['form', 'input']):
            return 'Form/Contact'
        elif soup.find('table'):
            return 'Data'
        else:
            return 'General'

    def __del__(self):
        if hasattr(self, 'driver'):
            self.driver.quit()
