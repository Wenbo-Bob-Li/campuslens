# CampusLens 演示讲稿

## 演示前准备

1. 启动本地服务，打开 `http://127.0.0.1:8000`，确认网络能加载地图。
2. 确认本机已配置自己的 API 密钥，先用样例完成一次实际 Gemma 调用。只有真实调用成功后才能这样向评委描述。
3. 准备 `campus-creators.png`、`ai-study-jam.png` 和 `location-pending.png`。它们都是 **虚构活动**，不应当被解释为校园当前活动。
4. 事先核对演示建筑的位置；地图点表示建筑附近位置，房间文字不会被解释成室内导航。
5. 切换真实活动视图和 **Demo map**，确认虚构样例只出现在 Demo map，演示内容有 Demo 标记。

## 约两分钟英文讲稿

**Opening — 20 seconds**

“Campus events are often shared as posters. Students have to read each image, find the time, and figure out where the building is. CampusLens turns a poster into an event you can review and place on a campus map.”

**Upload and extract — 35 seconds**

上传 `campus-creators.png` 并发起真实识别。

“This is an original fictional poster we created for the demo. Gemma 4 reads the image and extracts the event details. It keeps the time as written. If the poster does not provide a year or time zone, we do not invent one.”

展示识别结果，核对名称、时间和 `Price Center — West Ballroom`。

**Confirm and map — 35 seconds**

确认活动字段和建筑，保存活动，然后点击地图标记。

“The model reads the location text. The app matches that text to a campus building directory based primarily on official UC San Diego GIS data, and the user confirms it. This pin represents the building, while the room stays in the event details. Now the poster can be discovered spatially alongside other events.”

**Missing information — 20 seconds**

展示 `location-pending.png`，说明“Location to be announced”不能自动变成精确坐标。

“When a location is missing or ambiguous, CampusLens asks for human input. We can choose a building or place a pin manually.”

**Close — 10 seconds**

“Our prototype combines Gemma 4 image understanding, editable event details, and a campus map. The code and original demo posters are available in our open-source repository.”

只有公开仓库建立后才说最后一句；若尚未建立，改为 “We prepared the code, setup documentation, and original demo posters for release.”

## 中文理解版

“校园活动通常以海报传播，学生需要逐张读取并自己查找地点。CampusLens 让用户上传海报，由 Gemma 4 提取活动信息，核对后放到校园地图上。”

“这张是我们制作的虚构演示海报。模型读出活动名、时间和地点，程序负责查找建筑位置，用户确认结果。海报没写年份或时区，就保留未知。地图标记代表建筑，具体房间放在详情里。”

“如果地点待定或有歧义，系统请用户补充。我们希望把图片中分散的信息变成可以核对、可以在地图上发现的校园活动。”

## API 暂时不可用时

直接说明：“The live model request is unavailable right now. I can demonstrate the map using manually entered, clearly labeled demo data. This does not demonstrate a successful AI extraction.”

随后手动录入虚构样例，展示确认位置和地图详情。不要把预填结果、缓存结果或手工内容讲成现场真实识别。若已录制真实调用的视频，可明确标为先前录制的演示并播放。

## 常见问题

**Why Gemma 4?**

“It can read the poster image and produce useful event fields. The model handles image understanding; the application handles review, building matching, and map storage.”

**How do you avoid incorrect locations?**

“We do not ask the model to invent coordinates. We use a 622-location campus directory based primarily on official university GIS data, preserve room text, and ask the user to confirm or place the pin manually.”

**Are these real events?**

“No. The supplied sample posters and demo pins are explicitly fictional. Real events would need their own accurate details and organizer permission for public sharing.”

**Where is the data stored?**

“This version stores events and uploaded images locally with SQLite and files. The image is sent to Google's API when the user requests AI extraction. Public hosting would be a separate deployment step.”

**What is the current limitation?**

“This is a local campus prototype using a snapshot of the university's public GIS. It provides building-level pins rather than indoor navigation. Model output, the selected building, and the precise meeting point still need user review.”
