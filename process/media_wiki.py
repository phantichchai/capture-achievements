import requests
from typing import Dict, List, Optional
from bs4 import BeautifulSoup

BASE_URL = "https://genshin-impact.fandom.com"

class MediaWikiPageParser:
    def __init__(
        self,
        api_url: str = "https://genshin-impact.fandom.com/api.php",
        timeout: int = 10,
    ):
        self.api_url = api_url
        self.timeout = timeout

        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (compatible; GenshinScraper/1.0)"
        })

    # -----------------------------
    # Core API request
    # -----------------------------
    def _get(self, params: Dict) -> Dict:
        r = requests.get(self.api_url, params=params, timeout=self.timeout)
        r.raise_for_status()
        return r.json()

    # -----------------------------
    # Get all sections of a page
    # -----------------------------
    def get_sections(self, page: str) -> List[Dict]:
        """
        Returns a list of sections with:
        index, line (title), level
        """
        params = {
            "action": "parse",
            "page": page,
            "prop": "sections",
            "format": "json",
        }

        data = self._get(params)
        return data["parse"]["sections"]

    # -----------------------------
    # Get section index by name
    # -----------------------------
    def get_section_index(
        self,
        page: str,
        section_name: str,
    ) -> Optional[int]:
        for sec in self.get_sections(page):
            if sec["line"].strip().lower() == section_name.lower():
                return int(sec["index"])
        return None

    # -----------------------------
    # Get HTML (full page or section)
    # -----------------------------
    def get_html(
        self,
        page: str,
        section_index: Optional[int] = None,
    ) -> str:
        params = {
            "action": "parse",
            "page": page,
            "prop": "text",
            "format": "json",
        }

        if section_index is not None:
            params["section"] = section_index

        data = self._get(params)
        return data["parse"]["text"]["*"]


class GenshinAchievement:
    def __init__(self, parser: MediaWikiPageParser):
        self.parser = parser

    def get_all_achievements(self) -> list[str]:
        
        page = "Wonders_of_the_World"
        idx = self.parser.get_section_index(page=page, section_name="Achievement List")
        html = self.parser.get_html(page, idx)
        soup = BeautifulSoup(html, "html.parser")
        
        table = soup.find("table")

        headers = []
        data = []

        for th in table.find_all("th"):
            text = th.get_text(strip=True)
            header = text if text != "" else "Primogem" 
        
            headers.append(header)

        for row in table.find_all("tr")[1:]:
            cells = row.find_all(["td", "th"])
            row_dict = {}

            for header, cell in zip(headers, cells):
                text = cell.get_text(strip=True)
                row_dict[header] = text

                # If this is the Achievement column, extract link
                if header == "Achievement":
                    link_tag = cell.find("a", href=True)
                    if link_tag:
                        row_dict["Achievement_link"] = BASE_URL + link_tag["href"]

            if row_dict:
                data.append(row_dict)

        return data
        