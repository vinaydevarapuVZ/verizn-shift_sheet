# Automated Shift Planner

This folder contains a modular 24/7 shift planner for an 8-person team.

## Module structure

- `roster_config.py` - editable local roster settings
- `google_sheets_client.py` - Google Sheets connection and authentication
- `shift_scheduler.py` - scheduling rules, fairness scoring, and writing logic
- `main.py` - CLI entry point
- `shift_planner.py` - simple terminal launcher for the planner
- `settings/roster_config.json` - quick-edit place for member names and holidays

## Update members and holidays without changing the scheduling logic

Open the file:

- `shift_Planner_code/settings/roster_config.json`

Edit the `members` list and `holidays` map as needed.

Example:

```json
{
  "members": [
    "Alice",
    "Bharat",
    "Chris",
    "Diana"
  ],
  "holidays": {
    "2026-10-10": "Festival holiday",
    "2026-10-15": "Company holiday"
  }
}
```

You can update this file directly without restructuring the code or rerunning the entire core logic.

## Install dependencies

```bash
pip install gspread google-auth
```

## Google Sheets setup

1. Create a Google Cloud project.
2. Enable the Google Sheets API and Google Drive API.
3. Create a service account and download the JSON key.
4. Share the target spreadsheet with the service account email.
5. Set:

```bash
export GOOGLE_SERVICE_ACCOUNT_JSON="/path/to/service-account.json"
export GOOGLE_SHEET_URL="https://docs.google.com/spreadsheets/d/your-sheet-id/edit"
```

## Where to run it

Open a terminal in the workspace root (the folder that contains `shift_Planner_code`).

Windows PowerShell example:

```powershell
cd "C:\path\to\verizn-shift_sheet"
python .\shift_Planner_code\shift_planner.py --year 2026 --month 10
```

If you want to use the local editable config file:

```powershell
python .\shift_Planner_code\shift_planner.py --year 2026 --month 10 --use-config
```

Dry run without writing to Google Sheets:

```powershell
python .\shift_Planner_code\shift_planner.py --year 2026 --month 10 --dry-run
```

## Main entry file

Use this entry file for normal execution:

- `shift_Planner_code/shift_planner.py`

This is the cleanest script name to run from the terminal.

## Sheet structure expected

The workbook should contain:

- `Members` - one member per row
- `Leaves & Holidays` - leave and holiday rows
- `Main Planner` - script writes a date-by-member schedule

## Notes

- The scheduler prioritizes operational coverage and rest rules first.
- Fairness is optimized as a secondary goal to rotate Night and General shifts across members.
- A leave or holiday can be updated in the JSON config or in the live workbook tabs.
