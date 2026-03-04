# agents/tools/comms_tools.py
# CrewAI tools wrapping P4's comms (notification) endpoints.
# Notifications are simulated — writes to DB, no real Teams/email.
#
# P3→P4 CONTRACT CHECK: POST /api/comms/notify does not exist yet.
# P4 must add it. See INTEGRATION_NOTES.md.

import httpx
import os
import logging

logger = logging.getLogger(__name__)

BASE_URL = os.getenv("BACKEND_API_URL", "http://localhost:3001")


def send_notification(
    recipient_role: str,
    message: str,
    run_id: str,
    notification_type: str = "info",
) -> dict:
    """Send a notification (simulated — writes to DB via P4 API).
    Returns notification record or offline fallback."""
    try:
        resp = httpx.post(
            f"{BASE_URL}/api/comms/notify",
            json={
                "recipient_role": recipient_role,
                "message": message,
                "run_id": run_id,
                "type": notification_type,
            },
            timeout=15,
        )
        resp.raise_for_status()
        return resp.json()
    except (httpx.ConnectError, httpx.TimeoutException, httpx.HTTPStatusError) as e:
        logger.warning(f"Notification send failed: {e} — logging locally")
        return {
            "status": "offline",
            "recipient_role": recipient_role,
            "message": message,
        }
