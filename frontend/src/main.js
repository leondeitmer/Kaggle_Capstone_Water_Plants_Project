import './style.css';

// Default Data
const DEFAULT_PLANTS = [
  {
    id: "default-1",
    name: "Example Plant",
    species: "Water-loving Herbs",
    lastWatered: new Date().toISOString(),
    sunHours: 0.0,
    imageUrl: "/img/App_Logo.svg",
    description: "An example water-loving herb plant.",
    moisture_level: 100,
    status: "Healthy",
    next_watering_date: new Date().toISOString().split('T')[0],
    explanation: "The plant was watered today and is fully hydrated.",
    watering_tips: "The soil is moist. No watering needed for now.",
    rainExposure: false
  }
];

const DEFAULT_BALCONY = {
  city: "Berlin",
  country: "Germany",
  zipCode: "10967",
  defaultSunHours: 5.0,
  isCovered: false
};

// API style detection:
// - If running on port 8000 or port 5173 (Vite dev server), we query http://localhost:8000 using batch POST.
// - Else (port 8001 or deployed domain), we query relative using individual GET requests.
const isLocalBackend = window.location.port === "8000" || window.location.port === "5173";
const apiBase = isLocalBackend ? "http://localhost:8000" : "";

let currentUploadedImageDataUrl = "";

// App State (load from florawave keys, fallback to floracast keys)
let state = {
  plants: JSON.parse(localStorage.getItem("florawave_plants")) || JSON.parse(localStorage.getItem("floracast_plants")) || DEFAULT_PLANTS,
  balcony: JSON.parse(localStorage.getItem("florawave_balcony")) || JSON.parse(localStorage.getItem("floracast_balcony")) || DEFAULT_BALCONY
};

// DOM Elements
const plantsGrid = document.getElementById("plants-grid");
const plantCount = document.getElementById("plant-count");

const displayLocation = document.getElementById("display-location");
const displaySun = document.getElementById("display-sun");
const displayCovered = document.getElementById("display-covered");
const displayBalconyRain = document.getElementById("display-balcony-rain");

const modalPlant = document.getElementById("modal-plant");
const modalBalcony = document.getElementById("modal-balcony");
const loadingOverlay = document.getElementById("loading-overlay");
const loadingText = document.getElementById("loading-text");

const weatherWidget = document.getElementById("weather-widget");
const thirstyContainer = document.getElementById("thirsty-container");
const thirstyHeading = document.getElementById("thirsty-heading");

// Buttons & Actions
const btnAddPlant = document.getElementById("btn-add-plant");
const btnEditBalcony = document.getElementById("btn-edit-balcony");
const btnResetDefaults = document.getElementById("btn-reset-defaults");
const btnAnalyzeAll = document.getElementById("btn-analyze-all");

const btnBackupExport = document.getElementById("btn-backup-export");
const btnBackupImport = document.getElementById("btn-backup-import");
const backupFileInput = document.getElementById("backup-file-input");

// Close buttons
const closePlant = document.getElementById("close-modal-plant");
const closeBalcony = document.getElementById("close-modal-balcony");
const btnCancelPlant = document.getElementById("btn-cancel-plant");
const btnCancelBalcony = document.getElementById("btn-cancel-balcony");

// Form elements
const formPlant = document.getElementById("form-plant");
const formBalcony = document.getElementById("form-balcony");

const fieldPlantFile = document.getElementById("field-plant-file");
const fieldPlantImage = document.getElementById("field-plant-image");
const imagePreviewGroup = document.getElementById("image-preview-group");
const imagePreviewImg = document.getElementById("image-preview-img");
const btnRemoveImage = document.getElementById("btn-remove-image");

// Save to localStorage
function saveState() {
  localStorage.setItem("florawave_plants", JSON.stringify(state.plants));
  localStorage.setItem("florawave_balcony", JSON.stringify(state.balcony));
  // Keep floracast key in sync for backwards compatibility
  localStorage.setItem("floracast_plants", JSON.stringify(state.plants));
  localStorage.setItem("floracast_balcony", JSON.stringify(state.balcony));
}

