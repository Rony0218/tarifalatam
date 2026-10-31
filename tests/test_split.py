import numpy as np
import pandas as pd
import pytest
from fixtures import make_listings
from sklearn.model_selection import train_test_split

from tarifalatam.data.split import assert_disjoint_hosts, group_cv, split_by_host


def _many_hosts() -> pd.DataFrame:
    """60 anfitriones con 3 anuncios cada uno, repartidos entre dos ciudades."""
    return make_listings(n_hosts=60, per_host=3)


def test_split_by_host_never_shares_a_host():
    df = _many_hosts()
    train, test = split_by_host(df, test_size=0.2, seed=1)
    assert set(train["host_id"]).isdisjoint(test["host_id"])
    # cada anfitrión tiene anuncios en dos ciudades y aun así queda entero de un lado
    assert (train.groupby("host_id").size() == 3).all()
    assert (test.groupby("host_id").size() == 3).all()


def test_split_by_host_loses_no_rows():
    df = _many_hosts()
    train, test = split_by_host(df, test_size=0.2, seed=1)
    assert len(train) + len(test) == len(df)
    assert sorted(pd.concat([train, test])["id"]) == sorted(df["id"])


def test_split_by_host_puts_about_the_requested_share_of_hosts_in_test():
    train, test = split_by_host(_many_hosts(), test_size=0.2, seed=1)
    assert test["host_id"].nunique() == 12  # 20 % de 60 anfitriones


def test_split_by_host_is_reproducible_with_seed():
    df = _many_hosts()
    first, _ = split_by_host(df, seed=42)
    second, _ = split_by_host(df, seed=42)
    pd.testing.assert_frame_equal(first, second)


def test_assert_disjoint_hosts_raises_on_overlap():
    df = _many_hosts()
    with pytest.raises(AssertionError):
        assert_disjoint_hosts(df.iloc[:10], df.iloc[5:20])


def test_row_split_would_be_caught():
    """Si alguien parte por fila, el control lo detecta (FR-021)."""
    df = _many_hosts()
    train, test = train_test_split(df, test_size=0.2, random_state=0)
    with pytest.raises(AssertionError):
        assert_disjoint_hosts(train, test)


def test_group_cv_folds_do_not_share_hosts():
    df = _many_hosts()
    for train_idx, valid_idx in group_cv(n_splits=5).split(df, groups=df["host_id"]):
        train_hosts = set(df.iloc[train_idx]["host_id"])
        valid_hosts = set(df.iloc[valid_idx]["host_id"])
        assert train_hosts.isdisjoint(valid_hosts)
    assert np.all(df["host_id"].notna())


def test_split_by_host_fails_if_host_id_is_missing():
    """Un host_id vacío no se puede agrupar: dos anuncios vacíos podrían caer a ambos lados sin que se note."""
    df = _many_hosts()
    df["host_id"] = df["host_id"].astype(float)
    df.loc[0, "host_id"] = np.nan
    with pytest.raises(ValueError, match="host_id"):
        split_by_host(df)
