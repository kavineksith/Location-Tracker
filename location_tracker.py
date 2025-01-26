# Standard library imports
import os
import logging
import sqlite3
import time
import socket
from datetime import datetime
from configparser import ConfigParser

# Third-party imports
import requests
from cryptography.fernet import Fernet

# Custom Exception Classes
class LocationError(Exception):
    """Base class for exceptions in this module."""
    def __init__(self, message):
        self.message = message
        super().__init__(self.message)

class NetworkError(LocationError):
    """Exception raised when there's a network-related issue."""
    def __init__(self, message):
        self.message = message
        super().__init__(self.message)

class DatabaseError(LocationError):
    """Exception raised when there's a database-related issue."""
    def __init__(self, message):
        self.message = message
        super().__init__(self.message)

class APIKeyError(LocationError):
    """Exception raised when API key is invalid or missing."""
    def __init__(self, message):
        self.message = message
        super().__init__(self.message)

class ConfigurationError(LocationError):
    """Exception raised when configuration is invalid or missing."""
    def __init__(self, message):
        self.message = message
        super().__init__(self.message)

# Function to check internet connection
def is_connected():
    try:
        # Try connecting to an external server (e.g., Google's DNS server)
        socket.create_connection(("8.8.8.8", 53), timeout=5)
        return True
    except OSError:
        return False

# Base Class for Configuration Handling
class ConfigHandler:
    def __init__(self):
        self._api_key = None
        self._encryption_key = None
        self._encrypted_api_key = None

    def _load_config(self):
        """Load configuration from environment or config file."""
        self._api_key = os.getenv('GOOGLE_API_KEY')

        if not self._api_key:
            logging.info("API Key not found in environment variables, trying config file.")
            self._load_from_config_file()

        if not self._api_key:
            logging.info("API Key not found in config file, trying encrypted key.")
            self._load_from_encrypted_config()

        if not self._api_key:
            raise APIKeyError("API Key not found. Ensure it is set in environment variables, config file, or encrypted storage.")

    def _load_from_config_file(self):
        """Load API key from config file."""
        config = ConfigParser()
        config.read('config.ini')
        try:
            self._api_key = config.get('API', 'GOOGLE_API_KEY')
        except KeyError as e:
            logging.error(f"API Key not found in config.ini: {e}")
            raise ConfigurationError("API Key not found in config file.")

    def _load_from_encrypted_config(self):
        """Load and decrypt the API key from an encrypted config file."""
        try:
            # Decrypt the encrypted API key (key stored separately or in environment)
            encrypted_api_key = self._read_encrypted_api_key_from_file()
            self._api_key = self._decrypt_api_key(encrypted_api_key)
        except Exception as e:
            logging.error(f"Error decrypting API Key: {e}")
            raise APIKeyError("Error decrypting API Key.")

    def _decrypt_api_key(self, encrypted_api_key: bytes):
        """Decrypt the API key using the stored encryption key."""
        cipher_suite = Fernet(self._get_encryption_key())
        decrypted_key = cipher_suite.decrypt(encrypted_api_key).decode()
        return decrypted_key

    def _read_encrypted_api_key_from_file(self):
        """Read encrypted API key from a file (this is a simple placeholder)."""
        with open('encrypted_api_key.bin', 'rb') as file:
            encrypted_api_key = file.read()
        return encrypted_api_key

    def _get_encryption_key(self):
        """Get encryption key (could be stored in an environment variable)."""
        encryption_key = os.getenv('ENCRYPTION_KEY')
        if not encryption_key:
            raise APIKeyError("Encryption key not found in environment variables.")
        return encryption_key

    @property
    def api_key(self):
        """Property to get the API key."""
        if not self._api_key:
            self._load_config()
        return self._api_key