// Render Balcony Info
function renderBalcony() {
  displayLocation.textContent = `${state.balcony.city}, ${state.balcony.country || 'Germany'} (${state.balcony.zipCode})`;
  displaySun.textContent = `${state.balcony.defaultSunHours} hrs/day`;
  displayCovered.textContent = state.balcony.isCovered ? "Covered" : "Open";
  displayBalconyRain.textContent = state.balcony.isCovered ? "no" : "yes";
}

// Render Plant Cards
function renderPlants() {
  plantCount.textContent = state.plants.length;

  if (state.plants.length === 0) {
    plantsGrid.innerHTML = `
      <div class="no-plants-placeholder">
        <i class="fa-solid fa-seedling"></i>
        <p>No plants added yet. Click 'Add Plant' to start your inventory!</p>
      </div>
    `;
    return;
  }

  plantsGrid.innerHTML = state.plants.map(plant => {
    const defaultImg = "/img/App_Logo.svg";
    const imgUrl = plant.imageUrl || defaultImg;
    const isLogo = imgUrl === defaultImg || imgUrl.includes("App_Logo.svg");
    const logoClass = isLogo ? "logo-img" : "";

    let lastWateredDate = "Unknown";
    let isRainWatered = false;
    if (plant.watered_by_rain && plant.effective_last_watered) {
      try {
        lastWateredDate = new Date(plant.effective_last_watered).toLocaleDateString([], { dateStyle: 'short' });
        isRainWatered = true;
      } catch (e) {}
    } else if (plant.lastWatered) {
      try {
        lastWateredDate = new Date(plant.lastWatered).toLocaleString([], { dateStyle: 'short', timeStyle: 'short' });
      } catch (e) {}
    }

    const moisture = plant.moisture_level !== undefined ? `${plant.moisture_level}%` : "Not analyzed";
    const status = plant.status || "Healthy";
    const statusClass = status.toLowerCase().replace(" ", "-");

    return `
      <div class="plant-card glass fade-in">
        <div class="plant-card-img ${logoClass}" style="background-image: url('${imgUrl}')"></div>
        <div class="plant-card-content">
          <div class="plant-header">
            <h4>${plant.name}</h4>
            <span class="badge badge-${statusClass}">${status}</span>
          </div>
          <p class="plant-category"><i class="fa-solid fa-tag"></i> ${plant.species}</p>
          <p class="plant-meta"><strong>Sun:</strong> ${plant.sunHours} hrs/day</p>
          <p class="plant-meta"><strong>Last Watered:</strong> ${lastWateredDate} ${isRainWatered ? '<span class="badge badge-rain" style="background: rgba(59, 130, 246, 0.15); color: #60a5fa; font-size: 0.75rem; padding: 2px 6px; border-radius: 4px; margin-left: 6px;" title="Watered by natural rainfall"><i class="fa-solid fa-cloud-showers-heavy"></i> Rain</span>' : ''}</p>
          <p class="plant-meta"><strong>Rain Exposure:</strong> ${plant.rainExposure ? "Covered (Ignored)" : "Exposed"}</p>
          
          <div class="plant-moisture-bar">
            <div class="moisture-label">Moisture: <strong>${moisture}</strong></div>
            <div class="bar-bg">
              <div class="bar-fill moisture-${statusClass}" style="width: ${plant.moisture_level || 0}%"></div>
            </div>
          </div>

          ${plant.explanation ? `
          <details class="plant-explanation-details">
            <summary><i class="fa-solid fa-circle-info"></i> AI Explanation</summary>
            <div class="plant-explanation">${plant.explanation}</div>
          </details>
          ` : ""}
          ${plant.watering_tips ? `
          <details class="plant-tips-details">
            <summary><i class="fa-solid fa-lightbulb"></i> AI Watering Tip</summary>
            <div class="plant-watering-tip">${plant.watering_tips}</div>
          </details>
          ` : ""}
          ${plant.next_watering_date ? `<p class="plant-meta"><strong>Next Watering:</strong> ${plant.next_watering_date}</p>` : ""}

          <div class="plant-actions">
            <button class="btn btn-secondary btn-xs btn-analyze-single" data-id="${plant.id}" title="Run AI analysis">
              <i class="fa-solid fa-wand-magic-sparkles"></i> Analyze
            </button>
            <button class="btn btn-secondary btn-xs btn-edit-plant" data-id="${plant.id}" title="Edit plant values">
              <i class="fa-solid fa-pen"></i> Edit
            </button>
            <button class="btn btn-secondary btn-xs btn-delete-plant" data-id="${plant.id}" title="Remove plant" style="background: rgba(239, 68, 68, 0.05); color: #ff5f5f; border-color: rgba(239, 68, 68, 0.2);">
              <i class="fa-solid fa-trash"></i>
            </button>
          </div>
        </div>
      </div>
    `;
  }).join("");
}

