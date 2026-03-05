#!/usr/bin/env python3
# agents/run.py
# CLI entry point for the SupplyGuard AI pipeline.
#
# Usage:
#   python agents/run.py --event_id <uuid>      # fetch event from backend
#   python agents/run.py --fixture event_red     # load from test fixture (offline)
#   python agents/run.py --fixture event_green
#   python agents/run.py --fixture event_yellow

import argparse
import json
import logging
import os
import sys
from pathlib import Path

# Ensure project root is on sys.path for imports
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from dotenv import load_dotenv
load_dotenv(PROJECT_ROOT / ".env")

from agents.orchestrator import run_pipeline

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

FIXTURES_DIR = PROJECT_ROOT / "tests" / "fixtures"
OUTPUT_DIR = PROJECT_ROOT / "docs" / "example_decision_logs"


def load_event_from_fixture(name: str) -> dict:
    """Load a test fixture JSON file."""
    fixture_path = FIXTURES_DIR / f"{name}.json"
    if not fixture_path.exists():
        raise FileNotFoundError(
            f"Fixture not found: {fixture_path}\n"
            f"Valid fixtures: {', '.join(f.stem for f in FIXTURES_DIR.glob('*.json'))}"
        )
    return json.loads(fixture_path.read_text())


def load_event_from_backend(event_id: str) -> dict:
    """Fetch an event from P4's backend API."""
    import httpx

    backend_url = os.getenv("BACKEND_API_URL", "http://localhost:3001")
    try:
        resp = httpx.get(f"{backend_url}/api/events/{event_id}", timeout=15)
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        logger.error(f"Failed to fetch event {event_id} from backend: {e}")
        raise


def save_output(state_dict: dict, label: str):
    """Save pipeline output to docs/example_decision_logs/."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    output_path = OUTPUT_DIR / f"run_{label}.json"
    output_path.write_text(json.dumps(state_dict, indent=2, default=str))
    logger.info(f"Output saved to {output_path}")


def main():
    parser = argparse.ArgumentParser(
        description="SupplyGuard AI — Run the 5-agent pipeline"
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        "--event_id",
        type=str,
        help="Event UUID to fetch from backend API",
    )
    group.add_argument(
        "--fixture",
        type=str,
        choices=["event_red", "event_green", "event_yellow"],
        help="Load a test fixture (offline mode)",
    )
    args = parser.parse_args()

    # Load event
    if args.fixture:
        logger.info(f"Loading fixture: {args.fixture}")
        event = load_event_from_fixture(args.fixture)
        label = args.fixture.replace("event_", "")
    else:
        logger.info(f"Fetching event: {args.event_id}")
        event = load_event_from_backend(args.event_id)
        label = args.event_id[:8]

    # Run pipeline
    logger.info("=" * 60)
    logger.info("Starting SupplyGuard AI Pipeline")
    logger.info("=" * 60)

    state = run_pipeline(event)

    # Print results
    state_dict = state.model_dump()
    print("\n" + "=" * 60)
    print("PIPELINE RESULT")
    print("=" * 60)
    print(json.dumps(state_dict, indent=2, default=str))

    # Save output
    save_output(state_dict, label)

    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"  Run ID:           {state.run_id}")
    print(f"  Event ID:         {state.event_id}")
    print(f"  Composite Score:  {state.decision.composite_score if state.decision else 'N/A'}")
    print(f"  Action:           {state.decision.action if state.decision else 'N/A'}")
    print(f"  HITL Required:    {state.decision.hitl_required if state.decision else 'N/A'}")
    print(f"  Paused for HITL:  {state.paused_for_hitl}")
    print(f"  PO ID:            {state.executor.po_id if state.executor else 'N/A (paused)'}")
    print(f"  Audit Entries:    {len(state.audit_entries)}")
    print(f"  Error:            {state.error or 'None'}")
    print("=" * 60)

    return 0 if state.error is None else 1


if __name__ == "__main__":
    sys.exit(main())
