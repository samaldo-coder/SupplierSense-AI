"""
SupplyGuard AI — Supabase client singleton.

Returns None if SUPABASE_URL / SUPABASE_SERVICE_ROLE_KEY are not set
in the environment, so the app falls back to in-memory operation.
"""

import os
import logging

logger = logging.getLogger(__name__)

_client = None


def get_supabase():
    """Return the Supabase client, or None if not configured."""
    global _client
    if _client is not None:
        return _client

    url = os.getenv("SUPABASE_URL", "").strip()
    # Prefer service-role key (bypasses RLS); fall back to anon key
    key = (
        os.getenv("SUPABASE_SERVICE_ROLE_KEY", "").strip()
        or os.getenv("SUPABASE_ANON_KEY", "").strip()
    )

    if not url or not key:
        logger.warning(
            "[Supabase] SUPABASE_URL or SUPABASE_SERVICE_ROLE_KEY not set — "
            "running with in-memory storage only."
        )
        return None

    try:
        from supabase import create_client, Client  # type: ignore

        _client = create_client(url, key)
        logger.info(f"[Supabase] Connected to {url[:40]}...")
        return _client
    except ImportError:
        logger.error(
            "[Supabase] 'supabase' package not installed. "
            "Run: pip install supabase"
        )
        return None
    except Exception as e:
        logger.error(f"[Supabase] Connection failed: {e}")
        return None


def reset_client():
    """Force re-initialisation (useful in tests)."""
    global _client
    _client = None