// Delete Plant
function deletePlant(id) {
  if (confirm("Are you sure you want to remove this plant?")) {
    state.plants = state.plants.filter(p => String(p.id) !== String(id));
    saveState();
    renderPlants();
    updateThirstyPlants();
  }
}

// Open Edit Plant Modal
function openEditPlantModal(id) {
  const plant = state.plants.find(p => p.id === id);
  if (!plant) return;

  document.getElementById("field-plant-id").value = plant.id;
  document.getElementById("field-plant-name").value = plant.name;
  document.getElementById("field-plant-species").value = plant.species;
  document.getElementById("field-plant-sun").value = plant.sunHours;
  document.getElementById("field-plant-rain-exposure").checked = plant.rainExposure || false;

  let dateVal = "";
  if (plant.lastWatered) {
    try {
      dateVal = new Date(plant.lastWatered).toISOString().slice(0, 16);
    } catch (e) {
      dateVal = new Date().toISOString().slice(0, 16);
    }
  }
  document.getElementById("field-plant-last-watered").value = dateVal;

  if (plant.imageUrl && plant.imageUrl.startsWith("data:")) {
    document.getElementById("field-plant-image").value = "";
    currentUploadedImageDataUrl = plant.imageUrl;
    updateImagePreview(plant.imageUrl);
  } else {
    document.getElementById("field-plant-image").value = plant.imageUrl || "";
    currentUploadedImageDataUrl = "";
    updateImagePreview(plant.imageUrl || "");
  }
  document.getElementById("field-plant-file").value = "";
  document.getElementById("field-plant-desc").value = plant.description || "";

  document.getElementById("modal-plant-title").textContent = "Edit Plant Details";
  modalPlant.classList.add("show");
}

// Fetch Weather details
async function updateWeather() {
  try {
    const query = state.balcony.country ? `${state.balcony.city}, ${state.balcony.country}` : state.balcony.city;
    const data = await fetchWeatherInfo(query);

    weatherWidget.innerHTML = `
      <h3><i class="fa-solid fa-cloud-sun"></i> Current Weather in ${data.city}</h3>
      <div class="weather-grid">
        <div class="weather-metric">
          <span class="lbl">Temperature</span>
          <span class="val">${data.temp_c} °C / ${data.temp_f} °F</span>
        </div>
        <div class="weather-metric">
          <span class="lbl">Humidity</span>
          <span class="val">${data.humidity}%</span>
        </div>
        <div class="weather-metric">
          <span class="lbl">Precipitation</span>
          <span class="val">${data.precipitation_mm} mm / ${data.precipitation_in} in</span>
        </div>
      </div>
    `;
  } catch (err) {
    console.error("Weather load failed:", err);
    weatherWidget.innerHTML = `
      <h3><i class="fa-solid fa-triangle-exclamation"></i> Current Weather</h3>
      <p class="error-msg">Could not load weather details for "${state.balcony.city}".</p>
    `;
  }
}

