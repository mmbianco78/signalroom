# Raw Reference Data

Client-provided configuration and credentials reference.

---

## 713 - S3 Exports

**Bucket**: `s3://sticky-713-data-repo`

**Paths**:
- `/orders-create` - New order records
- `/orders-update` - Order status updates
- `/prospects-create` - New prospect/lead records

**Region**: `us-east-1`

**Projects in this data**:
- CCW (primary, first to implement)
- Expungement
- Others TBD

**Notes**:
- All projects' data is mixed in the same bucket
- Project identification happens at query time via:
  - Campaign ID lookups
  - Product ID lookups
  - Naming conventions
- See ROADMAP.md for project mapping strategy

---

## Client Registry

| Client ID | Name | S3 Bucket | Status |
|-----------|------|-----------|--------|
| 713 | 713 | sticky-713-data-repo | Active |
| cti | ClayTargetInstruction | TBD | Planned |

---

## Project Registry

| Client | Project ID | Name | Status |
|--------|------------|------|--------|
| 713 | ccw | CCW | Primary |
| 713 | expungement | Expungement | Planned |
| cti | TBD | TBD | Planned |
