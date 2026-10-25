'use strict';

const $ = (id) => document.getElementById(id);
const icon = (name) => `<svg class="icon" aria-hidden="true"><use href="#i-${name}"/></svg>`;
const escapeHTML = (value) => String(value ?? '').replace(/[&<>"']/g, (char) => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[char]));
const centralVenueIds = new Set(['price-center','geisel-library','design-and-innovation-building','rimac','epstein-family-amphitheater','student-center','conrad-prebys-music-center','atkinson-hall']);
const searchText = (value) => String(value ?? '').normalize('NFKD').replace(/[\u0300-\u036f]/g,'').toLowerCase().replace(/[^a-z0-9]+/g,' ').trim();
const categoryInfo = {
  learning: {label:'Learning', color:'#547d86', soft:'#eaf1f1', icon:'book'},
  social: {label:'Social', color:'#a67e40', soft:'#f6efdf', icon:'people'},
  arts: {label:'Arts', color:'#ab715a', soft:'#f7ece5', icon:'spark'},
  career: {label:'Career', color:'#738752', soft:'#edf2e4', icon:'book'},
  sports: {label:'Sports', color:'#8374a2', soft:'#eeebf5', icon:'spark'},
  other: {label:'Other', color:'#68825a', soft:'#edf1e7', icon:'calendar'},
};
const state = {
  config:null, venues:[], events:[], demoMode:false, query:'', category:'all', selectedId:null,
  map:null, landmarkLayer:null, eventLayer:null, markerByEvent:new Map(),
  file:null, previewURL:null, imageURL:'', posterId:'', evidence:[], warnings:[],
  busy:false, saving:false, picking:false, tileFailures:0, extractionController:null, isSample:false,
};

async function api(path, options={}) {
  let response;
  try { response = await fetch(path, options); }
  catch (error) {
    if (error.name === 'AbortError') throw error;
    throw new Error('The local app is not responding. Check that the CampusLens server is running.');
  }
  const type = response.headers.get('content-type') || '';
  let data;
  try { data = type.includes('application/json') ? await response.json() : null; }
  catch { throw new Error('The server returned an unreadable response. Please try again.'); }
  if (!response.ok) {
    const error = new Error(data?.error || `Request failed (${response.status}). Please try again.`);
    error.code = data?.code;
    throw error;
  }
  if (!data) throw new Error('The server did not return the expected data.');
  return data;
}

function toast(message, isError=false) {
  const element = document.createElement('div');
  element.className = `toast${isError ? ' error' : ''}`;
  element.textContent = message;
  $('toast-container').append(element);
  setTimeout(() => element.remove(), isError ? 7500 : 4500);
}

function showAlert(message='') {
  $('modal-alert').textContent = message;
  $('modal-alert').hidden = !message;
  if (message) $('modal-alert').scrollIntoView({block:'nearest',behavior:'smooth'});
}

function metaCategory(category) { return categoryInfo[category] || categoryInfo.other; }
function badgeHTML(category) {
  const info = metaCategory(category);
  return `<span class="category-badge" style="--category-color:${info.color};--category-soft:${info.soft}"><i class="category-dot"></i>${info.label}</span>`;
}

function venueFor(event) { return state.venues.find((venue) => venue.id === event.venue_id); }
function eventLocation(event) { return venueFor(event)?.name || event.location_text || 'Pinned campus location'; }
function eventDate(event) { return [event.date_text, event.time_text].filter(Boolean).join(' · ') || 'Date and time not specified'; }
function eventCoordinates(event) {
  const venue = venueFor(event);
  const lat = Number(venue?.lat ?? event.lat);
  const lng = Number(venue?.lng ?? event.lng);
  return Number.isFinite(lat) && Number.isFinite(lng) ? [lat,lng] : null;
}

function demoEvents() {
  const definitions = [
    {id:'demo-creators', title:'Campus Creators Meetup', date_text:'Sample event', time_text:'4:00–6:00 PM', location_text:'Price Center — West Ballroom', room:'West Ballroom', category:'social', venue_id:'price-center', description:'A fictional meetup for campus makers, designers, and curious people. A sample event to explore the map.', image_url:'/samples/campus-creators.png'},
    {id:'demo-ai', title:'Campus AI Study Jam', date_text:'Sample event', time_text:'2:00–4:00 PM', location_text:'Design and Innovation Building (DIB)', room:'Room 208', category:'learning', venue_id:'design-and-innovation-building', description:'A fictional study session. Share ideas, learn something new, and find your next collaborator.', image_url:'/samples/ai-study-jam.png'},
    {id:'demo-geisel', title:'Sketch & Slow Down', date_text:'Sample event', time_text:'3:00–4:30 PM', location_text:'Geisel Library', room:'Meet outside the main entrance', category:'arts', venue_id:'geisel-library', description:'A fictional afternoon of campus sketching. No experience needed; bring a notebook and your curiosity.', image_url:''},
  ];
  return definitions.map((event) => {
    const venue=venueFor(event);
    return venue ? {...event,venue_id:venue.id,lat:venue.lat,lng:venue.lng,is_demo:true} : null;
  }).filter(Boolean);
}

function filteredEvents() {
  const savedSamples=state.events.filter((event)=>event.is_demo);
  const samples=demoEvents().filter((sample)=>!savedSamples.some((event)=>
    event.title.trim().toLowerCase()===sample.title.trim().toLowerCase() && event.venue_id===sample.venue_id));
  const source = state.demoMode ? [...savedSamples,...samples] : state.events.filter((event)=>!event.is_demo);
  const query = state.query.trim().toLowerCase();
  return source.filter((event) => (state.category === 'all' || event.category === state.category) &&
    (!query || [event.title,event.location_text,event.room,event.organizer,event.description,eventLocation(event)].join(' ').toLowerCase().includes(query)));
}

function initializeMap() {
  if (!window.L) {
    $('tile-warning').hidden=false;
    $('tile-warning').textContent='The map library could not load. Your event list and poster upload are still available.';
    return;
  }
  const map = L.map('map', {zoomControl:false, minZoom:14, maxZoom:19, preferCanvas:true}).setView([32.8806,-117.2372],16);
  state.map = map;
  L.control.zoom({position:'topright'}).addTo(map);
  const tiles=L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png',{
    maxZoom:19, attribution:'&copy; <a href="https://www.openstreetmap.org/copyright" target="_blank" rel="noopener noreferrer">OpenStreetMap</a> contributors',
  });
  tiles.on('tileerror',() => {
    state.tileFailures += 1;
    if (state.tileFailures >= 4) $('tile-warning').hidden=false;
  });
  tiles.on('load',() => { if (state.tileFailures===0) $('tile-warning').hidden=true; });
  tiles.addTo(map);
  state.landmarkLayer=L.layerGroup().addTo(map);
  state.eventLayer=L.layerGroup().addTo(map);
  map.on('click',(event) => {
    if (!state.picking) return;
    completeMapPick(event.latlng.lat,event.latlng.lng);
  });
  map.on('zoomend',()=>{
    const radius=map.getZoom()>=17?3.5:2.3;
    state.landmarkLayer.eachLayer((layer)=>layer.setRadius(radius));
  });
}

