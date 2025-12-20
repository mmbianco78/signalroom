# API Reference

Quick-access reference for all external API integrations. Live documentation URLs are prominently marked for fast lookup.

---

## Quick Links (Live Documentation)

| Service | Live Docs URL | Status |
|---------|---------------|--------|
| **Everflow** | https://developers.everflow.io/ | Active |
| **Redtrack** | https://api.redtrack.io/docs/index.html | Active |
| **PostHog** | https://posthog.com/docs/api | Planned |
| **Mautic** | https://devdocs.mautic.org/ | Planned |
| **Google Sheets** | https://developers.google.com/sheets/api | Planned |

---

## Everflow

### LIVE DOCS: https://developers.everflow.io/

**API Base URL**: `https://api.eflow.team`

**Authentication**: Header-based API key
```
X-Eflow-API-Key: {api_key}
```

**Our API Key Env Var**: `EVERFLOW_API_KEY`

---

### Endpoints Used

| Endpoint | Method | Purpose | SignalRoom Resource |
|----------|--------|---------|---------------------|
| `/v1/networks/reporting/entity/table` | POST | Daily stats by affiliate/advertiser | `everflow.daily_stats` |

### Entity Table Request

**Endpoint**: `POST https://api.eflow.team/v1/networks/reporting/entity/table`

**Request**:
```json
{
  "from": "2025-12-01",
  "to": "2025-12-18",
  "timezone_id": 80,
  "currency_id": "USD",
  "columns": [
    {"column": "affiliate"},
    {"column": "advertiser"},
    {"column": "date"}
  ],
  "query": {
    "filters": [{"advertiser_id": 1}],
    "page": 1,
    "limit": 10000
  }
}
```

**Response**:
```json
{
  "table": [
    {
      "columns": [
        {"column_type": "affiliate", "id": "1", "label": "G2 - Meta"},
        {"column_type": "advertiser", "id": "1", "label": "CCW"},
        {"column_type": "date", "id": "1733097600"}
      ],
      "reporting": {
        "total_click": 150,
        "cv": 25,
        "revenue": 2500.00,
        "payout": 1875.00,
        "profit": 625.00
      }
    }
  ]
}
```

**Notes**:
- `timezone_id`: 80 = America/New_York
- `date.id`: Unix epoch timestamp (seconds)
- `advertiser_id`: 1 = CCW, 2 = EXP
- API filter on advertiser_id unreliable; we apply client-side filtering

---

### Endpoints Available (Not Yet Used)

| Endpoint | Method | Purpose | Priority |
|----------|--------|---------|----------|
| `/v1/networks/offers` | GET | List all offers | Medium |
| `/v1/networks/affiliates` | GET | List all affiliates | Medium |
| `/v1/networks/advertisers` | GET | List all advertisers | Low |
| `/reporting/network/aggregated-data` | POST | Aggregated report (simpler) | Low |

### Aggregated Report (Alternative)

**Endpoint**: `POST https://api.eflow.team/reporting/network/aggregated-data`

**Request**:
```json
{
  "date_from": "2025-12-01",
  "date_to": "2025-12-18",
  "timezone": "UTC",
  "grouping": ["date"],
  "columns": ["clicks", "conversions", "revenue", "payout", "profit"],
  "filters": [],
  "limit": 10000,
  "page": 1
}
```

**Notes**: Simpler endpoint but less granular than entity table. No affiliate breakdown.

---

### Key Constants

| Constant | Value | Description |
|----------|-------|-------------|
| Timezone ID (America/New_York) | `80` | Used in all requests |
| Advertiser ID (CCW) | `1` | Concealed Carry brand |
| Advertiser ID (EXP) | `2` | Expungement brand |

---

## Redtrack

### LIVE DOCS: https://api.redtrack.io/docs/index.html

**Alternative Docs**: https://help.redtrack.io/knowledgebase/kb/automation/

**API Base URL**: `https://api.redtrack.io`

**Authentication**: Header-based OR query param
```
# Header (preferred for POST)
X-API-KEY: {api_key}

# Query param (required for GET)
?api_key={api_key}
```

**Our API Key Env Var**: `REDTRACK_API_KEY`

---

### Endpoints Used

| Endpoint | Method | Purpose | SignalRoom Resource |
|----------|--------|---------|---------------------|
| `/report` | GET | Daily spend by traffic source | `redtrack.daily_spend` |

### Report GET Request

