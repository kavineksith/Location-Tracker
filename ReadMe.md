## Location Tracking Python Script Documentation

### Overview
This Python script is a location tracking system that continuously monitors the user's location and logs it into either a local SQLite database or a remote database based on internet connectivity. It uses multiple methods to determine the user's location, including IP geolocation and Wi-Fi-based geolocation. The system is equipped with configurable API key handling, error handling for various modules, and automated syncing between local and remote databases.

### Modules and Dependencies

#### Standard Library Imports:
- `os`: For interacting with the operating system (e.g., accessing environment variables).
- `logging`: To log application activities.
- `sqlite3`: For interacting with an SQLite database.
- `time`: For introducing delays (e.g., in periodic tasks).
- `socket`: To check for an internet connection.
- `datetime`: To manage timestamps.
- `configparser`: For reading configuration files.

#### Third-party Imports:
- `requests`: To make HTTP requests (e.g., for fetching IP and Wi-Fi-based geolocation data).
- `cryptography.fernet`: For encrypting and decrypting sensitive data (e.g., API keys).

#### Custom Classes:
- `LocationError`: A base exception class for location-related errors.
- `NetworkError`, `DatabaseError`, `APIKeyError`, `ConfigurationError`: Specific subclasses of `LocationError` for more granular exception handling.
  
### Classes

#### 1. `ConfigHandler`
Handles configuration management related to API key retrieval, including fallback mechanisms from environment variables, configuration files, and encrypted storage.

- **Methods**:
  - `_load_config`: Loads the API key from environment, config file, or encrypted file.
  - `_load_from_config_file`: Attempts to retrieve the API key from a `config.ini` file.
  - `_load_from_encrypted_config`: Loads and decrypts the API key from an encrypted file.
  - `_decrypt_api_key`: Decrypts the API key using a specified encryption key.
  - `_read_encrypted_api_key_from_file`: Reads the encrypted API key from a file.
  - `_get_encryption_key`: Retrieves the encryption key from the environment.
  - `api_key`: A property to get the API key by invoking `_load_config`.

#### 2. `LocationTracker`
Responsible for tracking the user's location, logging it either locally in an SQLite database or remotely, and handling location data syncing.

- **Methods**:
  - `create_database`: Initializes an SQLite database and creates a table if not already present.
  - `log_location`: Logs location data, deciding whether to send it to a remote database or store it locally based on internet connectivity.
  - `send_to_remote_database`: Sends location data to a remote database if the internet is available.
  - `store_locally`: Stores location data in the local SQLite database for later syncing.
  - `sync_local_data_to_remote`: Syncs all locally stored location data to the remote database.
  - `track_location`: Continuously tracks the location at specified intervals and logs it.
  - `get_location`: Retrieves the user's location by first attempting Wi-Fi-based geolocation, falling back to IP-based geolocation.
  - `validate_location_data`: Ensures that the necessary keys (e.g., 'ip', 'city', 'region', 'country') exist in the location data.
  - `scan_wifi_networks`: Scans nearby Wi-Fi networks depending on the platform (Windows or Linux).
  - `get_geolocation_from_wifi`: Uses Google’s Geolocation API to derive location data based on nearby Wi-Fi networks.
  
#### 3. `LocationError`, `NetworkError`, `DatabaseError`, `APIKeyError`, `ConfigurationError`
Custom exception classes to handle various errors that might occur during location tracking, network communication, database interactions, or configuration issues.

### Functions

#### `is_connected`
Checks whether the system has an active internet connection by attempting to establish a connection to Google's DNS server (`8.8.8.8`).

- **Returns**: `True` if the connection is successful, `False` otherwise.

#### `main`
The entry point of the application, where the location tracker is initialized and started. Logs location every hour.

- **Log Output**: Logs the start and stop of the tracker, as well as any errors.

### Location Tracking Flow

1. **Configuration Load**: The `ConfigHandler` class loads the API key from the environment, a configuration file, or an encrypted storage file.
   
2. **Location Tracking**: The `LocationTracker` class fetches location data by either scanning nearby Wi-Fi networks or using IP geolocation. It logs the location data based on the internet connection status:
   - **Remote Database**: If the system is connected to the internet, the data is sent to a remote database.
   - **Local Database**: If offline, the data is stored locally in an SQLite database for later syncing.

3. **Data Syncing**: If the system was offline and the location data was stored locally, it will be synced to the remote database once the system is online.

4. **Error Handling**: Specific errors (e.g., network failure, database error, missing API key) are caught and logged, ensuring the system can handle unexpected situations gracefully.

### Usage Instructions

1. **Prerequisites**:
   - Ensure the `requests`, `cryptography`, and other dependencies are installed via `pip`.
   - Configure the `GOOGLE_API_KEY` in the environment or the `config.ini` file.

2. **Running the Script**:
   To start location tracking, run the script:

   ```bash
   python location_tracker.py
   ```

3. **Logging**:
   Logs are saved in the file `location_tracker.log`, including detailed information about location tracking, errors, and data sync activities.

### Example Configuration (config.ini)
```ini
[API]
GOOGLE_API_KEY = your_api_key_here
```

### Exception Handling
The script uses custom exception classes to handle different types of errors:
- **LocationError**: Base class for all location-related exceptions.
- **NetworkError**: Raised when there's a network issue.
- **DatabaseError**: Raised for database-related issues.
- **APIKeyError**: Raised when the API key is missing or invalid.
- **ConfigurationError**: Raised when configuration settings are missing or invalid.

### Notes:
- **Encryption**: For extra security, the API key can be encrypted and stored separately. The script will decrypt the key when needed.
- **Wi-Fi Scanning**: The script scans nearby Wi-Fi networks for more accurate location tracking. The functionality is platform-dependent (Windows uses `pywifi`, while Linux uses `wifi`).

### Conclusion

This Python script provides a robust solution for tracking the location of a system, offering flexibility in how location data is retrieved and stored. By leveraging both IP-based and Wi-Fi-based geolocation, it ensures accurate tracking in various network conditions. The integration of local and remote database support, along with automatic syncing, ensures that location data is reliably logged and transmitted even when internet connectivity is intermittent.

The script's configuration system allows for secure handling of sensitive information like API keys, with support for both direct configuration and encrypted storage, ensuring that your credentials are protected. Additionally, the use of custom exception handling ensures that errors are properly logged and can be addressed without disrupting the entire tracking process.

Overall, this solution is well-suited for scenarios where continuous location tracking is needed, with the ability to operate in both online and offline environments. It can be easily customized or extended to fit specific needs, making it a valuable tool for various location-based applications or monitoring systems.

## **License**
This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

## **Disclaimer:**
Kindly note that this project is developed solely for educational purposes, not intended for industrial use, as its sole intention lies within the realm of education. We emphatically underscore that this endeavor is not sanctioned for industrial application. It is imperative to bear in mind that any utilization of this project for commercial endeavors falls outside the intended scope and responsibility of its creators. Thus, we explicitly disclaim any liability or accountability for such usage.