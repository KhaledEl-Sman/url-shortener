# ── Stage 1: lint ─────────────────────────────────────────────────────────────
FROM node:22-alpine AS linter

WORKDIR /lint

COPY package.json package-lock.json* ./
RUN npm install --prefer-offline 2>/dev/null || npm install

COPY . .
RUN npm run lint

# ── Stage 2: runtime (Nginx) ──────────────────────────────────────────────────
FROM nginx:1.27-alpine AS runtime

RUN rm /etc/nginx/conf.d/default.conf

COPY nginx.conf /etc/nginx/conf.d/app.conf

COPY --from=linter /lint/css   /usr/share/nginx/html/css
COPY --from=linter /lint/js    /usr/share/nginx/html/js
COPY --from=linter /lint/pages /usr/share/nginx/html/pages
COPY index.html                /usr/share/nginx/html/index.html

EXPOSE 80

HEALTHCHECK --interval=30s --timeout=5s \
    CMD wget -q -O- http://127.0.0.1/health || exit 1
