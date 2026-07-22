# eve-pi-sde-data

Automated re-hosting of the PI-relevant slice of [EVE Online's official Static Data Export](https://developers.eveonline.com/static-data).

CCP publishes the SDE as a ~94MB zip per game build. Google Apps Script's `UrlFetchApp` caps responses at ~50MB, so the [EVE PI Manager v2](https://github.com) spreadsheet can't fetch it directly. A scheduled GitHub Actions workflow here downloads the zip, filters four tables to compact English-only JSON (~4MB total), and commits them to `sde/`:

| File | Contents |
|---|---|
| `sde/meta.json` | `{buildNumber, refreshedAt}` — freshness check |
| `sde/types.json` | typeID, name, groupID, volume, published |
| `sde/groups.json` | groupID, categoryID, name, published |
| `sde/categories.json` | categoryID, name, published |
| `sde/planetSchematics.json` | schematicID, name, cycleTime, pins[] (runnable facility typeIDs), types[] (inputs/output with quantities) |
| `sde/planets.json` | planetID, solarSystemID, celestialIndex (planet number), radius (metres), typeID — every planet in New Eden |
| `sde/solarSystems.json` | solarSystemID, name (incl. J###### wormhole designations) — lets the PI Manager join a planet's radius by (system name, planet number) |

Planet `radius` lets the PI Manager scale factory templates to each planet's diameter: link power-cost rises with the surface distance between pins, so the same layout fits fewer factories on a larger planet. The planet/solar-system JSONL file names vary across SDE builds; the workflow auto-detects them and logs a raw sample line for schema verification.

Fetch via `https://raw.githubusercontent.com/<owner>/eve-pi-sde-data/main/sde/<file>.json`.

All game data © CCP hf., redistributed per the [Developer License Agreement](https://developers.eveonline.com/license-agreement).
