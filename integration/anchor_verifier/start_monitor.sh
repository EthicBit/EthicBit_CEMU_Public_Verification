#!/bin/bash
cd "$(dirname "$0")"
nohup ./monitor_anchors.sh > ../../logs/anchor_monitor_nohup.log 2>&1 &
echo $! > ../../logs/anchor_monitor.pid
echo "✅ Monitor 24/7 iniciado en background (PID: $(cat ../../logs/anchor_monitor.pid))"
echo "   Log principal: ../../logs/anchor_monitor_24h.log"
echo "   Log nohup:     ../../logs/anchor_monitor_nohup.log"
