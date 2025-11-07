export const regionNameMapping: Record<string, string> = {
  'Abyei PCA': 'Abyei',
  'Gezira': 'Al Jazirah',  // ← THE KEY FIX!
  'Blue Nile': 'Blue Nile',
  'Central Darfur': 'Central Darfur',
  'East Darfur': 'East Darfur',
  'Gedaref': 'Gedaref',
  'Kassala': 'Kassala',
  'Khartoum': 'Khartoum',
  'North Darfur': 'North Darfur',
  'North Kordofan': 'North Kordofan',
  'Northern': 'Northern',
  'Red Sea': 'Red Sea',
  'River Nile': 'River Nile',
  'Sennar': 'Sennar',
  'South Darfur': 'South Darfur',
  'South Kordofan': 'South Kordofan',
  'West Darfur': 'West Darfur',
  'West Kordofan': 'West Kordofan',
  'White Nile': 'White Nile',
}

export function normalizeRegionName(geoJsonName: string): string {
  return regionNameMapping[geoJsonName] || geoJsonName
}
