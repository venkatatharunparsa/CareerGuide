import logging
import smtplib
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Dict, List

logger = logging.getLogger(__name__)


class EmailService:
  def __init__(self):
    from app.config import get_settings

    s = get_settings()
    self.sender = s.gmail_sender
    self.password = s.gmail_app_password
    self.recipient = s.notification_email
    self.enabled = bool(self.sender and self.password and self.recipient)

  def send_job_digest(
    self,
    jobs: List[Dict],
    username: str,
    dashboard_url: str = "http://localhost:3000",
  ) -> bool:
    if not self.enabled or not jobs:
      return False
    try:
      msg = MIMEMultipart("alternative")
      today = datetime.now().strftime("%B %d, %Y · %I:%M %p")
      count = len(jobs)
      msg["Subject"] = f"Job Agent: {count} new matches found — {datetime.now().strftime('%b %d')}"
      msg["From"] = f"Job Agent <{self.sender}>"
      msg["To"] = self.recipient

      lines = [
        f"Job Agent found {count} matches for you.",
        f"User: {username}",
        f"Date: {today}",
        "",
        "TOP MATCHES:",
        "",
      ]
      for i, job in enumerate(jobs[:10], 1):
        lines += [
          f"{i}. {job.get('title')} @ {job.get('company')}",
          f"   Match: {job.get('match_score', 0)}%",
          f"   Location: {job.get('location', 'Remote')}",
          f"   Apply: {job.get('url', '')}",
          "",
        ]
      lines += [f"View full results: {dashboard_url}", "", "-- Job Agent (automated)"]

      msg.attach(MIMEText("\n".join(lines), "plain"))
      msg.attach(MIMEText(self._html(jobs, username, today, dashboard_url, count), "html"))

      with smtplib.SMTP_SSL("smtp.gmail.com", 465) as srv:
        srv.login(self.sender, self.password)
        srv.sendmail(self.sender, self.recipient, msg.as_string())

      logger.info("Digest email sent: %d jobs to %s", count, self.recipient)
      return True
    except Exception as e:
      logger.error("Email failed: %s", e)
      return False

  def _html(self, jobs, username, date, dashboard_url, count):
    rows = ""
    for job in jobs[:10]:
      score = job.get("match_score", 0) or 0
      color = "#22c55e" if score >= 80 else "#eab308" if score >= 60 else "#6b7280"
      matched = ", ".join((job.get("matched_skills") or [])[:4])
      rows += f"""
            <tr>
              <td style="padding:14px 12px;border-bottom:1px solid #1e293b;">
                <div style="font-weight:600;color:#f1f5f9;font-size:14px;">
                  {job.get('title','')}
                </div>
                <div style="color:#94a3b8;font-size:12px;margin-top:3px;">
                  {job.get('company','')} &nbsp;·&nbsp; {job.get('location','Remote')}
                </div>
                {f'<div style="color:#475569;font-size:11px;margin-top:3px;">Matched: {matched}</div>' if matched else ''}
              </td>
              <td style="padding:14px 12px;border-bottom:1px solid #1e293b;
                         color:#94a3b8;font-size:12px;white-space:nowrap;">
                {job.get('source','')}
              </td>
              <td style="padding:14px 12px;border-bottom:1px solid #1e293b;
                         text-align:center;white-space:nowrap;">
                <span style="background:{color}22;color:{color};padding:3px 10px;
                             border-radius:99px;font-size:12px;font-weight:700;">
                  {score}%
                </span>
              </td>
              <td style="padding:14px 12px;border-bottom:1px solid #1e293b;
                         text-align:center;">
                <a href="{job.get('url','#')}"
                   style="background:#0ea5e9;color:#fff;padding:6px 14px;
                          border-radius:6px;text-decoration:none;
                          font-size:12px;font-weight:600;">
                  Apply
                </a>
              </td>
            </tr>"""

    return f"""<!DOCTYPE html>
<html>
<body style="margin:0;padding:20px;background:#0f172a;font-family:Arial,sans-serif;">
<div style="max-width:680px;margin:0 auto;">
  <div style="background:#1e293b;border-radius:12px;overflow:hidden;
              border:1px solid #334155;">
    <div style="padding:24px;background:#0f172a;border-bottom:1px solid #1e293b;">
      <div style="display:flex;align-items:center;gap:12px;">
        <div style="background:#0ea5e9;width:36px;height:36px;border-radius:8px;
                    display:flex;align-items:center;justify-content:center;
                    font-size:18px;">🤖</div>
        <div>
          <div style="color:#f1f5f9;font-size:18px;font-weight:700;">Job Agent</div>
          <div style="color:#64748b;font-size:12px;">{count} new matches · {date}</div>
          <div style="color:#334155;font-size:11px;margin-top:4px;">User: {username}</div>
        </div>
      </div>
    </div>
    <div style="padding:0;">
      <table style="width:100%;border-collapse:collapse;">
        <thead>
          <tr style="background:#0f172a;">
            <th style="padding:10px 12px;text-align:left;color:#475569;
                       font-size:11px;text-transform:uppercase;letter-spacing:0.5px;">
              Position
            </th>
            <th style="padding:10px 12px;text-align:left;color:#475569;
                       font-size:11px;text-transform:uppercase;">Source</th>
            <th style="padding:10px 12px;text-align:center;color:#475569;
                       font-size:11px;text-transform:uppercase;">Match</th>
            <th style="padding:10px 12px;text-align:center;color:#475569;
                       font-size:11px;text-transform:uppercase;">Apply</th>
          </tr>
        </thead>
        <tbody>{rows}</tbody>
      </table>
    </div>
    <div style="padding:16px 20px;background:#0f172a;border-top:1px solid #1e293b;text-align:center;">
      <a href="{dashboard_url}"
         style="background:#1e293b;color:#38bdf8;padding:10px 24px;border-radius:8px;text-decoration:none;
                font-size:13px;font-weight:600;border:1px solid #334155;">
        View Full Dashboard →
      </a>
      <div style="color:#334155;font-size:11px;margin-top:12px;">
        Job Agent · Automated job search
      </div>
    </div>
  </div>
</div>
</body>
</html>"""


_instance = None


def get_email_service():
  global _instance
  if _instance is None:
    _instance = EmailService()
  return _instance

