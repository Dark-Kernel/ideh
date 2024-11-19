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


# API Documentation

## Endpoints Overview



### 1. **POST /login**
   - **Description**: Authenticates the user via Google OAuth. Redirects to Google login if not authenticated.
   - **Authentication**: None (initiates login flow)
   - **Response**: Redirect to Google login or `200 OK` with the authenticated user.

### 2. **GET /login/callback**
   - **Description**: Handles the callback from Google login after successful authentication. Logs in the user and stores session data.
   - **Authentication**: Requires successful login.
   - **Response**: Redirect to the dashboard if successful or a flash message on failure.

### 3. **GET /logout**
   - **Description**: Logs out the user by clearing the session and revoking the Google OAuth token (if available).
   - **Authentication**: Requires user to be logged in.
   - **Response**: Redirect to the home/login page with a flash message.

### 4. **GET /scraped-data**
   - **Description**: Fetches all the scraped data created by the authenticated user.
   - **Authentication**: Requires user to be logged in.
   - **Response**: `200 OK` with a JSON array containing scraped data objects.

   **Response Example**:
   ```json
   [
       {
           "id": 1,
           "url": "https://example.com",
           "content": "Page content here",
           "metadata": {"meta_title": "Example Title", "meta_description": "Example description"},
           "created_at": "2024-11-19T18:00:00+00:00"
       }
   ]

### 5. `GET /scraped-data`

#### Description:
                                                                                                                                                                        This endpoint retrieves all the scraped data that has been collected by the authenticated user. It returns the data in a JSON format, including the URL, content, metadata, and creation time for each scraped record.