function completeMapPick(lat,lng) {
  if (lat<32.84 || lat>32.91 || lng< -117.27 || lng> -117.20) {
    toast('Choose a building or meeting point within the UCSD campus area.',true);
    return;
  }
  $('f-lat').value=lat.toFixed(7);$('f-lng').value=lng.toFixed(7);
  stopPicking(true);updateLocationFeedback();
}

function renderLandmarks() {
  if (!state.landmarkLayer) return;
  state.landmarkLayer.clearLayers();
  state.venues.forEach((venue) => {
    const dot=L.circleMarker([venue.lat,venue.lng],{radius:state.map.getZoom()>=17?3.5:2.3,color:'#fffdf3',weight:1,fillColor:'#94a281',fillOpacity:.85});
    dot.bindTooltip(venue.name,{permanent:false,direction:'right',className:'campus-label'});
    dot.bindPopup(`<div class="popup-event"><span class="eyebrow">CAMPUS PLACE</span><h3>${escapeHTML(venue.name)}</h3><p>Building-level location. Room and event details appear on activity pins.</p><div class="popup-links"><a href="${escapeHTML(venue.source_url)}" target="_blank" rel="noopener noreferrer">Location source ↗</a></div></div>`);
    dot.on('click',()=>{if(state.picking){completeMapPick(venue.lat,venue.lng);dot.closePopup();}});
    dot.addTo(state.landmarkLayer);
  });
}

