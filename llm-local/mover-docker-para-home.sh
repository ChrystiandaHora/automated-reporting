#!/usr/bin/env bash
# Move os dados do Docker Engine nativo (/var/lib/docker e /var/lib/containerd)
# da raiz (32 GB) para /home/docker-data, usando bind mount no /etc/fstab.
# O Docker continua enxergando /var/lib/docker — nenhuma config do Docker muda.
#
#   sudo bash llm-local/mover-docker-para-home.sh
#
# Os originais ficam em /var/lib/<dir>.old até você conferir e apagar.
set -euo pipefail

[[ $EUID -eq 0 ]] || { echo "Rode com sudo."; exit 1; }

DEST=/home/docker-data
DIRS=(docker containerd)

for d in "${DIRS[@]}"; do
  if findmnt -n "/var/lib/$d" >/dev/null; then
    echo "/var/lib/$d já é um ponto de montagem — nada a fazer."; exit 0
  fi
done

echo ">> Parando Docker e containerd (os containers do Docker nativo param; o Docker Desktop não é afetado)"
systemctl stop docker.socket docker containerd

for d in "${DIRS[@]}"; do
  [[ -d "/var/lib/$d" ]] || continue
  echo ">> Copiando /var/lib/$d -> $DEST/$d ($(du -sh "/var/lib/$d" | cut -f1))"
  mkdir -p "$DEST/$d"
  cp -a "/var/lib/$d/." "$DEST/$d/"
  mv "/var/lib/$d" "/var/lib/$d.old"
  mkdir "/var/lib/$d"
  echo "$DEST/$d /var/lib/$d none bind,x-systemd.requires-mounts-for=/home 0 0" >> /etc/fstab
done

systemctl daemon-reload
mount -a

for d in "${DIRS[@]}"; do findmnt "/var/lib/$d"; done

echo ">> Subindo containerd e Docker"
systemctl start containerd docker

docker info --format 'Docker OK — root: {{.DockerRootDir}}'
df -h / /home

cat <<EOF

Pronto. Confira se seus containers/imagens do Docker nativo estão ok (docker --context default images).
Depois libere a raiz apagando os originais:
  sudo rm -rf /var/lib/docker.old /var/lib/containerd.old
Para desfazer: pare o docker, remova as 2 linhas de $DEST do /etc/fstab, e renomeie *.old de volta.
EOF
