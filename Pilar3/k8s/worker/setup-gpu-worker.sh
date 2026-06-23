#!/bin/bash
# =============================================================================
# setup-gpu-worker.sh — Configuración del Worker GPU en el clúster k3s de Ale
# =============================================================================
# Ejecutar UNA SOLA VEZ en el clúster de Ale.
# Requisitos previos:
#   - kubectl apuntando al clúster k3s de Ale
#   - Tener el archivo ar-reader-key.json (pedírselo a Naiara)
#   - NVIDIA device plugin instalado en k3s
#
# Uso:
#   chmod +x setup-gpu-worker.sh
#   ./setup-gpu-worker.sh <ruta-a-ar-reader-key.json>
# =============================================================================

set -euo pipefail

AR_KEY_FILE="${1:-ar-reader-key.json}"
NAMESPACE="g-naj"
REGISTRY="us-central1-docker.pkg.dev"

# Verificar que la clave existe
if [ ! -f "$AR_KEY_FILE" ]; then
  echo "❌ No se encontró el archivo de clave: $AR_KEY_FILE"
  echo "   Pedíle a Naiara el archivo ar-reader-key.json"
  exit 1
fi

echo "======================================================"
echo " StickerChain — Setup Worker GPU en k3s"
echo "======================================================"
echo ""

# 1. Crear namespace
echo "[1/4] Creando namespace '$NAMESPACE'..."
kubectl create namespace "$NAMESPACE" --dry-run=client -o yaml | kubectl apply -f -

# 2. Crear imagePullSecret para Artifact Registry de GCP
echo "[2/4] Creando imagePullSecret para Artifact Registry..."
kubectl create secret docker-registry gcr-artifact-registry \
  --docker-server="$REGISTRY" \
  --docker-username=_json_key \
  --docker-password="$(cat "$AR_KEY_FILE")" \
  --docker-email=stickerchain@noreply.com \
  --namespace="$NAMESPACE" \
  --dry-run=client -o yaml | kubectl apply -f -

# Borrar la clave del disco por seguridad
echo "    🔒 Eliminando clave JSON del disco local..."
rm -f "$AR_KEY_FILE"

# 3. Crear secret de RabbitMQ
echo "[3/4] Creando secret de RabbitMQ (miner_user)..."
kubectl create secret generic rabbitmq-secret \
  --from-literal=username=miner_user \
  --from-literal=password=miner2026 \
  --namespace="$NAMESPACE" \
  --dry-run=client -o yaml | kubectl apply -f -

# 4. Aplicar el deployment del worker GPU
echo "[4/4] Aplicando deployment del Worker GPU..."
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
kubectl apply -f "$SCRIPT_DIR/../Pilar3/k8s/worker/deployment-gpu-external.yaml"

echo ""
echo "======================================================"
echo " ✅ Setup completo. Verificando estado del pod..."
echo "======================================================"
echo ""
kubectl get pods -n "$NAMESPACE" -l app=worker-gpu
echo ""
echo "Para ver los logs del worker:"
echo "  kubectl logs -n $NAMESPACE -l app=worker-gpu -f"
