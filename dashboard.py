import dash
from dash import dcc, html, Input, Output, callback_context, dash_table
import plotly.graph_objs as go
import plotly.express as px
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from data_loader import load_beehive_data_from_json, get_data_info

# Initialize the Dash app
app = dash.Dash(__name__, title="Honey Production Intelligence Dashboard", requests_pathname_prefix='/dash_app/')
app.title = "Beehive Analytics Dashboard"
app.index_string = '''
<!DOCTYPE html>
<html>
    <head>
        {%metas%}
        <title>{%title%}</title>
        {%favicon%}
        {%css%}
        <style>
            .card {
                border: 1px solid #ddd;
                border-radius: 8px;
                padding: 20px;
                margin: 10px;
                text-align: center;
                background-color: #f9f9f9;
                min-width: 200px;
            }
            .card h3 {
                margin: 0 0 10px 0;
                color: #666;
            }
            .card h2 {
                margin: 0;
                color: #333;
            }
            /* Prevent plotly graphs from auto-resizing */
            .js-plotly-plot {
                width: 100% !important;
                height: 400px !important;
            }
        </style>
    </head>
    <body>
        {%app_entry%}
        <footer>
            {%config%}
            {%scripts%}
            {%renderer%}
        </footer>
    </body>
</html>'''

# Load initial data
try:
    df, hives_config = load_beehive_data_from_json()
    print("🚀 Dashboard initialized with auto-updating GitHub data loader")
except FileNotFoundError as e:
    print("❌ Error:", str(e))
    print("📝 Please ensure JSON files exist in your GitHub repository")
    exit(1)
except Exception as e:
    print("❌ Error loading data:", str(e))
    exit(1)

