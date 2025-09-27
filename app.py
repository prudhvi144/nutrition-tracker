from flask import Flask, render_template, request, jsonify, session, send_file, Response
from datetime import datetime, timedelta
import json
import os
import csv
import pandas as pd
import plotly.graph_objs as go
import plotly.utils
import io
import base64
import re
import requests
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__, template_folder='app_interface')
app.secret_key = 'your-secret-key-change-this'

# GitHub API Configuration
GITHUB_TOKEN = os.environ.get('GITHUB_TOKEN', '')  # Set this in environment variables
GITHUB_REPO = 'prudhvi144/nutrition-tracker'  # Your GitHub repo
GITHUB_API_BASE = 'https://api.github.com'

def get_github_headers():
    """Get headers for GitHub API requests"""
    return {
        'Authorization': f'token {GITHUB_TOKEN}',
        'Accept': 'application/vnd.github.v3+json',
        'Content-Type': 'application/json'
    }

def get_github_file(file_path):
    """Get file content from GitHub repository"""
    url = f'{GITHUB_API_BASE}/repos/{GITHUB_REPO}/contents/{file_path}'
    
    try:
        response = requests.get(url, headers=get_github_headers())
        if response.status_code == 200:
            file_data = response.json()
            # Decode base64 content
            content = base64.b64decode(file_data['content']).decode('utf-8')
            return json.loads(content), file_data['sha']
        elif response.status_code == 404:
            # File doesn't exist, return empty data
            return {}, None
        else:
            print(f"GitHub API Error: {response.status_code} - {response.text}")
            return {}, None
    except Exception as e:
        print(f"Error fetching GitHub file: {e}")
        return {}, None

