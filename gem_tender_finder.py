"""
GeM Tender Finder - Category Search & Tracking Module
"""

import re
import json
import requests
from typing import Dict, List, Optional


class GemTenderFinder:
    BASE_URL = "https://bidplus.gem.gov.in"
    SEARCH_PAGE_URL = f"{BASE_URL}/advance-search"
    SEARCH_API_URL = f"{BASE_URL}/search-bids"

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/124.0.0.0 Safari/537.36"
            ),
            "Referer": self.SEARCH_PAGE_URL,
            "Origin": self.BASE_URL,
            "X-Requested-With": "XMLHttpRequest",
        })
        self.csrf_token: Optional[str] = None
        self.category_map: Dict[str, str] = {}  # category_name_lower -> (cat_id, original_name)

    def init_session(self) -> bool:
        """Fetch advance-search page to extract CSRF token and category mappings."""
        try:
            resp = self.session.get(self.SEARCH_PAGE_URL, timeout=25)
            if resp.status_code != 200:
                print(f"[Error] Failed to load advance search page: HTTP {resp.status_code}")
                return False

            # Extract CSRF token
            csrf_match = re.search(r"csrf_bd_gem_nk['\"]\s*:\s*['\"]([a-f0-9]+)['\"]", resp.text)
            if csrf_match:
                self.csrf_token = csrf_match.group(1)
            elif "csrf_gem_cookie" in self.session.cookies:
                self.csrf_token = self.session.cookies["csrf_gem_cookie"]

            # Parse category dropdown options: <option value="cat_id">Category Name</option>
            options = re.findall(
                r'<option\s+value=["\']([^"\']+)["\'][^>]*>\s*([^<]+)\s*</option>',
                resp.text
            )
            for val, name in options:
                name_clean = name.strip()
                self.category_map[name_clean.lower()] = (val, name_clean)

            print(f"[Success] Initialized session. Loaded {len(self.category_map)} categories.")
            return True
        except Exception as e:
            print(f"[Error] Session initialization failed: {e}")
            return False

    def find_category_code(self, category_query: str) -> Optional[tuple]:
        """Find category code (cat_id, full_name) by exact match or substring match."""
        q = category_query.strip().lower()
        if q in self.category_map:
            return self.category_map[q]

        for k, v in self.category_map.items():
            if q in k:
                return v
        return None

    def search_category(self, category_query: str, page: int = 1) -> List[dict]:
        """Search tenders for a given category name."""
        if not self.csrf_token or not self.category_map:
            if not self.init_session():
                return []

        cat_info = self.find_category_code(category_query)
        if not cat_info:
            print(f"[Warning] Category '{category_query}' not found in GeM category list.")
            return []

        cat_id, full_cat_name = cat_info
        print(f"[Searching] Category: '{full_cat_name}' (Code: {cat_id}) | Page: {page}")

        payload = {
            "searchType": "bidNumber",
            "bidNumber": "",
            "category": cat_id,
            "bidEndFrom": "",
            "bidEndTo": "",
            "page": page,
        }

        post_data = {
            "payload": json.dumps(payload),
            "csrf_bd_gem_nk": self.csrf_token,
        }

        try:
            resp = self.session.post(self.SEARCH_API_URL, data=post_data, timeout=25)
            if resp.status_code == 404:
                # GeM returns 404 when no active bids match the search criteria
                return []
            if resp.status_code != 200:
                print(f"[Error] Search request failed: HTTP {resp.status_code}")
                return []

            res_json = resp.json()
            docs = res_json.get("response", {}).get("response", {}).get("docs", [])
            parsed_bids = []
            for doc in docs:
                bid_id = doc.get("b_id", [None])[0] if isinstance(doc.get("b_id"), list) else doc.get("b_id")
                bid_no = doc.get("b_bid_number", [None])[0] if isinstance(doc.get("b_bid_number"), list) else doc.get("b_bid_number")
                quantity = doc.get("b_total_quantity", [None])[0] if isinstance(doc.get("b_total_quantity"), list) else doc.get("b_total_quantity")
                start_date = doc.get("final_start_date_sort", [None])[0] if isinstance(doc.get("final_start_date_sort"), list) else doc.get("final_start_date_sort")
                end_date = doc.get("final_end_date_sort", [None])[0] if isinstance(doc.get("final_end_date_sort"), list) else doc.get("final_end_date_sort")
                dept = doc.get("ba_official_details_deptName", [None])[0] if isinstance(doc.get("ba_official_details_deptName"), list) else doc.get("ba_official_details_deptName")

                parsed_bids.append({
                    "bid_id": bid_id,
                    "bid_number": bid_no,
                    "category": full_cat_name,
                    "quantity": quantity,
                    "department": dept,
                    "start_date": start_date,
                    "end_date": end_date,
                    "document_url": f"{self.BASE_URL}/showbidDocument/{bid_id}" if bid_id else None
                })
            return parsed_bids
        except Exception as e:
            print(f"[Error] Search exception: {e}")
            return []


if __name__ == "__main__":
    finder = GemTenderFinder()
    if finder.init_session():
        # Test categories from user
        test_categories = [
            "Travis",
            "Veterinary Artificial Insemination Straws (low Absorption Type)",
            "Foreign Body (metal) Detector For Veterinary Use",
            "Cattle Lifting Machine"
        ]

        for cat in test_categories:
            print("\n" + "=" * 60)
            bids = finder.search_category(cat)
            print(f"Result for '{cat}': Found {len(bids)} active tenders")
            for b in bids:
                print(f"  - Bid No: {b['bid_number']} | Qty: {b['quantity']} | End: {b['end_date']}")
                print(f"    Dept: {b['department']}")
                print(f"    Doc:  {b['document_url']}")
