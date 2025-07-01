import json
import pandas as pd
from datetime import datetime
import os
import requests
from typing import Optional, Tuple, Dict, Any
import hashlib
import threading
import time

# Load environment variables if available
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

class GitHubDataLoader:
    def __init__(self):
        self.repo_owner = os.getenv('GITHUB_REPO_OWNER')
        self.repo_name = os.getenv('GITHUB_REPO_NAME')
        self.token = os.getenv('GITHUB_TOKEN')
        
        if not all([self.repo_owner, self.repo_name]):
            missing = []
            if not self.repo_owner: missing.append('GITHUB_REPO_OWNER')
            if not self.repo_name: missing.append('GITHUB_REPO_NAME')
            raise ValueError(f"Missing required environment variables: {', '.join(missing)}")
        
        self.base_url = f"https://api.github.com/repos/{self.repo_owner}/{self.repo_name}"
        self.headers = {}
        if self.token:
            self.headers['Authorization'] = f'token {self.token}'
        self.headers['Accept'] = 'application/vnd.github.v3+json'
        
        # Simple cache for auto-update
        self.data_cache = None
        self.config_cache = None
        self.last_data_hash = None
        self.last_config_hash = None
        self.check_interval = 30  # Check every 30 seconds
        self.monitoring = False

    def _get_file_hash_from_github(self, filename: str) -> Optional[str]:
        """Get file SHA hash from GitHub to detect changes without downloading content"""
        url = f"{self.base_url}/contents/{filename}"
        try:
            response = requests.get(url, headers=self.headers)
            if response.status_code == 200:
                file_data = response.json()
                return file_data.get('sha')
            return None
        except Exception:
            return None

    def _fetch_file_from_github_raw(self, filename: str) -> Optional[str]:
        """Fetch file content from GitHub raw URL (faster)"""
        raw_url = f"https://raw.githubusercontent.com/{self.repo_owner}/{self.repo_name}/main/{filename}"
        try:
            response = requests.get(raw_url)
            if response.status_code == 200:
                return response.text
            elif response.status_code == 404:
                raise FileNotFoundError(f"File {filename} not found in GitHub repository")
            else:
                raise Exception(f"Error fetching {filename}: {response.status_code}")
        except FileNotFoundError:
            raise
        except Exception as e:
            raise Exception(f"Error fetching file {filename} from GitHub: {e}")

    def load_json_from_github(self, filename: str) -> Dict[Any, Any]:
        """Load and parse JSON file from GitHub"""
        content = self._fetch_file_from_github_raw(filename)
        
        if not content or content.strip() == "":
            raise ValueError(f"File {filename} is empty or contains no content")
        
        try:
            return json.loads(content)
        except json.JSONDecodeError as e:
            raise ValueError(f"Error parsing JSON from {filename}: {e}")

    def check_for_updates(self) -> bool:
        """Check if files have been updated on GitHub"""
        try:
            # Get current file hashes
            data_hash = self._get_file_hash_from_github('beehive_data.json')
            config_hash = self._get_file_hash_from_github('hives_config.json')
            
            # Check if hashes changed
            data_updated = (data_hash != self.last_data_hash and self.last_data_hash is not None)
            config_updated = (config_hash != self.last_config_hash and self.last_config_hash is not None)
            
            # Update stored hashes
            self.last_data_hash = data_hash
            self.last_config_hash = config_hash
            
            if data_updated or config_updated:
                print(f"🔄 GitHub data update detected!")
                if data_updated:
                    print("   - beehive_data.json updated")
                if config_updated:
                    print("   - hives_config.json updated")
                return True
            
            return False
            
        except Exception as e:
            print(f"⚠️ Error checking for updates: {e}")
            return False

    def load_data_with_cache(self) -> Tuple[pd.DataFrame, list]:
        """Load data with caching and update detection"""
        # Check if we need to reload data
        if self.data_cache is None or self.config_cache is None or self.check_for_updates():
            try:
                print("📥 Loading fresh data from GitHub...")
                
                # Load main data from GitHub
                data = self.load_json_from_github('beehive_data.json')
                hives_config = self.load_json_from_github('hives_config.json')
                
                # Convert to DataFrame and handle timestamp conversion
                df = pd.DataFrame(data)
                df['timestamp'] = pd.to_datetime(df['timestamp'])
                
                # Update cache
                self.data_cache = df
                self.config_cache = hives_config
                
                print(f"✅ Loaded {len(df)} data points for {len(hives_config)} hives from GitHub")
                
            except Exception as e:
                print(f"❌ Error loading data: {e}")
                # Return cached data if available, otherwise raise error
                if self.data_cache is not None and self.config_cache is not None:
                    print("📋 Using cached data")
                    return self.data_cache.copy(), self.config_cache
                else:
                    raise e
        
        return self.data_cache.copy(), self.config_cache

    def start_monitoring(self):
        """Start background monitoring for GitHub updates"""
        if self.monitoring:
            return
        
        self.monitoring = True
        
        def monitor_loop():
            while self.monitoring:
                try:
                    self.check_for_updates()
                    time.sleep(self.check_interval)
                except Exception as e:
                    print(f"⚠️ Monitoring error: {e}")
                    time.sleep(self.check_interval)
        
        monitor_thread = threading.Thread(target=monitor_loop, daemon=True)
        monitor_thread.start()
        print(f"🔍 Started GitHub monitoring (checking every {self.check_interval}s)")

    def stop_monitoring(self):
        """Stop background monitoring"""
        self.monitoring = False
        print("⏹️ Stopped GitHub monitoring")

# Global instance
github_loader = GitHubDataLoader()

def load_beehive_data_from_json():
    """Load beehive data from GitHub repository with auto-update"""
    global github_loader
    
    try:
        # Start monitoring if not already started
        if not github_loader.monitoring:
            github_loader.start_monitoring()
        
        # Load data (will use cache if no updates detected)
        df, hives_config = github_loader.load_data_with_cache()
        return df, hives_config
        
    except ValueError as e:
        raise ValueError(f"GitHub configuration error: {e}")
    except FileNotFoundError as e:
        raise FileNotFoundError(f"{e}. Please ensure the JSON files exist in your GitHub repository.")
    except Exception as e:
        raise Exception(f"Error loading data from GitHub: {e}")

def get_data_info():
    """Get information about available data without loading it"""
    try:
        global github_loader
        
        data = github_loader.load_json_from_github('beehive_data.json')
        hives_config = github_loader.load_json_from_github('hives_config.json')
        
        timestamps = [item['timestamp'] for item in data]
        start_date = min(timestamps)
        end_date = max(timestamps)
        
        return {
            'source': 'github',
            'total_records': len(data),
            'num_hives': len(hives_config),
            'date_range': f"{start_date} to {end_date}",
            'hive_names': [hive['name'] for hive in hives_config],
            'auto_update': github_loader.monitoring
        }
        
    except Exception as e:
        return f"Error getting data info from GitHub: {e}"

def refresh_data():
    """Force reload data from GitHub repository"""
    global github_loader
    print("🔄 Force refreshing data from GitHub repository...")
    
    # Clear cache to force reload
    github_loader.data_cache = None
    github_loader.config_cache = None
    
    return load_beehive_data_from_json()

def force_check_updates():
    """Manually trigger update check"""
    global github_loader
    return github_loader.check_for_updates()