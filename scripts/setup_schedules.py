#!/usr/bin/env python3
"""Set up Temporal schedules for SignalRoom.

Schedules (Eastern Time):
- Hourly 7am-11pm: Sync Everflow + Redtrack (current day data)
- Daily 6am: Sync S3 exports
- Daily 7am: Send daily CCW report

Usage:
    python scripts/setup_schedules.py [--delete]

Options:
    --delete    Delete all schedules instead of creating them
"""

import asyncio
import sys
from datetime import timedelta
from typing import Any

# Load .env before importing signalroom (settings won't auto-load it)
from dotenv import load_dotenv

load_dotenv()

from temporalio.client import (
    Schedule,
    ScheduleActionStartWorkflow,
    ScheduleCalendarSpec,
    ScheduleOverlapPolicy,
    SchedulePolicy,
    ScheduleRange,
    ScheduleSpec,
    ScheduleState,
)

from signalroom.common import get_logger
from signalroom.temporal.activities import ReportInput
from signalroom.temporal.config import get_temporal_client
from signalroom.temporal.workflows import (
    RunReportWorkflow,
    ScheduledSyncInput,
    ScheduledSyncWorkflow,
    SyncSourceInput,
    SyncSourceWorkflow,
)

log = get_logger(__name__)

# Task queue must match the worker
TASK_QUEUE = "api-tasks"


async def create_hourly_sync_schedule(client: Any) -> str:
    """Create hourly sync schedule for Everflow + Redtrack.

    Runs hourly from 7am to 11pm Eastern Time (12:00-04:00 UTC next day).
    Syncs current day data to catch realtime updates.
    """
    schedule_id = "hourly-sync-everflow-redtrack"

    # Delete if exists (for idempotency)
    try:
        handle = client.get_schedule_handle(schedule_id)
        await handle.delete()
        print(f"Deleted existing schedule: {schedule_id}")
    except Exception:
        pass

    # Hourly from 7am-11pm ET = 12:00-04:00 UTC (winter) / 11:00-03:00 UTC (summer)
    # Using 12:00-04:00 UTC to be safe (covers EST)
    # Run at :15 past each hour to avoid peak load
    schedule = Schedule(
        action=ScheduleActionStartWorkflow(
            ScheduledSyncWorkflow.run,
            ScheduledSyncInput(
                sources=["everflow", "redtrack"],
                notify_on_failure=True,
            ),
            id="scheduled-sync-hourly",
            task_queue=TASK_QUEUE,
        ),
        spec=ScheduleSpec(
            calendars=[
                ScheduleCalendarSpec(
                    hour=[ScheduleRange(start=12, end=23)],  # 12:00-23:00 UTC = 7am-6pm EST
                    minute=[ScheduleRange(start=15)],  # :15 past each hour
                ),
                ScheduleCalendarSpec(
                    hour=[ScheduleRange(start=0, end=4)],  # 00:00-04:00 UTC = 7pm-11pm EST
                    minute=[ScheduleRange(start=15)],
                ),
            ],
        ),
        policy=SchedulePolicy(overlap=ScheduleOverlapPolicy.SKIP),
        state=ScheduleState(
            note="Hourly Everflow + Redtrack sync (7am-11pm ET)",
        ),
    )

    await client.create_schedule(schedule_id, schedule)
    print(f"✓ Created schedule: {schedule_id}")
    return schedule_id


async def create_daily_s3_schedule(client: Any) -> str:
    """Create daily S3 sync schedule.

    Runs at 6am Eastern Time (11:00 UTC winter / 10:00 UTC summer).
    Syncs yesterday's export files.
    """
    schedule_id = "daily-sync-s3"

    try:
        handle = client.get_schedule_handle(schedule_id)
        await handle.delete()
        print(f"Deleted existing schedule: {schedule_id}")
    except Exception:
        pass

    schedule = Schedule(
        action=ScheduleActionStartWorkflow(
            SyncSourceWorkflow.run,
            SyncSourceInput(
                source_name="s3_exports",
                notify_on_failure=True,
                notify_on_success=False,
            ),
            id="scheduled-sync-s3-daily",
            task_queue=TASK_QUEUE,
        ),
        spec=ScheduleSpec(
            calendars=[
                ScheduleCalendarSpec(
                    hour=[ScheduleRange(start=11)],  # 11:00 UTC = 6am EST
                    minute=[ScheduleRange(start=0)],
                ),
            ],
        ),
        policy=SchedulePolicy(overlap=ScheduleOverlapPolicy.SKIP),
        state=ScheduleState(
            note="Daily S3 exports sync (6am ET)",
        ),
    )

    await client.create_schedule(schedule_id, schedule)
    print(f"✓ Created schedule: {schedule_id}")
    return schedule_id


