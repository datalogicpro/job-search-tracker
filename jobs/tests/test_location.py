import pytest

from jobs.sources.base import location_accepts_us


@pytest.mark.parametrize(
    "location",
    [
        "",
        None,
        "Remote",
        "REMOTE",
        "USA",
        "United States",
        "US only",
        "US & Canada",
        "North America",
        "Americas",
        "Worldwide",
        "Global",
        "Anywhere in the World",
        "Anywhere",
        "Kansas",
        "New York City",
        "Austin",
        "San Francisco Bay Area",
        "Cambridge, MA",
        "Vancouver, WA",
        "Athens, Georgia",
    ],
)
def test_accepts_us_locations(location):
    assert location_accepts_us(location) is True


@pytest.mark.parametrize(
    "location",
    [
        "APAC",
        "EMEA/APAC",
        "Europe",
        "Remote from EU",
        "India",
        "Latin America",
        "Spain, UK, Poland, Romania",
        "Argentina",
        "Brazil",
        "Vancouver, BC",
        "Cambridge, UK",
        "Athens, Greece",
        "Vancouver",
        "Cambridge, or London",
    ],
)
def test_rejects_non_us_locations(location):
    assert location_accepts_us(location) is False