import pytest

from fixtures import make_train_rows
from tarifalatam.config import (
    AMENITY_FLAGS,
    FORBIDDEN_FEATURES,
    HOST_PROFILE_COLUMNS,
    REFERENCE_BINARY,
    REFERENCE_CATEGORICAL,
    REFERENCE_NUMERIC,
    SUSPICIOUS_FEATURES,
)
from tarifalatam.features.columns import SUSPICIOUS_DERIVED, check_feature_columns, feature_columns

REFERENCE = REFERENCE_CATEGORICAL + REFERENCE_NUMERIC + REFERENCE_BINARY


def test_column_lists_are_disjoint_and_cover_the_65_columns():
    lists = [FORBIDDEN_FEATURES, SUSPICIOUS_FEATURES, REFERENCE, HOST_PROFILE_COLUMNS]
    assert [len(cols) for cols in lists] == [18, 23, 13, 11]
    every = [col for cols in lists for col in cols]
    assert len(every) == len(set(every)) == 65  # ninguna columna en dos listas
    assert set(every) == set(make_train_rows().columns)


@pytest.mark.parametrize("column", FORBIDDEN_FEATURES)
def test_check_feature_columns_rejects_each_forbidden_column(column):
    with pytest.raises(ValueError, match=column):
        check_feature_columns(["accommodates", column])


def test_check_feature_columns_rejects_suspicious_unless_allowed():
    with pytest.raises(ValueError, match="estimated_occupancy_l365d"):
        check_feature_columns(["accommodates", "estimated_occupancy_l365d"])
    check_feature_columns(["accommodates", "estimated_occupancy_l365d"], allow_suspicious=True)  # no falla


def test_check_feature_columns_accepts_the_reference():
    check_feature_columns(REFERENCE)


def _all(columns: dict) -> list:
    return [col for group in columns.values() for col in group]


def test_feature_columns_reference():
    columns = feature_columns()
    assert columns["categorical"] == REFERENCE_CATEGORICAL
    assert columns["numeric"] == REFERENCE_NUMERIC
    assert columns["binary"] == REFERENCE_BINARY
    assert columns["target_encoded"] == []


@pytest.mark.parametrize(
    "idea, added",
    [
        (1, ["distance_to_center_km"]),
        (2, ["amenities_count", *AMENITY_FLAGS]),
        (3, ["people_per_bedroom", "people_per_bathroom", "beds_per_person"]),
        (
            4,
            [
                "host_listings_count",
                "calculated_host_listings_count",
                "calculated_host_listings_count_entire_homes",
                "calculated_host_listings_count_private_rooms",
                "calculated_host_listings_count_shared_rooms",
                "host_tenure_years",
                "user_tenure_years",
                "host_has_profile_pic",
                "host_identity_verified",
            ],
        ),
        (5, ["neighbourhood_cleansed"]),
    ],
)
def test_each_idea_adds_exactly_its_columns(idea, added):
    reference = _all(feature_columns())
    with_idea = _all(feature_columns(ideas=(idea,)))
    if idea == 5:  # el barrio entra además codificado con el promedio del objetivo
        assert feature_columns(ideas=(5,))["target_encoded"] == ["neighbourhood_cleansed"]
        assert len(with_idea) == len(reference) + 1
    else:
        assert sorted(set(with_idea) - set(reference)) == sorted(added)


@pytest.mark.parametrize("ideas", [(), (1,), (2, 3), (1, 2, 3, 4, 5)])
def test_feature_columns_never_include_forbidden_columns(ideas):
    for with_suspicious in (False, True):
        columns = _all(feature_columns(ideas=ideas, with_suspicious=with_suspicious))
        assert not set(columns) & set(FORBIDDEN_FEATURES)


def test_app_version_has_no_suspicious_columns():
    columns = _all(feature_columns(ideas=(1, 2, 3, 4, 5)))
    assert not set(columns) & (set(SUSPICIOUS_FEATURES) | set(SUSPICIOUS_DERIVED))
    check_feature_columns(columns)  # no falla


def test_with_suspicious_adds_them_and_their_derived_columns():
    added = set(_all(feature_columns(with_suspicious=True))) - set(_all(feature_columns()))
    expected = (set(SUSPICIOUS_FEATURES) - {"first_review", "last_review"}) | set(SUSPICIOUS_DERIVED)
    assert added == expected  # las dos fechas entran convertidas en días
