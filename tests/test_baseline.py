import numpy as np
import pandas as pd

from tarifalatam.models import baseline
from tarifalatam.models.baseline import MedianBaseline, baseline_cv_mae


def _train() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "city": ["belize", "belize", "belize", "rio-de-janeiro", "rio-de-janeiro"],
            "room_type": ["Entire home/apt", "Entire home/apt", "Private room", "Entire home/apt", "Entire home/apt"],
            "price_usd": [100.0, 300.0, 50.0, 80.0, 120.0],
        }
    )


def _hosts_panel(n_hosts: int = 50, per_host: int = 2) -> pd.DataFrame:
    rng = np.random.default_rng(0)
    return pd.DataFrame(
        {
            "host_id": np.repeat(np.arange(n_hosts), per_host),
            "city": "belize",
            "room_type": "Entire home/apt",
            "price_usd": rng.normal(100, 5, n_hosts * per_host).round(2),
        }
    )


def test_median_baseline_by_city_and_room_type():
    model = MedianBaseline().fit(_train())
    new = pd.DataFrame({"city": ["belize", "belize", "rio-de-janeiro"],
                        "room_type": ["Entire home/apt", "Private room", "Entire home/apt"]})
    assert model.predict(new).tolist() == [200.0, 50.0, 100.0]


def test_median_baseline_falls_back_to_city_median():
    model = MedianBaseline().fit(_train())
    new = pd.DataFrame({"city": ["rio-de-janeiro"], "room_type": ["Hotel room"]})
    assert model.predict(new).tolist() == [100.0]  # combinación no vista: mediana de Río


def test_baseline_cv_mae_fits_only_on_train_folds(monkeypatch):
    """En cada pliegue, los anfitriones con que se ajusta no son los que se evalúan."""
    calls = []
    original_fit, original_predict = MedianBaseline.fit, MedianBaseline.predict

    def spy_fit(self, df):
        calls.append(("fit", set(df["host_id"])))
        return original_fit(self, df)

    def spy_predict(self, df):
        calls.append(("predict", set(df["host_id"])))
        return original_predict(self, df)

    monkeypatch.setattr(baseline.MedianBaseline, "fit", spy_fit)
    monkeypatch.setattr(baseline.MedianBaseline, "predict", spy_predict)
    result = baseline_cv_mae(_hosts_panel(), n_splits=5)

    assert len(result["per_fold"]) == 5
    assert [kind for kind, _ in calls] == ["fit", "predict"] * 5
    for (_, fit_hosts), (_, valid_hosts) in zip(calls[::2], calls[1::2]):
        assert fit_hosts.isdisjoint(valid_hosts)
    assert np.isclose(result["mean"], np.mean(result["per_fold"]))