async def create_daily_report_schedule(client: Any, test_mode: bool = True) -> str:
    """Create daily report schedule.

    Runs at 7am Eastern Time (12:00 UTC winter / 11:00 UTC summer).

    Args:
        test_mode: If True, uses test_sync report (safe). If False, uses daily_ccw.
    """
    # Delete old schedule if exists
    for old_id in ["daily-report-ccw", "daily-report-test"]:
        try:
            handle = client.get_schedule_handle(old_id)
            await handle.delete()
            print(f"Deleted existing schedule: {old_id}")
        except Exception:
            pass

    if test_mode:
        schedule_id = "daily-report-test"
        report_name = "test_sync"
        note = "TEST: Daily sync status report (7am ET) - safe for public channel"
    else:
        schedule_id = "daily-report-ccw"
        report_name = "daily_ccw"
        note = "Daily CCW performance report (7am ET)"

    schedule = Schedule(
        action=ScheduleActionStartWorkflow(
            RunReportWorkflow.run,
            ReportInput(
                report_name=report_name,
                channel="slack",
                send=True,
            ),
            id=f"scheduled-report-{report_name}-daily",
            task_queue=TASK_QUEUE,
        ),
        spec=ScheduleSpec(
            calendars=[
                ScheduleCalendarSpec(
                    hour=[ScheduleRange(start=12)],  # 12:00 UTC = 7am EST
                    minute=[ScheduleRange(start=0)],
                ),
            ],
        ),
        policy=SchedulePolicy(overlap=ScheduleOverlapPolicy.SKIP),
        state=ScheduleState(
            note=note,
        ),
    )

    await client.create_schedule(schedule_id, schedule)
    print(f"✓ Created schedule: {schedule_id} (report: {report_name})")
    return schedule_id


async def list_schedules(client: Any) -> list[str]:
    """List all schedules."""
    schedules = []
    schedule_iter = await client.list_schedules()
    async for s in schedule_iter:
        schedules.append(s.id)
        note = s.info.note if s.info and hasattr(s.info, "note") else "No description"
        print(f"  - {s.id}: {note}")
    return schedules


async def delete_all_schedules(client: Any) -> None:
    """Delete all SignalRoom schedules."""
    print("Deleting all schedules...")

    schedule_ids = [
        "hourly-sync-everflow-redtrack",
        "daily-sync-s3",
        "daily-report-ccw",
    ]

    for schedule_id in schedule_ids:
        try:
            handle = client.get_schedule_handle(schedule_id)
            await handle.delete()
            print(f"✓ Deleted: {schedule_id}")
        except Exception as e:
            print(f"  Skipped {schedule_id}: {e}")


async def main(delete: bool = False, production: bool = False) -> None:
    """Main entry point.

    Args:
        delete: If True, delete all schedules instead of creating
        production: If True, use full reports. If False (default), use safe test reports.
    """
    print("Connecting to Temporal Cloud...")
    client = await get_temporal_client()
    print(f"✓ Connected to namespace: {client.namespace}")
    print()

    if delete:
        await delete_all_schedules(client)
        return

    mode = "PRODUCTION" if production else "TEST (safe for public channels)"
    print(f"Setting up schedules... Mode: {mode}")
    print()

    # Create hourly sync schedule
    await create_hourly_sync_schedule(client)

    # Create daily S3 schedule
    await create_daily_s3_schedule(client)

    # Create daily report schedule (test_sync by default, daily_ccw with --production)
    await create_daily_report_schedule(client, test_mode=not production)

    print()
    print("=" * 50)
    print("Current schedules:")
    await list_schedules(client)
    print("=" * 50)
    if not production:
        print("\nNote: Using TEST mode. Run with --production for full reports.")


if __name__ == "__main__":
    delete_mode = "--delete" in sys.argv
    production_mode = "--production" in sys.argv
    asyncio.run(main(delete=delete_mode, production=production_mode))
