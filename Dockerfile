# Kindalive — container image for hosting the dashboard so you can reach
# it from your phone without your computer running. See docs/web-ui.md
# ("Use it from your phone") for deploy instructions.
FROM python:3.11-slim

WORKDIR /app
COPY . /app

# Installs NiceGUI (core) + the Anthropic SDK ([live]) and bundles the
# web assets via package-data. The 3D face uses NiceGUI's own vendored
# Three.js, so no extra browser/CDN dependency is needed.
RUN pip install --no-cache-dir ".[live]"

# Bind to all interfaces inside the container; the platform maps the
# port. main() reads these env vars for its host/port defaults.
ENV KINDALIVE_HOST=0.0.0.0
# Most platforms inject $PORT; default to 8080 for a local `docker run`.
ENV PORT=8080
EXPOSE 8080

# Set ANTHROPIC_API_KEY (cloud LLM) at run time, e.g.:
#   docker run -p 8080:8080 -e ANTHROPIC_API_KEY=sk-ant-... kindalive
CMD ["python3", "-m", "kindalive.expression.web_ui"]
