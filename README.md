# Weekly Nutrition Tracker

A simple web app to help you track your daily nutrition intake and ensure you're meeting all essential nutrient requirements throughout the week.

## Features

- 📱 **Mobile-friendly design** - Works perfectly on phones and tablets
- 📊 **Daily tracking** - Log your nutrient intake for each day of the week
- 📈 **Progress visualization** - See how close you are to meeting your targets
- 🥗 **Food suggestions** - Get recommendations for Indian foods rich in specific nutrients
- 📋 **Weekly summary** - Overview of your nutrition progress for the entire week
- 🇮🇳 **Indian guidelines** - Based on ICMR-NIN 2020 recommendations for Indian adults

## Quick Start

1. **Install Python** (if not already installed)
   - Download from [python.org](https://python.org) if needed

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the app**:
   ```bash
   python app.py
   ```

4. **Open in browser**:
   - On computer: Go to `http://localhost:8080`
   - On phone: Go to `http://YOUR_COMPUTER_IP:8080` (e.g., `http://192.168.1.100:8080`)

## How to Use

### Daily Tracking
1. Select the day of the week you want to track
2. Enter the amounts of nutrients you've consumed
3. Click "Update" to save your progress
4. The progress bars show how close you are to daily targets

### Weekly Summary
- Switch to the "Weekly Summary" tab to see your overall progress
- Green indicates you've met targets, orange means you're close, red means you need more

### Finding Your Computer's IP (for phone access)
- **Windows**: Open Command Prompt, type `ipconfig`, look for "IPv4 Address"
- **Mac**: System Preferences > Network > Select your connection
- **Linux**: Terminal, type `ip addr show`

## Tracked Nutrients

### Macronutrients
- Carbohydrates (100g/day minimum)
- Proteins (54g/day for average adult male)
- Fats (25g/day minimum)
- Fiber (25g/day)
- Water (2.5L/day)

### Micronutrients
- Iron, Calcium, Vitamin B12, Vitamin D
- Vitamin C, Zinc, Folate, Vitamin A

## Data Storage

Your nutrition data is automatically saved in JSON files named by week (e.g., `nutrition_data_2024-09-23.json`). Each week gets its own file so you can track progress over time.

## Customization

To adjust targets for your specific needs, edit the `NUTRITION_REQUIREMENTS` dictionary in `app.py`. The current values are set for a sedentary adult male based on ICMR-NIN 2020 guidelines.

## Tips for Success

- 🌅 Get 15-20 minutes of sunlight daily for Vitamin D
- 🥛 Include dairy products for calcium and B12
- 🥬 Eat green leafy vegetables for iron and folate
- 🌾 Choose whole grains and millets over refined grains
- 💧 Keep a water bottle handy to stay hydrated

---

*Based on ICMR-NIN 2020 nutritional guidelines for Indian adults*
