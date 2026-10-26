# CampusLens｜Turn campus posters into events on the map

Seen an event poster but unsure when it starts or where to meet? CampusLens reads event details from JPG/PNG posters, lets you review the information and choose a campus building, then places the event on a UC San Diego map.

**Upload a poster → Review the details → Confirm the location → Save to the map**

[Project repository](https://github.com/Wenbo-Bob-Li/campuslens) · [Location data sources](docs/venue-sources.md)

![CampusLens campus map with 622 campus locations](docs/screenshots/expanded-campus-map.jpg)

## What you can do

- **Read event posters**: Use Gemma 4 to extract the name, date, time, location, room, organizer, and event description, and edit the details before saving.
- **Find campus buildings**: Search 622 campus locations and 2,086 names and aliases, or look up a street address.
- **Set a location manually**: Choose a meeting point on the campus map when no suitable building is listed.
- **Browse added events**: Search by keyword, filter by category, and click map markers to view details and posters.
- **Keep your event records**: Events and images are saved locally and remain available after you close and restart the app.

The current version runs on your own computer and is accessed through a browser. The map shows the events you add; on your first visit, you can explore fictional samples or add your first poster.

## Installation and startup

You need **Python 3.11 or later**, a browser, and an internet connection that can access the map basemap and Google's model service. Automatic extraction also requires your own Gemini API key; if you do not have one yet, you can explore samples or enter details manually.

### 1. Download the project

On the [GitHub repository](https://github.com/Wenbo-Bob-Li/campuslens), click **Code → Download ZIP** and extract it to your computer. Open a terminal in the folder containing `app.py` and `requirements.txt`.

### 2. Install dependencies and start the app

**Windows (PowerShell):**

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe app.py
```

**macOS / Linux:**

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python app.py
```

Once the startup address appears, open **<http://127.0.0.1:8000>** in your browser. Keep the terminal running while using the app; press `Ctrl+C` in the terminal when you are finished.

Dependencies only need to be installed once. Next time, enter the same project folder and run the last startup command shown above.

### 3. Enable automatic poster extraction

1. Open [Google AI Studio](https://aistudio.google.com/app/apikey) and create your own Gemini API key.
2. In the project folder, copy `.env.example` to `.env`. If `.env` already exists, edit it directly without overwriting your existing configuration.
3. Open `.env` in a text editor and replace the placeholder below with your own key:

```dotenv
GEMINI_API_KEY=your_api_key_here
GEMMA_MODEL=gemma-4-26b-a4b-it
```

4. Save the file, then click **How it works → Refresh status** in the app. Once **Gemma ready** appears, you can try analyzing a poster.

The app reloads the local configuration, so changing your key does not require a restart. The default model is `gemma-4-26b-a4b-it`; your account must have access to that model to use it. For service availability and quotas, see [Google's official documentation](https://ai.google.dev/gemma/docs/core/gemma_on_gemini_api).

`.env` contains private local configuration. Do not upload it to GitHub or put your key in browser-side code.

## Add an event

### Upload and analyze

1. Click **Add a poster**.
2. Drag in or select a JPG, JPEG, or PNG poster, up to **10 MB** per image. Use a complete, correctly oriented static image with clear text whenever possible.
3. Check the preview, click **Analyze poster**, and wait for extraction to finish.

If you do not have a poster, click **Use a sample poster**; to fill in the information yourself, click **Enter details manually**.

### Review the details and location

Check the event name, date, time, and organizer, and correct them to match the poster. If the poster only gives a weekday or does not specify a year or time zone, preserve that uncertainty.

Enter a building name, abbreviation, or address in **Find a campus building**, then select the building from the **Campus building** dropdown. For example:

| Name or abbreviation to enter | Corresponding building |
| --- | --- |
| `CENTR` | Center Hall |
| `WLH` | Warren Lecture Hall |
| `CSE` | Computer Science and Engineering Building |
| `DIB` | Design and Innovation Building |
| `Geisel` | Geisel Library |

Enter the room number or meeting point in **Room or meeting point**. If the location is not in the directory, select **Choose a point on the map…** from the building dropdown, then click **Pick on map** to choose a location. You can also enter latitude and longitude within the campus area.

If you are using a fictional poster, check **This is a sample or fictional event**. Finally, confirm the details and location, check the confirmation box, and click **Add event to map**.

### View it on the map

After saving, the map centers on the event. Click an event card or map marker to view its time, building, room, description, and poster; if you entered a valid event link, you can also open it from the details.

Use the search box on the left to find added events and the category buttons to filter them. Fictional samples appear only in the sample view; on your first visit, click **Explore sample events** to enter it, and click **Exit** to return to the real-events view.

## Location coverage and accuracy

The built-in directory covers UC San Diego's central campus, residential colleges, Scripps coastal facilities, east campus, and some medical, sports, and support buildings, primarily using the university's official public GIS data. For full sources, see the [location documentation](docs/venue-sources.md).

Map markers indicate a **building or venue area**. Confirm the room, exact entrance, and specific meeting point using the event information. A building's inclusion in the directory does not mean it is open to the public or permits events; follow the organizer's information.

## Data and privacy

- When you click **Analyze poster**, the poster image is sent to Google's model API for extraction; make sure the image content is suitable for sending to that service.
- Your API key is read by the local backend and stored in your own `.env` file.
- Saved events and images are stored in the project's `runtime/` folder. To keep your records, back up this folder when moving or downloading the project again; backups may contain private images and should be kept securely.
- In the current version, records remain on the computer running the service. They do not automatically sync to other devices, and saving them to the map does not publish them publicly.

## Frequently asked questions

**What if the page will not open?**

Make sure the service is still running in your terminal and open the address shown there. Do not open `static/index.html` directly by double-clicking it.

**What if port 8000 is already in use?**

Choose a different port at startup. For example, on Windows, run:

```powershell
.\.venv\Scripts\python.exe app.py --port 8001
```

Then open <http://127.0.0.1:8001>. On macOS / Linux, use `.venv/bin/python app.py --port 8001`.

**What if extraction still fails after I enter my key?**

Make sure the file is named `.env`, not `.env.txt`, and is in the same folder as `app.py`. Save it, then click **How it works → Refresh status**. If the page reports a permissions, quota, or network error, check your Google account and connection as indicated; you can also enter event details manually for now.

**What if the map is blank or the basemap fails to load?**

Check whether your connection can access the OpenStreetMap basemap. If the basemap fails to load, you can still view the event list and enter information; confirm the location by selecting a known building or entering coordinates.

**What if I cannot find a building, or there are multiple candidate locations?**

Try the full building name, another abbreviation, or an address, and check the buildings in the dropdown. You need to confirm the correct location when there are multiple candidates; if you still cannot find it, place a point on the map manually.

**Why is the event I just saved missing from the real-events list?**

If you checked the fictional sample option, the event is saved in the sample view. Check which view you are in, and clear any search terms or category filters that may be hiding the event.

## License and further information

CampusLens's original code, documentation, and included fictional samples are provided under the [MIT License](LICENSE). Models and APIs, maps, campus data, and user-uploaded images are subject to their respective licenses or terms of use.

- [Gemma model and API documentation](https://ai.google.dev/gemma/docs/core/gemma_on_gemini_api)
- [Leaflet license](static/vendor/leaflet-LICENSE.txt)
- [OpenStreetMap data and attribution](https://www.openstreetmap.org/copyright)
- [Campus location sources](docs/venue-sources.md)
- [Project verification records](docs/verification.md)

If you encounter a problem, describe the steps you took and the page's messages in [GitHub Issues](https://github.com/Wenbo-Bob-Li/campuslens/issues); remove API keys and any private information in the poster before sharing.
