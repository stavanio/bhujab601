#!/usr/bin/env bash
set -euo pipefail

IFACE="${1:-can0}"
BITRATE="${2:-1000000}"

sudo ip link set "$IFACE" down 2>/dev/null || true
sudo ip link set "$IFACE" type can bitrate "$BITRATE"
sudo ip link set "$IFACE" up

ip -details link show "$IFACE"
