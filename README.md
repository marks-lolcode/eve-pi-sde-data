# eve-pi-sde-data

Automated re-hosting of the PI-relevant slice of [EVE Online's official Static Data Export](https://developers.eveonline.com/static-data).

CCP publishes the SDE as a ~94MB zip per game build. Google Apps Script's `UrlFetchApp` caps responses at ~50MB, so the [EVE PI Manager v2](https://github.com) spreadsheet can't fetch it directly. A scheduled GitHub Actions workflow here downloads the zip, filters a handful of tables to compact English-only JSON, and commits them to `sde/`:

| File | Contents |
|---|---|
| `sde/meta.json` | `{buildNumber, refreshedAt}` — freshness check |
| `sde/types.json` | typeID, name, groupID, volume, published, portionSize, metaGroupID |
| `sde/groups.json` | groupID, categoryID, name, published |
| `sde/categories.json` | categoryID, name, published |
| `sde/planetSchematics.json` | schematicID, name, cycleTime, pins[] (runnable facility typeIDs), types[] (inputs/output with quantities) |
| `sde/typeMaterials.json` | typeID, materialTypeID, quantity — one row per material: what one batch of a type reprocesses into, before any yield multiplier |
| `sde/planets.json` | planetID, solarSystemID, celestialIndex (planet number), radius (metres), typeID — every planet in New Eden |
| `sde/solarSystems.json` | solarSystemID, name (incl. J###### wormhole designations) — lets the PI Manager join a planet's radius by (system name, planet number) |

Planet `radius` lets the PI Manager scale factory templates to each planet's diameter: link power-cost rises with the surface distance between pins, so the same layout fits fewer factories on a larger planet. The planet/solar-system JSONL file names vary across SDE builds; the workflow auto-detects them and logs a raw sample line for schema verification.

`typeMaterials.json` quantities are stated **per `portionSize` batch**, which is why `portionSize`
sits on the type row rather than here — the two are only meaningful together, and a partial batch
reprocesses to nothing. Neither number has any yield, skill or station tax applied; that is the
consumer's job.

`metaGroupID` is the tech tier: 1 Tech I, 2 Tech II, 3 Storyline, 4 Faction, 5 Officer,
6 Deadspace, 14 Tech III. Most types (ore, minerals, blueprints, anything that is not a module or
hull) carry no metaGroupID at all and are emitted as **1** — for a consumer reasoning in tiers,
"no tier" and "Tech I" are the same answer. The workflow guard therefore counts types **above**
Tech I, not types with any value: a renamed field would default the whole column to 1, pass a
naive non-zero check, and silently tell every consumer that nothing in EVE is Tech II.

Fetch via `https://raw.githubusercontent.com/<owner>/eve-pi-sde-data/main/sde/<file>.json`.

All game data © CCP hf., redistributed per the [Developer License Agreement](https://developers.eveonline.com/license-agreement).
