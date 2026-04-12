# Software Construction Exam Project

A full-stack movie discovery platform built with **Django REST Framework** (backend) and **Next.js** (frontend), powered by The Movie Database (TMDB) API.

## Project Structure

```
├── backend/          # Django REST API
│   ├── cinequest/    # Project settings & URLs
│   ├── movies/       # Movies app (models, views, TMDB service)
│   ├── users/        # Custom user model & auth
│   └── recommendations/  # Recommendation engine & watchlist
├── frontend/         # Next.js application
│   ├── src/app/      # Pages (home, search, movie detail, etc.)
│   ├── src/components/  # Reusable UI components
│   ├── src/lib/      # API client, auth context, utilities
│   └── src/types/    # TypeScript type definitions
```

## Getting Started

### Backend
```bash
cd backend
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
python manage.py migrate
python manage.py sync_movies --genres
python manage.py sync_movies --trending 2
python manage.py runserver
```

### Frontend
```bash
cd frontend
npm install
npm run dev
```

### Environment Variables
Create a `.env` file in the `backend/` directory using `.env.example` as a template:

```bash
cp .env.example .env
Then fill in your actual values:

- `TMDB_API_KEY` - Get your free API key from https://www.themoviedb.org/settings/api
- `SECRET_KEY` - Any random secret string
- `DEBUG` - Set to `True` for development, `False` for production
- `ALLOWED_HOSTS` - Comma separated list of allowed hosts
- `CORS_ORIGINS` - Comma separated list of allowed frontend origins

> **Note:** Never commit your `.env` file to GitHub. It is already listed in `.gitignore`.

## TMDB API
Get your free API key at: https://www.themoviedb.org/settings/api
# project-based-exam