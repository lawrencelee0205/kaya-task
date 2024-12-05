# Installation
1. Clone the repo to the local
2. Create .env file on project root path, kindly use the example below.
    ```
    SECRET_KEY='django-insecure-x^8d64%-ucm1ea@@y#6jno))2g=6$ry!2m%5vu*&9m%6ieg1%t'
    DEBUG=True
    ALLOWED_HOSTS=localhost,127.0.0.1
    DB_NAME=postgres
    DB_USER=postgres
    DB_PASSWORD=
    DB_HOST=db
    DB_PORT=5432
    DATABASE_URL=postgres://${DB_USER}:${DB_PASSWORD}@${DB_HOST}:${DB_PORT}/${DB_NAME}
    ```
3. Install pipenv
    ```
    pip install pipenv
    ```
4. Install dependencies from Pipfile.lock
    ```
    pipenv sync
    ```
5. (Shortcut) Run `./dev_start_compose.sh` to automatically build docker image and start services.
    ```
    ./dev_start_compose.sh
    ```
### ❗Important
Always rebuild image when installing package with pipenv. The command should be run sequentially as below:
1. ```pipenv install <package_name>```
2. ```pipenv requirements > requirements.txt```
3. ```docker compose up -d --build```

# Database migration
1. Run `docker compose exec app python manage.py migrate` to migrate the database
    ```
    docker compose exec app python manage.py migrate
    ```

# Create superuser
1. Create superuser to access the local django admin panel
    ```
    docker compose exec app python manage.py createsuperuser
    ```
2. Once the superuser is created, access the django admin panel on [Admin panel](http://localhost:8000/admin) with the username and password.

# Using the APIs
1. **Registration**: Submit a post request to http://localhost:8000/analytics/api/v1/register/ with the example json body below.
    ```
    {
        "username": <username>,
        "password": <password>
    }
    ```
2. **Login**: Submit a post request to http://localhost:8000/analytics/api/v1/login/ with the example json body below. A token will be returned in the response body, keep this token for other API requests.
    ```
    {
        "username": <username>,
        "password": <password>
    }
    ```
3. Requesting to the API should include the auth token in the request header `Token xxxxxx`. Example in get request to http://localhost:8000/analytics/api/v1/campaigns/
    ```
    curl --request GET \
    --url http://localhost:8000/analytics/api/v1/campaigns/ \
    --header 'Authorization: Token <your_token>'
    ```
# List of APIs
### GET
1. http://localhost:8000/analytics/api/v1/campaigns/
2. http://localhost:8000/analytics/api/v1/performance-comparison/
3. http://localhost:8000/analytics/api/v1/performance-time-series/

### PATCH
1. http://localhost:8000/analytics/api/v1/campaigns/

### POST
1. http://localhost:8000/analytics/api/v1/register/
2. http://localhost:8000/analytics/api/v1/login/


# Testing
1. Unit tests located at `analytics/tests/test_apis.py`
2. To run unit tests on local, run command:
    ```
    docker compose exec app pytest --reuse-db
    ```

# Assumptions
1. Impression, clicks, conversion, cost from AdGroupStats should be equal or greater than 0.
2. Campaign name and type should be composite unique.
3. AdGroup name should be unique.

# Additional features
1. Only authenticated user can make request to the APIs.
2. Authenticated user has a global request rate limit to the APIs.
3. New user need to register and obtain a token for requesting the APIs.

# Summary
Users or clients need to be authenticated through registration. Obtaining the token by signing in. A global request rate limit is implemented to all APIs. APIs' Input and query parameter is sanitized by the serializer default or custom validation. Message will be returned for successful or unsuccessful request.
