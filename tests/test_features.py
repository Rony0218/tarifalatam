import json

import numpy as np
import pandas as pd
import pytest

from tarifalatam.features.engineering import (
    AmenityFeatures,
    CapacityRatios,
    CityCenterDistance,
    HostProfile,
    RareCategoryGrouper,
    SuspiciousFeatures,
)


def _same_as_before(original: pd.DataFrame, copy: pd.DataFrame) -> bool:
    return original.equals(copy)


# --- RareCategoryGrouper (decisión 11 del EDA) ---------------------------------------------------------------


def test_rare_category_grouper_learns_frequent_categories_only_in_fit():
    fit_data = pd.DataFrame({"barrio": ["A"] * 3 + ["B"] * 2 + ["C"]})
    grouper = RareCategoryGrouper(min_count=2).fit(fit_data)
    # en datos nuevos C sigue siendo rara aunque ahora aparezca muchas veces: lo frecuente se aprendió en fit
    new = pd.DataFrame({"barrio": ["A", "B", "C", "C", "C"]})
    assert grouper.transform(new)["barrio"].tolist() == ["A", "B", "Other", "Other", "Other"]


def test_rare_category_grouper_sends_unknown_and_missing_to_other():
    grouper = RareCategoryGrouper(min_count=1).fit(pd.DataFrame({"barrio": ["A", "B"]}))
    new = pd.DataFrame({"barrio": ["A", "Z", np.nan]})
    assert grouper.transform(new)["barrio"].tolist() == ["A", "Other", "Other"]


def test_rare_category_grouper_does_not_modify_the_input():
    data = pd.DataFrame({"barrio": ["A", "A", "B"]})
    before = data.copy()
    RareCategoryGrouper(min_count=2).fit(data).transform(data)
    assert _same_as_before(before, data)


# --- Idea 1: CityCenterDistance --------------------------------------------------------------------------------


def _cities() -> pd.DataFrame:
    return pd.DataFrame(
        {"city": ["x", "x", "x", "y"], "latitude": [10.0, 10.0, 10.0, -5.0], "longitude": [20.0, 20.0, 20.0, 30.0]}
    )


def test_city_center_distance_one_degree_of_latitude_is_about_111_km():
    model = CityCenterDistance().fit(_cities())  # centro de x = (10, 20)
    new = pd.DataFrame({"city": ["x"], "latitude": [11.0], "longitude": [20.0]})
    assert model.transform(new)["distance_to_center_km"].iloc[0] == pytest.approx(111.19, abs=0.01)


def test_city_center_distance_uses_the_centers_seen_in_fit():
    model = CityCenterDistance().fit(_cities())
    far = pd.DataFrame({"city": ["x"] * 3, "latitude": [50.0] * 3, "longitude": [20.0] * 3})
    # transformar datos lejanos no mueve el centro: el anuncio en (10, 20) sigue a 0 km
    model.transform(far)
    at_center = pd.DataFrame({"city": ["x"], "latitude": [10.0], "longitude": [20.0]})
    assert model.transform(at_center)["distance_to_center_km"].iloc[0] == pytest.approx(0.0)


def test_city_center_distance_unseen_city_is_missing():
    model = CityCenterDistance().fit(_cities())
    new = pd.DataFrame({"city": ["z"], "latitude": [0.0], "longitude": [0.0]})
    assert np.isnan(model.transform(new)["distance_to_center_km"].iloc[0])


def test_city_center_distance_does_not_modify_the_input():
    data = _cities()
    before = data.copy()
    CityCenterDistance().fit(data).transform(data)
    assert _same_as_before(before, data)


# --- Idea 2: AmenityFeatures -----------------------------------------------------------------------------------


def _amenities(*lists) -> pd.DataFrame:
    return pd.DataFrame({"amenities": [item if isinstance(item, str) else json.dumps(item) for item in lists]})


def test_amenity_features_empty_list_counts_zero():
    out = AmenityFeatures().fit_transform(_amenities([]))
    assert out["amenities_count"].iloc[0] == 0
    assert (out[["amenity_pool", "amenity_gym", "amenity_hot_tub"]].iloc[0] == 0).all()


def test_amenity_features_uses_exact_names_only():
    out = AmenityFeatures().fit_transform(_amenities(["Pool table", "Wifi"], ["Pool", "Air conditioning"]))
    assert out["amenity_pool"].tolist() == [0, 1]  # "Pool table" es una mesa de billar, no una piscina
    assert out["amenity_air_conditioning"].tolist() == [0, 1]
    assert out["amenities_count"].tolist() == [2, 2]


