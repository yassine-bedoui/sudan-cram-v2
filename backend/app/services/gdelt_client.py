# backend/app/services/gdelt_client.py

from __future__ import annotations

import csv
import io
import logging
import os
import zipfile
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Dict, Iterable, List, Optional

import requests

logger = logging.getLogger(__name__)


class GDELTApiError(RuntimeError):
    """Raised when a GDELT file or response cannot be fetched or parsed."""
    pass


@dataclass
class GDELTEventRecord:
    """
    Lightweight parsed GDELT event for downstream ETL into Postgres.

    This is aligned with your SQLAlchemy model app/models/gdelt.py:

        class GDELTEvent(Base):
            __tablename__ = "gdelt_events"

            id = Column(Integer, primary_key=True, index=True)
            event_id = Column(String(50), unique=True, nullable=False)
            event_date = Column(DateTime, nullable=False, index=True)

            region = Column(String(100), index=True)
            latitude = Column(Float)
            longitude = Column(Float)

            event_code = Column(String(10))
            quad_class = Column(Integer)

            actor1_name = Column(String(200))
            actor2_name = Column(String(200))

            goldstein_scale = Column(Float)
            avg_tone = Column(Float)
    """

    event_id: str
    event_date: datetime
    region: str
    latitude: Optional[float]
    longitude: Optional[float]
    event_code: Optional[str]
    quad_class: Optional[int]
    actor1_name: Optional[str]
    actor2_name: Optional[str]
    goldstein_scale: Optional[float]
    avg_tone: Optional[float]

    # Optional: keep raw row for debugging
    raw: Optional[Dict[str, str]] = None


