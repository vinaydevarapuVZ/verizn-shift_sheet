from __future__ import annotations

from calendar import monthrange
from collections import defaultdict
from datetime import date, datetime, timedelta
from typing import DefaultDict, Dict, Iterable, List, Optional, Set, Tuple

SHIFT_ORDER = ["MORNING", "GENERAL", "SECOND", "NIGHT"]
SHIFT_TIMINGS = {
    "MORNING": ("06:00", "14:30"),
    "GENERAL": ("13:30", "22:30"),
    "SECOND": ("14:00", "23:00"),
    "NIGHT": ("22:00", "06:30"),
}


def month_dates(year: int, month: int) -> List[date]:
    """Return all dates in the chosen month."""
    last_day = monthrange(year, month)[1]
    return [date(year, month, day) for day in range(1, last_day + 1)]


def normalise_name(value: object) -> str:
    return str(value).strip().replace("\n", " ").strip()


def parse_date_value(value: object) -> Optional[date]:
    text = str(value).strip() if value is not None else ""
    if not text:
        return None
    for fmt in (
        "%Y-%m-%d",
        "%d-%m-%Y",
        "%d/%m/%Y",
        "%m/%d/%Y",
        "%Y/%m/%d",
        "%d-%b-%Y",
        "%d %b %Y",
        "%d %B %Y",
        "%Y-%m-%d %H:%M:%S",
    ):
        try:
            return datetime.strptime(text, fmt).date()
        except ValueError:
            continue
    return None


def read_members(sheet) -> List[str]:
    """Read members from the Members worksheet."""
    rows = sheet.get_all_values()
    if not rows:
        raise ValueError("The 'Members' sheet is empty.")

    names: List[str] = []
    seen: Set[str] = set()
    for row in rows:
        if not row:
            continue
        name = normalise_name(row[0])
        if not name or name.lower() in {"member", "members", "name", "team member"}:
            continue
        if name.lower() not in seen:
            seen.add(name.lower())
            names.append(name)
    return names


def read_leave_rows(sheet) -> Tuple[Dict[date, Set[str]], Set[date]]:
    """Read leave rows and holiday markers from the Leave & Holidays sheet."""
    rows = sheet.get_all_values()
    leave_map: DefaultDict[date, Set[str]] = defaultdict(set)
    holiday_dates: Set[date] = set()

    for row in rows:
        if not row:
            continue
        cells = [normalise_name(cell) for cell in row if str(cell).strip()]
        if not cells:
            continue
        if any(cell.lower() in {"date", "member", "name", "holiday", "leave"} for cell in cells[:2]):
            continue

        date_index = next((idx for idx, cell in enumerate(cells) if parse_date_value(cell) is not None), None)
        if date_index is None:
            continue
        day = parse_date_value(cells[date_index])
        if day is None:
            continue

        if date_index == 0:
            member_name = cells[1] if len(cells) > 1 else ""
            if member_name.lower() in {"all", "global", "company", "everyone", "holiday"}:
                holiday_dates.add(day)
            elif member_name:
                leave_map[day].add(member_name)
            else:
                holiday_dates.add(day)
        else:
            member_name = cells[0]
            if member_name.lower() in {"all", "global", "company", "everyone", "holiday"}:
                holiday_dates.add(day)
            else:
                leave_map[day].add(member_name)

    return leave_map, holiday_dates


def is_weekday(day: date) -> bool:
    return day.weekday() < 5


def week_id(day: date) -> int:
    return day.isocalendar()[1]


def shift_margins(day: date, shift_name: str) -> Tuple[datetime, datetime]:
    start_str, end_str = SHIFT_TIMINGS[shift_name]
    start_dt = datetime.combine(day, datetime.strptime(start_str, "%H:%M").time())
    end_dt = datetime.combine(day, datetime.strptime(end_str, "%H:%M").time())
    if shift_name == "NIGHT":
        end_dt += timedelta(days=1)
    return start_dt, end_dt


def can_assign_member(member: str, day: date, shift_name: str, schedule: Dict[date, Dict[str, str]],
                      leave_map: Dict[date, Set[str]], member_history: Dict[str, List[Tuple[datetime, datetime]]],
                      member_day_presence: Dict[str, Set[date]]) -> bool:
    """Hard constraints that must be respected."""
    if day in leave_map and member in leave_map[day]:
        return False
    if day in schedule and any(member == assigned for assigned in schedule[day].values()):
        return False
    if shift_name == "GENERAL" and not is_weekday(day):
        return False

    shift_start, shift_end = shift_margins(day, shift_name)
    for prev_start, prev_end in member_history.get(member, []):
        if prev_end < shift_start:
            if shift_start - prev_end < timedelta(hours=12):
                return False
        elif shift_start < prev_end:
            return False
        else:
            if prev_start - shift_end < timedelta(hours=12):
                return False

    recent_days = [
        d for d in member_day_presence.get(member, set())
        if day - d <= timedelta(days=6) and day - d >= timedelta(days=0)
    ]
    if len(recent_days) + 1 > 5:
        return False

    return True


