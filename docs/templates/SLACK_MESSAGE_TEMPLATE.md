# Slack Message Templates

## Implementation Sign-off Request

Use when sharing an implementation summary doc with the team for QA and sign-off.

---

### Template

```
📊 **[Source Name] Integration Ready for QA**

SignalRoom now pulls [data type] from [Source] into Supabase. Need sign-off before merging.

**What's loaded:**
• [Date range] → [X] rows, [X] [dimensions]
• [Key stat 1]: [value]
• [Key stat 2]: [value]

**Scheduling:**
• [Frequency] sync [time range]
• [Special behavior if any]

**Action needed:**
Compare the QA Checklist values against [Source] UI and confirm they match.

📎 See attached: `[SOURCE]_IMPLEMENTATION.md`
```

---

### Example (Everflow)

```
📊 **Everflow Integration Ready for QA**

SignalRoom now pulls affiliate data from Everflow into Supabase. Need sign-off before merging.

**What's loaded:**
• Dec 1-18, 2025 → 444 rows, 9 advertisers
• CCW: 4,592 conversions, $124K payout

**Scheduling (to replace automated-reporting):**
• Hourly sync 7am-11pm ET (17 runs/day)
• Intraday data, same as current system
• 7am: previous day final + current day start

**Action needed:**
Compare the QA Checklist values against Everflow UI and confirm they match.

📎 See attached: `EVERFLOW_IMPLEMENTATION.md`
```

---

## Phase Complete Notification

Use when a phase is approved and merged to main.

---

### Template

```
✅ **Phase [X]: [Source Name] - Merged to Main**

[Brief description of what was completed]

**Stats:**
• [X] rows loaded
• [Key metric]: [value]

**Next up:** Phase [X+1] - [Next source/feature]
```

---

### Example

```
✅ **Phase 1: Everflow - Merged to Main**

Affiliate performance data now syncing to Supabase.

**Stats:**
• 444 rows loaded (Dec 1-18)
• 4,592 CCW conversions tracked

**Next up:** Phase 2 - Redtrack (ad spend data)
```

---

## Daily/Weekly Status Update

Use for regular progress updates.

---

### Template

```
📈 **SignalRoom Status Update**

**Completed:**
• [Task 1]
• [Task 2]

**In Progress:**
• [Task 3] - [brief status]

**Blocked/Needs Input:**
• [Item if any]

**Next Steps:**
• [Upcoming task]
```
