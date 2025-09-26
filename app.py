from flask import Flask, render_template, request, jsonify, session
from datetime import datetime, timedelta
import json
import os
import csv
import pandas as pd

app = Flask(__name__, template_folder='app_interface')
app.secret_key = 'your-secret-key-change-this'

def load_nutrition_data():
    """Load nutrition requirements from CSV file"""
    try:
        # Use the edited CSV file with updated values for 65kg male and 70kg female
        df = pd.read_csv('weekly_nutrition_requirements_EDITED_Moderate_65kgM_70kgF.csv')
        return df.to_dict('records')
    except Exception as e:
        print(f"Error loading CSV: {e}")
        # Fallback to original file if edited version not found
        try:
            df = pd.read_csv('weekly_nutrition_requirements.csv')
            return df.to_dict('records')
        except Exception as e2:
            print(f"Error loading fallback CSV: {e2}")
            return []

# Key nutritional requirements based on ICMR-NIN 2020 guidelines
NUTRITION_REQUIREMENTS = {
    'macronutrients': {
        'Carbohydrates': {'daily_min': 100, 'unit': 'g', 'description': 'Primary energy source for brain and body'},
        'Proteins': {'daily_min': 54, 'unit': 'g', 'description': 'Building blocks for tissues and enzymes'},
        'Fats': {'daily_min': 25, 'unit': 'g', 'description': 'Essential for hormone production and vitamin absorption'},
        'Fiber': {'daily_min': 25, 'unit': 'g', 'description': 'Important for digestive health'},
        'Water': {'daily_min': 2.5, 'unit': 'L', 'description': 'Essential for all body functions'}
    },
    'micronutrients': {
        'Iron': {'daily_min': 19, 'unit': 'mg', 'description': 'Prevents anemia, supports oxygen transport'},
        'Calcium': {'daily_min': 1000, 'unit': 'mg', 'description': 'Strong bones and teeth, muscle function'},
        'Vitamin B12': {'daily_min': 2.2, 'unit': 'µg', 'description': 'Red blood cell formation, nerve function'},
        'Vitamin D': {'daily_min': 600, 'unit': 'IU', 'description': 'Bone health, immune function'},
        'Vitamin C': {'daily_min': 65, 'unit': 'mg', 'description': 'Immune system, iron absorption'},
        'Zinc': {'daily_min': 17, 'unit': 'mg', 'description': 'Immune function, wound healing'},
        'Folate': {'daily_min': 220, 'unit': 'µg', 'description': 'DNA synthesis, prevents birth defects'},
        'Vitamin A': {'daily_min': 840, 'unit': 'µg', 'description': 'Vision, immune function, skin health'}
    }
}

INDIAN_FOOD_SOURCES = {
    'Iron': ['Dal (lentils)', 'Spinach', 'Chickpeas', 'Ragi', 'Jaggery'],
    'Calcium': ['Milk', 'Paneer', 'Curd', 'Ragi', 'Sesame seeds'],
    'Vitamin B12': ['Eggs', 'Fish', 'Milk', 'Paneer', 'Fortified cereals'],
    'Vitamin D': ['Sunlight exposure', 'Fatty fish', 'Egg yolks', 'Fortified milk'],
    'Vitamin C': ['Amla', 'Lemon', 'Tomatoes', 'Guava', 'Bell peppers'],
    'Zinc': ['Legumes', 'Nuts', 'Seeds', 'Whole grains', 'Paneer'],
    'Folate': ['Green leafy vegetables', 'Legumes', 'Fortified cereals', 'Citrus fruits'],
    'Vitamin A': ['Carrots', 'Sweet potatoes', 'Spinach', 'Mango', 'Papaya'],
    'Carbohydrates': ['Rice', 'Wheat', 'Millets', 'Quinoa', 'Sweet potatoes'],
    'Proteins': ['Dal', 'Paneer', 'Eggs', 'Fish', 'Chicken'],
    'Fats': ['Ghee', 'Coconut oil', 'Nuts', 'Seeds', 'Avocado'],
    'Fiber': ['Whole grains', 'Vegetables', 'Fruits', 'Legumes', 'Nuts'],
    'Water': ['Plain water', 'Coconut water', 'Herbal teas', 'Fruits', 'Soups']
}