// Fetch weather info dynamically (proxy vs direct Open-Meteo depending on backend mode)
async function fetchWeatherInfo(city) {
  if (!isLocalBackend) {
    // Cloud Run Mode (FastAPI proxy)
    const res = await fetch(`${apiBase}/api/weather/${encodeURIComponent(city)}`);
    if (!res.ok) throw new Error("Weather fetch failed");
    return await res.json();
  } else {
    // Local Backend Mode (Direct Open-Meteo fetch)
    const geoUrl = `https://geocoding-api.open-meteo.com/v1/search?name=${encodeURIComponent(city)}&count=1&format=json`;
    const geoRes = await fetch(geoUrl);
    if (!geoRes.ok) throw new Error("Geocoding failed");
    const geoData = await geoRes.json();
    if (!geoData.results || geoData.results.length === 0) {
      throw new Error("City not found");
    }
    const location = geoData.results[0];
    const lat = location.latitude;
    const lon = location.longitude;
    const displayName = `${location.name}, ${location.country || ''}`;

    const weatherUrl = `https://api.open-meteo.com/v1/forecast?latitude=${lat}&longitude=${lon}&current=temperature_2m,relative_humidity_2m,precipitation&timezone=auto`;
    const weatherRes = await fetch(weatherUrl);
    if (!weatherRes.ok) throw new Error("Weather forecast failed");
    const weatherData = await weatherRes.json();
    
    const current = weatherData.current;
    const temp_c = current.temperature_2m;
    const temp_f = (temp_c * 9/5) + 32;
    const precip_mm = current.precipitation;
    const precip_in = precip_mm * 0.03937;
    const humidity = current.relative_humidity_2m;

    return {
      city: displayName,
      temp_c: Math.round(temp_c * 10) / 10,
      temp_f: Math.round(temp_f * 10) / 10,
      humidity: humidity,
      precipitation_mm: Math.round(precip_mm * 100) / 100,
      precipitation_in: Math.round(precip_in * 100) / 100
    };
  }
}

// Update Thirsty Plants Panel
function updateThirstyPlants() {
  const thirsty = state.plants.filter(p => p.status === "Water Now");
  const total = state.plants.length;

  if (thirsty.length === 0) {
    if (thirstyHeading) {
      thirstyHeading.innerHTML = `<i class="fa-solid fa-droplet-slash"></i> ${total} ${total === 1 ? 'Plant' : 'Plants'} well hydrated`;
    }
    thirstyContainer.innerHTML = '<p class="empty-thirsty">All plants are well hydrated!</p>';
    return;
  }

  if (thirstyHeading) {
    thirstyHeading.innerHTML = `<i class="fa-solid fa-droplet-slash"></i> ${thirsty.length} Thirsty ${thirsty.length === 1 ? 'Plant' : 'Plants'}`;
  }

  thirstyContainer.innerHTML = thirsty.map(p => {
    const moisture = p.moisture_level !== undefined ? `${p.moisture_level}%` : "0%";
    return `
      <div class="thirsty-item">
        <span class="thirsty-name"><i class="fa-solid fa-droplet animate-pulse"></i> ${p.name}</span>
        <span class="thirsty-moisture">Moisture: ${moisture}</span>
      </div>
    `;
  }).join("");
}

