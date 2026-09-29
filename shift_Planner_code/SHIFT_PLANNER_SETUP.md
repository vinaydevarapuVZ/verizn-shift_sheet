# Shift Planner Setup and Run Guide

## Where to run it

Run the script from the workspace folder that contains the `shift_Planner_code` directory.

Example Windows path:

```powershell
cd "C:\path\to\verizn-shift_sheet"
```

Then run:

```powershell
python .\shift_Planner_code\shift_planner.py --year 2026 --month 10
```

## Dry run mode

This generates the schedule locally without writing to Google Sheets:

```powershell
python .\shift_Planner_code\shift_planner.py --year 2026 --month 10 --dry-run
```

## Use local editable config

If you want to update names and holidays from the config file instead of the live Google Sheet:

```powershell
python .\shift_Planner_code\shift_planner.py --year 2026 --month 10 --use-config
```

## Environment variables

Set these before running the Google Sheets version:

```powershell
$env:GOOGLE_SERVICE_ACCOUNT_JSON = "C:\path\to\service-account.json"
$env:GOOGLE_SHEET_URL = "https://docs.google.com/spreadsheets/d/your-sheet-id/edit"
```

## Output

The script prints the generated planner summary in the terminal and writes the final schedule to the `Main Planner` sheet.
