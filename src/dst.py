def fix_dst(year, month, day, hour, minute, second, dow):
    last_sunday = get_last_sunday_date(day, dow)
    past_last_sunday = day >= last_sunday
    if (
        4 <= month <= 9
        or (month == 3 and past_last_sunday)
        or (month == 10 and not past_last_sunday)
    ):
        delta = 2
    else:
        delta = 1
    hour = (hour + delta) % 24
    return hour, minute


def get_last_sunday_date(day, dow):
    until_end_of_month = 31 - day
    weeks_to_add = until_end_of_month // 7 + 1
    last_sunday = day + weeks_to_add * 7 - dow - 1
    if last_sunday > 31:
        last_sunday -= 7
    return last_sunday