// Analyze Single Plant (individual GET call for gcloud)
async function analyzeSinglePlant(id) {
  const plant = state.plants.find(p => p.id === id);
  if (!plant) return;

  loadingOverlay.classList.add("show");
  loadingText.textContent = `Analyzing ${plant.name} via Agent Runtime...`;

  try {
    const url = new URL(apiBase ? `${apiBase}/api/analyze` : '/api/analyze', window.location.origin);
    url.searchParams.append("city", state.balcony.city);
    url.searchParams.append("country", state.balcony.country || "Germany");
    url.searchParams.append("plant_name", plant.name);
    url.searchParams.append("species", plant.species);
    url.searchParams.append("last_watered", plant.lastWatered);
    url.searchParams.append("sun_hours", plant.sunHours);
    url.searchParams.append("is_covered", state.balcony.isCovered);
    url.searchParams.append("rain_exposure", plant.rainExposure || false);

    const res = await fetch(url);
    if (!res.ok) {
      const errBody = await res.json();
      throw new Error(errBody.detail || "Agent execution failed");
    }

    const data = await res.json();
    const analysis = data.analysis;

    // Update plant details
    plant.moisture_level = analysis.moisture_level;
    plant.status = analysis.status;
    plant.next_watering_date = analysis.next_watering_date;
    plant.explanation = analysis.explanation;
    plant.watering_tips = analysis.watering_tips;
    plant.watered_by_rain = analysis.watered_by_rain;
    plant.effective_last_watered = analysis.effective_last_watered;

    saveState();
    renderPlants();
    updateThirstyPlants();

  } catch (err) {
    alert(`Analysis failed for ${plant.name}: ${err.message}`);
  } finally {
    loadingOverlay.classList.remove("show");
  }
}

// Analyze All Plants in Batch (local POST request)
async function analyzeAllPlantsBatch() {
  if (state.plants.length === 0) {
    alert("Please add at least one plant to run analyses.");
    return;
  }

  loadingOverlay.classList.add("show");
  loadingText.textContent = "AI agents evaluating soil moisture & water needs...";

  const requestBody = {
    balconyConfig: state.balcony,
    plants: state.plants.map(p => ({
      id: p.id,
      name: p.name,
      species: p.species,
      lastWatered: p.lastWatered,
      sunHours: p.sunHours,
      imageUrl: p.imageUrl,
      description: p.description,
      rainExposure: p.rainExposure || false
    }))
  };

  try {
    const response = await fetch(`${apiBase}/api/analyze`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify(requestBody)
    });

    if (!response.ok) {
      const errData = await response.json();
      throw new Error(errData.detail || "Server error during analysis.");
    }

    const data = await response.json();

    if (data.success && data.analyses) {
      // Merge results back into plants state
      data.analyses.forEach(result => {
        const plantIndex = state.plants.findIndex(p => p.id === result.plant_id);
        if (plantIndex !== -1) {
          state.plants[plantIndex].moisture_level = result.moisture_level;
          state.plants[plantIndex].status = result.status;
          state.plants[plantIndex].next_watering_date = result.next_watering_date;
          state.plants[plantIndex].explanation = result.explanation;
          state.plants[plantIndex].watering_tips = result.watering_tips;
          state.plants[plantIndex].watered_by_rain = result.watered_by_rain;
          state.plants[plantIndex].effective_last_watered = result.effective_last_watered;
        }
      });

      saveState();
      renderPlants();
      updateThirstyPlants();
    } else {
      throw new Error("Invalid analysis result received.");
    }

  } catch (err) {
    alert(`Error during AI analysis: ${err.message}\n\nMake sure the FastAPI server is running (Port 8000) and the GEMINI_API_KEY is set.`);
  } finally {
    loadingOverlay.classList.remove("show");
  }
}

// Run AI Analysis Trigger (Unified)
btnAnalyzeAll.addEventListener("click", async () => {
  if (state.plants.length === 0) {
    alert("Please add at least one plant to run analyses.");
    return;
  }

  if (isLocalBackend) {
    // Local batch analysis
    await analyzeAllPlantsBatch();
  } else {
    // Gcloud sequential individual analyses
    for (const plant of state.plants) {
      await analyzeSinglePlant(plant.id);
    }
  }
});