def score_member(member: str, day: date, shift_name: str, schedule: Dict[date, Dict[str, str]],
                 member_history: Dict[str, List[Tuple[datetime, datetime]]], member_day_presence: Dict[str, Set[date]],
                 member_weekly_days: Dict[str, int], shift_counts: Dict[str, int], fair_counts: Dict[str, Dict[str, int]]) -> int:
    """Fairness-aware scoring for the next candidate assignment."""
    score = 0
    current_week = week_id(day)
    week_workdays = sum(1 for d in member_day_presence.get(member, set()) if week_id(d) == current_week)

    score += max(0, 5 - week_workdays) * 20
    score -= fair_counts["NIGHT"].get(member, 0) * 6
    score -= fair_counts["GENERAL"].get(member, 0) * 6
    score -= week_workdays * 8
    score -= shift_counts.get(member, 0) * 2

    if shift_name in {"NIGHT", "GENERAL"}:
        avg = sum(fair_counts[shift_name].values()) / max(1, len(fair_counts[shift_name]))
        score -= abs((fair_counts[shift_name].get(member, 0) + 1) - avg) * 3

    if day in schedule and any(member == assigned for assigned in schedule[day].values()):
        return -10_000

    return score


def build_month_schedule(member_names: List[str], leave_map: Dict[date, Set[str]], holiday_dates: Set[date], year: int, month: int) -> Dict[date, Dict[str, str]]:
    """Greedy assignment scheduler for the month."""
    schedule: DefaultDict[date, Dict[str, str]] = defaultdict(dict)
    member_history: DefaultDict[str, List[Tuple[datetime, datetime]]] = defaultdict(list)
    member_day_presence: DefaultDict[str, Set[date]] = defaultdict(set)
    member_weekly_days: DefaultDict[str, int] = defaultdict(int)
    shift_counts: DefaultDict[str, int] = defaultdict(int)
    fair_counts: Dict[str, DefaultDict[str, int]] = {
        "NIGHT": defaultdict(int),
        "GENERAL": defaultdict(int),
    }

    for day in month_dates(year, month):
        for shift_name in SHIFT_ORDER:
            if shift_name == "GENERAL" and not is_weekday(day):
                continue

            candidates = [
                member for member in member_names
                if member not in leave_map.get(day, set())
                and can_assign_member(member, day, shift_name, schedule, leave_map, member_history, member_day_presence)
            ]

            if not candidates:
                fallback = [member for member in member_names if member not in leave_map.get(day, set())]
                if not fallback:
                    raise ValueError(f"No available person on {day.isoformat()} for {shift_name}.")
                chosen = sorted(
                    fallback,
                    key=lambda m: (
                        len(member_day_presence.get(m, set())),
                        fair_counts["NIGHT"].get(m, 0),
                        fair_counts["GENERAL"].get(m, 0),
                    ),
                )[0]
            else:
                chosen = max(
                    candidates,
                    key=lambda m: score_member(
                        m,
                        day,
                        shift_name,
                        schedule,
                        member_history,
                        member_day_presence,
                        member_weekly_days,
                        shift_counts,
                        fair_counts,
                    ),
                )

            schedule[day][shift_name] = chosen
            if day not in member_day_presence[chosen]:
                member_day_presence[chosen].add(day)
                member_weekly_days[chosen] += 1
            shift_counts[chosen] += 1
            if shift_name == "NIGHT":
                fair_counts["NIGHT"][chosen] += 1
            if shift_name == "GENERAL":
                fair_counts["GENERAL"][chosen] += 1

            start_dt, end_dt = shift_margins(day, shift_name)
            member_history[chosen].append((start_dt, end_dt))

    return schedule


def write_schedule_to_sheet(workbook, members: List[str], schedule: Dict[date, Dict[str, str]], all_dates: List[date], leave_map: Dict[date, Set[str]]) -> None:
    """Write the schedule to the 'Main Planner' worksheet."""
    planner = workbook.worksheet("Main Planner")
    rows = [["Member"] + [day.isoformat() for day in all_dates]]

    for member in members:
        row = [member]
        for day in all_dates:
            if day in leave_map and member in leave_map[day]:
                row.append("LEAVE")
                continue
            value = "OFF"
            assignment = next((shift for shift in SHIFT_ORDER if schedule.get(day, {}).get(shift) == member), None)
            if assignment:
                value = assignment
            row.append(value)
        rows.append(row)

    planner.clear()
    planner.update("A1", rows)
