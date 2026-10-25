# Local verification

Verified on 2026-10-25 with the project's configured Python 3.12.13 interpreter.

- The current suite of **38 unit and local HTTP integration tests** passed: `python -m unittest discover -s tests -v`. This includes the regression checks added for the expanded campus directory.
- In Edge, opened the real local application at `http://127.0.0.1:8000`.
- In the initial eight-place version, verified the live OpenStreetMap basemap, fictional demo pins, category filtering and event detail popups.
- Used the application's sample PNG to verify image preview, manual upload, review, building selection, local saving and persistence after page reload.
- Verified that saved fictional events do not appear as real campus events. Removed the single agent-created QA event after checking.
- Verified that choosing a building after entering invalid manual coordinates disables the unused coordinate fields.
- Verified that clicking a campus building while picking a map point returns the coordinates to the review form.
- After the user configured the API key locally, two live requests to `gemma-4-26b-a4b-it` successfully processed the original `campus-creators.png` fixture. The key was not included in this report.
- The first response omitted the weekday-only `date_text`. The extraction prompt was updated to preserve a weekday even when no calendar date is supplied. A second live request correctly returned `Campus Creators Meetup`, `Friday`, `4:00–6:00 PM`, and `Price Center — West Ballroom`, with `West Ballroom` as the room, `CampusLens Demo` as the organizer, and `social` as the category. Warnings correctly noted the missing exact calendar date, year, and time zone. The review form identified the fixture as a fictional demo.
- All 29 local unit and HTTP integration tests passed again after the date-prompt update. This fixture check does not establish general inference accuracy for other posters.
- Saved the live extraction with `is_demo=true`, confirmed its Price Center map marker, then reloaded the browser. `Friday`, `4:00–6:00 PM`, the venue and room persisted. The real-events view stayed empty; the saved fictional event appeared only in the demo view. Matching built-in samples are suppressed so the saved sample does not appear twice.
- After being asked to select the JPG manually and verify its flow, the user reported that verification was complete. The JPG manual check is therefore recorded as user-confirmed; the agent did not automatically perform or independently repeat that browser step.
- The browser's earlier permission request for automatic local JPG file selection was cancelled. No alternate automatic upload path was used to bypass that decision; the subsequent manual check was performed by the user.
- The agent has not separately tested real-model inference on the missing-location fixture.

## Campus directory expansion

The directory was subsequently expanded from eight to **622 application locations**: 621 GIS-backed entries representing 622 active official building points, plus the retained Student Center complex entry. The original eight application IDs remain valid, and 614 new IDs were added. The Price Center West and East Expansion source points share the existing Price Center application entry.

The snapshot covers latitude 32.84–32.91 and longitude −117.27–−117.20. It includes additional teaching, residential, coastal, medical, recreation, and support buildings. Source provenance and alias policies are documented in [venue-sources.md](venue-sources.md). These are building or venue-area points, not verified room locations or guarantees of public access.

The expanded interface displayed the 622-location total. Browser checks confirmed that exact `CENTR` search returned only Center Hall, and exact `CSE` search returned only Computer Science and Engineering Building. Changing the building search cleared the previous location-confirmation checkbox. Searches with no matches showed the no-result prompt, and the manual location option still allowed coordinates. No test events were saved and no model API requests were made during this expansion check. All 38 local tests passed again after the directory and matching changes.

The initial eight-place checks above do not imply that every imported location was individually inspected on the map. Expansion screenshot: [622 campus locations and building search](screenshots/expanded-campus-places.jpg).

Preview screenshot: [CampusLens demo map](screenshots/campuslens-preview.jpg).

Live Gemma extraction saved on the map: [Verified PNG result](screenshots/gemma-live-preview.jpg).

The app currently runs on this computer only. Public hosting and hackathon submission have not been performed.
