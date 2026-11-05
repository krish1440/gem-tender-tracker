"""
Main entry point for GeM Tender Finder
Executes tender check, records new tenders, and sends email alerts.
"""

import json
import os
import sys
from datetime import datetime
from tracker import TenderTracker
from email_notifier import EmailNotifier

CONFIG_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.json")
LOG_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "run.log")


def log(msg: str):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    formatted = f"[{timestamp}] {msg}"
    print(formatted)
    try:
        with open(LOG_PATH, "a", encoding="utf-8") as f:
            f.write(formatted + "\n")
    except Exception:
        pass


def run():
    log("================== Starting Daily GeM Tender Check ==================")

    if not os.path.exists(CONFIG_PATH):
        log(f"[Error] config.json not found at {CONFIG_PATH}")
        return

    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        config = json.load(f)

    email_conf = config.get("email", {})
    categories = config.get("watched_categories", [])

    if not categories:
        log("[Warning] No categories configured in config.json.")
        return

    tracker = TenderTracker()
    log(f"Checking {len(categories)} categories: {', '.join(categories)}")
    new_tenders = tracker.check_new_tenders(categories)

    total_new = sum(len(bids) for bids in new_tenders.values())
    log(f"Check completed. Found {total_new} new tender(s).")

    if total_new > 0:
        sender = email_conf.get("sender_email")
        app_pass = email_conf.get("app_password")
        recipient = email_conf.get("recipient_email")

        if not app_pass or app_pass.strip() == "":
            log("[Action Required] New tenders found, but email 'app_password' is not set in config.json!")
            log("Please add your 16-character Gmail App Password to config.json.")
        else:
            log(f"Sending email notification from {sender} to {recipient}...")
            notifier = EmailNotifier(sender, app_pass, recipient)
            success = notifier.send_tender_alert(new_tenders)
            if success:
                log("Email successfully sent.")
            else:
                log("[Error] Could not send email. See console output for details.")
    else:
        log("No new tenders found today. No alert needed.")

    log("================== Finished Daily GeM Tender Check ==================\n")


if __name__ == "__main__":
    run()