# Base Class for Location Tracking
class LocationTracker:
    def __init__(self, db_name='locations.db'):
        self.db_name = db_name
        self.remote_database_url = None
        self.config_handler = ConfigHandler()  # Configuration handling
        self.create_database()  # Create SQLite database

    def create_database(self):
        """Create the SQLite database and the locations table if it doesn't exist."""
        try:
            conn = sqlite3.connect(self.db_name)
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS location_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    ip TEXT,
                    city TEXT,
                    region TEXT,
                    country TEXT
                )
            ''')
            conn.commit()
            conn.close()
            logging.info("Database created or already exists.")
        except sqlite3.DatabaseError as e:
            logging.error(f"Database creation error: {e}")
            raise DatabaseError(f"Error creating database: {e}")
    
    def log_location(self, location_data):
        """Log the location data to the SQLite database or remote database depending on internet connectivity."""
        try:
            if is_connected():
                self.send_to_remote_database(location_data)
            else:
                self.store_locally(location_data)
        except Exception as e:
            logging.error(f"Error logging location: {e}")

    def send_to_remote_database(self, location_data):
        """Send location data to the remote database."""
        try:
            # Get the public IP address from an external API (e.g., ipify or httpbin)
            ip_response = requests.get('https://api.ipify.org')
            ip_response.raise_for_status()  # Check if the request was successful
            current_ip = ip_response.text  # Extract the IP address from the response
            
            # Construct the remote database URL using the public IP
            self.remote_database_url = f'http://{current_ip}:80/v1/location' # for testing purposes
            
            # Create a timestamp for the remote database
            remote_timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            # Prepare the data to be sent
            data = {
                'timestamp': location_data.get('timestamp'),
                'ip': location_data.get('ip'),
                'city': location_data.get('city', 'Unknown'),
                'region': location_data.get('region', 'Unknown'),
                'country': location_data.get('country', 'Unknown'),
                'public_ip': current_ip,  # New column for public IP
                'remote_timestamp': remote_timestamp  # New column for remote timestamp
            }

            # Assuming you're sending data as a POST request
            response = requests.post(self.remote_database_url, json=data) # Send the data as a POST request
            response.raise_for_status()

            logging.info(f"Location data sent to remote database: {location_data.get('city')}, {location_data.get('country')}")
        except requests.exceptions.RequestException as e:
            logging.error(f"Error sending data to remote database: {e}")
            raise NetworkError(f"Error sending data to remote database: {e}")

    def store_locally(self, location_data):
        """Store location data in SQLite database for later sync."""
        try:
            conn = sqlite3.connect(self.db_name)
            cursor = conn.cursor()
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            cursor.execute('''
                INSERT INTO location_log (timestamp, ip, city, region, country)
                VALUES (?, ?, ?, ?, ?)
            ''', (timestamp, location_data.get('ip'), location_data.get('city', 'Unknown'),
                  location_data.get('region', 'Unknown'), location_data.get('country', 'Unknown')))
            conn.commit()
            conn.close()
            logging.info(f"Location logged locally: {location_data.get('city')}, {location_data.get('country')}")
        except sqlite3.DatabaseError as e:
            logging.error(f"Database error while logging location: {e}")
            raise DatabaseError(f"Error logging location to the database: {e}")

    def sync_local_data_to_remote(self):
        """Sync all local data to the remote database when internet connection is available."""
        try:
            conn = sqlite3.connect(self.db_name)
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM location_log")
            rows = cursor.fetchall()
            for row in rows:
                location_data = {
                    'timestamp': row[1],  # SQLite timestamp
                    'ip': row[2],
                    'city': row[3],
                    'region': row[4],
                    'country': row[5]
                }
                self.send_to_remote_database(location_data)
                cursor.execute("DELETE FROM location_log WHERE id = ?", (row[0],))  # Delete after syncing
            conn.commit()
            conn.close()
            logging.info("Local data synced to remote database.")
        except sqlite3.DatabaseError as e:
            logging.error(f"Error syncing local data to remote: {e}")
            raise DatabaseError(f"Error syncing local data to remote: {e}")

    def track_location(self, interval_seconds=3600):
        """Continuously track the location and log it at regular intervals."""
        while True:
            try:
                location_data = self.get_location()
                if location_data:
                    self.log_location(location_data)
                    print(f"Location logged: {location_data.get('city')}, {location_data.get('country')}")
                    # Sync local data to remote if internet is available
                    if is_connected():
                        self.sync_local_data_to_remote()
            except LocationError as e:
                logging.error(f"Location error: {e}")
                print(f"Error: {e}")
            time.sleep(interval_seconds)

    def get_location(self):
        """Fetch location data using either IP geolocation or Wi-Fi geolocation."""
        
        # Try to get Wi-Fi networks nearby
        wifi_networks = self.scan_wifi_networks()  # Scan for nearby Wi-Fi networks
        
        if wifi_networks:
            # If Wi-Fi networks are found, use them to get a more precise location
            logging.info("Wi-Fi networks found. Attempting to fetch location using Wi-Fi...")
            location_data = self.get_geolocation_from_wifi(wifi_networks)
            
            if location_data:
                logging.info("Location successfully fetched using Wi-Fi.")
                return location_data
            else:
                logging.warning("Failed to fetch location using Wi-Fi networks. Falling back to IP geolocation.")
        
        # If no Wi-Fi networks are found or Wi-Fi geolocation fails, fall back to IP geolocation
        logging.info("Wi-Fi networks not found or failed. Attempting to fetch location using IP...")
        
        try:
            # Use IP-based geolocation as a fallback
            response = requests.get("https://ipinfo.io")
            response.raise_for_status()  # Raise HTTPError for bad responses
            location_data = response.json()

            # Validate the location data to ensure it contains necessary info
            if not self.validate_location_data(location_data):
                logging.error("Invalid location data received from IP geolocation.")
                return None  # Return None if the data is invalid
            
            logging.info(f"Location fetched from IP: {location_data.get('city')}, {location_data.get('country')}")
            return location_data
        except requests.exceptions.RequestException as e:
            logging.error(f"Network error while fetching location: {e}")
            raise NetworkError(f"Error fetching location: {e}")

    def validate_location_data(self, location_data):
        """Validate location data to ensure necessary keys exist."""
        required_keys = ['ip', 'city', 'region', 'country']
        
        for key in required_keys:
            if key not in location_data:
                logging.warning(f"Missing key: {key} in location data.")
                return False
        
        # Further validation (optional): Check if any values are empty or invalid
        if not location_data['ip'] or not location_data['city'] or not location_data['region'] or not location_data['country']:
            logging.warning("One or more values in location data are empty.")
            return False
        
        return True

    def scan_wifi_networks(self):
        """Scan for nearby Wi-Fi networks, platform-dependent."""
        wifi_networks = []

        # Check platform and use appropriate Wi-Fi scanning method
        if os.name == 'nt':  # If running on Windows
            import pywifi  # Use pywifi for Windows compatibility
            wifi_interface = pywifi.PyWiFi().interfaces()[0]
            wifi_networks = self._scan_pywifi(wifi_interface)
        else:
            import wifi  # Use wifi for Linux/Unix-based systems
            networks = wifi.Cell.all('wlan0')  # 'wlan0' is the network interface (adjust if needed)
            wifi_networks = self._scan_wifi(networks)
        
        return wifi_networks

    def _scan_wifi(self, networks):
        """Helper function for scanning Wi-Fi on Linux/Unix"""
        wifi_networks = []
        for network in networks:
            wifi_networks.append({
                'SSID': network.ssid,
                'MAC': network.address,
                'Signal Strength': network.signal
            })
        return wifi_networks

    def _scan_pywifi(self, wifi_interface):
        """Helper function for scanning Wi-Fi on Windows using pywifi"""
        wifi_networks = []
        wifi_interface.scan()  # Start the scan
        time.sleep(2)  # Give some time for scan to complete
        networks = wifi_interface.scan_results()
        for network in networks:
            wifi_networks.append({
                'SSID': network.ssid,
                'MAC': network.bssid,
                'Signal Strength': network.signal
            })
        return wifi_networks

    def get_geolocation_from_wifi(self, wifi_networks):
        """Get location based on nearby Wi-Fi networks using Google Geolocation API."""
        url = "https://www.googleapis.com/geolocation/v1/geolocate?key=" + self.config_handler.api_key
        headers = {"Content-Type": "application/json"}
        
        # Prepare the payload with nearby Wi-Fi networks
        payload = {
            "wifiAccessPoints": [
                {
                    "macAddress": network['MAC'],
                    "signalStrength": network['Signal Strength'],
                    "signalToNoiseRatio": 40
                }
                for network in wifi_networks
            ]
        }
        
        try:
            response = requests.post(url, json=payload, headers=headers)
            response.raise_for_status()  # Raise an exception for bad HTTP responses
            location_data = response.json()
            logging.info("Location derived from Wi-Fi networks.")
            return location_data
        except requests.exceptions.RequestException as e:
            logging.error(f"Error fetching location from Wi-Fi data: {e}")
            return None

# Main Application
def main():
    logging.basicConfig(
        filename='location_tracker.log', 
        level=logging.DEBUG, 
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    logging.info("Starting location tracker.")
    
    try:
        tracker = LocationTracker()
        tracker.track_location(interval_seconds=3600)  # Track every hour
    except LocationError as e:
        logging.error(f"Failed to start location tracker: {e}")
        print(f"Error: {e}")
    except KeyboardInterrupt:
        logging.info("Location tracker stopped by user.")
        print("Tracker stopped.")

if __name__ == "__main__":
    main()