# Dashboard layout
app.layout = html.Div([
    # Header
    html.Div([
        html.H1("🐝 Advanced Beehive Analytics Dashboard with Production Tracking", 
               style={'textAlign': 'center', 'color': '#2E86AB', 'marginBottom': '30px'}),
        html.Hr()
    ]),
    
    # Control Panel
    html.Div([
        html.Div([
            html.H4("Control Panel", style={'marginBottom': '15px'}),
            html.Div([
                html.Div([
                    html.Label("Time Range:", style={'fontWeight': 'bold'}),
                    dcc.Dropdown(
                        id='time-range-dropdown',
                        options=[
                            {'label': 'Last 24 Hours', 'value': '24h'},
                            {'label': 'Last 7 Days', 'value': '7d'},
                            {'label': 'Last 30 Days', 'value': '30d'}
                        ],
                        value='7d',
                        style={'marginBottom': '10px'}
                    )
                ], style={'width': '48%', 'display': 'inline-block'}),
                html.Div([
                    html.Label("Select Hive:", style={'fontWeight': 'bold'}),
                    dcc.Dropdown(
                        id='hive-dropdown',
                        options=[{'label': 'All Hives', 'value': 'all'}] + 
                               [{'label': hive['name'], 'value': hive['id']} for hive in hives_config],
                        value='all',
                        style={'marginBottom': '10px'}
                    )
                ], style={'width': '48%', 'float': 'right', 'display': 'inline-block'})
            ])
        ], style={'padding': '20px', 'backgroundColor': '#f8f9fa', 'border': '1px solid #dee2e6', 'borderRadius': '5px'})
    ], style={'marginBottom': '30px'}),
    
    # KPI Cards - Updated with Production Metrics
    html.Div([
        html.Div([
            html.H3(id="avg-temperature", style={'color': '#2E86AB', 'margin': '0'}),
            html.P("Average Temperature", style={'margin': '5px 0'}),
            html.Small(id="temp-trend", style={'color': '#6c757d'})
        ], style={'textAlign': 'center', 'padding': '20px', 'backgroundColor': '#e3f2fd', 'borderRadius': '5px', 'width': '13%', 'display': 'inline-block', 'margin': '1%'}),
        
        html.Div([
            html.H3(id="avg-humidity", style={'color': '#17a2b8', 'margin': '0'}),
            html.P("Average Humidity", style={'margin': '5px 0'}),
            html.Small(id="humidity-trend", style={'color': '#6c757d'})
        ], style={'textAlign': 'center', 'padding': '20px', 'backgroundColor': '#e0f7fa', 'borderRadius': '5px', 'width': '13%', 'display': 'inline-block', 'margin': '1%'}),
        
        html.Div([
            html.H3(id="total-weight", style={'color': '#28a745', 'margin': '0'}),
            html.P("Total Weight", style={'margin': '5px 0'}),
            html.Small(id="weight-trend", style={'color': '#6c757d'})
        ], style={'textAlign': 'center', 'padding': '20px', 'backgroundColor': '#e8f5e8', 'borderRadius': '5px', 'width': '13%', 'display': 'inline-block', 'margin': '1%'}),
        
        html.Div([
            html.H3(id="total-production", style={'color': '#ffc107', 'margin': '0'}),
            html.P("Total Production", style={'margin': '5px 0'}),
            html.Small(id="production-trend", style={'color': '#6c757d'})
        ], style={'textAlign': 'center', 'padding': '20px', 'backgroundColor': '#fff3cd', 'borderRadius': '5px', 'width': '13%', 'display': 'inline-block', 'margin': '1%'}),
        
        html.Div([
            html.H3(id="daily-production", style={'color': '#fd7e14', 'margin': '0'}),
            html.P("Daily Production", style={'margin': '5px 0'}),
            html.Small("Last 24h Average", style={'color': '#6c757d'})
        ], style={'textAlign': 'center', 'padding': '20px', 'backgroundColor': '#ffeaa7', 'borderRadius': '5px', 'width': '13%', 'display': 'inline-block', 'margin': '1%'}),
        
        html.Div([
            html.H3(id="active-hives", style={'color': '#6f42c1', 'margin': '0'}),
            html.P("Active Hives", style={'margin': '5px 0'}),
            html.Small("Monitoring Status", style={'color': '#6c757d'})
        ], style={'textAlign': 'center', 'padding': '20px', 'backgroundColor': '#e2d5f1', 'borderRadius': '5px', 'width': '13%', 'display': 'inline-block', 'margin': '1%'}),
        
        html.Div([
            html.H3(id="alerts-count", style={'color': '#dc3545', 'margin': '0'}),
            html.P("Active Alerts", style={'margin': '5px 0'}),
            html.Small("Requires Attention", style={'color': '#6c757d'})
        ], style={'textAlign': 'center', 'padding': '20px', 'backgroundColor': '#f8d7da', 'borderRadius': '5px', 'width': '13%', 'display': 'inline-block', 'margin': '1%'}),
        
        html.Div([
            html.H3(id="avg-efficiency", style={'color': '#20c997', 'margin': '0'}),
            html.P("Avg Efficiency", style={'margin': '5px 0'}),
            html.Small("Production/Activity", style={'color': '#6c757d'})
        ], style={'textAlign': 'center', 'padding': '20px', 'backgroundColor': '#d1ecf1', 'borderRadius': '5px', 'width': '13%', 'display': 'inline-block', 'margin': '1%'})
    ], style={'marginBottom': '30px'}),
    
    # Production Charts Row
    html.Div([
        html.Div([
            html.H4("Cumulative Production Over Time", style={'textAlign': 'center', 'marginBottom': '15px'}),
            dcc.Graph(id='production-cumulative-chart')
        ], style={'width': '49%', 'display': 'inline-block', 'padding': '15px', 'backgroundColor': '#f8f9fa', 'borderRadius': '5px', 'marginRight': '2%'}),
        
        html.Div([
            html.H4("Daily Production Rate", style={'textAlign': 'center', 'marginBottom': '15px'}),
            dcc.Graph(id='production-daily-chart')
        ], style={'width': '49%', 'display': 'inline-block', 'padding': '15px', 'backgroundColor': '#f8f9fa', 'borderRadius': '5px'})
    ], style={'marginBottom': '30px', 'display': 'flex', 'justifyContent': 'space-between'}),
    
    # Main Charts Row 1
    html.Div([
        html.Div([
            html.H4("Temperature Trends Over Time", style={'textAlign': 'center', 'marginBottom': '15px'}),
            dcc.Graph(id='temperature-chart')
        ], style={'width': '49%', 'display': 'inline-block', 'padding': '15px', 'backgroundColor': '#f8f9fa', 'borderRadius': '5px', 'marginRight': '2%'}),
        
        html.Div([
            html.H4("Production Efficiency Analysis", style={'textAlign': 'center', 'marginBottom': '15px'}),
            dcc.Graph(id='efficiency-chart')
        ], style={'width': '49%', 'display': 'inline-block', 'padding': '15px', 'backgroundColor': '#f8f9fa', 'borderRadius': '5px'})
    ], style={'marginBottom': '30px', 'display': 'flex', 'justifyContent': 'space-between'}),
    
    # Main Charts Row 2
    html.Div([
        html.Div([
            html.H4("Hive Weight Analysis", style={'textAlign': 'center', 'marginBottom': '15px'}),
            dcc.Graph(id='weight-chart')
        ], style={'width': '65%', 'display': 'inline-block', 'padding': '15px', 'backgroundColor': '#f8f9fa', 'borderRadius': '5px', 'marginRight': '2%'}),
        
        html.Div([
            html.H4("Production by Hive Type", style={'textAlign': 'center', 'marginBottom': '15px'}),
            dcc.Graph(id='production-by-type')
        ], style={'width': '33%', 'display': 'inline-block', 'padding': '15px', 'backgroundColor': '#f8f9fa', 'borderRadius': '5px'})
    ], style={'marginBottom': '30px', 'display': 'flex', 'justifyContent': 'space-between'}),
    
    # Advanced Analytics Row
    html.Div([
        html.Div([
            html.H4("Production vs Environmental Conditions", style={'textAlign': 'center', 'marginBottom': '15px'}),
            dcc.Graph(id='production-correlation-chart')
        ], style={'width': '49%', 'display': 'inline-block', 'padding': '15px', 'backgroundColor': '#f8f9fa', 'borderRadius': '5px', 'marginRight': '2%'}),
        
        html.Div([
            html.H4("Hive Performance Comparison", style={'textAlign': 'center', 'marginBottom': '15px'}),
            dcc.Graph(id='performance-chart')
        ], style={'width': '49%', 'display': 'inline-block', 'padding': '15px', 'backgroundColor': '#f8f9fa', 'borderRadius': '5px'})
    ], style={'marginBottom': '30px', 'display': 'flex', 'justifyContent': 'space-between'}),
    
    # Alerts and Data Table
    html.Div([
        html.Div([
            html.H4("Recent Alerts", style={'textAlign': 'center', 'marginBottom': '15px'}),
            html.Div(id='alerts-table')
        ], style={'width': '49%', 'display': 'inline-block', 'padding': '15px', 'backgroundColor': '#f8f9fa', 'borderRadius': '5px', 'marginRight': '2%'}),
        
        html.Div([
            html.H4("Latest Readings", style={'textAlign': 'center', 'marginBottom': '15px'}),
            html.Div(id='data-table')
        ], style={'width': '49%', 'display': 'inline-block', 'padding': '15px', 'backgroundColor': '#f8f9fa', 'borderRadius': '5px'})
    ], style={'marginBottom': '30px', 'display': 'flex', 'justifyContent': 'space-between'}),
    
    # Auto-refresh interval
    dcc.Interval(
        id='interval-component',
        interval=30*1000,  # 30 seconds
        n_intervals=0
    )
    
], style={'padding': '20px', 'fontFamily': 'Arial, sans-serif'})

