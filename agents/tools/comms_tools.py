# agents/tools/comms_tools.py
# Tools wrapping the notification/comms system (simulated Teams).
#
# When running in-process with the backend, writes directly to NOTIFICATIONS.
# When running standalone, falls back to HTTP calls.

import os
import uuid
import logging
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

BASE_URL = os.getenv("BACKEND_API_URL", "http://localhost:3001")


def _get_notifications_store():
    """Try to import the in-memory NOTIFICATIONS list from the backend."""
    try:
        from api.main import NOTIFICATIONS
        return NOTIFICATIONS
    except ImportError:
        return None


def send_notification(
    recipient_role: str,
    message: str,
    run_id: str,
    notification_type: str = "info",
) -> dict:
    """Send a notification (simulated — writes to DB).
    Returns notification record or offline fallback."""

    # ── Direct in-memory access (avoids HTTP self-deadlock) ──
    notifications = _get_notifications_store()
    if notifications is not None:
        notification_id = str(uuid.uuid4())
        record = {
            "notification_id": notification_id,
            "recipient_role": recipient_role,
            "notification_type": notification_type,
            "title": f"[{notification_type.upper()}] {message[:60]}",
            "body": message,
            "metadata": {"run_id": run_id},
            "is_read": False,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        notifications.append(record)
        return {"notification_id": notification_id, "status": "sent"}

    # ── Fallback: HTTP call ──
    try:
        import httpx
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
    except Exception as e:
        logger.warning(f"Notification send failed: {e} — logging locally")
        return {
            "status": "offline",
            "recipient_role": recipient_role,
            "message": message,
        }
