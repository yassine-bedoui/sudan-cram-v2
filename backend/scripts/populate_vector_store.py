from datetime import datetime, timedelta
import os

from backend.app.services.vector_store import VectorStore
from backend.app.models.gdelt import GDELTEvent
from backend.app.models.acled import ACLEDEvent
from backend.database import SessionLocal
from backend.app.config.countries import get_country_config


def populate(country_iso3: str | None = None) -> None:
    """
    Populate the vector store for a single country.

    Country is chosen by (in order of precedence):
      - function argument `country_iso3`
      - VECTOR_COUNTRY_ISO3 env var
      - default: "SDN"
    """
    if country_iso3 is None:
        country_iso3 = os.getenv("VECTOR_COUNTRY_ISO3", "SDN")

    country_iso3 = (country_iso3 or "SDN").upper()
    cfg = get_country_config(country_iso3)

    print("=" * 60)
    print(f"CRAM - Vector Store Population ({cfg.iso3})")
    print("=" * 60)

    db = SessionLocal()
    vs = VectorStore()

    cutoff = datetime.now() - timedelta(days=90)
    print(f"\n📅 Fetching events since: {cutoff.strftime('%Y-%m-%d')}")
    print(f"🌍 Country: {cfg.iso3} ({getattr(cfg, 'name', cfg.iso3)})\n")

    # ---------------- GDELT ----------------
    print("🔍 Processing GDELT events...")
    gdelt_events = (
        db.query(GDELTEvent)
        .filter(
            GDELTEvent.country_iso3 == cfg.iso3,
            GDELTEvent.event_date >= cutoff,
        )
        .order_by(GDELTEvent.event_date.desc())
        .all()
    )

    gdelt_added = 0
    for event in gdelt_events:
        text = f"{event.actor1_name} {event.event_code} against {event.actor2_name} in {event.region}"

        if vs.add_event(
            event_id=f"gdelt-{event.id}",
            text=text,
            metadata={
                "source": "GDELT",
                "country_iso3": cfg.iso3,
                "country_name": getattr(cfg, "name", cfg.iso3),
                "db_id": event.id,
                "db_event_id": event.event_id,
                "region": event.region,
                "date": event.event_date.isoformat(),
                "actors": [event.actor1_name, event.actor2_name],
                "event_type": event.event_code,
            },
        ):
            gdelt_added += 1
            if gdelt_added and gdelt_added % 100 == 0:
                print(f"  ✓ {gdelt_added} GDELT events indexed")

    # ---------------- ACLED ----------------
    print("\n🔍 Processing ACLED events...")
    acled_events = (
        db.query(ACLEDEvent)
        .filter(
            ACLEDEvent.country_iso3 == cfg.iso3,
            ACLEDEvent.event_date >= cutoff.date(),
        )
        .order_by(ACLEDEvent.event_date.desc())
        .all()
    )

    acled_added = 0
    for event in acled_events:
        text = (
            f"{event.event_type}: {event.actor1} vs {event.actor2} "
            f"in {event.region}, {event.fatalities} fatalities"
        )

        if vs.add_event(
            event_id=f"acled-{event.id}",
            text=text,
            metadata={
                "source": "ACLED",
                "country_iso3": cfg.iso3,
                "country_name": getattr(cfg, "name", cfg.iso3),
                "db_id": event.id,
                "db_event_id": event.event_id,
                "region": event.region,
                "date": event.event_date.isoformat(),
                "actors": [event.actor1, event.actor2],
                "event_type": event.event_type,
                "fatalities": event.fatalities,
            },
        ):
            acled_added += 1
            if acled_added and acled_added % 50 == 0:
                print(f"  ✓ {acled_added} ACLED events indexed")

    print("\n" + "=" * 60)
    print("✅ COMPLETE")
    print(
        f"   GDELT: {gdelt_added} | ACLED: {acled_added} | Total: {gdelt_added + acled_added}"
    )
    print(f"   Vector Store Count: {vs.get_event_count()}")
    print(f"   Country: {cfg.iso3}")
    print("=" * 60)

    db.close()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Populate the vector store from GDELT + ACLED events."
    )
    parser.add_argument(
        "--country",
        "-c",
        help="ISO3 country code (e.g. SDN, SOM). Overrides VECTOR_COUNTRY_ISO3.",
    )
    args = parser.parse_args()

    iso3 = (args.country or os.getenv("VECTOR_COUNTRY_ISO3", "SDN")).upper()
    populate(country_iso3=iso3)
