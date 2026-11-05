"""
Email Notification Service for GeM Tender Alerts
Sends modern, mobile-responsive HTML emails matching UX Pilot design with exact header.
"""

import smtplib
import os
import base64
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
from datetime import datetime
from typing import Dict, List

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
BUILDING_LOGO_PATH = os.path.join(BASE_DIR, "building_logo.png")
SHIELD_LOGO_PATH = os.path.join(BASE_DIR, "shield_logo.png")


class EmailNotifier:
    SMTP_SERVER = "smtp.gmail.com"
    SMTP_PORT = 465  # SSL

    def __init__(self, sender_email: str, app_password: str, recipient_email: str):
        self.sender_email = sender_email
        self.app_password = app_password.replace(" ", "").strip()
        self.recipient_email = recipient_email

    @staticmethod
    def _format_date(date_str: str) -> str:
        """Format ISO date string (e.g. 2026-11-09T18:00:00Z) to readable format."""
        if not date_str:
            return "N/A"
        try:
            clean = date_str.replace("Z", "")
            if "T" in clean:
                dt = datetime.fromisoformat(clean)
                return dt.strftime("%d-%b-%Y, %I:%M %p")
            return date_str
        except Exception:
            return date_str

    def send_tender_alert(self, new_tenders_by_category: Dict[str, List[dict]]) -> bool:
        """Format and send an alert email for newly discovered tenders."""
        total_new = sum(len(bids) for bids in new_tenders_by_category.values())
        if total_new == 0:
            print("[Info] No new tenders to email.")
            return False

        if not self.app_password:
            print("[Warning] App password is not set in config.json. Cannot send email.")
            return False

        subject = f"🔔 GeM Alert: {total_new} New Tender{'s' if total_new > 1 else ''} Found Today"
        html_body = self._build_html_template(new_tenders_by_category, total_new)

        msg = MIMEMultipart("related")
        msg["Subject"] = subject
        msg["From"] = f"GeM Tender Alert <{self.sender_email}>"
        msg["To"] = self.recipient_email

        alt_part = MIMEMultipart("alternative")
        plain_text = f"Hello,\n\nFound {total_new} new tenders on GeM matching your watched categories.\nPlease view this email in HTML for full cards and download links."
        alt_part.attach(MIMEText(plain_text, "plain"))
        alt_part.attach(MIMEText(html_body, "html"))
        msg.attach(alt_part)

        # Attach CID Images for 100% reliable rendering in Gmail
        if os.path.exists(BUILDING_LOGO_PATH):
            try:
                with open(BUILDING_LOGO_PATH, "rb") as f:
                    img = MIMEImage(f.read())
                    img.add_header("Content-ID", "<gem_logo>")
                    img.add_header("Content-Disposition", "inline", filename="gem_logo.png")
                    msg.attach(img)
            except Exception as e:
                print(f"[Warning] Could not attach building logo: {e}")

        if os.path.exists(SHIELD_LOGO_PATH):
            try:
                with open(SHIELD_LOGO_PATH, "rb") as f:
                    img = MIMEImage(f.read())
                    img.add_header("Content-ID", "<shield_logo>")
                    img.add_header("Content-Disposition", "inline", filename="shield_logo.png")
                    msg.attach(img)
            except Exception as e:
                print(f"[Warning] Could not attach shield logo: {e}")

        try:
            with smtplib.SMTP_SSL(self.SMTP_SERVER, self.SMTP_PORT, timeout=25) as server:
                server.login(self.sender_email, self.app_password)
                server.sendmail(self.sender_email, self.recipient_email, msg.as_string())
            print(f"[Success] Email alert successfully sent to {self.recipient_email}!")
            return True
        except smtplib.SMTPAuthenticationError:
            print("[Error] SMTP Authentication failed. Please check your Gmail App Password.")
            return False
        except Exception as e:
            print(f"[Error] Failed to send email: {e}")
            return False

    def _build_html_template(self, new_tenders: Dict[str, List[dict]], total_count: int) -> str:
        current_time_str = datetime.now().strftime("%d %b %Y, %I:%M %p")

        category_sections_html = ""

        for cat, bids in new_tenders.items():
            if not bids:
                continue

            cards_html = ""
            for b in bids:
                bid_no = b.get("bid_number") or "N/A"
                qty = b.get("quantity") if b.get("quantity") is not None else "N/A"
                dept = b.get("department") or "N/A"
                start_d = self._format_date(b.get("start_date"))
                end_d = self._format_date(b.get("end_date"))
                doc_url = b.get("document_url") or "#"

                cards_html += f"""
                <!-- TENDER CARD -->
                <table width="100%" cellpadding="0" cellspacing="0" border="0" style="background:#ffffff; border:1px solid #e2e8f0; border-radius:10px; margin-bottom:18px; box-shadow:0 2px 6px rgba(15,23,42,0.04); overflow:hidden;">
                    <tr>
                        <td style="padding:18px 20px;">
                            <!-- ROW 1: BID NUMBER & QUANTITY -->
                            <table width="100%" cellpadding="0" cellspacing="0" border="0">
                                <tr>
                                    <td valign="top" style="text-align:left;">
                                        <div style="font-size:10px; font-weight:700; color:#64748b; letter-spacing:0.8px; text-transform:uppercase;">BID NUMBER</div>
                                        <div style="font-size:16px; font-weight:800; color:#0f172a; margin-top:3px; word-break:break-all;">{bid_no}</div>
                                    </td>
                                    <td valign="top" style="text-align:right; width:90px;">
                                        <div style="font-size:10px; font-weight:700; color:#64748b; letter-spacing:0.8px; text-transform:uppercase;">QUANTITY</div>
                                        <div style="font-size:16px; font-weight:800; color:#0f172a; margin-top:3px;">{qty}</div>
                                    </td>
                                </tr>
                            </table>

                            <!-- ROW 2: DEPARTMENT -->
                            <div style="margin-top:14px;">
                                <div style="font-size:10px; font-weight:700; color:#64748b; letter-spacing:0.8px; text-transform:uppercase;">DEPARTMENT</div>
                                <div style="font-size:13px; font-weight:500; color:#334155; margin-top:3px; line-height:1.4;">{dept}</div>
                            </div>

                            <!-- ROW 3: DATE BOXES -->
                            <table width="100%" cellpadding="0" cellspacing="0" border="0" style="margin-top:14px;">
                                <tr>
                                    <td width="48%" valign="top" style="background:#f8fafc; border:1px solid #e2e8f0; border-radius:6px; padding:10px 12px;">
                                        <div style="font-size:9px; font-weight:700; color:#64748b; letter-spacing:0.6px; text-transform:uppercase;">START DATE</div>
                                        <div style="font-size:12px; font-weight:600; color:#1e293b; margin-top:3px;">
                                            📅 {start_d}
                                        </div>
                                    </td>
                                    <td width="4%"></td>
                                    <td width="48%" valign="top" style="background:#fef2f2; border:1px solid #fecaca; border-radius:6px; padding:10px 12px;">
                                        <div style="font-size:9px; font-weight:700; color:#dc2626; letter-spacing:0.6px; text-transform:uppercase;">END DATE (DEADLINE)</div>
                                        <div style="font-size:12px; font-weight:700; color:#b91c1c; margin-top:3px;">
                                            ⏱️ {end_d}
                                        </div>
                                    </td>
                                </tr>
                            </table>

                            <!-- ROW 4: BUTTON -->
                            <table width="100%" cellpadding="0" cellspacing="0" border="0" style="margin-top:14px;">
                                <tr>
                                    <td align="center">
                                        <a href="{doc_url}" target="_blank" style="display:block; width:100%; box-sizing:border-box; background-color:#1d4ed8; color:#ffffff; font-size:13px; font-weight:700; text-align:center; text-decoration:none; padding:12px 0; border-radius:6px; letter-spacing:0.5px;">
                                            📄 &nbsp; VIEW OFFICIAL DOCUMENT
                                        </a>
                                    </td>
                                </tr>
                            </table>
                        </td>
                    </tr>
                </table>
                """

            category_sections_html += f"""
            <!-- CATEGORY BLOCK -->
            <div style="margin-bottom:28px;">
                <table width="100%" cellpadding="0" cellspacing="0" border="0" style="margin-bottom:12px;">
                    <tr>
                        <td align="left" style="font-size:13px; font-weight:800; color:#1d4ed8; letter-spacing:0.8px; text-transform:uppercase;">
                            CATEGORY: {cat}
                        </td>
                        <td align="right" style="width:110px;">
                            <span style="display:inline-block; background-color:#eff6ff; color:#1d4ed8; font-size:11px; font-weight:700; padding:4px 10px; border-radius:12px; border:1px solid #bfdbfe;">
                                {len(bids)} new
                            </span>
                        </td>
                    </tr>
                </table>
                {cards_html}
            </div>
            """

        return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Daily Tender Alerts</title>
