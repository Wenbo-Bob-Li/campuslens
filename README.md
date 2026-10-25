# CampusLens \| Turn Campus Posters into Map-Based Events

Have you ever seen an event poster but weren't sure when the event
starts or where to meet? CampusLens extracts event information from
JPG/PNG posters, lets you review the details and choose a campus
building, and then places the event on the UC San Diego map.

**Upload a poster → Review the details → Confirm the location → Save to
the map**

[Project Repository](https://github.com/Wenbo-Bob-Li/campuslens) ·
[Venue Data Sources](docs/venue-sources.md)

![CampusLens campus map showing 622 campus
locations](docs/screenshots/expanded-campus-map.jpg)

## What You Can Do with CampusLens

-   **Extract information from event posters**: Use Gemma 4 to extract
    the event name, date, time, location, room, organizer, and
    description. You can edit the details before saving.
-   **Find campus buildings**: Search 622 campus locations and 2,086
    names and aliases, or search by address.
-   **Choose a location manually**: If no suitable building is
    available, select a meeting point directly on the campus map.
-   **Browse added events**: Search by keyword, filter by category, and
    click map markers to view event details and posters.
-   **Keep your own event records**: Events and images are stored
    locally and remain available when you restart the app.

The current version runs on your own computer and is accessed through a
browser. The map displays the events you add. When using the app for the
first time, you can explore fictional sample events or add your first
poster.

## Installation and Launch

You need **Python 3.11 or later**, a browser, and an internet connection
that can access the map tiles and Google's model service. Automatic
poster recognition also requires your own Gemini API key. If you don't
have a key yet, you can explore the samples or enter event details
manually.

### 1. Download the Project

Open the [GitHub
repository](https://github.com/Wenbo-Bob-Li/campuslens), click **Code →
Download ZIP**, and extract the archive to your computer. Open a
terminal in the folder containing `app.py` and `requirements.txt`.

### 2. Install Dependencies and Launch

**Windows (PowerShell):**

``` powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe app.py
```

**macOS / Linux:**

``` bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python app.py
```

When the terminal displays the server address, open
**<http://127.0.0.1:8000>** in your browser. Keep the terminal running
while you use the app. To stop the app, press `Ctrl+C` in the terminal.

You only need to install the dependencies once. The next time you use
CampusLens, open the same project folder and run the final launch
command for your operating system.

### 3. Enable Automatic Poster Recognition

1.  Open [Google AI Studio](https://aistudio.google.com/app/apikey) and
    create your own Gemini API key.
2.  In the project folder, copy `.env.example` and name the copy `.env`.
    If a `.env` file already exists, edit it directly rather than
    overwriting the existing configuration.
3.  Open `.env` in a text editor and replace the placeholder values
    below with your own key:

``` dotenv
GEMINI_API_KEY=your_api_key_here
GEMMA_MODEL=gemma-4-26b-a4b-it
```

4.  Save the file, then click **How it works → Refresh status** in the
    app. When the status shows **Gemma ready**, you can try analyzing a
    poster.

The app reloads the local configuration, so you don't need to restart it
after changing the API key. The default model is `gemma-4-26b-a4b-it`.
Your account must have access to the selected model to use it. For
service availability and quota information, see [Google's official
documentation](https://ai.google.dev/gemma/docs/core/gemma_on_gemini_api).

The `.env` file contains private local configuration. Do not upload it
to GitHub or put your API key in the web page's code.

## Add an Event

### Upload and Analyze a Poster

1.  Click **Add a poster**.
2.  Drag in or select a JPG, JPEG, or PNG poster. Each file must be no
    larger than **10 MB**. For best results, use a static image with
    clear, complete text and the correct orientation.
3.  Review the preview and click **Analyze poster**, then wait for the
    analysis to finish.

If you don't have a poster, click **Use a sample poster**. To enter the
information yourself, click **Enter details manually**.

### Review the Details and Confirm the Location

Review the event name, date, time, and organizer, and correct them to
match the original poster. If the poster gives only a day of the week
and does not specify a year or time zone, preserve that uncertainty
rather than guessing.

Under **Find a campus building**, enter a building name, abbreviation,
or address, then choose a building from the **Campus building**
dropdown. For example:

  Name or abbreviation   Building
  ---------------------- -------------------------------------------
  `CENTR`                Center Hall
  `WLH`                  Warren Lecture Hall
  `CSE`                  Computer Science and Engineering Building
  `DIB`                  Design and Innovation Building
  `Geisel`               Geisel Library

Enter the room number or meeting point under **Room or meeting point**.
If the location is not in the directory, select **Choose a point on the
map...** from the building dropdown, then click **Pick on map** to
select a location. You can also enter latitude and longitude within the
campus area.

If you're using a fictional poster, check **This is a sample or
fictional event**. Finally, verify the event details and location, check
the confirmation box, and click **Add event to map**.

### View the Event on the Map

After saving, the map will focus on the event. Click the event card or
map marker to view the time, building, room, description, and poster. If
you entered a valid event link, you can also open it from the event
details.

Use the search box on the left to find events you've added, and use the
category buttons to filter them. Fictional samples appear only in the
sample view. The first time you use the app, click **Explore sample
events** to open that view, then click **Exit** to return to the
real-event view.

## Venue Coverage and Location Accuracy

The built-in directory covers UC San Diego's central campus, residential
colleges, Scripps coastal facilities, East Campus, and some medical,
sports, and support buildings. It primarily uses publicly available
official university GIS data. See the [venue
documentation](docs/venue-sources.md) for the complete list of sources.

Map markers indicate a **building or site area**. Check the event
description to confirm the room, exact entrance, or specific meeting
point. A building's presence in the directory does not mean it is open
to the public or available for events; follow the organizer's
information.

## Data and Privacy

-   When you click **Analyze poster**, the poster image is sent to
    Google's model API for recognition. Make sure the image content is
    appropriate to share with that service.
-   The local backend reads your API key from your `.env` file.
-   Saved events and images are stored in the project's `runtime/`
    folder. To keep your records when moving or downloading the project
    again, back up this folder as well. Backups may contain private
    images, so store them carefully.
-   In the current version, records are stored on the computer running
    the service. They are not automatically synced to other devices, and
    saving an event to the map does not publish it publicly.

## Frequently Asked Questions

**What should I do if the page won't open?**

Make sure the service is still running in the terminal, then open the
address displayed there. Do not open `static/index.html` by
double-clicking it.

**What should I do if port 8000 is already in use?**

Start the app on a different port. For example, on Windows, run:

``` powershell
.\.venv\Scripts\python.exe app.py --port 8001
```

Then open <http://127.0.0.1:8001>. On macOS or Linux, use
`.venv/bin/python app.py --port 8001`.

**I've entered my API key, but poster recognition still doesn't work.
What should I do?**

Make sure the file is named `.env`, not `.env.txt`, and is in the same
directory as `app.py`. After saving it, click **How it works → Refresh
status**. If you see a permissions, quota, or network error, follow the
message on the page to check your Google account and network connection.
You can also enter event details manually.

**What should I do if the map is blank or the basemap fails to load?**

Check whether your network can access the OpenStreetMap basemap. If the
basemap fails to load, you can still view the event list and enter
information. Confirm the location by selecting a known building or
entering coordinates.

**What if I can't find a building or see multiple candidate locations?**

Try the full building name, another abbreviation, or an address, and
verify the building selected in the dropdown. If multiple candidates
appear, confirm the correct one yourself. If you still can't find it,
place a marker manually on the map.

**Why isn't an event I just saved showing up in the real-event list?**

If you checked the fictional-sample option, the event is stored in the
sample view. Check which view you're in, and clear any search terms or
category filters that may be hiding the event.

## License and More Information

CampusLens's original code, documentation, and included fictional
samples are provided under the [MIT License](LICENSE). Models and APIs,
map services, campus data, and user-uploaded images are subject to their
respective licenses or terms of use.

-   [Gemma Model and API
    Documentation](https://ai.google.dev/gemma/docs/core/gemma_on_gemini_api)
-   [Leaflet License](static/vendor/leaflet-LICENSE.txt)
-   [OpenStreetMap Data and
    Attribution](https://www.openstreetmap.org/copyright)
-   [Campus Venue Sources](docs/venue-sources.md)
-   [Project Verification Records](docs/verification.md)

If you encounter a problem, describe the steps you took and the message
shown on the page in [GitHub
Issues](https://github.com/Wenbo-Bob-Li/campuslens/issues). Please
remove API keys and private information from posters before sharing
details.
