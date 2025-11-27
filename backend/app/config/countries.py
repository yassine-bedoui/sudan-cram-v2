# backend/app/config/countries.py

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Optional
import os


@dataclass(frozen=True)
class CountryConfig:
    iso3: str
    name: str

    # ACLED filters
    acled_country_name: str      # 👈 name matches script usage
    acled_iso3: str

    # Geo/admin1
    admin1_geojson: str
    admin1_name_field: str

    # GDELT filters (FIPS / ActionGeo_CountryCode, e.g. "SU" for Sudan, "SO" for Somalia)
    gdelt_country_code: Optional[str] = None

    # DTM / IPC / IDMC
    dtm_country_name: Optional[str] = None
    ipc_country_code: Optional[str] = None
    idmc_iso3: Optional[str] = None
    idmc_country_name: Optional[str] = None

    # WaPOR (optional)
    wapor_rain_collection: Optional[str] = None
    wapor_rain_measure: Optional[str] = None
    wapor_rain_time_dimension: Optional[str] = None

    # Optional convenience alias (in case you ever call .acled_country)
    @property
    def acled_country(self) -> str:
        return self.acled_country_name


def _sdn_from_env() -> CountryConfig:
    """Sudan defaults + env overrides."""
    return CountryConfig(
        iso3="SDN",
        name="Sudan",
        acled_country_name="Sudan",
        acled_iso3="SDN",
        admin1_geojson=os.getenv(
            "SUDAN_ADMIN1_GEOJSON",
            "backend/data/geo/sudan_admin1.geojson",
        ),
        admin1_name_field=os.getenv("SUDAN_ADMIN1_NAME_FIELD", "shapeName"),

        # GDELT: FIPS/ActionGeo country code for Sudan
        gdelt_country_code=os.getenv("SUDAN_GDELT_COUNTRY_CODE", "SU"),

        dtm_country_name=os.getenv("DTM_COUNTRY_NAME", "Sudan"),
        ipc_country_code=os.getenv("IPC_COUNTRY_CODE", "SDN"),
        idmc_iso3=os.getenv("IDMC_COUNTRY_ISO3", "SDN"),
        idmc_country_name=os.getenv("IDMC_COUNTRY_NAME", "Sudan"),
        wapor_rain_collection=os.getenv("WAPOR_RAIN_COLLECTION"),
        wapor_rain_measure=os.getenv("WAPOR_RAIN_MEASURE"),
        wapor_rain_time_dimension=os.getenv("WAPOR_RAIN_TIME_DIMENSION"),
    )


def _som_from_env() -> CountryConfig:
    """Somalia defaults + env overrides."""
    return CountryConfig(
        iso3="SOM",
        name="Somalia",
        acled_country_name="Somalia",
        acled_iso3="SOM",
        admin1_geojson=os.getenv(
            "SOMALIA_ADMIN1_GEOJSON",
            "backend/data/geo/som_admin1.geojson",
        ),
        admin1_name_field=os.getenv("SOMALIA_ADMIN1_NAME_FIELD", "adm1_name"),

        # GDELT: FIPS/ActionGeo country code for Somalia
        gdelt_country_code=os.getenv("SOMALIA_GDELT_COUNTRY_CODE", "SO"),

        dtm_country_name=os.getenv("SOMALIA_DTM_COUNTRY_NAME", "Somalia"),
        ipc_country_code="SOM",
        idmc_iso3="SOM",
        idmc_country_name="Somalia",
        wapor_rain_collection=os.getenv(
            "SOMALIA_WAPOR_RAIN_COLLECTION",
            os.getenv("WAPOR_RAIN_COLLECTION"),
        ),
        wapor_rain_measure=os.getenv(
            "SOMALIA_WAPOR_RAIN_MEASURE",
            os.getenv("WAPOR_RAIN_MEASURE"),
        ),
        wapor_rain_time_dimension=os.getenv(
            "SOMALIA_WAPOR_RAIN_TIME_DIMENSION",
            os.getenv("WAPOR_RAIN_TIME_DIMENSION"),
        ),
    )


_COUNTRY_CONFIGS: Dict[str, CountryConfig] = {
    "SDN": _sdn_from_env(),
    "SOM": _som_from_env(),
}


def get_country_config(code: str) -> CountryConfig:
    """
    Look up a CountryConfig by ISO3 code (e.g. 'SDN', 'SOM').
    """
    if not code:
        raise ValueError("country_iso3 is required")

    iso3 = code.upper()
    try:
        return _COUNTRY_CONFIGS[iso3]
    except KeyError:
        supported = ", ".join(sorted(_COUNTRY_CONFIGS.keys()))
        raise ValueError(f"Unsupported country code '{code}'. Supported: {supported}")