function popupEventHTML(event) {
  const room = event.room ? `<div class="popup-meta">${icon('pin')}<span>${escapeHTML(event.room)}</span></div>` : '';
  const evidence=Array.isArray(event.evidence)&&event.evidence.length ? `<details class="evidence-box"><summary>Poster evidence</summary><ul>${event.evidence.map((line)=>`<li>${escapeHTML(line)}</li>`).join('')}</ul></details>` : '';
  const posterURL = /^\/(uploads|samples)\/[a-zA-Z0-9_.-]+$/.test(event.image_url||'') ? event.image_url : '';
  let signup='';
  try { const link=new URL(event.signup_url); if(['http:','https:'].includes(link.protocol)) signup=link.href; } catch {}
  return `<article class="popup-event">${badgeHTML(event.category)}${event.is_demo?'<span class="demo-tag"> &nbsp;FICTIONAL DEMO</span>':''}<h3>${escapeHTML(event.title)}</h3><div class="popup-meta">${icon('calendar')}<span>${escapeHTML(eventDate(event))}</span></div><div class="popup-meta">${icon('pin')}<span>${escapeHTML(eventLocation(event))}</span></div>${room}${event.description?`<p>${escapeHTML(event.description)}</p>`:''}${event.organizer?`<p>By ${escapeHTML(event.organizer)}</p>`:''}${evidence}<div class="popup-links">${posterURL?`<a href="${escapeHTML(posterURL)}" target="_blank" rel="noopener noreferrer">View poster ↗</a>`:''}${signup?`<a href="${escapeHTML(signup)}" target="_blank" rel="noopener noreferrer">Event link ↗</a>`:''}</div><div class="popup-precision">BUILDING / MEETING-POINT LOCATION</div></article>`;
}

function renderMapEvents(events) {
  if (!state.eventLayer) return;
  state.eventLayer.clearLayers();
  state.markerByEvent.clear();
  const groups=new Map();
  events.forEach((event) => {
    const coordinates=eventCoordinates(event);
    if (!coordinates) return;
    const key=coordinates.map((n)=>n.toFixed(5)).join(',');
    if (!groups.has(key)) groups.set(key,{coordinates,events:[]});
    groups.get(key).events.push(event);
  });
  groups.forEach((group) => {
    const selected = group.events.some((event) => event.id===state.selectedId);
    const color=group.events.length>1?'#173e35':metaCategory(group.events[0].category).color;
    const markerIcon=L.divIcon({className:`event-marker${selected?' selected':''}`,iconSize:[36,42],iconAnchor:[18,41],popupAnchor:[0,-36],html:`<div class="pin-body" style="--pin-color:${color}"><span>${group.events.length>1?group.events.length:icon(metaCategory(group.events[0].category).icon)}</span></div>`});
    const marker=L.marker(group.coordinates,{icon:markerIcon,keyboard:true,title:group.events.map((event)=>event.title).join(', ')});
    marker.bindPopup(group.events.map(popupEventHTML).join(''),{maxHeight:360,maxWidth:300,autoPanPadding:[30,35]});
    marker.on('click',()=> { if(state.picking){completeMapPick(...group.coordinates);marker.closePopup();}else{state.selectedId=group.events[0].id;updateSelectedCards();} });
    marker.addTo(state.eventLayer);
    group.events.forEach((event)=>state.markerByEvent.set(event.id,marker));
  });
}

function updateSelectedCards() {
  document.querySelectorAll('.event-card').forEach((card)=>{
    const selected=card.dataset.eventId===String(state.selectedId);
    card.classList.toggle('selected',selected);
    card.setAttribute('aria-pressed',String(selected));
  });
  const selected=state.markerByEvent.get(state.selectedId);
  for(const marker of new Set(state.markerByEvent.values())) marker.getElement()?.classList.toggle('selected',marker===selected);
}

