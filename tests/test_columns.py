import pytest

from fixtures import make_train_rows
from tarifalatam.config import (
    FORBIDDEN_FEATURES,
    HOST_PROFILE_COLUMNS,
    REFERENCE_BINARY,
    REFERENCE_CATEGORICAL,
    REFERENCE_NUMERIC,
    SUSPICIOUS_FEATURES,
)
from tarifalatam.features.columns import check_feature_columns

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
