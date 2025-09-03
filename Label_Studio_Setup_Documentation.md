
# 📄 Label Studio Project Setup Documentation

## 1. Clone the Repository

```bash
git clone https://github.com/SaiPrasadBM/label-studio.git
```

---

## 2. Install package dependencies

```bash
pip install poetry
poetry install
```

---
## 3. Set Up the Frontend

```bash
cd label-studio/web
yarn install --frozen-lockfile
yarn ls:watch
```
```
yarn dev
```
Resolve watchpack error using following command
```
$ sudo sysctl fs.inotify.max_user_watches=131070
```
---

## 4. Set Up the Backend

Return to the project root:

```bash
cd ..
```

Run the migrations:

```bash
poetry run python label_studio/manage.py migrate
```

Collect static files:

```bash
poetry run python label_studio/manage.py collectstatic
```

Run the backend server:

```bash
poetry run python label_studio/manage.py runserver
```
Open [localhost:8080](http://127.0.0.1:8080/) to access the label studio interface

---

## 5. Access Django Admin Interface

### a. Navigate to the Django App Directory:

```bash
cd label-studio/label_studio
```

### b. Create a Superuser:

```bash
python manage.py createsuperuser
```

You will be prompted to provide:

- Email Address  
- Password  
- Confirm Password  

### c. Disable Inactivity Session Timeout:

Disable the InactivitySessionTimeoutMiddleware via the environment (.env file):

```bash
set INACTIVITY_SESSION_TIMEOUT_ENABLED=0
```

*(On Linux/macOS, use `export` instead of `set`)*

### d. Restart the Server:

```bash
poetry run python manage.py runserver
```

---

### e. Access Django Admin Panel:

Open the following URL in your browser:

```
http://127.0.0.1:8080/admin/
```

Login using the superuser credentials you created earlier.