def get_current_week():
    """Get the current week's Monday date"""
    today = datetime.now()
    monday = today - timedelta(days=today.weekday())
    return monday.strftime('%Y-%m-%d')

def load_user_data():
    """Load user's weekly tracking data"""
    week = get_current_week()
    filename = f'nutrition_data_{week}.json'
    
    if os.path.exists(filename):
        with open(filename, 'r') as f:
            return json.load(f)
    else:
        # Initialize empty data for the week
        days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        data = {}
        for day in days:
            data[day] = {}
            for category in NUTRITION_REQUIREMENTS:
                data[day][category] = {}
                for nutrient in NUTRITION_REQUIREMENTS[category]:
                    data[day][category][nutrient] = 0
        return data

def save_user_data(data):
    """Save user's weekly tracking data"""
    week = get_current_week()
    filename = f'nutrition_data_{week}.json'
    with open(filename, 'w') as f:
        json.dump(data, f, indent=2)

@app.route('/')
def index():
    """Main dashboard page"""
    user_data = load_user_data()
    current_week = get_current_week()
    nutrition_data = load_nutrition_data()
    return render_template('index.html', 
                         requirements=NUTRITION_REQUIREMENTS,
                         food_sources=INDIAN_FOOD_SOURCES,
                         user_data=user_data,
                         current_week=current_week,
                         nutrition_data=nutrition_data)

@app.route('/update_nutrient', methods=['POST'])
def update_nutrient():
    """Update nutrient intake for a specific day"""
    data = request.json
    day = data['day']
    category = data['category']
    nutrient = data['nutrient']
    amount = float(data['amount'])
    
    user_data = load_user_data()
    user_data[day][category][nutrient] = amount
    save_user_data(user_data)
    
    return jsonify({'status': 'success'})

@app.route('/education')
def nutrition_education():
    """Nutrition education page"""
    return app.send_static_file('nutrition_education.html')

@app.route('/complete-guide')
def complete_nutrition_guide():
    """Complete nutrition guide with all JSON data"""
    return app.send_static_file('complete_nutrition_guide.html')

@app.route('/structured-guide')
def structured_nutrition_guide():
    """Structured nutrition guide with interactive references"""
    return app.send_static_file('structured_nutrition_guide.html')

@app.route('/refresh-nutrition-data')
def refresh_nutrition_data():
    """Refresh nutrition data from CSV file"""
    try:
        nutrition_data = load_nutrition_data()
        return jsonify({
            'status': 'success',
            'message': f'Loaded {len(nutrition_data)} nutrition records',
            'data': nutrition_data
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'Error refreshing data: {str(e)}'
        }), 500

@app.route('/get_weekly_summary')
def get_weekly_summary():
    """Get weekly summary of nutrition intake"""
    user_data = load_user_data()
    summary = {}
    
    for category in NUTRITION_REQUIREMENTS:
        summary[category] = {}
        for nutrient in NUTRITION_REQUIREMENTS[category]:
            total_intake = 0
            daily_target = NUTRITION_REQUIREMENTS[category][nutrient]['daily_min']
            weekly_target = daily_target * 7
            
            for day in user_data:
                total_intake += user_data[day][category].get(nutrient, 0)
            
            summary[category][nutrient] = {
                'total_intake': total_intake,
                'weekly_target': weekly_target,
                'percentage': round((total_intake / weekly_target) * 100, 1) if weekly_target > 0 else 0
            }
    
    return jsonify(summary)

if __name__ == '__main__':
    import os
    port = int(os.environ.get('PORT', 8080))
    app.run(debug=False, host='0.0.0.0', port=port)
