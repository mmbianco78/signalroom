"""Report definitions.

This module defines all available reports. Import it to register reports.
"""

from signalroom.reports.registry import Report, register_report

# Daily CCW Report
daily_ccw = register_report(
    Report(
        name="daily_ccw",
        description="Daily CCW performance summary with affiliate breakdown",
        query="daily_ccw.sql",
        templates={
            "slack": "daily_ccw.slack.j2",
            "email": "daily_ccw.email.mjml",
            "sms": "daily_ccw.sms.j2",
        },
        schedule="0 7 * * *",  # 7am daily
        params={
            "advertiser_id": 1,  # CCW
        },
    )
)

# Alert Report (for pipeline failures, warnings, etc.)
alert = register_report(
    Report(
        name="alert",
        description="Generic alert notification for errors and warnings",
        query="",  # No query - data passed directly
        templates={
            "slack": "alert.slack.j2",
            "email": "alert.email.mjml",
            "sms": "alert.sms.j2",
        },
        params={
            "level": "error",  # error, warning, info
            "title": "Alert",
            "message": "",
            "details": {},
            "source": "signalroom",
        },
    )
)

# Test Sync Report (for validating the deployment)
test_sync = register_report(
    Report(
        name="test_sync",
        description="Test report showing basic sync totals - no sensitive data",
        query="test_sync.sql",
        templates={
            "slack": "test_sync.slack.j2",
        },
        schedule="0 7 * * *",  # 7am daily (will replace daily_ccw schedule)
        params={},
    )
)

# Daily EXP Report (placeholder for future)
# daily_exp = register_report(
#     Report(
#         name="daily_exp",
#         description="Daily Expungement performance summary",
#         query="daily_ccw.sql",  # Same query, different advertiser_id
#         templates={
#             "slack": "daily_ccw.slack.j2",
#             "email": "daily_ccw.email.mjml",
#             "sms": "daily_ccw.sms.j2",
#         },
#         schedule="0 7 * * *",
#         params={
#             "advertiser_id": 2,  # EXP
#         },
#     )
# )
