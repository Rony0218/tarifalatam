import numpy as np
import pytest

from fixtures import make_train_rows
from tarifalatam.data.folds import fold_indices, load_folds, make_folds, reserve_hosts, save_folds


def test_make_folds_keeps_each_host_in_one_fold():
    train = make_train_rows()
    folds = make_folds(train)
    fold_of = train[["id", "host_id"]].merge(folds, on="id")
    assert (fold_of.groupby("host_id")["fold"].nunique() == 1).all()
    assert set(folds["fold"]) == {0, 1, 2, 3, 4}


def test_make_folds_puts_each_listing_in_exactly_one_fold():
    train = make_train_rows()
    folds = make_folds(train)
    assert len(folds) == len(train)
    assert folds["id"].is_unique
    assert set(folds["id"]) == set(train["id"])


def test_make_folds_is_deterministic_with_the_same_seed():
    train = make_train_rows()
    assert make_folds(train, seed=42).equals(make_folds(train, seed=42))
    # el orden de las filas no cambia la asignación de cada anuncio
    shuffled = train.sample(frac=1, random_state=1)
    by_id = make_folds(train).set_index("id")["fold"]
    by_id_shuffled = make_folds(shuffled).set_index("id")["fold"]
    assert by_id.sort_index().equals(by_id_shuffled.sort_index())


def test_make_folds_fails_with_missing_host_id():
    train = make_train_rows()
    train.loc[0, "host_id"] = np.nan
    with pytest.raises(ValueError, match="host_id"):
        make_folds(train)


def test_save_and_load_folds_roundtrip(tmp_path):
    folds = make_folds(make_train_rows())
    save_folds(folds, tmp_path / "folds.csv")
    assert load_folds(tmp_path / "folds.csv").equals(folds)


def test_load_folds_says_how_to_create_them(tmp_path):
    with pytest.raises(FileNotFoundError, match="04_features"):
        load_folds(tmp_path / "no_existe.csv")


def test_fold_indices_returns_validation_rows_of_each_fold():
    train = make_train_rows()
    folds = make_folds(train)
    pairs = fold_indices(train, folds)
    assert len(pairs) == 5
    seen = np.concatenate([valid for _, valid in pairs])
    assert sorted(seen) == list(range(len(train)))  # cada fila se valida exactamente una vez
    for fit, valid in pairs:
        assert set(train.iloc[fit]["host_id"]).isdisjoint(set(train.iloc[valid]["host_id"]))


def test_fold_indices_exact_fails_if_ids_differ():
    train = make_train_rows()
    folds = make_folds(train)
    with pytest.raises(ValueError, match="no coinciden"):
        fold_indices(train.iloc[5:], folds)  # faltan anuncios
    with pytest.raises(ValueError, match="no coinciden"):
        fold_indices(train, folds.iloc[5:])  # sobran anuncios en el entrenamiento


def test_fold_indices_subset_uses_the_same_folds():
    train = make_train_rows()
    folds = make_folds(train)
    subset = train.iloc[10:40].reset_index(drop=True)
    pairs = fold_indices(subset, folds, exact=False)
    fold_of = subset[["id"]].merge(folds, on="id")["fold"].to_numpy()
    for k, (_, valid) in enumerate(pairs):
        assert (fold_of[valid] == k).all()  # cada anuncio conserva su pliegue
    with pytest.raises(ValueError, match="no están en la asignación"):
        fold_indices(subset, folds.iloc[15:], exact=False)


def test_reserve_hosts_has_no_shared_hosts_and_loses_no_rows():
    train = make_train_rows(n_hosts=40)
    search, reserved = reserve_hosts(train)
    assert set(search["host_id"]).isdisjoint(set(reserved["host_id"]))
    assert len(search) + len(reserved) == len(train)
    assert reserved["host_id"].nunique() == 10  # 25 % de 40 anfitriones


def test_fold_indices_fails_if_a_fold_is_missing():
    train = make_train_rows()
    folds = make_folds(train)
    two_folds = train[train["id"].isin(folds.loc[folds["fold"] < 2, "id"])]
    with pytest.raises(ValueError, match="pliegue"):
        fold_indices(two_folds, folds, exact=False)


def test_reserve_hosts_fails_with_missing_host_id():
    train = make_train_rows()
    train.loc[0, "host_id"] = np.nan
    with pytest.raises(ValueError, match="host_id"):
        reserve_hosts(train)
