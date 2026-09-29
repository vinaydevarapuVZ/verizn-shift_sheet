from __future__ import annotations

import argparse
from datetime import date
from typing import Dict, Set

from roster_config import load_config
from google_sheets_client import open_google_sheet
from shift_scheduler import build_month_schedule, month_dates, read_leave_rows, read_members, write_schedule_to_sheet


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build a 24/7 shift schedule from Google Sheets.")
    parser.add_argument("--year", type=int, default=2026, help="The year to schedule (default 2026).")
    parser.add_argument("--month", type=int, default=10, help="The month to schedule (default 10).")
    parser.add_argument("--sheet-url", type=str, default=None, help="Google Sheet URL.")
    parser.add_argument("--credentials-json", type=str, default=None, help="Service account JSON path.")
    parser.add_argument("--dry-run", action="store_true", help="Generate locally without writing to the workbook.")
    parser.add_argument("--use-config", action="store_true", help="Use the editable local config file instead of the members list from the sheet.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    config = load_config()

    year = args.year
    month = args.month
    dates = month_dates(year, month)

    if args.use_config:
        members = config["members"]
        holidays = config["holidays"]
        leave_map: Dict[date, Set[str]] = {}
        holiday_dates = set()
        for date_value, reason in holidays.items():
            try:
                parsed = __import__("datetime").datetime.strptime(date_value, "%Y-%m-%d").date()
            except ValueError:
                continue
            holiday_dates.add(parsed)
        schedule = build_month_schedule(members, leave_map, holiday_dates, year, month)
        print("Using local roster config from settings/roster_config.json")
        print(f"Members: {members}")
        if not args.dry_run:
            workbook = open_google_sheet(args.sheet_url, args.credentials_json)
            write_schedule_to_sheet(workbook, members, schedule, dates, leave_map)
        return

    workbook = open_google_sheet(args.sheet_url, args.credentials_json)
    members_sheet = workbook.worksheet("Members")
    leave_sheet = workbook.worksheet("Leaves & Holidays")

    members = read_members(members_sheet)
    leave_map, holiday_dates = read_leave_rows(leave_sheet)
    schedule = build_month_schedule(members, leave_map, holiday_dates, year, month)

    if args.dry_run:
        print(f"Dry run. Generated schedule for {year}-{month:02d}.")
        for day in dates:
            if day in schedule:
                print(day.isoformat(), schedule[day])
        return

    write_schedule_to_sheet(workbook, members, schedule, dates, leave_map)
    print(f"Schedule created successfully for {year}-{month:02d}.")


if __name__ == "__main__":
    main()
