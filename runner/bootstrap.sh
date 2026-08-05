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
# ⚠ 2026-08-06 實測教訓：**絕對不要裝 iptables-persistent**——它與 ufw 互斥，
# apt 會直接把 ufw 移除（`Remove: ufw:amd64`）。DOCKER-USER 規則改用 systemd
# unit 在每次開機/docker 重啟後重建，不依賴任何持久化套件。
if dpkg -l iptables-persistent 2>/dev/null | grep -q '^ii'; then
  echo "偵測到 iptables-persistent（與 ufw 互斥）→ 移除"
  apt-get purge -y -qq iptables-persistent netfilter-persistent
fi
apt-get install -y -qq ufw
ufw --force reset >/dev/null
ufw default deny incoming
ufw default allow outgoing
ufw allow 22/tcp comment 'ssh'
ufw allow from "$A_HOST_IP" to any port 8080 proto tcp comment 'runner from A'
ufw --force enable

# docker 直接改 iptables 繞過 ufw（FORWARD 鏈）→ 需在 DOCKER-USER 補規則。
# 寫成 systemd unit：docker 啟動後套用，重開機自動生效。
cat > /usr/local/sbin/runner-firewall <<SCRIPT
#!/usr/bin/env bash
# 冪等：先刪同規則再插入，避免重複堆疊
set -u
RULE=(-p tcp --dport 8080 ! -s "$A_HOST_IP" -j DROP)
while iptables -D DOCKER-USER "\${RULE[@]}" 2>/dev/null; do :; done
iptables -I DOCKER-USER "\${RULE[@]}"
SCRIPT
chmod +x /usr/local/sbin/runner-firewall

cat > /etc/systemd/system/runner-firewall.service <<'UNIT'
[Unit]
Description=Restrict runner port to server A (DOCKER-USER chain)
After=docker.service
Requires=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
ExecStart=/usr/local/sbin/runner-firewall

[Install]
WantedBy=multi-user.target
UNIT
systemctl daemon-reload
systemctl enable --now runner-firewall.service

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

echo "== 5/5 驗證 =="
fail=0
check() { # check <說明> <條件指令>
  # 子 shell 內關掉 pipefail：`cmd | grep -q` 命中即結束會讓上游收 SIGPIPE（rc=141），
  # 在 pipefail 下會被誤判為失敗（2026-08-06 實測踩到，SSH 檢查假性 FAIL）
  if ( set +o pipefail; eval "$2" ) >/dev/null 2>&1; then
    echo "  [OK]   $1"
  else
    echo "  [FAIL] $1"
    fail=1
  fi
}
check "swap 已啟用"            "swapon --show | grep -q /swapfile"
check "docker 可用"            "docker info"
check "ufw 存在且啟用"         "ufw status | grep -q '^Status: active'"
check "ufw 放行 SSH"           "ufw status | grep -q '22/tcp'"
check "ufw 限制 8080 來源"     "ufw status | grep -q '$A_HOST_IP'"
check "DOCKER-USER 規則就位"   "iptables -S DOCKER-USER | grep -q -- '--dport 8080'"
check "firewall unit 已啟用"   "systemctl is-enabled runner-firewall.service"
check "SSH 密碼登入已關閉"     "sshd -T | grep -q '^passwordauthentication no'"

echo
free -m | head -2
docker --version
if [[ $fail -ne 0 ]]; then
  echo
  echo "⚠ 有項目未通過，請貼上上面的 [FAIL] 行" >&2
  exit 1
fi
echo "全部通過。下一步：cd ~/runner && cp .env.example .env && 填入 RUNNER_TOKEN && bash deploy.sh"
