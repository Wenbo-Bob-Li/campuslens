# UC San Diego venue directory

`data/venues.json` contains **622 campus locations and 2,086 aliases**, expanded on 2026-10-25 from UC San Diego's public campus GIS. It covers named active building points within the application's UCSD area: latitude **32.84–32.91**, longitude **−117.27–−117.20**. This includes the central teaching campus, residential colleges, Scripps coastal facilities, east-campus and medical buildings, recreation facilities, and campus support buildings. It does not assert that every record is an event venue or publicly accessible.

Markers identify a **building or venue area**, not an indoor room, an entrance, an accessible route, or a surveyed meeting point. `precision: "building"` is the application's common location label; Epstein Family Amphitheater is an outdoor venue and Student Center is a building complex. Users must still confirm the correct building and keep the room or meeting-point details from their poster.

## Official GIS source

- [UC San Diego: Campus Map Vector — all layers](https://admin-enterprise-gis.ucsd.edu/server/rest/services/BaseData/Campus_Map_Vector/MapServer/layers)
- [Building Points Public, layer 26](https://admin-enterprise-gis.ucsd.edu/server/rest/services/BaseData/Campus_Map_Vector/MapServer/26)
- [Documented, read-only Query operation](https://admin-enterprise-gis.ucsd.edu/server/rest/services/BaseData/Campus_Map_Vector/MapServer/26/query)

The layer publishes point geometry and these public attributes: `OBJECTID`, `FacilityLongName`, `BuildingAliases`, `StreetAddress`, `City`, `Zipcode`, `FacilityStatus`, `Longitude`, and `Latitude`. No login, token, private fields, or model API call was used. The layer allows up to 2,000 records per query and supports pagination. The downloaded snapshot returned **752 records**, below that limit, with no exceeded-transfer-limit flag. Exactly **622** had a nonempty name, `FacilityStatus = Active`, and coordinates inside the bounds above; there were no duplicate source names or identical coordinate pairs in that subset.

The source query was:

```text
https://admin-enterprise-gis.ucsd.edu/server/rest/services/BaseData/Campus_Map_Vector/MapServer/26/query
  ?where=1%3D1
  &outFields=OBJECTID%2CFacilityLongName%2CBuildingAliases%2CStreetAddress%2CCity%2CZipcode%2CFacilityStatus%2CLongitude%2CLatitude
  &returnGeometry=false
  &resultRecordCount=2000
  &orderByFields=OBJECTID
  &f=pjson
```

Line breaks are shown for readability; join the lines into one URL to repeat it. If a future snapshot exceeds 2,000 records, follow the layer's documented pagination instead of assuming a single response is complete.

Coordinates use the published **Latitude/Longitude attributes directly**, not the layer's Web Mercator geometry or a geocoded address. The stored decimal places are copied from the official data and do not imply equivalent positional accuracy. No physical or survey verification has been performed.

Each imported record links to a read-only **single-object GIS query** through `source_url`. `source_id` stores that snapshot's `OBJECTID`, `address` stores the published street address, and `facility_status` records the published status. New application IDs use `ucsd-<OBJECTID>`; existing IDs below remain unchanged. After publication, application IDs should be retained even if a GIS service republishes or renumbers its object IDs.

## Preserving existing locations and merging duplicates

The application previously shipped eight locations. Their IDs remain unchanged so saved events keep their references. Their known aliases are also retained, while seven locations now use the official GIS coordinates. Price Center is represented once as the existing complex-level venue; its West and East Expansion source records are merged into that entry.

| Existing application ID | Official GIS object IDs | Current treatment |
| --- | --- | --- |
| `price-center` | 1960, 2267 | Combines Price Center West and Price Center East Expansion. Uses the West point as the representative complex marker. `source_id` is 1960 and `source_ids` preserves both IDs. West/East ballrooms and The Loft remain aliases. |
| `geisel-library` | 1814 | Replaces the original calendar map center with the GIS building point. |
| `design-and-innovation-building` | 5082 | Uses the GIS building point; DIB, The Basement and DIB Makerspace aliases remain. |
| `rimac` | 1961 | Uses the GIS building point; official GIS alias LionTree Arena is included. |
| `epstein-family-amphitheater` | 1692 | Uses the official GIS venue point. |
| `conrad-prebys-music-center` | 2287 | Uses the GIS building point; performance-room aliases remain. |
| `atkinson-hall` | 2121 | Uses the GIS building point; Qualcomm Institute aliases remain. |
| `student-center` | Not merged | Retains the existing official-calendar complex-level point and source. The GIS has multiple named Student Center sub-buildings rather than one equivalent complex record, so those sub-buildings remain independently selectable. |

The final catalog therefore has **621 GIS-backed entries representing 622 GIS source points**, plus **one existing Student Center complex entry**, for **622 application locations**. There are 614 new application IDs. Apart from the explicit Price Center merge, adjacent official building points are not collapsed by distance or shared address.

The remaining Student Center coordinate, **32.877097, −117.239402**, comes from [UC San Diego Events Calendar: UNO Social](https://calendar.ucsd.edu/event/uno-social), where the published `Event Location Map` embed center is associated with Student Center at 9360 Eucalyptus Grove Lane. This is a published map/address approximation. The event specifies The Stage Room; the application marker remains at complex level. Student Center and Student Services Center are different places.

## Aliases and ambiguity

GIS `BuildingAliases` values are split on `|`, trimmed, and deduplicated without regard to case. The import excludes:

- Empty strings, purely numeric aliases, and one-character aliases.
- Generic standalone labels such as `Building`, `Hall`, `Center`, `Library`, `College`, `Campus`, `UCSD`, `Room`, `Auditorium`, `Main Campus`, and cardinal directions.
- Bare numbered/lettered building labels such as `Building A` and `Building 1`, and unqualified `North Tower`/`South Tower` labels, which recur across complexes.
- Standalone college or area names such as `Muir`, `Revelle`, `Warren`, `ERC`, and `SIO`, which do not identify one building.
- Alias fragments containing `...` or an ellipsis. Ten source records have visibly truncated alias strings; complete earlier segments are retained and the truncated fragment is discarded.

Whole names such as `Muir College Commons`, `Student Center A - Building H`, and `Warren Lecture Hall` remain useful specific aliases. A college name alone does not acquire a fabricated coordinate at one of its buildings.

The only exact shared alias remaining after normalization is **`GSA, Student Center A`**:

| Application ID | Official name |
| --- | --- |
| `ucsd-1990` | Student Center A - Building ES |
| `ucsd-1988` | Student Center A - Building H |

That alias requires the user to choose a building. A longer explicit building name should take precedence over a name nested inside it; for example, `RIMAC Annex` should identify the Annex, and `Student Center A - Building H` should identify that sub-building. Independent mentions of multiple buildings remain ambiguous. Matching must not silently select the first candidate.

## Common new locations

| Application ID | Official name | Selected aliases |
| --- | --- | --- |
| `ucsd-1760` | Center Hall | CENTR |
| `ucsd-1737` | Biology Building | M2B; Muir Biology Building; Muir Biology |
| `ucsd-2037` | Warren Lecture Hall | WLH |
| `ucsd-2122` | Computer Science and Engineering Building | CSE; CSE Building; EBU-3B; EBU3B |
| `ucsd-2415` | Franklin Antonio Hall | Interdisciplinary Engineering Building |
| `ucsd-2431` | Mayer Hall | Mayer Hall |
| `ucsd-3324` | Urey Hall | Urey Hall |
| `ucsd-2039` | York Hall | Undergraduate Sciences Building |
| `ucsd-1953` | Peterson Hall | Robert O. Peterson Hall |
| `ucsd-2166` | Sally T. WongAvery Library | WongAvery Library; BSB Addition |
| `ucsd-2098` | Great Hall | ERC Great Hall; Roosevelt College, Great Hall |
| `ucsd-2343` | Structural and Materials Engineering Building | SME |
| `ucsd-5083` | Jacobs Hall | EBU-1; EBU1; Engineering Building Unit I |

The only new manually shortened alias is **Muir Biology**, derived from the GIS's explicit `Muir Biology Building` alias. The original eight entries retain their earlier convenience and room aliases. Most new aliases are copied directly from the GIS and may include historical names supplied by the university.

## Original venue-page references

These official pages support the retained room and complex aliases. Their embedded map API keys are not copied into this project.

- [University Centers: Price Center directory](https://universitycenters.ucsd.edu/visit/directory.html) identifies the West/East ballrooms, Price Center Theater, and The Loft (level 2, room 2633).
- [DIB: Take a Tour](https://dib.ucsd.edu/about/tour.html) identifies DIB, The Basement on floor 1, and the Makerspace.
- [UC San Diego Recreation: facilities](https://recreation.ucsd.edu/facilities/) and [LionTree Arena](https://recreation.ucsd.edu/facilities/liontree-arena/) describe the RIMAC complex and arena.
- [Conrad Prebys Music Center](https://calendar.ucsd.edu/conrad-prebys-music-center) identifies the building and its performance spaces.
- [Qualcomm Institute: Contact & Directions](https://qi.ucsd.edu/contact/) identifies Atkinson Hall as its location.

## Snapshot checks and maintenance

The resulting JSON was decoded and checked for unique IDs/names, valid bounds, nonempty usable aliases, and source coverage. It has **no duplicate application IDs, duplicate names, or identical coordinate pairs**. Its UTF-8 snapshot size is **513,575 bytes** (PowerShell's formatted JSON with a UTF-8 BOM); the application reads UTF-8 with BOM support. The temporary downloaded public-field source snapshot is **667,519 bytes** and is not required at runtime.

To update the catalog, repeat the documented public query, check transfer limits and statuses, apply the same geographic filter and alias policy, and preserve the stable application IDs and explicit merges above. A new or ambiguous poster location should remain unresolved until the user selects a building or places a manual point. The model must never invent latitude or longitude.