// Modals logic
btnAddPlant.addEventListener("click", () => {
  formPlant.reset();
  document.getElementById("field-plant-id").value = "";
  document.getElementById("field-plant-sun").value = state.balcony.defaultSunHours;
  document.getElementById("field-plant-rain-exposure").checked = state.balcony.isCovered || false;

  const dateInput = document.getElementById("field-plant-last-watered");
  const oneDayAgo = new Date(Date.now() - 24 * 60 * 60 * 1000);
  dateInput.value = oneDayAgo.toISOString().slice(0, 16);

  currentUploadedImageDataUrl = "";
  updateImagePreview("");
  fieldPlantFile.value = "";

  document.getElementById("modal-plant-title").textContent = "Add New Plant";
  modalPlant.classList.add("show");
});

btnEditBalcony.addEventListener("click", () => {
  document.getElementById("field-balcony-city").value = state.balcony.city;
  document.getElementById("field-balcony-country").value = state.balcony.country || "Germany";
  document.getElementById("field-balcony-zip").value = state.balcony.zipCode;
  document.getElementById("field-balcony-sun").value = state.balcony.defaultSunHours;
  document.getElementById("field-balcony-covered").checked = state.balcony.isCovered;
  modalBalcony.classList.add("show");
});

function closeModal() {
  modalPlant.classList.remove("show");
  modalBalcony.classList.remove("show");
}

closePlant.addEventListener("click", closeModal);
closeBalcony.addEventListener("click", closeModal);
btnCancelPlant.addEventListener("click", closeModal);
btnCancelBalcony.addEventListener("click", closeModal);
window.addEventListener("click", (e) => {
  if (e.target === modalPlant || e.target === modalBalcony) closeModal();
});

// Image Upload utilities
function updateImagePreview(src) {
  if (src) {
    imagePreviewImg.src = src;
    imagePreviewGroup.style.display = "block";
  } else {
    imagePreviewImg.src = "";
    imagePreviewGroup.style.display = "none";
  }
}

fieldPlantImage.addEventListener("input", () => {
  const val = fieldPlantImage.value.trim();
  if (val) {
    currentUploadedImageDataUrl = ""; // URL takes precedence
    updateImagePreview(val);
  } else {
    updateImagePreview(currentUploadedImageDataUrl);
  }
});

fieldPlantFile.addEventListener("change", (e) => {
  const file = e.target.files[0];
  if (!file) return;

  const reader = new FileReader();
  reader.onload = function (event) {
    const img = new Image();
    img.onload = function () {
      const canvas = document.createElement("canvas");
      const maxDim = 400;
      let width = img.width;
      let height = img.height;

      if (width > height) {
        if (width > maxDim) {
          height = Math.round((height * maxDim) / width);
          width = maxDim;
        }
      } else {
        if (height > maxDim) {
          width = Math.round((width * maxDim) / height);
          height = maxDim;
        }
      }

      canvas.width = width;
      canvas.height = height;
      const ctx = canvas.getContext("2d");
      ctx.drawImage(img, 0, 0, width, height);

      currentUploadedImageDataUrl = canvas.toDataURL("image/jpeg", 0.75);
      fieldPlantImage.value = ""; // Clear URL if uploading file
      updateImagePreview(currentUploadedImageDataUrl);
    };
    img.src = event.target.result;
  };
  reader.readAsDataURL(file);
});

btnRemoveImage.addEventListener("click", () => {
  currentUploadedImageDataUrl = "";
  fieldPlantImage.value = "";
  fieldPlantFile.value = "";
  updateImagePreview("");
});

