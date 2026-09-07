import json
import requests
from typing import Dict, List, Optional
from bs4 import BeautifulSoup

BASE_URL = "https://genshin-impact.fandom.com"


class CatalogueRefreshError(RuntimeError):
    """Raised when the achievement catalogue cannot be fetched or updated."""

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


def refresh_achievement_catalogue(
    output_path: str = "all_achievements.json",
    strict: bool = False,
) -> Dict[str, int]:
    """Fetch, compare, and optionally update the local achievement catalogue.

    In normal processing mode, refresh failures are warnings and the caller can
    continue using the existing catalogue. In strict mode, failures are raised
    so a fetch-only command can return a non-zero exit code.
    """
    try:
        with open(output_path, "r", encoding="utf-8") as f:
            local_achievements = json.load(f)

        parser = MediaWikiPageParser()
        remote_achievements = GenshinAchievement(parser).get_all_achievements()

        if not isinstance(local_achievements, list) or not isinstance(remote_achievements, list):
            raise ValueError("catalogue data must be a list")

        local_by_title = {
            item["Achievement"]: item
            for item in local_achievements
            if isinstance(item, dict) and item.get("Achievement")
        }
        remote_by_title = {
            item["Achievement"]: item
            for item in remote_achievements
            if isinstance(item, dict) and item.get("Achievement")
        }

        added = remote_by_title.keys() - local_by_title.keys()
        shared = remote_by_title.keys() & local_by_title.keys()
        updated = {
            title for title in shared
            if remote_by_title[title] != local_by_title[title]
        }
        unchanged = shared - updated
        missing_remotely = local_by_title.keys() - remote_by_title.keys()

        if added or updated:
            merged_achievements = remote_achievements + [
                local_by_title[title]
                for title in local_by_title
                if title in missing_remotely
            ]
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(merged_achievements, f, indent=4, ensure_ascii=False)
                f.write("\n")

        summary = {
            "added": len(added),
            "updated": len(updated),
            "missing_remotely": len(missing_remotely),
            "unchanged": len(unchanged),
        }
        print(
            "Achievement catalogue: "
            f"{summary['added']} added, "
            f"{summary['updated']} updated, "
            f"{summary['missing_remotely']} missing remotely, "
            f"{summary['unchanged']} unchanged"
        )
        return summary
    except Exception as exc:
        message = f"Could not refresh achievement catalogue: {exc}"
        if strict:
            raise CatalogueRefreshError(message) from exc
        print(f"Warning: {message}")
        return {
            "added": 0,
            "updated": 0,
            "missing_remotely": 0,
            "unchanged": 0,
        }
