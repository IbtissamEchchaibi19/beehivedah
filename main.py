# Add these endpoints to your FastAPI app:

from fastapi import FastAPI
from fastapi.middleware.wsgi import WSGIMiddleware
import uvicorn
from data_loader import refresh_data, get_data_info, force_check_updates

# Your existing FastAPI app
app = FastAPI(
    title="Beehive Analytics API",
    description="API with integrated Beehive Dashboard",
    version="1.0.0"
)

# Import your existing dashboard
from dashboard import app as dash_app

if dash_app:
    app.mount("/dash_app", WSGIMiddleware(dash_app.server))

@app.get("/")
async def root():
    return {"message": "Beehive Analytics API", "dashboard_url": "/dashboard"}

@app.get("/api/hives")
async def get_hives():
    from dashboard import hives_config
    return {"hives": hives_config}

# NEW ENDPOINTS FOR DATA MANAGEMENT:

@app.get("/api/data/info")
async def get_data_info_endpoint():
    """Get information about the current data"""
    info = get_data_info()
    return {"data_info": info}

@app.post("/api/data/refresh")
async def refresh_data_endpoint():
    """Manually refresh data from GitHub"""
    try:
        df, hives_config = refresh_data()
        return {
            "status": "success",
            "message": "Data refreshed successfully",
            "records": len(df),
            "hives": len(hives_config)
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Failed to refresh data: {str(e)}"
        }

@app.get("/api/data/check-updates")
async def check_updates_endpoint():
    """Check if GitHub data has been updated"""
    try:
        has_updates = force_check_updates()
        return {
            "has_updates": has_updates,
            "message": "Updates detected" if has_updates else "No updates detected"
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Failed to check updates: {str(e)}"
        }


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)