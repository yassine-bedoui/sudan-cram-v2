import psycopg2

conn = psycopg2.connect(
    "postgresql://sudan_cram_user:0iUMUWn4LLMvzyYxMu1ZB7Ry8n8nPSH7@dpg-d453f2euk2gs73fs5lgg-a.oregon-postgres.render.com/sudan_cram_db"
)
cursor = conn.cursor()

cursor.execute("SELECT COUNT(*) FROM gdelt_events WHERE event_date >= NOW() - INTERVAL '90 days'")
print(f"GDELT events: {cursor.fetchone()[0]}")

cursor.execute("SELECT COUNT(*) FROM acled_events WHERE event_date >= NOW() - INTERVAL '90 days'")
print(f"ACLED events: {cursor.fetchone()[0]}")

conn.close()