# Callback for updating all components with auto-reload functionality
@app.callback(
    [Output('avg-temperature', 'children'),
     Output('avg-humidity', 'children'),
     Output('total-weight', 'children'),
     Output('total-production', 'children'),
     Output('daily-production', 'children'),
     Output('active-hives', 'children'),
     Output('alerts-count', 'children'),
     Output('avg-efficiency', 'children'),
     Output('temp-trend', 'children'),
     Output('humidity-trend', 'children'),
     Output('weight-trend', 'children'),
     Output('production-trend', 'children'),
     Output('production-cumulative-chart', 'figure'),
     Output('production-daily-chart', 'figure'),
     Output('temperature-chart', 'figure'),
     Output('efficiency-chart', 'figure'),
     Output('weight-chart', 'figure'),
     Output('production-by-type', 'figure'),
     Output('production-correlation-chart', 'figure'),
     Output('performance-chart', 'figure'),
     Output('alerts-table', 'children'),
     Output('data-table', 'children')],
    [Input('time-range-dropdown', 'value'),
     Input('hive-dropdown', 'value'),
     Input('interval-component', 'n_intervals')]
)
def update_dashboard(time_range, selected_hive, n):
    # IMPORTANT: Reload data on each callback to get latest updates from GitHub
    global df, hives_config
    try:
        df, hives_config = load_beehive_data_from_json()
    except Exception as e:
        print(f"⚠️ Warning: Could not reload data: {e}")
        # Continue with existing data if reload fails
    
    # Filter data based on time range
    now = datetime.now()
    if time_range == '24h':
        start_time = now - timedelta(hours=24)
    elif time_range == '7d':
        start_time = now - timedelta(days=7)
    else:  # 30d
        start_time = now - timedelta(days=30)
    
    filtered_df = df[df['timestamp'] >= start_time].copy()
    
    # Filter by hive if not 'all'
    if selected_hive != 'all':
        filtered_df = filtered_df[filtered_df['hive_id'] == selected_hive]
    
    # Calculate KPIs
    latest_data = filtered_df.groupby('hive_id').last().reset_index()
    
    avg_temp = latest_data['temperature'].mean()
    avg_humidity = latest_data['humidity'].mean()
    total_weight = latest_data['weight'].sum()
    active_hives = len(latest_data)
    total_production = latest_data['cumulative_production'].sum()
    avg_efficiency = latest_data['production_efficiency'].mean()
    
    # Calculate daily production (last 24 hours)
    last_24h = now - timedelta(hours=24)
    daily_data = df[df['timestamp'] >= last_24h]
    daily_production = daily_data.groupby('hive_id')['hourly_production'].sum().mean()
    
    # Calculate trends (compare with previous period)
    prev_start = start_time - (now - start_time)
    prev_data = df[(df['timestamp'] >= prev_start) & (df['timestamp'] < start_time)]
    if not prev_data.empty:
        prev_latest = prev_data.groupby('hive_id').last().reset_index()
        temp_trend = avg_temp - prev_latest['temperature'].mean()
        humidity_trend = avg_humidity - prev_latest['humidity'].mean()
        weight_trend = total_weight - prev_latest['weight'].sum()
        production_trend = total_production - prev_latest['cumulative_production'].sum()
    else:
        temp_trend = humidity_trend = weight_trend = production_trend = 0
    
    # Generate alerts (including production-based alerts)
    alerts = []
    for _, row in latest_data.iterrows():
        if row['temperature'] > 38:
            alerts.append({'Type': '⚠️ High Temp', 'Hive': row['hive_name'], 'Value': f"{row['temperature']}°C"})
        if row['temperature'] < 30:
            alerts.append({'Type': '🔵 Low Temp', 'Hive': row['hive_name'], 'Value': f"{row['temperature']}°C"})
        if row['humidity'] > 80:
            alerts.append({'Type': '💧 High Humidity', 'Hive': row['hive_name'], 'Value': f"{row['humidity']}%"})
        if row['weight'] < 30:
            alerts.append({'Type': '⚖️ Low Weight', 'Hive': row['hive_name'], 'Value': f"{row['weight']}kg"})
        if row['production_efficiency'] < 0.01:  # Low production efficiency
            alerts.append({'Type': '📉 Low Efficiency', 'Hive': row['hive_name'], 'Value': f"{row['production_efficiency']:.3f}"})
    
    alerts_count = len(alerts)
    
    # Create charts
    # Cumulative production chart
    prod_cum_fig = px.line(filtered_df, x='timestamp', y='cumulative_production', color='hive_name',
                          title='Cumulative Production Over Time', 
                          labels={'cumulative_production': 'Cumulative Production (kg)'})
    prod_cum_fig.update_layout(height=300)
    
    # Daily production rate chart (calculate rolling 24h sum)
    filtered_df_copy = filtered_df.copy()
    filtered_df_copy['daily_production'] = filtered_df_copy.groupby('hive_id')['hourly_production'].rolling(window=24, min_periods=1).sum().values
    
    prod_daily_fig = px.line(filtered_df_copy, x='timestamp', y='daily_production', color='hive_name',
                            title='Daily Production Rate (24h Rolling)', 
                            labels={'daily_production': 'Daily Production (kg/day)'})
    prod_daily_fig.update_layout(height=300)
    
    # Temperature chart
    temp_fig = px.line(filtered_df, x='timestamp', y='temperature', color='hive_name',
                       title='Temperature Trends', labels={'temperature': 'Temperature (°C)'})
    temp_fig.update_layout(height=300)
    
    # Production efficiency chart
    eff_fig = px.line(filtered_df, x='timestamp', y='production_efficiency', color='hive_name',
                     title='Production Efficiency Over Time', 
                     labels={'production_efficiency': 'Efficiency (kg/activity unit)'})
    eff_fig.update_layout(height=300)
    
    # Weight chart
    weight_fig = px.line(filtered_df, x='timestamp', y='weight', color='hive_name',
                        title='Weight Trends', labels={'weight': 'Weight (kg)'})
    weight_fig.update_layout(height=300)
    
    # Production by hive type
    prod_by_type = latest_data.groupby('hive_type')['cumulative_production'].sum().reset_index()
    type_fig = px.pie(prod_by_type, values='cumulative_production', names='hive_type',
                     title='Total Production by Hive Type')
    type_fig.update_layout(height=300)
    
    # Production correlation scatter plot
    prod_corr_fig = px.scatter(latest_data, x='temperature', y='hourly_production', 
                              size='activity_level', color='hive_name',
                              title='Production vs Temperature (Size = Activity)',
                              labels={'hourly_production': 'Hourly Production (kg)'})
    prod_corr_fig.update_layout(height=300)
    
    # Performance comparison (including production metrics)
    perf_data = latest_data.melt(id_vars=['hive_name'], 
                                value_vars=['temperature', 'humidity', 'weight', 'activity_level', 'cumulative_production'],
                                var_name='metric', value_name='value')
    perf_fig = px.bar(perf_data, x='hive_name', y='value', color='metric',
                     title='Hive Performance Metrics', barmode='group')
    perf_fig.update_layout(height=300)
    
    # Create alerts table
    if alerts:
        alerts_table = dash_table.DataTable(
            data=alerts,
            columns=[{"name": i, "id": i} for i in alerts[0].keys()],
            style_cell={'textAlign': 'left', 'fontSize': 12},
            style_header={'backgroundColor': 'rgb(230, 230, 230)', 'fontWeight': 'bold'},
            page_size=5
        )
    else:
        alerts_table = html.P("No alerts at this time", className="text-success")
    
    # Create data table (including production data)
    table_data = latest_data[['hive_name', 'temperature', 'humidity', 'weight', 
                             'activity_level', 'cumulative_production', 'production_efficiency']].copy()
    
    data_table = dash_table.DataTable(
        data=table_data.to_dict('records'),
        columns=[
            {"name": "Hive", "id": "hive_name"},
            {"name": "Temp (°C)", "id": "temperature", "type": "numeric", "format": {"specifier": ".1f"}},
            {"name": "Humidity (%)", "id": "humidity", "type": "numeric", "format": {"specifier": ".1f"}},
            {"name": "Weight (kg)", "id": "weight", "type": "numeric", "format": {"specifier": ".1f"}},
            {"name": "Activity", "id": "activity_level", "type": "numeric", "format": {"specifier": ".0f"}},
            {"name": "Production (kg)", "id": "cumulative_production", "type": "numeric", "format": {"specifier": ".3f"}},
            {"name": "Efficiency", "id": "production_efficiency", "type": "numeric", "format": {"specifier": ".4f"}}
        ],
        style_cell={'textAlign': 'center', 'fontSize': 11},
        style_header={'backgroundColor': 'rgb(230, 230, 230)', 'fontWeight': 'bold'},
        page_size=5
    )
    
    return (
        f"{avg_temp:.1f}°C",
        f"{avg_humidity:.1f}%",
        f"{total_weight:.1f}kg",
        f"{total_production:.3f}kg",
        f"{daily_production:.4f}kg/day",
        str(active_hives),
        str(alerts_count),
        f"{avg_efficiency:.4f}",
        f"{'↑' if temp_trend > 0 else '↓'} {abs(temp_trend):.1f}°C",
        f"{'↑' if humidity_trend > 0 else '↓'} {abs(humidity_trend):.1f}%",
        f"{'↑' if weight_trend > 0 else '↓'} {abs(weight_trend):.1f}kg",
        f"{'↑' if production_trend > 0 else '↓'} {abs(production_trend):.3f}kg",
        prod_cum_fig,
        prod_daily_fig,
        temp_fig,
        eff_fig,
        weight_fig,
        type_fig,
        prod_corr_fig,
        perf_fig,
        alerts_table,
        data_table
    )