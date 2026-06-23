# ─── Etapa 1: Build de la app Vite/React ───────────────────────────────────────
FROM node:20-alpine AS builder

WORKDIR /app

# Copiar manifiestos de dependencias primero (mejor uso de cache de capas)
COPY package.json package-lock.json ./
RUN npm ci --silent

# Copiar el resto del código fuente
COPY . .

# Build de producción (genera /app/dist)
RUN npm run build

# ─── Etapa 2: Servir con Nginx (imagen mínima) ─────────────────────────────────
FROM nginx:1.27-alpine AS runtime

# Eliminar la config default de nginx
RUN rm /etc/nginx/conf.d/default.conf

# Config personalizada: SPA routing (redirige 404 → index.html para React Router)
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Copiar el build estático desde la etapa anterior
COPY --from=builder /app/dist /usr/share/nginx/html

EXPOSE 80

HEALTHCHECK --interval=30s --timeout=3s --start-period=5s \
  CMD wget -qO- http://localhost/index.html || exit 1

CMD ["nginx", "-g", "daemon off;"]
