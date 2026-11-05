"""
GeM Tender Tracker & State Manager
Tracks seen tenders in a local JSON database so duplicates are never alerted.
"""

import json
import os
from typing import List, Dict, Set
from gem_tender_finder import GemTenderFinder

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SEEN_DB_FILE = os.path.join(BASE_DIR, "seen_tenders.json")


class TenderTracker:
    def __init__(self, db_path: str = SEEN_DB_FILE):
        self.db_path = db_path
        self.seen_ids: Set[str] = self._load_seen()
        self.finder = GemTenderFinder()

    def _load_seen(self) -> Set[str]:
        if os.path.exists(self.db_path):
            try:
                with open(self.db_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    return set(data.keys())
            except Exception as e:
                print(f"[Warning] Could not load {self.db_path}: {e}")
        return set()

    def _save_tender(self, tender: dict):
        current_data = {}
        if os.path.exists(self.db_path):
            try:
                with open(self.db_path, "r", encoding="utf-8") as f:
                    current_data = json.load(f)
            except Exception:
                current_data = {}

        bid_key = str(tender["bid_number"])
        current_data[bid_key] = tender

        with open(self.db_path, "w", encoding="utf-8") as f:
            json.dump(current_data, f, indent=2)

    def check_new_tenders(self, categories: List[str]) -> Dict[str, List[dict]]:
        """
        Check for new tenders across categories.
        Returns a dict of {category_name: [new_tenders_list]}
        and automatically records them as seen.
        """
        if not self.finder.init_session():
            print("[Error] Failed to connect to GeM.")
            return {}

        new_tenders_by_category = {}

        for cat in categories:
            bids = self.finder.search_category(cat)
            new_for_cat = []

            for bid in bids:
                bid_key = str(bid["bid_number"])
                if bid_key not in self.seen_ids:
                    new_for_cat.append(bid)
                    self.seen_ids.add(bid_key)
                    self._save_tender(bid)

            new_tenders_by_category[cat] = new_for_cat

        return new_tenders_by_category


if __name__ == "__main__":
    tracker = TenderTracker()

    watched_categories = [
        "Travis",
        "Veterinary Artificial Insemination Straws (low Absorption Type)",
        "Foreign Body (metal) Detector For Veterinary Use",
        "Cattle Lifting Machine",
    ]

    print("Checking for NEW tenders...")
    results = tracker.check_new_tenders(watched_categories)

    for cat, new_bids in results.items():
        print(f"\nCategory: {cat} -> {len(new_bids)} new tender(s)")
        for b in new_bids:
            print(f"  [NEW] {b['bid_number']} | Qty: {b['quantity']} | End: {b['end_date']}")
            print(f"        Dept: {b['department']}")
            print(f"        Doc:  {b['document_url']}")

