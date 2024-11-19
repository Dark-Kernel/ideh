# Docker Deployment Instructions

## Prerequisites
- Docker
- Docker Compose
- Your Google credentials JSON file

## Deployment Steps

1. Place your Google credentials JSON file in a `credentials` directory in the same folder as your `docker-compose.yml`

2. Modify your application code to use the credentials:
   ```python
   import os

   # Find the first .json file in the credentials directory
   def find_credentials_file():
       credentials_dir = '/app/credentials'
       for filename in os.listdir(credentials_dir):
           if filename.endswith('.json'):
               return os.path.join(credentials_dir, filename)
       return None

   # Set the environment variable dynamically
   credentials_path = find_credentials_file()
   if credentials_path:
       os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = credentials_path
   ```

3. Run the application:
   ```bash
   docker-compose up --build
   ```

## Notes
- Ensure your `.env` file is in the same directory
- The PostgreSQL connection is automatically handled by Docker Compose
- The application will look for a .json credentials file in the `credentials` directory
