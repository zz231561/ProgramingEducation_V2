#!/usr/bin/env bash
# B 機一次性初始化 — swap / docker / 防火牆 / SSH 收斂。
# 冪等：重跑安全。用法（在 B 機上）：sudo bash bootstrap.sh <A機公網IP>
set -euo pipefail

A_HOST_IP="${1:-}"
if [[ -z "$A_HOST_IP" ]]; then
  echo "用法：sudo bash bootstrap.sh <A機公網IP>" >&2
  exit 1
fi

echo "== 1/5 swap 2G =="
if ! swapon --show | grep -q /swapfile; then
  fallocate -l 2G /swapfile
  chmod 600 /swapfile
  mkswap /swapfile
  swapon /swapfile
  grep -q '^/swapfile' /etc/fstab || echo '/swapfile none swap sw 0 0' >> /etc/fstab
  # 2C2G：偏好留在記憶體，swap 僅作編譯尖峰的安全網
  sysctl -w vm.swappiness=10
  grep -q '^vm.swappiness' /etc/sysctl.conf || echo 'vm.swappiness=10' >> /etc/sysctl.conf
else
  echo "swap 已存在，略過"
fi

echo "== 2/5 docker =="
if ! command -v docker >/dev/null; then
  apt-get update -qq
  apt-get install -y -qq docker.io docker-compose-v2
  systemctl enable --now docker
else
  echo "docker 已安裝，略過"
fi

echo "== 3/5 防火牆（runner port 僅放行 A 機）=="
apt-get install -y -qq ufw
ufw --force reset >/dev/null
ufw default deny incoming
ufw default allow outgoing
ufw allow 22/tcp comment 'ssh'
ufw allow from "$A_HOST_IP" to any port 8080 proto tcp comment 'runner from A'
ufw --force enable
# docker 會直接改 iptables 繞過 ufw（FORWARD 鏈），需額外擋外部直連容器
iptables -I DOCKER-USER -p tcp --dport 8080 ! -s "$A_HOST_IP" -j DROP 2>/dev/null || true
apt-get install -y -qq iptables-persistent >/dev/null 2>&1 || true
netfilter-persistent save >/dev/null 2>&1 || true

echo "== 4/5 SSH 收斂（禁密碼登入）=="
if grep -q '^ *PasswordAuthentication *yes' /etc/ssh/sshd_config /etc/ssh/sshd_config.d/* 2>/dev/null; then
  sed -i 's/^ *PasswordAuthentication *yes/PasswordAuthentication no/' /etc/ssh/sshd_config
  sed -i 's/^ *PasswordAuthentication *yes/PasswordAuthentication no/' /etc/ssh/sshd_config.d/* 2>/dev/null || true
  systemctl reload ssh
  echo "已禁用密碼登入（金鑰仍可用）"
else
  echo "密碼登入已關閉或未顯式啟用"
fi
# 清掉重複的 authorized_keys 條目（R3 安裝時貼了兩次）
for home in /root /home/ubuntu; do
  ak="$home/.ssh/authorized_keys"
  [[ -f "$ak" ]] && sort -u "$ak" -o "$ak"
done

echo "== 5/5 完成 =="
free -m | head -2
docker --version
ufw status numbered | head -10
