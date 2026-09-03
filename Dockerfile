# Nicomachus as a hosted web server — runs anywhere that takes a container.
FROM python:3.12-slim

WORKDIR /app

# deps first, for layer caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# app + the committed corpus and curated notes
COPY nicomachus/ ./nicomachus/
COPY topics/ ./topics/
COPY corpus/ ./corpus/
COPY README.md .

# Build the search index at image-build time so first request is fast.
RUN python -m nicomachus index

# Render/Fly inject $PORT. Default to 10000 (Render's convention) so the
# image also runs the same way locally with `docker run -p 10000:10000`.
ENV PORT=10000
EXPOSE 10000

# NICOMACHUS_TOKEN must be set in the platform's secrets — the server refuses
# a public bind without it. ANTHROPIC_API_KEY / GEMINI_API_KEY are optional
# (offline mode still serves retrieval, library, search).
CMD ["python", "-m", "nicomachus", "serve", "--no-open"]