function focusEvent(event) {
  state.selectedId=event.id;
  updateSelectedCards();
  const coordinates=eventCoordinates(event);
  const marker=state.markerByEvent.get(event.id);
  if (coordinates && state.map) {
    state.map.setView(coordinates,Math.max(state.map.getZoom(),17),{animate:!matchMedia('(prefers-reduced-motion: reduce)').matches});
    marker?.openPopup();
    if(window.innerWidth<=820) $('map').scrollIntoView({behavior:'smooth',block:'center'});
  }
}

function render() {
  const events=filteredEvents();
  $('saved-count').textContent=state.events.filter((event)=>!event.is_demo).length;
  $('venue-count').textContent=state.venues.length;
  $('list-label').textContent=state.demoMode?'SAMPLE EVENTS':'YOUR EVENTS';
  $('list-count').textContent=`${events.length} ${events.length===1?'place':'places'} to be`;
  $('demo-notice').hidden=!state.demoMode;
  const list=$('event-list');
  list.replaceChildren();
  list.scrollTop=0;
  if(!events.length) {
    const empty=document.createElement('div'); empty.className='empty-state';
    if(state.query || state.category!=='all') {
      empty.innerHTML=`<div class="empty-illustration">${icon('search')}</div><h3>No events found.</h3><p>Try a different search or category.</p><button class="button button-secondary" id="clear-filters">Clear filters</button>`;
    } else {
      empty.innerHTML=`<div class="empty-illustration">${icon('pin')}</div><h3>Your next thing starts here.</h3><p>Spotted something on a noticeboard?<br>Add a poster and put it on the map.</p><button class="button button-primary" id="empty-add">${icon('plus')}Add your first poster</button><button class="text-button" id="show-demo">Explore sample events ${icon('arrow')}</button>`;
    }
    list.append(empty);
    $('empty-add')?.addEventListener('click',openEventModal);
    $('show-demo')?.addEventListener('click',()=>{state.demoMode=true;render();fitCampus();});
    $('clear-filters')?.addEventListener('click',clearFilters);
  } else {
    events.forEach((event)=>{
      const card=document.createElement('button'); card.type='button'; card.className='event-card';card.dataset.eventId=event.id;
      card.setAttribute('aria-label',`${event.title}. ${eventDate(event)}. ${eventLocation(event)}. Show on map.`);
      card.innerHTML=`<div class="card-top">${badgeHTML(event.category)}${event.is_demo?'<span class="demo-tag">DEMO</span>':''}</div><h3>${escapeHTML(event.title)}</h3><div class="card-meta">${icon('calendar')}<span>${escapeHTML(eventDate(event))}</span></div><div class="card-meta card-location">${icon('pin')}<span>${escapeHTML(eventLocation(event))}${event.room?` · ${escapeHTML(event.room)}`:''}</span></div><div class="card-bottom"><span>${event.is_demo?'Fictional sample event':'Confirmed campus location'}</span><span>View on map ${icon('arrow')}</span></div>`;
      card.addEventListener('click',()=>focusEvent(event)); list.append(card);
    });
  }
  renderMapEvents(events);
  updateSelectedCards();
}

function clearFilters() {
  state.category='all';state.query='';$('event-search').value='';
  document.querySelectorAll('.filter').forEach((button)=>{const active=button.dataset.category==='all';button.classList.toggle('active',active);button.setAttribute('aria-pressed',String(active));});
  render();
}

function fitCampus() {
  if(!state.map) return;
  const events=filteredEvents().map(eventCoordinates).filter(Boolean);
  const positions=events.length?events:state.venues.filter((venue)=>centralVenueIds.has(venue.id)).map((venue)=>[venue.lat,venue.lng]);
  if(positions.length>1) state.map.fitBounds(L.latLngBounds(positions),{paddingTopLeft:[60,110],paddingBottomRight:[60,120],maxZoom:16,animate:false});
  else if(positions.length===1) state.map.setView(positions[0],16);
  else state.map.setView([32.8806,-117.2372],16);
}

