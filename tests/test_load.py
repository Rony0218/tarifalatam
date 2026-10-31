import pytest

from fixtures import make_train_rows
from tarifalatam.data.load import load_train


def test_load_train_reads_the_65_columns(tmp_path):
    path = tmp_path / "train.csv.gz"
    make_train_rows().to_csv(path, index=False)
    train = load_train(path)
    assert train.shape == (60, 65)
    assert train["id"].is_unique


def test_load_train_fails_on_missing_or_extra_columns(tmp_path):
    path = tmp_path / "train.csv.gz"
    make_train_rows().drop(columns=["accommodates"]).assign(columna_nueva=1).to_csv(path, index=False)
    with pytest.raises(ValueError, match="accommodates") as error:
        load_train(path)
    assert "columna_nueva" in str(error.value)


def test_load_train_fails_if_the_file_is_missing(tmp_path):
    with pytest.raises(FileNotFoundError, match="03_preprocesamiento"):
        load_train(tmp_path / "no_existe.csv.gz")
