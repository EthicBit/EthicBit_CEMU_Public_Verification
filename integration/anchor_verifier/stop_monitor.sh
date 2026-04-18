#!/bin/bash
PIDFILE="../../logs/anchor_monitor.pid"
if [ -f "$PIDFILE" ]; then
    kill $(cat "$PIDFILE") 2>/dev/null
    rm -f "$PIDFILE"
    echo "🛑 Monitor 24/7 detenido correctamente"
else
    echo "⚠️  No se encontró PID del monitor"
fi