// Save Plant Form
formPlant.addEventListener("submit", (e) => {
  e.preventDefault();

  const id = document.getElementById("field-plant-id").value || `plant-${Math.random().toString(36).substring(2, 9)}`;
  const name = document.getElementById("field-plant-name").value.trim();
  const species = document.getElementById("field-plant-species").value;
  const sunHours = parseFloat(document.getElementById("field-plant-sun").value);
  const lastWatered = new Date(document.getElementById("field-plant-last-watered").value).toISOString();
  const description = document.getElementById("field-plant-desc").value.trim();
  const rainExposure = document.getElementById("field-plant-rain-exposure").checked;

  const urlInput = fieldPlantImage.value.trim();
  const imageUrl = urlInput || currentUploadedImageDataUrl || "";

  const existingIdx = state.plants.findIndex(p => p.id === id);

  if (existingIdx !== -1) {
    const oldPlant = state.plants[existingIdx];
    state.plants[existingIdx] = {
      ...oldPlant,
      name,
      species,
      sunHours,
      lastWatered,
      imageUrl,
      description,
      rainExposure
    };
  } else {
    const plantData = {
      id,
      name,
      species,
      sunHours,
      lastWatered,
      imageUrl,
      description,
      status: "Healthy",
      moisture_level: undefined,
      next_watering_date: undefined,
      explanation: undefined,
      rainExposure
    };
    state.plants.push(plantData);
  }

  saveState();
  renderPlants();
  updateThirstyPlants();
  closeModal();
});

// Save Balcony Form
formBalcony.addEventListener("submit", (e) => {
  e.preventDefault();

  state.balcony.city = document.getElementById("field-balcony-city").value.trim();
  state.balcony.country = document.getElementById("field-balcony-country").value.trim();
  state.balcony.zipCode = document.getElementById("field-balcony-zip").value.trim();
  state.balcony.defaultSunHours = parseFloat(document.getElementById("field-balcony-sun").value);
  state.balcony.isCovered = document.getElementById("field-balcony-covered").checked;

  saveState();
  renderBalcony();
  updateWeather();
  closeModal();
});

// Reset Defaults
btnResetDefaults.addEventListener("click", () => {
  if (confirm("Reset balcony settings and plant inventory to original defaults? All local edits will be cleared.")) {
    state.plants = DEFAULT_PLANTS;
    state.balcony = DEFAULT_BALCONY;
    saveState();
    renderBalcony();
    renderPlants();
    updateWeather();
    updateThirstyPlants();
  }
});

// Backup Export
btnBackupExport.addEventListener("click", () => {
  const backupData = JSON.stringify(state, null, 2);
  const blob = new Blob([backupData], { type: "application/json" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = `florawave_backup_${new Date().toISOString().split('T')[0]}.json`;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
});

// Backup Import Trigger
btnBackupImport.addEventListener("click", () => {
  backupFileInput.click();
});

backupFileInput.addEventListener("change", (e) => {
  const file = e.target.files[0];
  if (!file) return;

  const reader = new FileReader();
  reader.onload = (event) => {
    try {
      const importedState = JSON.parse(event.target.result);
      if (importedState.balcony && Array.isArray(importedState.plants)) {
        state = importedState;
        saveState();
        renderBalcony();
        renderPlants();
        updateWeather();
        updateThirstyPlants();
        alert("Backup successfully imported!");
      } else {
        throw new Error("Invalid data structure.");
      }
    } catch (err) {
      alert("Error loading backup: " + err.message);
    }
  };
  reader.readAsText(file);
});

// Plant card action buttons
plantsGrid.addEventListener("click", (e) => {
  const btnDelete = e.target.closest(".btn-delete-plant");
  const btnAnalyze = e.target.closest(".btn-analyze-single");
  const btnEdit = e.target.closest(".btn-edit-plant");

  if (btnDelete) {
    const id = btnDelete.getAttribute("data-id");
    deletePlant(id);
  } else if (btnAnalyze) {
    const id = btnAnalyze.getAttribute("data-id");
    analyzeSinglePlant(id);
  } else if (btnEdit) {
    const id = btnEdit.getAttribute("data-id");
    openEditPlantModal(id);
  }
});

// Initial Setup
function init() {
  renderBalcony();
  renderPlants();
  updateWeather();
  updateThirstyPlants();
}

window.addEventListener("DOMContentLoaded", init);
