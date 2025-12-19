# Future Improvements

Notes and insights for future phases, captured from AJ's experience with Everflow and Redtrack integrations.

---

## 1. Additional Everflow API Endpoints

### Current State
- Only using the Reporting Entity Table endpoint (`/v1/networks/reporting/entity/table`)
- Groups by date, affiliate, advertiser

### Endpoints to Add

| Endpoint | Purpose | Priority |
|----------|---------|----------|
| [Advertisers](https://developers.everflow.io/docs/network/advertisers/#find-all) | Sync advertiser metadata | Medium |
| [Affiliates](https://developers.everflow.io/docs/network/affiliates/#fetch-affiliates) | Sync affiliate metadata | High |
| [Offers](https://developers.everflow.io/docs/network/offers/#fetch-offers) | Sync offer metadata | High |

### Why This Matters
- Currently we hardcode advertiser IDs (1=CCW, 2=EXP)
- Affiliate names come from reporting API but could become stale
- Offer data would enable more robust affiliate mapping (see Section 3)

---

## 2. Additional Redtrack API Filters

### Current State
- Only filtering/grouping by `source_id` (traffic source)

### Filters to Add

| Filter | Purpose |
|--------|---------|
| `campaign_id` | Group by RT campaign |
| `offer_id` | Group by RT offer (key for mapping) |
| `landing_id` | Group by landing pages |
| `network_id` | Group by offer source/network |

### Redtrack Object Model

Understanding the RT hierarchy helps with future integrations:

```
Network (Offer Source)
└── Offer (destination URL / EF redirect)
    └── Campaign (actual ad URL)
        ├── Source (traffic channel / ad account)
        └── Lander (optional presale page)
```

| RT Term | UI Name | Description |
|---------|---------|-------------|
| Network | Offer Source | Where offers come from. We use "713 Online Everflow" with global postback |
| Offer | Offer | Destination URL, usually an Everflow redirect |
| Source | Traffic Channel | Connection to a single ad account (Meta, Google, TikTok) |
| Lander | Landing | Optional presale page with dynamic RT /click links |
| Campaign | Campaign | Combination of source + lander(s) + offer(s), generates the ad URL |

---

## 3. Robust Affiliate Mapping

### Current Problem

The RedTrack → Everflow object model doesn't align cleanly:

- **Everflow**: Advertiser/Brand → Affiliate/Partner → Offer
- **Redtrack**: No direct affiliate layer - multiple affiliates (Jeff, Stephanie) run inside one RT account with different campaigns

### Current Solution (Fragile)

We map at the **traffic channel level** via `internal-affiliates.csv`:
- Facebook ad account X → Affiliate "G2 - Meta"
- Google account Y → Affiliate "SB - Google"

**Problems:**
- Requires manual maintenance as channels/ownership change
- Mappings can become stale
- "Good enough" for iMessage reporting but not ideal long-term

### Better Solution (Offer-Based Mapping)

Map at the **offer level** using the destination URL:

1. Every RT campaign is tied to an offer
2. Pull offer details from RT API
3. Inspect destination URL (or resolved redirect URL)
4. Extract `AFFID` parameter from URL
5. `Everflow Offer ID + AFFID` = correct affiliate mapping

**Example:**
```
RT Offer URL: https://everflow.io/track/offer/123?affid=456
               └── Offer ID: 123    └── Affiliate ID: 456
```

### Blockers

- RT API doesn't cleanly expose offer details via standard endpoints
- RT may support **offer export to S3** - could ingest on daily/weekly cadence
- Need to investigate RT API more or request S3 export setup

### Implementation Plan (Future Phase)

1. Investigate RT `/offers` or `/campaigns` endpoints
2. If not available, set up RT → S3 offer export
3. Create `redtrack.offers` table with destination URLs
4. Parse URLs to extract AFFID
5. Build automated mapping: `(rt_offer_id, ef_offer_id, ef_affiliate_id)`
6. Replace manual `internal-affiliates.csv` with automated lookup

---

## 4. Priority Matrix

| Improvement | Impact | Effort | Priority |
|-------------|--------|--------|----------|
| EF Affiliates endpoint | Medium | Low | P2 |
| EF Offers endpoint | High | Low | P1 |
| RT offer_id grouping | High | Low | P1 |
| Offer-based mapping | Very High | High | P1 (after above) |
| RT → S3 offer export | High | Medium | P2 (if API blocked) |

---

## 5. References

- [Everflow API Docs](https://developers.everflow.io/)
- [Redtrack API Docs](https://help.redtrack.io/hc/en-us/categories/360003146479-API)
- Current mapping file: `data/clients/713/mappings/internal-affiliates.csv`

---

*Notes captured from AJ, December 2025*
