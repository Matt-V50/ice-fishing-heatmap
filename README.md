# 🎣 Ice Fishing Booking Heatmap

Interactive heatmap for visualizing ice fishing timeslot bookings. See at a glance which days and times are most heavily booked.

## Live Demo

👉 https://Matt-V50.github.io/ice-fishing-heatmap/

## Usage

1. Place your `timeslots.csv` in the `data/` folder — the page auto-loads it on open.
2. Or click **"Upload New CSV"** to load a different file locally (no upload to server).

### CSV Format

| date | status | start_time | end_time | A | B | start_date | end_date | ... |
|---|---|---|---|---|---|---|---|---|
| 2026-02-27 | A | 10:00 | 14:00 | 5 | 5 | 1772204400 | 1772218800 | ... |

- **`B`** = number of bookings for that timeslot (used for heatmap intensity)
- Overlapping timeslots accumulate — brighter = more bookings stacked

## Features

- 🗺️ Heatmap: days × time, color intensity = booking density
- ❄️ Three ice-themed color palettes (Frost / Aurora / Blizzard)
- 🔍 Hover tooltip with exact booking count
- ⚙️ Adjustable time resolution (15 min / 30 min)
- 📂 Local CSV re-upload for quick debugging

## Deploy

```bash
git clone https://github.com/YOUR_USERNAME/ice-fishing-heatmap.git
# put your timeslots.csv in data/
# enable GitHub Pages → Settings → Pages → main branch / root
```

No build step. Pure HTML + vanilla JS.