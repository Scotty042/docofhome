FROM node:22.16-alpine AS frontend-build
WORKDIR /frontend

# Suppress non-actionable install notices during image builds. The explicit
# runtime audit below remains enabled and reports only shipped dependencies.
ENV NPM_CONFIG_AUDIT=false \
    NPM_CONFIG_FUND=false \
    NPM_CONFIG_UPDATE_NOTIFIER=false

COPY frontend/package*.json frontend/.npmrc ./
RUN if [ -f package-lock.json ]; then \
      npm ci --ignore-scripts --no-audit --no-fund; \
    else \
      echo "Hinweis: Kein package-lock.json vorhanden; verwende npm install."; \
      npm install --ignore-scripts --no-audit --no-fund; \
    fi

# The final image contains only static frontend output. Therefore audit the
# production dependency tree separately from build and test tooling.
RUN npm audit --omit=dev --audit-level=high || \
    echo "WARNUNG: npm audit meldet produktive Abhängigkeiten; Details oben prüfen."

COPY frontend/ ./
RUN npm run build

FROM python:3.13.5-slim AS runtime
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1
WORKDIR /app

COPY backend/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt
COPY backend/app ./app
COPY backend/alembic.ini ./alembic.ini
COPY backend/migrations ./migrations
COPY VERSION ./VERSION
COPY CHANGELOG.md RELEASE_NOTES_*.md ./release-notes/
COPY --from=frontend-build /frontend/dist ./static

RUN mkdir -p /data/database /data/backups /data/cache /data/logs /data/restore

# Fail the image build when the complete FastAPI application cannot be imported.
# This catches runtime annotation and router-import errors before a container is created.
RUN python -c "from app.main import app; assert app is not None"

EXPOSE 8000
CMD ["sh", "-c", "python -m app.core.restore_pending && alembic upgrade head && exec uvicorn app.main:app --host 0.0.0.0 --port 8000"]