function renderVenueOptions(selected=$('f-venue').value) {
  const query=searchText($('venue-search').value);
  const tokens=query.split(' ').filter(Boolean);
  const exactMatches=query?state.venues.filter((venue)=>[venue.name,...(venue.aliases||[])].some((name)=>searchText(name)===query)):[];
  const matches=exactMatches.length?exactMatches:state.venues.filter((venue)=>{
    const text=searchText([venue.name,...(venue.aliases||[]),venue.address||''].join(' '));
    return tokens.every((token)=>text.includes(token));
  });
  const select=$('f-venue');
  select.replaceChildren(new Option(query?'Choose a search result…':'Choose a building…',''));
  matches.forEach((venue)=>select.add(new Option(venue.name,venue.id)));
  select.add(new Option('Choose a point on the map…','manual'));
  if([...select.options].some((option)=>option.value===selected)) select.value=selected;
  $('venue-search-status').textContent=query
    ?`${matches.length} of ${state.venues.length} campus places match. ${matches.length?'Choose a building below.':'Try another name, or choose a point on the map.'}`
    :`${state.venues.length} campus places. Search by building name, abbreviation, or address.`;
}

function applyConfig(config) {
  state.config=config;state.venues=Array.isArray(config.venues)?[...config.venues].sort((a,b)=>a.name.localeCompare(b.name,undefined,{numeric:true,sensitivity:'base'})):[];
  $('api-dot').className=`status-dot ${config.gemma_configured?'ready':'pending'}`;
  $('api-status').textContent=config.gemma_configured?'Gemma ready · Saved on this computer':'Gemma setup pending · Manual entry available';
  $('setup-note').hidden=Boolean(config.gemma_configured);
  $('analyze-poster').disabled=!state.file || !config.gemma_configured || state.busy;
  $('help-status').textContent=config.gemma_configured?'API key configured. Your next step is a real poster analysis.':'API key not configured yet. Save your key in .env, then refresh status.';
  renderVenueOptions();
  renderLandmarks();
  render();
}

async function refreshConfig() {
  const config=await api('/api/config');applyConfig(config);return config;
}

function resetEventForm() {
  state.extractionController?.abort();state.extractionController=null;
  if(state.previewURL) URL.revokeObjectURL(state.previewURL);
  state.file=null;state.previewURL=null;state.imageURL='';state.posterId='';state.evidence=[];state.warnings=[];state.isSample=false;
  $('poster-file').value='';$('review-stage').reset();
  renderVenueOptions('');
  $('poster-preview').hidden=true;$('poster-preview').removeAttribute('src');
  $('upload-placeholder').hidden=false;$('selected-file').hidden=true;$('review-thumb').replaceChildren();
  $('evidence-box').hidden=true;$('review-warnings').hidden=true;$('manual-location').hidden=true;$('location-feedback').textContent='';
  showAlert();showStage('upload');setBusy(false);state.saving=false;
}

function openEventModal() {
  if(!$('event-modal').open){resetEventForm();$('event-modal').showModal();}
  refreshConfig().catch(()=>{});
}

function closeEventModal() {
  if(state.saving){toast('Finishing the save. Please wait.');return;}
  state.extractionController?.abort();state.extractionController=null;
  $('event-modal').close();setBusy(false);
}

function showStage(stage) {
  const reviewing=stage==='review';
  $('upload-stage').hidden=reviewing;$('review-stage').hidden=!reviewing;
  $('step-upload').classList.toggle('active',!reviewing);$('step-upload').classList.toggle('done',reviewing);
  $('step-review').classList.toggle('active',reviewing);$('step-save').classList.remove('active');
  $('event-modal').scrollTop=0;
}

function setBusy(busy) {
  state.busy=busy;
  $('analyze-poster').disabled=busy || !state.file || !state.config?.gemma_configured;
  $('analyze-poster').innerHTML=busy?'<span class="spinner" aria-hidden="true"></span><span>Reading your poster…</span>':`${icon('spark')}<span>Analyze poster</span>`;
  $('manual-entry').disabled=busy;$('use-sample').disabled=busy;
  $('upload-zone').setAttribute('aria-disabled',String(busy));
}

