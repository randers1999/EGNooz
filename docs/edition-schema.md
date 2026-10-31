# EGNooz edition JSON (schemaVersion 1)

Timezone for all dates: `Australia/Melbourne`.

Android, the public page, and email all render the **published** file. Drafts stay private on the VPS.

## Public files (only after Publish)

- `https://krystalbbs.net/editions/latest.json` — last published edition (yesterday stays until today is published)
- `https://krystalbbs.net/editions/YYYY-MM-DD.json` — that day’s published edition

Unpublished days return HTTP 404. Ingest never writes these files.

## Shape

```json
{
  "schemaVersion": 1,
  "timezone": "Australia/Melbourne",
  "editionDate": "2026-10-31",
  "status": "published",
  "generatedAt": "2026-10-31T05:00:12+11:00",
  "publishedAt": "2026-10-31T07:12:04+11:00",
  "editorNote": "Quiet news day; council meeting tonight.",
  "warnings": {
    "source": "VicEmergency",
    "attribution": "Data from the State of Victoria, Australia.",
    "attributionUrl": "https://www.emv.vic.gov.au/responsibilities/victorias-warning-system/emergency-data",
    "license": "CC BY 3.0 AU",
    "disclaimer": "EGNooz is not an emergency service. For warnings use VicEmergency.",
    "feedLastUpdated": "2026-10-31T15:50:40+11:00",
    "fetchedAt": "2026-10-31T05:00:08+11:00",
    "districtFireDanger": "MODERATE",
    "districtTotalFireBan": "NO - RESTRICTIONS MAY APPLY",
    "items": [
      {
        "id": "vicemergency-43557",
        "title": "Advice",
        "url": "https://www.emergency.vic.gov.au/respond/",
        "location": "East Gippsland",
        "category": "Advice — Health",
        "status": "Minor",
        "updatedAt": "2026-10-31T14:03:11+11:00",
        "feedType": "warning",
        "matchedPlaces": ["East Gippsland"]
      }
    ]
  },
  "items": [
    {
      "id": "bairnsdale-advertiser-ab12cd34ef56",
      "title": "Roads damaged, cars floating",
      "url": "https://bairnsdaleadvertiser.com.au/22341/roads-damaged-cars-floating/",
      "sourceId": "bairnsdale-advertiser",
      "sourceName": "Bairnsdale Advertiser",
      "publishedAt": "2026-10-07T00:00:00+11:00",
      "snippet": "Bairnsdale SES volunteers responded to more than 75 requests…",
      "matchReason": "local-source",
      "matchedPlaces": ["Bairnsdale"]
    }
  ]
}
```

`matchReason` is `local-source`, `mention`, or `manual`.

Draft JSON (not public) also has `included` on each item and an `ingestLog` array. Published JSON drops both, and only includes ticked items.

Snippets are short feed summaries. There is no article body and no publisher photos.
