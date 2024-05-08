import os

# File upload settings
UPLOAD_FOLDER = os.getenv('UPLOAD_FOLDER', 'uploads')
MAX_CONTENT_LENGTH = int(os.getenv('MAX_FILE_SIZE', 16 * 1024 * 1024))  # 16MB default
ALLOWED_EXTENSIONS = set(os.getenv('ALLOWED_EXTENSIONS', 'txt,pdf,png,jpg,jpeg,gif').split(','))
TEMP_FILE_EXPIRATION = int(os.getenv('TEMP_FILE_EXPIRATION', 7))  # 7 days default

# Security settings
SECURITY_TOKEN = os.getenv('SECURITY_TOKEN')

# Logging settings
LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
LOG_FILE = os.getenv('LOG_FILE', 'app.log')

# Additional settings
# Add more configuration options as needed