function selectFile(file,isSample=false) {
  if(state.busy) return;
  if(!file) return;
  showAlert();
  const accepted=['image/jpeg','image/png'];
  if(!accepted.includes(file.type)) {showAlert('Choose a JPG or PNG image. Other file types are not supported.');return;}
  const max=(state.config?.max_upload_mb||10)*1024*1024;
  if(file.size>max) {showAlert(`This image is too large. Choose an image smaller than ${state.config?.max_upload_mb||10} MB.`);return;}
  if(!file.size) {showAlert('This image is empty. Choose another file.');return;}
  if(state.previewURL) URL.revokeObjectURL(state.previewURL);
  state.file=file;state.previewURL=URL.createObjectURL(file);state.imageURL='';state.posterId='';state.isSample=isSample;
  $('poster-preview').src=state.previewURL;$('poster-preview').hidden=false;$('upload-placeholder').hidden=true;
  $('selected-file').hidden=false;$('selected-name').textContent=file.name;
  $('analyze-poster').disabled=!state.config?.gemma_configured;
}

async function useSample() {
  try {
    const response=await fetch('/samples/campus-creators.png');
    if(!response.ok) throw new Error('The sample poster is not available yet. Choose your own JPG or PNG.');
    const blob=await response.blob();
    if($('event-modal').open) selectFile(new File([blob],'campus-creators-sample.png',{type:'image/png'}),true);
  } catch(error) {showAlert(error.message);}
}

function fillReview(event={},match={}) {
  const fields={title:'f-title',date_text:'f-date',time_text:'f-time',location_text:'f-location',room:'f-room',organizer:'f-organizer',description:'f-description',signup_url:'f-url'};
  for(const [key,id] of Object.entries(fields)) $(id).value=typeof event[key]==='string'?event[key]:'';
  $('f-category').value=Object.hasOwn(categoryInfo,event.category)?event.category:'other';
  $('venue-search').value='';
  renderVenueOptions(match.status==='matched'?match.venue_id:'');
  $('f-lat').value='';$('f-lng').value='';$('confirm-details').checked=false;$('f-demo').checked=state.isSample;
  state.evidence=Array.isArray(event.evidence)?event.evidence.filter((line)=>typeof line==='string'):[];
  state.warnings=Array.isArray(event.warnings)?event.warnings.filter((line)=>typeof line==='string'):[];
  $('evidence-list').replaceChildren();state.evidence.forEach((line)=>{const li=document.createElement('li');li.textContent=line;$('evidence-list').append(li);});
  $('evidence-box').hidden=!state.evidence.length;
  $('review-warnings').textContent=state.warnings.join(' · ');$('review-warnings').hidden=!state.warnings.length;
  $('review-thumb').replaceChildren();
  if(state.previewURL){const img=document.createElement('img');img.src=state.previewURL;img.alt='Poster being reviewed';$('review-thumb').append(img);}
  updateLocationFeedback(match);
  showStage('review');
  setTimeout(()=>$('f-title').focus(),20);
}

function updateLocationFeedback(match) {
  const selected=$('f-venue').value;
  $('manual-location').hidden=selected!=='manual';
  $('f-lat').disabled=selected!=='manual';$('f-lng').disabled=selected!=='manual';
  const feedback=$('location-feedback');
  feedback.classList.remove('needs-attention');
  if(selected==='manual') {
    const hasCoordinates=$('f-lat').value&&$('f-lng').value;
    const lat=Number($('f-lat').value),lng=Number($('f-lng').value);
    const valid=Number.isFinite(lat)&&Number.isFinite(lng)&&lat>=32.84&&lat<=32.91&&lng>= -117.27&&lng<= -117.20;
    feedback.textContent=hasCoordinates?(valid?'Your chosen point will be used. Check that it is the event location.':'This point is outside the campus area. Choose a point on the map instead.'):'Pick a point on the map, or enter campus coordinates.';
    if(hasCoordinates&&!valid)feedback.classList.add('needs-attention');
  } else if(selected) {
    const venue=state.venues.find((v)=>v.id===selected);
    feedback.textContent=`Suggested building: ${venue?.name || selected}. Check the building; the room stays in the event details.`;
  } else if(match?.status==='ambiguous') {
    const names=Array.isArray(match.candidates)?match.candidates.map((venue)=>venue.name).filter(Boolean):[];
    feedback.textContent=`More than one building may match${names.length?`: ${names.join(', ')}`:''}. Please choose the event's building.`;
    feedback.classList.add('needs-attention');
  } else {
    feedback.textContent='Choose the event’s building, or place a pin manually if the location is not listed.';
    feedback.classList.add('needs-attention');
  }
}