def test_amenity_features_unreadable_text_is_missing():
    out = AmenityFeatures().fit_transform(_amenities("esto no es una lista", '{"a": 1}'))
    assert out["amenities_count"].isna().all()
    assert out["amenity_pool"].isna().all()


def test_amenity_features_does_not_modify_the_input():
    data = _amenities(["Pool"])
    before = data.copy()
    AmenityFeatures().fit_transform(data)
    assert _same_as_before(before, data)


# --- Idea 3: CapacityRatios ------------------------------------------------------------------------------------


def test_capacity_ratios_hand_case_and_zero_divisions():
    data = pd.DataFrame(
        {
            "accommodates": [4, 2, 0, 3],
            "bedrooms": [2.0, 0.0, 1.0, np.nan],  # 0 habitaciones = estudio (cuenta como 1)
            "bathrooms_count": [2.0, 0.0, 1.0, 1.0],  # 0 baños -> vacío
            "beds": [2.0, 1.0, 1.0, np.nan],
        }
    )
    out = CapacityRatios().fit_transform(data)
    assert out["people_per_bedroom"].tolist()[:3] == [2.0, 2.0, 0.0]
    assert np.isnan(out["people_per_bedroom"].iloc[3])  # falta bedrooms
    assert out["people_per_bathroom"].iloc[0] == 2.0
    assert np.isnan(out["people_per_bathroom"].iloc[1])
    assert out["beds_per_person"].iloc[0] == 0.5
    assert np.isnan(out["beds_per_person"].iloc[2])  # accommodates = 0
    assert np.isnan(out["beds_per_person"].iloc[3])  # falta beds


def test_capacity_ratios_does_not_modify_the_input():
    data = pd.DataFrame({"accommodates": [2], "bedrooms": [1.0], "bathrooms_count": [1.0], "beds": [1.0]})
    before = data.copy()
    CapacityRatios().fit_transform(data)
    assert _same_as_before(before, data)


# --- Idea 4: HostProfile ---------------------------------------------------------------------------------------


def _hosts() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "hosts_time_as_host_years": [2.0, 0.0, np.nan],
            "hosts_time_as_host_months": [6.0, 3.0, 1.0],
            "hosts_time_as_user_years": [5.0, 1.0, 1.0],
            "hosts_time_as_user_months": [0.0, 6.0, 0.0],
            "host_has_profile_pic": ["t", "f", "x"],
            "host_identity_verified": ["f", "t", np.nan],
        }
    )


def test_host_profile_tenure_and_true_false():
    out = HostProfile().fit_transform(_hosts())
    assert out["host_tenure_years"].tolist()[:2] == [2.5, 0.25]
    assert np.isnan(out["host_tenure_years"].iloc[2])  # falta uno de los dos
    assert out["user_tenure_years"].tolist() == [5.0, 1.5, 1.0]
    assert out["host_has_profile_pic"].tolist()[:2] == [1.0, 0.0]
    assert np.isnan(out["host_has_profile_pic"].iloc[2])  # otro valor -> vacío
    assert out["host_identity_verified"].tolist()[:2] == [0.0, 1.0]
    assert np.isnan(out["host_identity_verified"].iloc[2])


def test_host_profile_does_not_modify_the_input():
    data = _hosts()
    before = data.copy()
    HostProfile().fit_transform(data)
    assert _same_as_before(before, data)


# --- Medición con sospechosas: SuspiciousFeatures --------------------------------------------------------------


def _reviews() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "last_scraped": ["2026-09-22", "2026-09-22"],
            "first_review": ["2026-09-12", np.nan],
            "last_review": ["2026-09-20", np.nan],
            "has_availability": ["t", "f"],
            "host_is_superhost": ["f", "t"],
        }
    )


def test_suspicious_features_days_until_the_cut():
    out = SuspiciousFeatures().fit_transform(_reviews())
    assert out["days_since_first_review"].iloc[0] == 10
    assert out["days_since_last_review"].iloc[0] == 2
    assert np.isnan(out["days_since_first_review"].iloc[1])  # sin reseñas
    assert out["has_availability"].tolist() == [1.0, 0.0]
    assert out["host_is_superhost"].tolist() == [0.0, 1.0]


def test_suspicious_features_does_not_modify_the_input():
    data = _reviews()
    before = data.copy()
    SuspiciousFeatures().fit_transform(data)
    assert _same_as_before(before, data)
