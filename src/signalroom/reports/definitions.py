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
        },
        schedule="0 7 * * *",  # 7am daily
        params={
            "advertiser_id": 1,  # CCW
        },
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
#         },
#         schedule="0 7 * * *",
#         params={
#             "advertiser_id": 2,  # EXP
#         },
#     )
# )
