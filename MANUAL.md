# Battery Tracker — User Manual

A personal web app for tracking your power tool battery inventory across multiple brands.

---

## Getting Started

### Requirements
- Python 3.10+
- pip

### Installation

```bash
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # macOS/Linux
pip install -r requirements.txt
```

### Running the App

```bash
python app.py
```

Open **http://127.0.0.1:5000** in your browser.

The database (`batteries.db`) is created automatically on first run.

---

## Choosing Your Brand

Before adding batteries, set your tool brand in **Settings** (gear icon in the top-right of the nav bar).

### Supported Brands

| Brand | Voltages | Theme Colour |
|-------|----------|--------------|
| Makita | 12V, 18V, 40V | Teal |
| DeWalt | 12V, 20V, 60V | Yellow |
| Milwaukee | 12V, 18V | Red |
| AEG | 12V, 18V | Orange |
| Ryobi | 18V, 36V, 40V | Green |
| Bosch | 12V, 18V | Blue |
| Hikoki | 18V, 36V | Green |

Changing the brand updates:
- The entire colour theme across the app
- The voltage options available when adding/editing batteries
- The OEM type label (e.g. "OEM (Makita)" becomes "OEM (DeWalt)")
- The nav bar branding and logo colour

**Note:** Existing batteries keep their voltage even if it's not in the new brand's list. The edit form will include the battery's current voltage alongside the new brand's options.

---

## Adding a Battery

Click **+ Add** in the nav bar.

### Fields

| Field | Required | Description |
|-------|----------|-------------|
| **Battery Label** | Yes | A physical ID you write on the battery (e.g. B001, MAK-01). Used to match physical batteries to their records. |
| **Type** | Yes | **OEM** (genuine brand) or **Aftermarket** (third-party). |
| **Voltage** | Yes | Select from the voltages available for your chosen brand. |
| **Capacity (Ah)** | Yes | Battery capacity. Options: 1.5, 2.0, 3.0, 4.0, 5.0, 6.0, 9.0, 12.0 Ah. |
| **Status** | Yes | Current battery status (defaults to "New" for new batteries). |
| **Status Changed** | No | Date the status was last changed. Auto-set when status changes. |
| **Purchase Date** | No | When you bought the battery. Used to calculate battery age. |
| **Price ($)** | No | Purchase price. Used for investment tracking in stats. |
| **History & Notes** | No | Free-form notes. Status changes are logged here automatically. |

### Date Picker
Click any date field to open a calendar picker. Dates are displayed in Australian format (DD/MM/YYYY). If the field is empty, the calendar opens to today's month.

---

## Battery Statuses

Each battery has a status that tracks its lifecycle:

| Status | Meaning | Badge Colour |
|--------|---------|--------------|
| **New** | Purchased but not yet deployed | Purple |
| **In Use** | Currently active and in rotation | Green |
| **For Repair** | Faulty, sent for repair or assessment | Amber |
| **Repaired** | Back from repair, returned to service | Blue |
| **Dead** | End of life, no longer functional | Red |

### Automatic History Logging

When you add a battery, the notes field is automatically updated with:
```
13/02/2026 - Added - New
```

When you change a battery's status during editing, a new line is added:
```
15/03/2026 - In Use
```

You can add your own notes alongside these entries on the same line or on new lines.

---

## Inventory View

The home page shows your full battery inventory.

### Stats Cards

Three cards at the top show:
- **Total Batteries** — count with voltage breakdown
- **Total Invested** — sum of all prices with per-battery average
- **Status Overview** — badge count for each status

When a status filter is active, the battery count and investment cards update to reflect only the filtered set.

### Status Filters

Below the stats, pill-shaped filter buttons let you view batteries by status:
- **All** — shows every battery
- Individual status pills only appear if batteries exist with that status
- Each pill shows the count for that status
- The section badge shows "X of Y units" when filtering

### Inventory Table

| Column | Description |
|--------|-------------|
| Label | The physical ID written on the battery |
| Voltage | Voltage with a branded badge |
| Capacity | Ah rating |
| Type | OEM (brand name) or Aftermarket |
| Status | Colour-coded status badge |
| Status Changed | Date the status was last updated (DD/MM/YYYY) |
| Purchased | Purchase date (DD/MM/YYYY) |
| Age | Calculated age from purchase date (e.g. "2y 3m", "5m", "< 1m") |
| Price | Purchase price |
| Actions | Edit and Delete buttons |

Batteries are sorted alphabetically by label.

### Table Footer

When batteries have prices recorded, a footer row shows the total count and combined investment for the current view.

---

## Editing a Battery

Click **Edit** on any battery row. The form is pre-filled with the battery's current data. Change any fields and click **Update Battery**.

If you change the status, the status changed date is automatically set to today and a history entry is added to the notes.

---

## Deleting a Battery

Click **Delete** on any battery row. A confirmation dialog appears showing the battery label. Click **Delete** to confirm or **Cancel** to abort.

This action cannot be undone.

---

## Data Storage

All data is stored locally in a SQLite database file (`batteries.db`) in the app directory. There is no cloud sync or external server.

To back up your data, copy the `batteries.db` file. To reset, delete it and restart the app.

---

## Mobile Support

The interface is responsive. On smaller screens:
- Stats cards stack vertically
- The table switches to a card-based layout with labelled fields
- Form fields stack to single-column