**Endpoint**: `GET https://api.redtrack.io/report`

**Request**:
```
GET /report?api_key={key}&date_from=2025-12-01&date_to=2025-12-01&timezone=America/New_York&group=source&sortby=clicks&direction=desc
```

**Response**:
```json
[
  {
    "source_id": "66c79f91be26fd4634569658",
    "source": "Facebook CCW",
    "source_alias": "facebook",
    "clicks": 1523,
    "conversions": 45,
    "cost": 7825.50
  },
  {
    "source_id": "62b29551c6880d00014d8c73",
    "source": "Google Ads CCW",
    "source_alias": "google",
    "clicks": 892,
    "conversions": 28,
    "cost": 1240.00
  }
]
```

**Notes**:
- POST to `/report` returns 404; must use GET
- Rate limited; we add 1s delay between daily requests
- Exponential backoff on 429 (1s, 2s, 4s)
- Use `conversions` field only (not `total_conversions` which includes all event types)

---

### Report POST Request (Does Not Work)

**Endpoint**: `POST https://api.redtrack.io/report`

**Request** (documented but returns 404):
```json
{
  "date_from": "2025-12-01",
  "date_to": "2025-12-07",
  "timezone": "America/New_York",
  "group_by": ["date", "traffic_source"],
  "columns": ["clicks", "conversions", "cost"],
  "filters": {},
  "limit": 10000,
  "page": 1
}
```

**Status**: Not working. Use GET instead.

---

### Endpoints Available (Not Yet Used)

| Endpoint | Method | Purpose | Priority |
|----------|--------|---------|----------|
| `/campaigns` | GET | List campaigns | Medium |
| `/sources` | GET | List traffic sources | Low |
| `/offers` | GET | List offers | Low |

---

### Key Source IDs

| Source Name | Source ID | Platform |
|-------------|-----------|----------|
| Facebook CCW | `66c79f91be26fd4634569658` | Meta |
| Meta CCW AWF2 Stephanie | `6807d9120ee9ffc623c1d7e5` | Meta |
| Meta CCW SB Political | `68b87e99882b48e6620a3116` | Meta |
| Google Ads CCW | `62b29551c6880d00014d8c73` | Google |
| Facebook EXP | `67c097f0aee15ff71f3f99aa` | Meta |

---

## PostHog (Planned)

### LIVE DOCS: https://posthog.com/docs/api

**API Reference**: https://posthog.com/docs/api/query

**API Base URL**: `https://app.posthog.com` (or self-hosted)

**Authentication**: Personal API key in header
```
Authorization: Bearer {api_key}
```

**Our Env Vars**:
- `POSTHOG_API_KEY`
- `POSTHOG_PROJECT_ID`
- `POSTHOG_HOST`

---

### Endpoints to Use

| Endpoint | Method | Purpose | Priority |
|----------|--------|---------|----------|
| `/api/projects/:id/query/` | POST | Query events via HogQL | High |
| `/api/projects/:id/feature_flags/` | GET | List feature flags | Medium |
| `/api/projects/:id/experiments/` | GET | List experiments | Medium |

### Query API Request (Recommended)

**Endpoint**: `POST https://app.posthog.com/api/projects/{project_id}/query/`

**Request**:
```json
{
  "query": {
    "kind": "HogQLQuery",
    "query": "SELECT event, timestamp, properties FROM events WHERE timestamp > now() - interval 1 day LIMIT 100"
  }
}
```

**Response**:
```json
{
  "results": [
    ["$pageview", "2025-12-18T10:30:00Z", {"$current_url": "https://example.com"}],
    ["signup_completed", "2025-12-18T10:31:00Z", {"plan": "pro"}]
  ],
  "columns": ["event", "timestamp", "properties"]
}
```

**Notes**:
- Events API is deprecated; use Query API instead
- Rate limit: 2400 requests/hour
- HogQL is PostHog's SQL dialect

---

### Events API (Deprecated)

**Endpoint**: `GET https://app.posthog.com/api/projects/{project_id}/events/`

**Status**: Deprecated. Migrate to Query API.

**Limitations**:
- Max pagination offset: 50000
- Default: last 24 hours only
- Max date range: < 1 year

---

## Mautic (Planned)

### LIVE DOCS: https://devdocs.mautic.org/

**API Reference (Contacts)**: https://devdocs.mautic.org/en/5.x/rest_api/contacts.html