async function analyzePoster() {
  if(!state.file || state.busy) return;
  showAlert();setBusy(true);
  const controller=new AbortController();state.extractionController=controller;
  try {
    const data=await api('/api/extract',{method:'POST',headers:{'Content-Type':state.file.type},body:state.file,signal:controller.signal});
    if(state.extractionController!==controller || !$('event-modal').open) return;
    state.imageURL=data.image_url||'';state.posterId=data.poster_id||'';
    fillReview(data.event||{},data.location_match||{});
  } catch(error) {
    if(error.name!=='AbortError') {
      showAlert(error.message);
      if(error.code==='missing_api_key') {await refreshConfig().catch(()=>{});}
    }
  } finally {
    if(state.extractionController===controller){state.extractionController=null;setBusy(false);}
  }
}

async function manualEntry() {
  if(state.busy) return;
  showAlert();
  if(state.file && !state.imageURL) {
    setBusy(true);
    const controller=new AbortController();state.extractionController=controller;
    try {
      const data=await api('/api/upload',{method:'POST',headers:{'Content-Type':state.file.type},body:state.file,signal:controller.signal});
      if(state.extractionController!==controller || !$('event-modal').open) return;
      state.imageURL=data.image_url||'';state.posterId=data.poster_id||'';
    } catch(error){if(error.name!=='AbortError')showAlert(error.message);return;}
    finally {if(state.extractionController===controller){state.extractionController=null;setBusy(false);}}
  }
  if(!$('event-modal').open) return;
  fillReview({},{});
  toast('Manual entry — fill in the details from your poster.');
}

function startPicking() {
  if(!state.map){showAlert('The map is unavailable. Enter latitude and longitude instead.');return;}
  state.picking=true;$('event-modal').close();$('map-pick-bar').hidden=false;
  document.querySelector('.map-section').classList.add('picking-location');
  if(window.innerWidth<=820)$('map').scrollIntoView({behavior:'smooth',block:'center'});
  fitCampus();
}

function stopPicking(reopen) {
  state.picking=false;$('map-pick-bar').hidden=true;document.querySelector('.map-section').classList.remove('picking-location');
  if(reopen && !$('event-modal').open){$('event-modal').showModal();$('f-venue').focus();}
}

async function saveEvent(event) {
  event.preventDefault();
  if(state.saving)return;
  showAlert();
  if(!$('review-stage').reportValidity())return;
  const selected=$('f-venue').value;
  const payload={title:$('f-title').value.trim(),date_text:$('f-date').value.trim(),time_text:$('f-time').value.trim(),location_text:$('f-location').value.trim(),room:$('f-room').value.trim(),organizer:$('f-organizer').value.trim(),description:$('f-description').value.trim(),signup_url:$('f-url').value.trim(),category:$('f-category').value,venue_id:selected==='manual'?'':selected,location_confirmed:$('confirm-details').checked,image_url:state.imageURL,evidence:state.evidence,warnings:state.warnings,is_demo:$('f-demo').checked};
  if(!payload.location_text) payload.location_text=state.venues.find((venue)=>venue.id===selected)?.name || (selected==='manual'?'Manually pinned campus location':'');
  if(!payload.title){showAlert('Add an event name before saving.');$('f-title').focus();return;}
  if(selected==='manual') {
    if(!$('f-lat').value || !$('f-lng').value){showAlert('Choose a point on the map, or fill in both coordinates.');return;}
    payload.lat=Number($('f-lat').value);payload.lng=Number($('f-lng').value);
  }
  const saveButton=$('save-event');state.saving=true;saveButton.disabled=true;saveButton.innerHTML='<span class="spinner" aria-hidden="true"></span><span>Adding your event…</span>';
  try {
    const data=await api('/api/events',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(payload)});
    state.events.unshift(data.event);state.demoMode=Boolean(data.event.is_demo);clearFilters();
    state.saving=false;closeEventModal();focusEvent(data.event);
    toast('Your event has a place on the map.');
  } catch(error) {showAlert(error.message);}
  finally {state.saving=false;saveButton.disabled=false;saveButton.innerHTML=`${icon('plus')}<span>Add event to map</span>`;}
}

