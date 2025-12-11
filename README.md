# Anime AI Study Companion

A personalized, anime-themed AI study buddy powered by Groq (Llama 3) and Next.js.

## Project Structure

This project is organized as a monorepo:

- **`/backend`**: Python FastAPI server handling AI logic and Groq API integration.
- **`/frontend`**: Next.js (React) application for the user interface.

## Quick Start

### Backend

1.  Navigate to `/backend`
2.  Install dependencies: `pip install -r requirements.txt`
3.  Run server: `uvicorn main:app --reload`

### Frontend

1.  Navigate to `/frontend`
2.  Install dependencies: `npm install`
3.  Run dev server: `npm run dev`

## Tech Stack

- **AI:** Groq API (Llama 3)
- **Backend:** FastAPI (Python)
- **Frontend:** Next.js, Tailwind CSS, Framer Motion