</head>
<body style="margin:0; padding:0; background-color:#f1f5f9; font-family:-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; -webkit-font-smoothing:antialiased; color:#1e293b;">
    <center style="width:100%; background-color:#f1f5f9; padding:20px 0;">
        <table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" style="max-width:600px; margin:0 auto; background-color:#ffffff; border-radius:14px; overflow:hidden; box-shadow:0 4px 14px rgba(0,0,0,0.06);">
            
            <!-- HERO HEADER WITH EXACT GEOMETRIC DESIGN -->
            <tr>
                <td style="background-color:#0d172a; background: #0d172a linear-gradient(125deg, #09111e 0%, #0d172a 58%, #162335 58.5%, #1e2e46 60%, #566882 60.5%, #76869d 100%); padding:24px 20px 24px 20px; text-align:center;">
                    
                    <!-- TOP BRANDING ROW (3 COLUMNS) -->
                    <table width="100%" cellpadding="0" cellspacing="0" border="0" style="margin-bottom:12px;">
                        <tr>
                            <!-- LEFT: BUSINESS EXCELLENCE -->
                            <td width="36%" valign="top" align="left" style="padding-top:2px;">
                                <div style="font-size:7.5px; font-weight:800; color:#94a3b8; letter-spacing:1.8px; text-transform:uppercase; font-family:monospace, sans-serif;">
                                    BUSINESS EXCELLENCE
                                </div>
                                <div style="font-size:6.5px; font-weight:600; color:#64748b; letter-spacing:0.8px; margin-top:4px; font-family:monospace, sans-serif;">
                                    <span style="border-bottom:1px solid #64748b; padding-bottom:1px;">PEOPLE</span> &nbsp;/&nbsp; STRATEGY &nbsp;/&nbsp; RESULTS
                                </div>
                            </td>

                            <!-- CENTER: BUILDING ICON -->
                            <td width="28%" valign="top" align="center">
                                <img src="cid:gem_logo" width="38" height="38" alt="GeM Emblem" style="display:block; margin:0 auto; width:38px; height:38px;" />
                            </td>

                            <!-- RIGHT: HIGHER STANDARD -->
                            <td width="36%" valign="top" align="right" style="padding-top:2px;">
                                <div style="font-size:7.5px; font-weight:800; color:#334155; letter-spacing:1px; text-transform:uppercase; font-family:monospace, sans-serif;">
                                    HIGHER STANDARD
                                </div>
                                <div style="font-size:6.5px; font-weight:600; color:#334155; letter-spacing:0.8px; margin-top:4px; font-family:monospace, sans-serif;">
                                    STRONGER TOMORROW
                                </div>
                            </td>
                        </tr>
                    </table>

                    <!-- SUB-TITLE -->
                    <div style="font-size:10.5px; font-weight:800; color:#38bdf8; letter-spacing:1.8px; text-transform:uppercase; margin-bottom:8px;">
                        GOVERNMENT E-MARKETPLACE
                    </div>

                    <!-- MAIN TITLE (REFINED & SLIGHTLY SMALLER SIZE) -->
                    <div style="font-size:22px; font-weight:800; color:#ffffff; letter-spacing:-0.4px; margin-bottom:12px;">
                        Daily Tender Alerts
                    </div>

                    <!-- PILL BADGE -->
                    <table role="presentation" cellpadding="0" cellspacing="0" border="0" align="center" style="margin:0 auto 10px auto;">
                        <tr>
                            <td style="background-color:#2563eb; padding:7px 22px; border-radius:22px; box-shadow:0 3px 10px rgba(37,99,235,0.35);">
                                <span style="font-size:13px; font-weight:800; color:#ffffff; letter-spacing:0.3px;">
                                    {total_count} New Tenders Found Today
                                </span>
                            </td>
                        </tr>
                    </table>

                    <!-- ALERT RUN TIMESTAMP -->
                    <div style="font-size:11px; color:#94a3b8; font-weight:500;">
                        Alert Run: {current_time_str}
                    </div>
                </td>
            </tr>

            <!-- INTRO TEXT -->
            <tr>
                <td style="padding:28px 24px 16px 24px; background-color:#ffffff;">
                    <div style="font-size:15px; font-weight:700; color:#0f172a; margin-bottom:6px;">
                        Hello,
                    </div>
                    <div style="font-size:13px; color:#475569; line-height:1.6;">
                        Here are the latest tender opportunities matching your profile from the Government e-Marketplace (GeM). Stay updated and never miss an opportunity to bid.
                    </div>
                </td>
            </tr>

            <!-- TENDER CARDS CONTENT -->
            <tr>
                <td style="padding:10px 24px 20px 24px; background-color:#ffffff;">
                    {category_sections_html}
                </td>
            </tr>

            <!-- FOOTER -->
            <tr>
                <td align="center" style="background-color:#0b1322; padding:30px 24px; text-align:center; color:#94a3b8;">
                    
                    <!-- SHIELD ICON (CID) -->
                    <table role="presentation" cellpadding="0" cellspacing="0" border="0" align="center" style="margin:0 auto 10px auto;">
                        <tr>
                            <td align="center">
                                <img src="cid:shield_logo" width="30" height="30" alt="Verified Shield" style="display:block; margin:0 auto; width:30px; height:30px;" />
                            </td>
                        </tr>
                    </table>

                    <!-- FOOTER TITLE -->
                    <div style="font-size:11px; font-weight:700; color:#38bdf8; letter-spacing:1.8px; text-transform:uppercase; margin-bottom:10px;">
                        AUTOMATED ALERT SYSTEM
                    </div>

                    <!-- FOOTER DESCRIPTION -->
                    <div style="font-size:12px; color:#94a3b8; line-height:1.5; max-width:440px; margin:0 auto 18px auto;">
                        This is an automated notification from the GeM Tender Alert System. You are receiving this because you subscribed to daily alerts for matching government bids.
                    </div>

                    <div style="border-top:1px solid #1e293b; padding-top:16px; font-size:11px; color:#64748b; line-height:1.5;">
                        © 2026 Government e-Marketplace. All rights reserved.<br>
                        Note: This email is for informational purposes only. Please verify bid details on the official GeM portal.
                    </div>
                </td>
            </tr>

        </table>
    </center>
</body>
</html>"""