function bindUI() {
  ['add-event','map-add'].forEach((id)=>$(id).addEventListener('click',openEventModal));
  $('close-event-modal').addEventListener('click',closeEventModal);
  $('event-modal').addEventListener('cancel',(event)=>{if(state.saving){event.preventDefault();return;}state.extractionController?.abort();setBusy(false);});
  $('how-button').addEventListener('click',()=>$('help-modal').showModal());
  $('setup-help').addEventListener('click',()=>$('help-modal').showModal());
  $('close-help').addEventListener('click',()=>$('help-modal').close());
  $('refresh-status').addEventListener('click',async()=>{
    $('refresh-status').disabled=true;
    try {await refreshConfig();toast(state.config.gemma_configured?'API key is configured. Try analyzing a poster.':'API key is still missing. Add it to the local .env file.');}
    catch(error){$('help-status').textContent=error.message;}
    finally{$('refresh-status').disabled=false;}
  });
  $('recenter').addEventListener('click',fitCampus);
  $('event-search').addEventListener('input',(event)=>{state.query=event.target.value;render();});
  document.querySelectorAll('.filter').forEach((button)=>button.addEventListener('click',()=>{
    state.category=button.dataset.category;
    document.querySelectorAll('.filter').forEach((item)=>{const active=item===button;item.classList.toggle('active',active);item.setAttribute('aria-pressed',String(active));});render();
  }));
  $('exit-demo').addEventListener('click',()=>{state.demoMode=false;clearFilters();});
  $('upload-zone').addEventListener('click',()=>{if(!state.busy)$('poster-file').click();});
  $('upload-zone').addEventListener('keydown',(event)=>{if((event.key==='Enter'||event.key===' ')&&!state.busy){event.preventDefault();$('poster-file').click();}});
  $('poster-file').addEventListener('change',(event)=>selectFile(event.target.files[0]));
  for(const eventName of ['dragenter','dragover'])$('upload-zone').addEventListener(eventName,(event)=>{event.preventDefault();$('upload-zone').classList.add('dragging');});
  for(const eventName of ['dragleave','drop'])$('upload-zone').addEventListener(eventName,(event)=>{event.preventDefault();$('upload-zone').classList.remove('dragging');});
  $('upload-zone').addEventListener('drop',(event)=>{if(event.dataTransfer.files.length>1){showAlert('Choose one poster at a time. You can add more events afterward.');return;}selectFile(event.dataTransfer.files[0]);});
  $('use-sample').addEventListener('click',useSample);
  $('analyze-poster').addEventListener('click',analyzePoster);
  $('manual-entry').addEventListener('click',manualEntry);
  $('review-stage').addEventListener('submit',saveEvent);
  $('venue-search').addEventListener('input',()=>{renderVenueOptions();updateLocationFeedback();$('confirm-details').checked=false;});
  $('f-venue').addEventListener('change',()=>{updateLocationFeedback();$('confirm-details').checked=false;});
  ['f-lat','f-lng'].forEach((id)=>$(id).addEventListener('input',()=>{$('confirm-details').checked=false;updateLocationFeedback();}));
  $('pick-location').addEventListener('click',startPicking);
  $('cancel-pick').addEventListener('click',()=>stopPicking(true));
  for(const id of ['change-poster','back-upload'])$(id).addEventListener('click',()=>{showAlert();showStage('upload');});
  document.addEventListener('keydown',(event)=>{
    if(event.key==='/'&&!['INPUT','TEXTAREA','SELECT'].includes(document.activeElement.tagName)&&!$('event-modal').open&&!$('help-modal').open){event.preventDefault();$('event-search').focus();}
    if(event.key==='Escape'&&state.picking)stopPicking(true);
  });
  window.addEventListener('resize',()=>state.map?.invalidateSize());
}

async function initialize() {
  bindUI();initializeMap();
  try {
    const [config,data]=await Promise.all([api('/api/config'),api('/api/events')]);
    state.events=Array.isArray(data.events)?data.events:[];applyConfig(config);fitCampus();
  } catch(error) {
    $('api-status').textContent='Local server unavailable';render();toast(error.message,true);
  }
}

initialize();
