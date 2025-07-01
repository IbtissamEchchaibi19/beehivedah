import pandas as pd
import numpy as np
import json
from datetime import datetime, timedelta

def generate_beehive_data():
    """Generate realistic beehive monitoring data with production tracking"""
    
    # Define hive structure
    hives_config = [
        {'id': 'master_001', 'name': 'Master Hive Alpha', 'type': 'master', 'location': 'North Field', 'master_id': None},
        {'id': 'worker_001', 'name': 'Worker Hive 1', 'type': 'worker', 'location': 'North Field', 'master_id': 'master_001'},
        {'id': 'worker_002', 'name': 'Worker Hive 2', 'type': 'worker', 'location': 'North Field', 'master_id': 'master_001'},
        {'id': 'worker_003', 'name': 'Worker Hive 3', 'type': 'worker', 'location': 'East Field', 'master_id': 'master_001'},
        {'id': 'master_002', 'name': 'Master Hive Beta', 'type': 'master', 'location': 'South Field', 'master_id': None},
        {'id': 'worker_004', 'name': 'Worker Hive 4', 'type': 'worker', 'location': 'South Field', 'master_id': 'master_002'},
        {'id': 'worker_005', 'name': 'Worker Hive 5', 'type': 'worker', 'location': 'West Field', 'master_id': 'master_002'},
    ]
    
    # Generate time series data
    end_time = datetime.now()
    start_time = end_time - timedelta(days=30)  # 30 days of data
    time_range = pd.date_range(start=start_time, end=end_time, freq='h')
    
    data = []
    
    # Initialize cumulative production for each hive
    cumulative_production = {hive['id']: 0 for hive in hives_config}
    
    for timestamp in time_range:
        hour = timestamp.hour
        day_of_year = timestamp.timetuple().tm_yday
        
        for hive in hives_config:
            # Simulate realistic beehive patterns
            # Temperature: varies with time of day and season
            base_temp = 35 + 3 * np.sin(2 * np.pi * hour / 24) + 2 * np.sin(2 * np.pi * day_of_year / 365)
            temp_noise = np.random.normal(0, 0.5)
            temperature = base_temp + temp_noise
            
            # Humidity: inverse relationship with temperature
            base_humidity = 65 - 10 * np.sin(2 * np.pi * hour / 24) + 5 * np.sin(2 * np.pi * day_of_year / 365)
            humidity_noise = np.random.normal(0, 2)
            humidity = max(30, min(90, base_humidity + humidity_noise))
            
            # Weight: seasonal variation + daily foraging patterns
            base_weight = 40 if hive['type'] == 'master' else 32
            seasonal_weight = 5 * np.sin(2 * np.pi * day_of_year / 365)
            daily_weight = -2 * np.sin(2 * np.pi * (hour - 6) / 24) if 6 <= hour <= 18 else 0
            weight_noise = np.random.normal(0, 0.3)
            weight = base_weight + seasonal_weight + daily_weight + weight_noise
            
            # Activity level (0-100)
            base_activity = 50 + 30 * np.sin(2 * np.pi * (hour - 6) / 12) if 6 <= hour <= 18 else 20
            activity = max(0, min(100, base_activity + np.random.normal(0, 10)))
            
            # Production calculations
            # Hourly production rate (kg) - influenced by activity, temperature, and hive type
            production_multiplier = 1.5 if hive['type'] == 'master' else 1.0
            
            # Optimal production conditions: temp 33-37°C, humidity 45-65%, high activity
            temp_factor = 1.0 if 33 <= temperature <= 37 else 0.7
            humidity_factor = 1.0 if 45 <= humidity <= 65 else 0.8
            activity_factor = activity / 100
            
            # Seasonal production factor (spring/summer peak)
            seasonal_factor = 0.5 + 0.8 * (0.5 + 0.5 * np.sin(2 * np.pi * (day_of_year - 80) / 365))
            
            # Base hourly production (very small amounts, realistic for honey production)
            base_hourly_production = 0.008 * production_multiplier  # ~0.008 kg/hour max
            
            # Only produce during active hours (6 AM to 8 PM)
            if 6 <= hour <= 20:
                hourly_production = (base_hourly_production * temp_factor * 
                                   humidity_factor * activity_factor * seasonal_factor)
                # Add some randomness
                hourly_production *= np.random.uniform(0.7, 1.3)
            else:
                hourly_production = 0
            
            # Update cumulative production
            cumulative_production[hive['id']] += hourly_production
            
            # Calculate production efficiency (production per unit activity)
            production_efficiency = hourly_production / (activity / 100) if activity > 0 else 0
            
            data.append({
                'timestamp': timestamp.isoformat(),  # Convert to string for JSON
                'hive_id': hive['id'],
                'hive_name': hive['name'],
                'hive_type': hive['type'],
                'location': hive['location'],
                'master_id': hive['master_id'],
                'temperature': round(temperature, 1),
                'humidity': round(humidity, 1),
                'weight': round(weight, 1),
                'activity_level': round(activity, 0),
                'hourly_production': round(hourly_production, 4),
                'cumulative_production': round(cumulative_production[hive['id']], 3),
                'production_efficiency': round(production_efficiency, 4)
            })
    
    return data, hives_config

def save_data_to_json():
    """Generate data and save to JSON files"""
    print("Generating beehive data...")
    data, hives_config = generate_beehive_data()
    
    # Save main data
    with open('beehive_data.json', 'w') as f:
        json.dump(data, f, indent=2)
    
    # Save hives configuration
    with open('hives_config.json', 'w') as f:
        json.dump(hives_config, f, indent=2)
    
    print(f"✅ Generated {len(data)} data points for {len(hives_config)} hives")
    print("✅ Data saved to 'beehive_data.json'")
    print("✅ Configuration saved to 'hives_config.json'")
    
    return True

if __name__ == "__main__":
    # Run this script to generate and save JSON data
    save_data_to_json()