**API Reference (Campaigns)**: https://devdocs.mautic.org/en/5.x/rest_api/campaigns.html

**API Base URL**: `https://{your-mautic-instance}/api/`

**Authentication**: OAuth2 Client Credentials
```
# Get token
POST /oauth/v2/token
{
  "grant_type": "client_credentials",
  "client_id": "{client_id}",
  "client_secret": "{client_secret}"
}

# Use token
Authorization: Bearer {access_token}
```

**Our Env Vars**:
- `MAUTIC_BASE_URL`
- `MAUTIC_CLIENT_ID`
- `MAUTIC_CLIENT_SECRET`

---

### Endpoints to Use

| Endpoint | Method | Purpose | Priority |
|----------|--------|---------|----------|
| `/contacts` | GET | List contacts | High |
| `/contacts/{id}` | GET | Get contact details | High |
| `/campaigns` | GET | List campaigns | Medium |
| `/emails` | GET | List email templates | Medium |
| `/emails/{id}/stats` | GET | Email performance | Medium |

### List Contacts Request

**Endpoint**: `GET https://{instance}/api/contacts`

**Request**:
```
GET /api/contacts?search=email:*@example.com&limit=50&start=0
```

**Response**:
```json
{
  "total": 150,
  "contacts": {
    "1": {
      "id": 1,
      "fields": {
        "core": {
          "email": {"value": "john@example.com"},
          "firstname": {"value": "John"},
          "lastname": {"value": "Doe"}
        }
      },
      "dateAdded": "2025-12-01T10:00:00+00:00"
    }
  }
}
```

**Notes**:
- Contacts keyed by ID in response object
- Pagination via `start` and `limit` params
- Token must be cached and refreshed

---

## Google Sheets (Planned)

### LIVE DOCS: https://developers.google.com/sheets/api

**Python Quickstart**: https://developers.google.com/workspace/sheets/api/quickstart/python

**API Reference**: https://googleapis.github.io/google-api-python-client/docs/dyn/sheets_v4.html

**API Base URL**: `https://sheets.googleapis.com/v4/spreadsheets`

**Authentication**: Service Account or OAuth2
```python
from google.oauth2.service_account import Credentials
creds = Credentials.from_service_account_file('credentials.json')
```

**Our Env Vars**:
- `GOOGLE_SHEETS_CREDENTIALS_PATH` (file path)
- `GOOGLE_SHEETS_CREDENTIALS_JSON` (inline JSON)

---

### Endpoints to Use

| Endpoint | Method | Purpose | Priority |
|----------|--------|---------|----------|
| `/{spreadsheetId}/values/{range}` | GET | Read cell values | High |
| `/{spreadsheetId}/values/{range}` | PUT | Write cell values | Medium |
| `/{spreadsheetId}` | GET | Get spreadsheet metadata | Low |

### Read Range Request

**Endpoint**: `GET https://sheets.googleapis.com/v4/spreadsheets/{id}/values/{range}`

**Request**:
```
GET /v4/spreadsheets/1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgvE2upms/values/Sheet1!A1:D10
```

**Response**:
```json
{
  "range": "Sheet1!A1:D10",
  "majorDimension": "ROWS",
  "values": [
    ["Name", "Email", "Amount", "Date"],
    ["John Doe", "john@example.com", "100", "2025-12-01"],
    ["Jane Smith", "jane@example.com", "250", "2025-12-02"]
  ]
}
```

---

### Python Library Options

| Library | Description | Docs |
|---------|-------------|------|
| `gspread` | Most popular, high-level | https://docs.gspread.org/ |
| `pygsheets` | Alternative, good for automation | https://pygsheets.readthedocs.io/ |
| `google-api-python-client` | Official, low-level | https://googleapis.github.io/google-api-python-client/ |

---

## Adding a New Integration

When adding a new API integration:

1. **Add to Quick Links table** at top of this doc
2. **Create section** with:
   - `### LIVE DOCS: {url}` (prominently labeled)
   - API base URL
   - Authentication method
   - Env var names
3. **Document endpoints**:
   - Endpoints Used (what we've implemented)
   - Endpoints Available (for future use)
4. **Include request/response examples** from actual API calls
5. **Note any quirks** (rate limits, auth issues, field naming)
6. **Update `docs/SOURCES.md`** with implementation details

---

## Changelog

| Date | Change |
|------|--------|
| 2025-12-19 | Initial creation with Everflow, Redtrack, PostHog, Mautic, Google Sheets |