def update_github_file(file_path, content, sha=None, commit_message="Update BMI data"):
    """Update file in GitHub repository"""
    url = f'{GITHUB_API_BASE}/repos/{GITHUB_REPO}/contents/{file_path}'
    
    # Encode content to base64
    content_encoded = base64.b64encode(json.dumps(content, indent=2).encode('utf-8')).decode('utf-8')
    
    data = {
        'message': commit_message,
        'content': content_encoded
    }
    
    if sha:
        data['sha'] = sha
    
    try:
        response = requests.put(url, headers=get_github_headers(), json=data)
        if response.status_code in [200, 201]:
            return True
        else:
            print(f"GitHub API Error: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        print(f"Error updating GitHub file: {e}")
        return False

def get_user_data_file(user_name):
    """Get file path for user's BMI data"""
    return f'bmi_data/{user_name.lower().replace(" ", "_")}_bmi.json'

def init_bmi_storage():
    """Initialize GitHub storage - create directory structure if needed"""
    # This will be handled automatically when we create the first file
    pass

def calculate_bmi(height_cm, weight_kg):
    """Calculate BMI given height in cm and weight in kg"""
    height_m = height_cm / 100
    return weight_kg / (height_m * height_m)

def get_bmi_category(bmi):
    """Get BMI category and description"""
    if bmi < 18.5:
        return "Underweight", "Consider gaining weight for better health", "#2196F3"
    elif 18.5 <= bmi < 25:
        return "Normal Weight", "Healthy weight range - keep it up!", "#4CAF50"
    elif 25 <= bmi < 30:
        return "Overweight", "Consider weight management strategies", "#FF9800"
    else:
        return "Obese", "Consult healthcare provider for guidance", "#F44336"


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

# BMI Tracker Routes
@app.route('/bmi-tracker')
def bmi_tracker():
    """BMI Calculator & Tracker main page"""
    return render_template('bmi_tracker.html')

@app.route('/save_user_profile', methods=['POST'])
def save_user_profile():
    """Save user profile with height preference"""
    data = request.json
    name = data['name']
    height_cm = float(data['height_cm'])
    unit_preference = data.get('unit_preference', 'metric')
    
    # Get user's data file
    file_path = get_user_data_file(name)
    user_data, sha = get_github_file(file_path)
    
    # Update profile information
    if not user_data:
        user_data = {
            'profile': {},
            'records': []
        }
    
    user_data['profile'] = {
        'name': name,
        'height_cm': height_cm,
        'unit_preference': unit_preference,
        'created_at': datetime.now().isoformat()
    }
    
    # Save to GitHub
    success = update_github_file(file_path, user_data, sha, f"Update profile for {name}")
    
    if success:
        return jsonify({'status': 'success', 'message': 'Profile saved successfully'})
    else:
        return jsonify({'status': 'error', 'message': 'Failed to save profile'}), 500

@app.route('/get_user_profile/<name>')
def get_user_profile(name):
    """Get user profile"""
    file_path = get_user_data_file(name)
    user_data, _ = get_github_file(file_path)
    
    if user_data and 'profile' in user_data:
        profile = user_data['profile']
        return jsonify({
            'name': profile['name'],
            'height_cm': profile['height_cm'],
            'unit_preference': profile['unit_preference']
        })
    else:
        return jsonify({'error': 'User not found'}), 404

@app.route('/add_bmi_record', methods=['POST'])
def add_bmi_record():
    """Add new BMI record"""
    data = request.json
    user_name = data['user_name']
    date = data['date']
    weight = float(data['weight'])
    weight_unit = data.get('weight_unit', 'kg')
    
    # Get user's data
    file_path = get_user_data_file(user_name)
    user_data, sha = get_github_file(file_path)
    
    if not user_data or 'profile' not in user_data:
        return jsonify({'error': 'User profile not found. Please save profile first.'}), 404
    
    height_cm = user_data['profile']['height_cm']
    
    # Convert weight to kg if needed
    weight_kg = weight
    if weight_unit.lower() in ['lbs', 'lb', 'pounds']:
        weight_kg = weight * 0.453592
    
    # Calculate BMI
    bmi = calculate_bmi(height_cm, weight_kg)
    
    # Create new record
    new_record = {
        'date': date,
        'weight': weight,
        'bmi': round(bmi, 2),
        'weight_unit': weight_unit,
        'created_at': datetime.now().isoformat()
    }
    
    # Add record to user data
    if 'records' not in user_data:
        user_data['records'] = []
    
    user_data['records'].append(new_record)
    
    # Sort records by date (newest first)
    user_data['records'].sort(key=lambda x: x['date'], reverse=True)
    
    # Save to GitHub
    success = update_github_file(file_path, user_data, sha, f"Add BMI record for {user_name} on {date}")
    
    if success:
        category, description, color = get_bmi_category(bmi)
        return jsonify({
            'status': 'success',
            'bmi': round(bmi, 1),
            'category': category,
            'description': description,
            'color': color
        })
    else:
        return jsonify({'error': 'Failed to save BMI record'}), 500

@app.route('/get_bmi_records/<user_name>')
def get_bmi_records(user_name):
    """Get all BMI records for a user"""
    file_path = get_user_data_file(user_name)
    user_data, _ = get_github_file(file_path)
    
    if user_data and 'records' in user_data:
        records = user_data['records']
        return jsonify([{
            'date': record['date'],
            'weight': record['weight'],
            'bmi': round(record['bmi'], 1),
            'weight_unit': record['weight_unit']
        } for record in records])
    else:
        return jsonify([])

@app.route('/export_bmi_csv/<user_name>')
def export_bmi_csv(user_name):
    """Export BMI data as CSV"""
    file_path = get_user_data_file(user_name)
    user_data, _ = get_github_file(file_path)
    
    if not user_data or 'records' not in user_data:
        return jsonify({'error': 'No data found'}), 404
    
    records = user_data['records']
    # Sort by date ascending for CSV export
    records_sorted = sorted(records, key=lambda x: x['date'])
    
    # Create CSV content
    csv_content = "Date,Weight,BMI,Weight Unit\n"
    for record in records_sorted:
        csv_content += f"{record['date']},{record['weight']},{record['bmi']:.1f},{record['weight_unit']}\n"
    
    # Create response
    response = Response(
        csv_content,
        mimetype='text/csv',
        headers={'Content-Disposition': f'attachment; filename={user_name}_bmi_data.csv'}
    )
    
    return response

@app.route('/get_bmi_chart/<user_name>')
def get_bmi_chart(user_name):
    """Generate BMI progress chart"""
    file_path = get_user_data_file(user_name)
    user_data, _ = get_github_file(file_path)
    
    if not user_data or 'records' not in user_data or not user_data['records']:
        return jsonify({'error': 'No data found'}), 404
    
    # Sort records by date ascending for charts
    records = sorted(user_data['records'], key=lambda x: x['date'])
    
    dates = [record['date'] for record in records]
    weights = [record['weight'] for record in records]
    bmis = [record['bmi'] for record in records]
    
    # Create BMI chart
    fig = go.Figure()
    
    # Add BMI line
    fig.add_trace(go.Scatter(
        x=dates,
        y=bmis,
        mode='lines+markers',
        name='BMI',
        line=dict(color='#2196F3', width=3),
        marker=dict(size=8)
    ))
    
    # Add BMI category zones
    fig.add_hline(y=18.5, line_dash="dash", line_color="blue", 
                  annotation_text="Underweight", annotation_position="bottom right")
    fig.add_hline(y=25, line_dash="dash", line_color="green", 
                  annotation_text="Normal", annotation_position="bottom right")
    fig.add_hline(y=30, line_dash="dash", line_color="orange", 
                  annotation_text="Overweight", annotation_position="bottom right")
    
    fig.update_layout(
        title=f'{user_name}\'s BMI Progress',
        xaxis_title='Date',
        yaxis_title='BMI',
        hovermode='x unified',
        template='plotly_white'
    )
    
    # Create weight chart
    fig2 = go.Figure()
    
    fig2.add_trace(go.Scatter(
        x=dates,
        y=weights,
        mode='lines+markers',
        name='Weight',
        line=dict(color='#4CAF50', width=3),
        marker=dict(size=8)
    ))
    
    fig2.update_layout(
        title=f'{user_name}\'s Weight Progress',
        xaxis_title='Date',
        yaxis_title='Weight (kg)',
        hovermode='x unified',
        template='plotly_white'
    )
    
    return jsonify({
        'bmi_chart': plotly.utils.PlotlyJSONEncoder().encode(fig),
        'weight_chart': plotly.utils.PlotlyJSONEncoder().encode(fig2)
    })


if __name__ == '__main__':
    # Initialize GitHub storage
    init_bmi_storage()
    
    import os
    port = int(os.environ.get('PORT', 8080))
    app.run(debug=False, host='0.0.0.0', port=port)
