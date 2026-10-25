# CampusLens — MLH submission draft

下面的英文内容可直接用于 MLH 表单。提交前核对队员及所选奖项；源码仓库链接已填入，当前应用只在本机运行，尚未公开托管。所有自带样例海报与 Demo 活动均为虚构。

## Project title

CampusLens

## One-line pitch

Turn campus event posters into reviewable event pins with Gemma 4 image understanding and an interactive campus map.

## Project description — Markdown

以下代码框内为可复制的项目介绍，涵盖已实现功能及限制。

```markdown
### The problem

Campus events are often shared as image posters. Students have to read each image, find the event details, and work out where the venue is. Useful information stays scattered across posters instead of appearing together on a map.

### What CampusLens does

CampusLens turns JPG and PNG posters into editable event details and campus map pins. A user uploads a poster, requests AI extraction, reviews the result, confirms a campus building or picks a map point, and saves the event. Clicking a pin shows the event details and poster. Events and uploaded images persist locally, and the map supports category filtering.

Fictional demo events are clearly labeled and kept out of the real-events view. All supplied sample posters are original, fictional fixtures marked “SAMPLE / FICTIONAL EVENT.”

### Why Gemma 4 is important

Gemma 4 reads the poster image and extracts the title, date and time text, venue, room, organizer, category, and description. Our application uses the hosted `gemma-4-26b-a4b-it` model through the Gemini API. This image-to-event conversion is the central AI step in the project.

The extraction prompt asks Gemma to preserve incomplete date information and flag missing dates, years, or time zones. People review the model's output before saving an event. Building coordinates come from a 622-location campus directory, primarily based on UC San Diego's official public GIS, or from a user-selected map point; we do not ask the model to invent coordinates. Users can search building names, aliases, and addresses before confirming a location.

### What we built

- A poster upload and review flow for JPG and PNG images.
- A Python backend that validates images and calls Gemma 4 through the Gemini REST API.
- Editable event fields, searchable campus building matching, and manual map-point selection.
- A 622-location campus directory with official GIS sources, building aliases, and street addresses.
- An interactive UC San Diego campus map with event markers, category filters, and detail popups.
- Local SQLite persistence and local uploaded-image storage.
- Persistent Demo labels and separate real-event and demo views.
- Original sample posters, setup documentation, and local unit and HTTP integration tests.

### Architecture

The browser interface uses HTML, CSS, JavaScript, Leaflet, and an OpenStreetMap basemap. A local Python HTTP server handles image processing, model requests, event validation, and storage. Pillow processes images, python-dotenv loads local configuration, and SQLite stores events. The API key stays in server-side local configuration rather than browser code.

### Validation and current limits

Thirty-eight local unit and HTTP integration tests passed, including regressions for the expanded campus directory. Browser checks confirmed the 622-location total, exact building-alias search, location confirmation reset after search changes, no-result handling, and manual coordinates. We verified live PNG extraction with Gemma 4, and the project owner confirmed the manual JPG check. The extracted PNG event was saved to the map and persisted after page reload. The extraction preserves weekday-only dates and flags missing calendar dates, years, and time zones.

The prototype runs locally. Its location snapshot covers named active building points within the application's UCSD area, including the central campus, residential colleges, Scripps coastal facilities, east-campus and medical buildings. It does not establish that every building is an event venue or publicly accessible. Pins indicate building or venue-area locations, and users review extracted details and coordinates before saving. Rooms and precise meeting points need separate confirmation. Live model checks have focused on the supplied complete event poster; broader poster coverage remains future validation work. AI extraction and the basemap require network access. Images requested for AI analysis are sent to Google's API.

### Open source and licenses

The original application code, documentation, and fictional sample posters are provided under the MIT License. We call a hosted Gemma 4 model and do not distribute model weights. Gemma 4's model license is Apache 2.0; the API, map resources, and university source data remain subject to their own terms. Model, API, map, dependency, and campus GIS references are linked in the README and venue-source documentation.
```

## Technologies used

Python, HTML, CSS, JavaScript, Leaflet, OpenStreetMap, SQLite, Pillow, python-dotenv, Gemini API, Gemma 4 (`gemma-4-26b-a4b-it`).

## AI models and development tools

| Form question | Suggested answer |
| --- | --- |
| AI that the application calls | Gemma 4 (`gemma-4-26b-a4b-it`), hosted through the Gemini API; used for poster image understanding and event-information extraction. |
| AI coding tool used during development | OpenAI Codex; assisted with implementation, debugging, tests, and documentation. |
| Exact coding-assistant model, if requested | Fill in the model actually shown in the development session if known. Do not enter Gemma 4 here merely because the application calls it. |

如实区分“应用调用的模型”和“帮助开发的工具”。不要将手动录入或预置 Demo 内容描述为真实 AI 识别。

## Challenges to select

These are the intended challenge selections; confirm the final event form wording before submission:

- **Best Open-Source AI Project** — Gemma 4 is central to the application. Publish the GitHub source repository with the MIT license, README, and model-license references before submitting.
- **Best Use of Gemma 4** — the application uses Gemma 4 image understanding to extract event details from posters.

## Links to fill in

| Form field | What to enter |
| --- | --- |
| Source code / repository URL | https://github.com/Wenbo-Bob-Li/campuslens |
| Optional live demo URL | Leave blank unless a working public deployment is created. `http://127.0.0.1:8000` only works on the local computer and is not a public demo link. |
| Optional video or slides URL | Leave blank until the actual artifact is uploaded and its reviewable link is available. |

源码仓库为 [Wenbo-Bob-Li/campuslens](https://github.com/Wenbo-Bob-Li/campuslens)；最终 MLH 提交仍需完成，线上部署为可选。

## 90-second demo sequence

| Time | Action | Suggested narration |
| --- | --- | --- |
| 0:00–0:15 | Open the map and start uploading `campus-creators.png`. | “CampusLens turns image posters into events you can review on a campus map. This is an original fictional poster, created for the demo.” |
| 0:15–0:40 | Request the live extraction, then show the returned event fields. | “Gemma 4 reads the image. We preserve Friday and the stated time, while missing calendar dates, years, and time zones stay unknown. The user can correct the result.” |
| 0:40–1:00 | Confirm Price Center, keep the fictional Demo label, and save. | “The app matches the venue to a campus building. The room remains in the event text, and the user confirms the location.” |
| 1:00–1:20 | In Demo map, click the saved pin, then reload and open it again. | “The event appears with its poster and details. SQLite and local image storage preserve it after a reload.” |
| 1:20–1:30 | Show the real-events view and return to Demo map. | “Fictional samples are separated from real events. This local prototype combines Gemma 4 image understanding, human review, and a campus map.” |

现场 API 延迟会改变节奏；提前实测。若实时调用失败，说明故障后展示已保存的 Demo 结果或手动录入，并明确这是备用演示，不能称为本次实时识别成功。若播放录像，明确说明是此前录制。所有自带样例均为虚构活动。
