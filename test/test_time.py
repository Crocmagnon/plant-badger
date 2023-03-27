import pytest

from dst import fix_dst, get_last_sunday_date


@pytest.mark.parametrize(
    "year, month, day, hour, minute, second, dow, expected",
    [
        (2023, 3, 2, 17, 22, 0, 3, (18, 22)),
        (2023, 3, 25, 17, 22, 0, 5, (18, 22)),
        (2023, 3, 26, 17, 22, 0, 6, (19, 22)),
        (2023, 3, 27, 17, 22, 0, 0, (19, 22)),
        (2023, 3, 28, 17, 22, 0, 1, (19, 22)),
        (2023, 10, 2, 17, 22, 0, 0, (19, 22)),
        (2023, 10, 28, 17, 22, 0, 5, (19, 22)),
        (2023, 10, 29, 17, 22, 0, 6, (18, 22)),
        (2023, 10, 30, 17, 22, 0, 0, (18, 22)),
        (2023, 10, 31, 17, 22, 0, 1, (18, 22)),
    ],
)
def test_fix_dst(year, month, day, hour, minute, second, dow, expected):
    assert fix_dst(year, month, day, hour, minute, second, dow) == expected


@pytest.mark.parametrize(
    "day, dow, expected",
    [
        (2, 3, 26),
        (15, 2, 26),
        (25, 5, 26),
        (17, 0, 30),
        (24, 5, 25),
        (27, 0, 26),
        (31, 2, 28),
    ],
)
def test_get_last_sunday_date(day, dow, expected):
    assert get_last_sunday_date(day, dow) == expected
