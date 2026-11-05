"""
Email Notification Service for GeM Tender Alerts
Sends formatted HTML emails via Gmail SMTP with App Password.
"""

import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Dict, List


class EmailNotifier:
    SMTP_SERVER = "smtp.gmail.com"
    SMTP_PORT = 465  # SSL

    def __init__(self, sender_email: str, app_password: str, recipient_email: str):
        self.sender_email = sender_email
        # Remove any spaces user might paste from Google App Password
        self.app_password = app_password.replace(" ", "").strip()
        self.recipient_email = recipient_email

    def send_tender_alert(self, new_tenders_by_category: Dict[str, List[dict]]) -> bool:
        """Format and send an alert email for newly discovered tenders."""
        total_new = sum(len(bids) for bids in new_tenders_by_category.values())
        if total_new == 0:
            print("[Info] No new tenders to email.")
            return False

        if not self.app_password or self.app_password == "YOUR_16_CHAR_APP_PASSWORD":
            print("[Warning] App password is not set in config.json. Cannot send email.")
            return False

        subject = f"🔔 GeM Alert: {total_new} New Tender{'s' if total_new > 1 else ''} Found!"
        html_body = self._build_html_template(new_tenders_by_category, total_new)

        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = f"GeM Tender Alert <{self.sender_email}>"
        msg["To"] = self.recipient_email

        # Plaintext fallback
        plain_text = f"Found {total_new} new tenders on GeM.\nPlease open this email with an HTML viewer to view full tender cards and document links."
        msg.attach(MIMEText(plain_text, "plain"))
        msg.attach(MIMEText(html_body, "html"))

        try:
            with smtplib.SMTP_SSL(self.SMTP_SERVER, self.SMTP_PORT, timeout=20) as server:
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
        category_sections = ""
        for cat, bids in new_tenders.items():
            if not bids:
                continue

            cards_html = ""
            for b in bids:
                cards_html += f"""
                <div style="background: #ffffff; border-left: 4px solid #1a73e8; border-radius: 6px; padding: 14px 18px; margin-bottom: 12px; box-shadow: 0 1px 3px rgba(0,0,0,0.08);">
                    <div style="font-size: 15px; font-weight: bold; color: #1a73e8; margin-bottom: 6px;">
                        Bid No: {b.get('bid_number')}
                    </div>
                    <table style="width: 100%; border-collapse: collapse; font-size: 13px; color: #333333;">
                        <tr>
                            <td style="padding: 4px 0; width: 120px; font-weight: 600; color: #666;">Quantity:</td>
                            <td style="padding: 4px 0;"><b>{b.get('quantity')}</b></td>
                        </tr>
                        <tr>
                            <td style="padding: 4px 0; font-weight: 600; color: #666;">Department:</td>
                            <td style="padding: 4px 0;">{b.get('department') or 'N/A'}</td>
                        </tr>
                        <tr>
                            <td style="padding: 4px 0; font-weight: 600; color: #666;">End Date:</td>
                            <td style="padding: 4px 0; color: #d93025; font-weight: bold;">{b.get('end_date')}</td>
                        </tr>
                    </table>
                    <div style="margin-top: 10px;">
                        <a href="{b.get('document_url')}" target="_blank" style="display: inline-block; background-color: #1a73e8; color: #ffffff; padding: 6px 14px; text-decoration: none; border-radius: 4px; font-size: 12px; font-weight: bold;">
                            📄 Download Bid Document
                        </a>
                    </div>
                </div>
                """

            category_sections += f"""
            <div style="margin-bottom: 24px;">
                <h3 style="color: #202124; margin: 0 0 10px 0; font-size: 16px; border-bottom: 2px solid #e0e0e0; padding-bottom: 6px;">
                    📁 {cat} <span style="background: #e8f0fe; color: #1a73e8; font-size: 12px; padding: 2px 8px; border-radius: 12px; margin-left: 8px;">{len(bids)} new</span>
                </h3>
                {cards_html}
            </div>
            """

        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>GeM New Tenders Alert</title>
        </head>
        <body style="font-family: Arial, -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background-color: #f6f8fa; margin: 0; padding: 20px;">
            <div style="max-width: 650px; margin: 0 auto; background: #fafafa; border: 1px solid #e1e4e8; border-radius: 8px; overflow: hidden;">
                <div style="background: linear-gradient(135deg, #1a73e8, #0d47a1); padding: 20px; color: #ffffff;">
                    <h2 style="margin: 0; font-size: 20px;">🚨 Government e Marketplace (GeM) Alert</h2>
                    <p style="margin: 6px 0 0 0; font-size: 14px; opacity: 0.9;">
                        Found <b>{total_count}</b> new active tender(s) matching your watched categories.
                    </p>
                </div>
                <div style="padding: 20px;">
                    {category_sections}
                </div>
                <div style="background: #f1f3f4; padding: 12px 20px; text-align: center; font-size: 12px; color: #5f6368; border-top: 1px solid #e0e0e0;">
                    Automated alert from your GeM Tender Finder • Run at 10:00 AM Daily
                </div>
            </div>
        </body>
        </html>
        """