class GDELTClient:
    """
    Client for the GDELT 2.0 Events 15-minute stream.

    There is no API key: you fetch zipped TSV files from:

        http://data.gdeltproject.org/gdeltv2/YYYYMMDDHHMM00.export.CSV.zip

    Each file contains all events observed in that 15 minute window.

    This client:
      - Builds the correct filenames for a datetime window
      - Downloads & decompresses each file
      - Parses TSV rows into GDELTEventRecord objects
      - Filters events by ActionGeo_CountryCode (e.g. "SU" = Sudan)
    """

    # Base URL for GDELT v2 event stream
    BASE_URL = os.getenv("GDELT_BASE_URL", "http://data.gdeltproject.org/gdeltv2")

    # Default country filter using FIPS / CAMEO country code for Sudan
    DEFAULT_COUNTRY_CODE = os.getenv("GDELT_SUDAN_COUNTRY_CODE", "SU")

    # Column indices for GDELT 2.0 Event table (0-based)
    # (From GDELT 2.0 Event Database schema)
    IDX_GLOBALEVENTID = 0
    IDX_SQLDATE = 1           # YYYYMMDD (int)
    IDX_ACTOR1NAME = 6
    IDX_ACTOR2NAME = 16
    IDX_EVENTCODE = 26
    IDX_QUADCLASS = 29
    IDX_GOLDSTEIN = 30
    IDX_NUM_MENTIONS = 31
    IDX_AVGTONE = 34

    # Geolocation (ActionGeo_*) – where the event takes place
    IDX_ACTIONGEO_FULLNAME = 52
    IDX_ACTIONGEO_COUNTRYCODE = 53
    IDX_ACTIONGEO_ADM1CODE = 54
    IDX_ACTIONGEO_LAT = 56
    IDX_ACTIONGEO_LONG = 57

    # DATEADDED and SOURCEURL (not currently used, but left here for context)
    # IDX_DATEADDED = 59
    # IDX_SOURCEURL = 60

    def __init__(self, session: Optional[requests.Session] = None) -> None:
        self.session = session or requests.Session()

    # ------------------------------------------------------------------ #
    # Helpers for time windows                                           #
    # ------------------------------------------------------------------ #

    @staticmethod
    def _to_utc(dt: datetime) -> datetime:
        """Ensure a datetime is timezone-aware in UTC."""
        if dt.tzinfo is None:
            return dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc)

    @staticmethod
    def _round_down_to_quarter_hour(dt: datetime) -> datetime:
        """
        Round a datetime down to the nearest 15-minute boundary.

        E.g. 12:07 -> 12:00, 12:29 -> 12:15, 12:44 -> 12:30, 12:59 -> 12:45
        """
        dt = dt.replace(second=0, microsecond=0)
        minute_block = (dt.minute // 15) * 15
        return dt.replace(minute=minute_block)

    @staticmethod
    def _round_up_to_quarter_hour(dt: datetime) -> datetime:
        """
        Round a datetime up to the next 15-minute boundary (inclusive).

        E.g. 12:07 -> 12:15, 12:29 -> 12:30, 12:44 -> 12:45, 12:59 -> 13:00
        """
        dt = dt.replace(second=0, microsecond=0)
        minute_block = ((dt.minute + 14) // 15) * 15
        if minute_block == 60:
            return (dt.replace(minute=0) + timedelta(hours=1))
        return dt.replace(minute=minute_block)

    def _iter_quarter_hours(self, start: datetime, end: datetime) -> Iterable[datetime]:
        """
        Yield all 15-minute timestamps between [start, end], inclusive,
        rounded to quarter-hour boundaries in UTC.
        """
        start_utc = self._to_utc(start)
        end_utc = self._to_utc(end)

        t = self._round_down_to_quarter_hour(start_utc)
        end_rounded = self._round_up_to_quarter_hour(end_utc)

        while t <= end_rounded:
            yield t
            t += timedelta(minutes=15)

    # ------------------------------------------------------------------ #
    # Low-level download + parse                                         #
    # ------------------------------------------------------------------ #

    def _build_export_filename(self, dt: datetime) -> str:
        """
        Construct the GDELT 2.0 export filename for a UTC datetime.

        Pattern (no auth, public):

            YYYYMMDDHHMM00.export.CSV.zip

        Example:
            2024-05-01 12:30 UTC -> "20240501123000.export.CSV.zip"
        """
        dt_utc = self._to_utc(dt)
        return dt_utc.strftime("%Y%m%d%H%M00.export.CSV.zip")

    def _download_export_file(self, dt: datetime) -> Optional[bytes]:
        """
        Download a single 15-minute export ZIP file, if it exists.

        Returns:
            Raw bytes of the ZIP file, or None if the file is missing (404).

        Raises:
            GDELTApiError on other non-200 responses.
        """
        filename = self._build_export_filename(dt)
        url = f"{self.BASE_URL}/{filename}"

        logger.info(f"🔎 Fetching GDELT export: {url}")
        resp = self.session.get(url, timeout=60)

        if resp.status_code == 404:
            # No file for this window – normal when backfilling older ranges
            logger.debug(f"GDELT export not found for {dt} (404).")
            return None

        if resp.status_code != 200:
            body = resp.text[:200].replace("\n", " ")
            logger.warning(
                "⚠️ GDELT non-200 response\n"
                f"   URL:    {url}\n"
                f"   Status: {resp.status_code}\n"
                f"   Body:   {body}..."
            )
            raise GDELTApiError(
                f"GDELT export fetch failed ({resp.status_code}) for {url}"
            )

        return resp.content

    def _parse_export_zip(
        self,
        content: bytes,
        country_code: str,
        start: datetime,
        end: datetime,
    ) -> List[GDELTEventRecord]:
        """
        Parse a GDELT 2.0 export ZIP and return filtered GDELTEventRecord objects.

        Filters:
          - ActionGeo_CountryCode == country_code
          - SQLDATE between start.date() and end.date() (inclusive)
        """
        events: List[GDELTEventRecord] = []

        try:
            with zipfile.ZipFile(io.BytesIO(content)) as zf:
                names = zf.namelist()
                if not names:
                    logger.warning("Empty GDELT ZIP (no files inside).")
                    return events

                # Each export ZIP should contain a single TSV file.
                inner_name = names[0]
                with zf.open(inner_name) as f:
                    # GDELT uses tab-separated values, no header row.
                    text_stream = io.TextIOWrapper(
                        f,
                        encoding="utf-8",
                        errors="replace",
                    )
                    reader = csv.reader(text_stream, delimiter="\t")

                    for row in reader:
                        # Defensive: make sure we have enough columns
                        if len(row) <= self.IDX_ACTIONGEO_LONG:
                            continue

                        try:
                            rec = self._row_to_event_record(
                                row=row,
                                country_code=country_code,
                                start=start,
                                end=end,
                            )
                        except Exception as e:
                            # Skip malformed rows but log once in a while
                            logger.debug(
                                f"Skipping malformed GDELT row (len={len(row)}): {e}"
                            )
                            continue

                        if rec is not None:
                            events.append(rec)

        except zipfile.BadZipFile as e:
            raise GDELTApiError(f"Failed to read GDELT ZIP: {e}") from e

        return events

    def _row_to_event_record(
        self,
        row: List[str],
        country_code: str,
        start: datetime,
        end: datetime,
    ) -> Optional[GDELTEventRecord]:
        """
        Convert a raw GDELT row (list of strings) into a GDELTEventRecord.

        Returns None if:
          - Country does not match ActionGeo_CountryCode
          - SQLDATE falls outside [start.date(), end.date()]
        """
        # Filter by ActionGeo_CountryCode – e.g. "SU" for Sudan
        action_country = row[self.IDX_ACTIONGEO_COUNTRYCODE].strip()
        if not action_country or action_country.upper() != country_code.upper():
            return None

        # Parse SQLDATE (YYYYMMDD) into a datetime
        sql_date_str = row[self.IDX_SQLDATE]
        try:
            event_date = datetime.strptime(sql_date_str, "%Y%m%d").replace(
                tzinfo=timezone.utc
            )
        except ValueError:
            # If SQLDATE is malformed, drop the row
            return None

        # Filter by date range
        if event_date.date() < start.date() or event_date.date() > end.date():
            return None

        # Map fields – we use GlobalEventID as stable event_id
        global_event_id = row[self.IDX_GLOBALEVENTID].strip()
        if not global_event_id:
            return None
        event_id = f"gdelt-{global_event_id}"

        # Geolocation: use ActionGeo_FullName as region, lat/long as floats
        region = row[self.IDX_ACTIONGEO_FULLNAME].strip()
        lat_str = row[self.IDX_ACTIONGEO_LAT].strip()
        lon_str = row[self.IDX_ACTIONGEO_LONG].strip()

        try:
            latitude = float(lat_str) if lat_str else None
        except ValueError:
            latitude = None

        try:
            longitude = float(lon_str) if lon_str else None
        except ValueError:
            longitude = None

        # Other fields
        event_code = row[self.IDX_EVENTCODE].strip() or None
        quad_class_str = row[self.IDX_QUADCLASS].strip()
        goldstein_str = row[self.IDX_GOLDSTEIN].strip()
        avg_tone_str = row[self.IDX_AVGTONE].strip()

        try:
            quad_class = int(quad_class_str) if quad_class_str else None
        except ValueError:
            quad_class = None

        try:
            goldstein_scale = float(goldstein_str) if goldstein_str else None
        except ValueError:
            goldstein_scale = None

        try:
            avg_tone = float(avg_tone_str) if avg_tone_str else None
        except ValueError:
            avg_tone = None

        actor1_name = row[self.IDX_ACTOR1NAME].strip() or None
        actor2_name = row[self.IDX_ACTOR2NAME].strip() or None

        # Optionally keep raw row in a dict for debugging
        raw = {
            "GlobalEventID": global_event_id,
            "SQLDATE": sql_date_str,
            "Actor1Name": actor1_name,
            "Actor2Name": actor2_name,
            "EventCode": event_code,
            "QuadClass": quad_class_str,
            "GoldsteinScale": goldstein_str,
            "AvgTone": avg_tone_str,
            "ActionGeo_FullName": region,
            "ActionGeo_CountryCode": action_country,
            "ActionGeo_Lat": lat_str,
            "ActionGeo_Long": lon_str,
        }

        return GDELTEventRecord(
            event_id=event_id,
            event_date=event_date,
            region=region,
            latitude=latitude,
            longitude=longitude,
            event_code=event_code,
            quad_class=quad_class,
            actor1_name=actor1_name,
            actor2_name=actor2_name,
            goldstein_scale=goldstein_scale,
            avg_tone=avg_tone,
            raw=raw,
        )

    # ------------------------------------------------------------------ #
    # Public API                                                         #
    # ------------------------------------------------------------------ #

    def fetch_events_for_window(
        self,
        start: datetime,
        end: datetime,
        country_code: Optional[str] = None,
    ) -> List[GDELTEventRecord]:
        """
        Fetch GDELT events for a given datetime window and country.

        Args:
            start: Start datetime (naive or timezone-aware). Treated as UTC if naive.
            end:   End datetime (inclusive, naive or tz-aware).
            country_code: ActionGeo_CountryCode to filter on (default "SU" for Sudan).

        Returns:
            List of GDELTEventRecord objects.

        Usage example:

            from datetime import datetime, timedelta, timezone
            client = GDELTClient()
            end = datetime.now(timezone.utc)
            start = end - timedelta(days=1)
            events = client.fetch_events_for_window(start, end)
        """
        if country_code is None:
            country_code = self.DEFAULT_COUNTRY_CODE

        start_utc = self._to_utc(start)
        end_utc = self._to_utc(end)

        logger.info("============================================================")
        logger.info(" GDELT EVENTS FETCH")
        logger.info("============================================================")
        logger.info(f" Country     : {country_code}")
        logger.info(f" Date range  : {start_utc.isoformat()} -> {end_utc.isoformat()}")
        logger.info("============================================================")

        all_events: List[GDELTEventRecord] = []

        for ts in self._iter_quarter_hours(start_utc, end_utc):
            try:
                content = self._download_export_file(ts)
            except GDELTApiError as e:
                # Log and continue – better partial coverage than a hard crash
                logger.warning(f"⚠️ Skipping 15-min window {ts} due to error: {e}")
                continue

            if not content:
                # No file for this interval – nothing to parse
                continue

            window_events = self._parse_export_zip(
                content=content,
                country_code=country_code,
                start=start_utc,
                end=end_utc,
            )

            if window_events:
                logger.info(
                    f"  ✓ {len(window_events)} events for {ts.strftime('%Y-%m-%d %H:%M')}"
                )

            all_events.extend(window_events)

        logger.info("------------------------------------------------------------")
        logger.info(f" Total GDELT events fetched: {len(all_events)}")
        logger.info("============================================================")

        return all_events
