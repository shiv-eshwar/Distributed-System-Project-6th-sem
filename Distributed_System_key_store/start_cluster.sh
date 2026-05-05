#!/usr/bin/env bash
# ============================================================
#  start_cluster.sh
#  Distributed Key-Value Store - Automatic Cluster Launcher
#
#  HOW TO USE:
#    1. Change NUM_NODES below to however many nodes you want
#    2. (Optional) Change START_PORT if 5001 is taken
#    3. Run:  bash start_cluster.sh
#
#  CHANGE THIS VALUE to set the number of nodes:
# ============================================================

NUM_NODES=4          # <-- CHANGE THIS (e.g., 3, 5, 6)
START_PORT=5001      # <-- First node's port (others follow: 5002, 5003...)

# ============================================================
#  DO NOT EDIT BELOW THIS LINE
# ============================================================

# Color codes for pretty output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m' # No Color

# Resolve the directory where this script lives (= project root)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CONFIG_FILE="$SCRIPT_DIR/config/config.py"
NODE_SERVER="$SCRIPT_DIR/node/node_server.py"

echo -e "${BOLD}${CYAN}"
echo "  ╔══════════════════════════════════════════════════════╗"
echo "  ║     Distributed Key-Value Store - Cluster Launcher   ║"
echo "  ╚══════════════════════════════════════════════════════╝"
echo -e "${NC}"

# ── Validate inputs ────────────────────────────────────────
if ! [[ "$NUM_NODES" =~ ^[0-9]+$ ]] || [ "$NUM_NODES" -lt 1 ]; then
    echo -e "${RED}[ERROR] NUM_NODES must be a positive integer. You set: $NUM_NODES${NC}"
    exit 1
fi

# ── Detect Python interpreter ──────────────────────────────
if command -v python3 &>/dev/null; then
    PYTHON="python3"
elif command -v python &>/dev/null; then
    PYTHON="python"
else
    echo -e "${RED}[ERROR] Python not found. Please install Python 3.${NC}"
    exit 1
fi

echo -e "${GREEN}[INFO]${NC} Python interpreter : ${BOLD}$PYTHON${NC}"
echo -e "${GREEN}[INFO]${NC} Project root       : ${BOLD}$SCRIPT_DIR${NC}"
echo -e "${GREEN}[INFO]${NC} Number of nodes    : ${BOLD}${YELLOW}$NUM_NODES${NC}"
echo -e "${GREEN}[INFO]${NC} Port range         : ${BOLD}$START_PORT - $((START_PORT + NUM_NODES - 1))${NC}"
echo ""

# ── Detect available terminal emulator ────────────────────
detect_terminal() {
    for term in gnome-terminal xterm konsole xfce4-terminal lxterminal mate-terminal tilix; do
        if command -v "$term" &>/dev/null; then
            echo "$term"
            return
        fi
    done
    echo "none"
}

TERMINAL=$(detect_terminal)
if [ "$TERMINAL" = "none" ]; then
    echo -e "${RED}[ERROR] No supported terminal emulator found.${NC}"
    echo -e "  Install one of: gnome-terminal, xterm, konsole, xfce4-terminal"
    exit 1
fi
echo -e "${GREEN}[INFO]${NC} Terminal emulator  : ${BOLD}$TERMINAL${NC}"
echo ""

# ── Build the NODES list and patch config.py ──────────────
echo -e "${YELLOW}[STEP 1]${NC} Updating ${BOLD}config/config.py${NC} for $NUM_NODES nodes..."

# Build the Python list string
NODES_LIST="NODES = ["$'\n'
for i in $(seq 0 $((NUM_NODES - 1))); do
    PORT=$((START_PORT + i))
    NODES_LIST+="    (\"localhost\", $PORT),"$'\n'
done
NODES_LIST+="]"

# Replace the NODES = [...] block in config.py using Python itself (safe & portable)
$PYTHON - <<PYEOF
import re, sys

config_path = "$CONFIG_FILE"
try:
    with open(config_path, 'r') as f:
        content = f.read()
except FileNotFoundError:
    print(f"[ERROR] config.py not found at {config_path}")
    sys.exit(1)

new_nodes = """$NODES_LIST"""

# Replace ONLY the active NODES = [...] block (last occurrence, not commented ones)
# Strategy: find the last un-commented NODES = [ block and replace it
pattern = r'^NODES\s*=\s*\[.*?\]'
new_content = re.sub(pattern, new_nodes.strip(), content, flags=re.DOTALL | re.MULTILINE)

if new_content == content:
    print("[WARNING] NODES block not found or already matches. config.py unchanged.")
else:
    with open(config_path, 'w') as f:
        f.write(new_content)
    print(f"[OK] config.py updated with {$NUM_NODES} nodes (ports {$START_PORT}-{$START_PORT + $NUM_NODES - 1})")
PYEOF

if [ $? -ne 0 ]; then
    echo -e "${RED}[ERROR] Failed to update config.py. Aborting.${NC}"
    exit 1
fi

echo ""

# ── Track launched processes ──────────────────────────────
declare -a PIDS=()
declare -a PORTS=()

# ── Cleanup function called on Ctrl+C ────────────────────
cleanup() {
    echo ""
    echo -e "${YELLOW}[SHUTDOWN]${NC} Stopping all nodes..."
    for pid in "${PIDS[@]}"; do
        if kill -0 "$pid" 2>/dev/null; then
            kill "$pid" 2>/dev/null
            echo -e "  ${RED}✗${NC} Killed process $pid"
        fi
    done
    echo -e "${GREEN}[DONE]${NC} All nodes stopped. Goodbye!"
    exit 0
}

trap cleanup SIGINT SIGTERM

# ── Launch each node in its own terminal window ────────────
echo -e "${YELLOW}[STEP 2]${NC} Launching ${BOLD}$NUM_NODES${NC} nodes in separate terminals..."
echo ""

for i in $(seq 0 $((NUM_NODES - 1))); do
    PORT=$((START_PORT + i))
    NODE_TITLE="Node $PORT | Distributed KV Store"
    CMD="cd '$SCRIPT_DIR' && $PYTHON '$NODE_SERVER' $PORT; echo ''; echo '[Node $PORT exited. Press Enter to close.]'; read"

    case "$TERMINAL" in
        gnome-terminal)
            gnome-terminal --title="$NODE_TITLE" -- bash -c "$CMD" &
            PIDS+=($!)
            ;;
        xterm)
            xterm -title "$NODE_TITLE" -fa 'Monospace' -fs 11 -e bash -c "$CMD" &
            PIDS+=($!)
            ;;
        konsole)
            konsole --title "$NODE_TITLE" -e bash -c "$CMD" &
            PIDS+=($!)
            ;;
        xfce4-terminal)
            xfce4-terminal --title="$NODE_TITLE" -e "bash -c \"$CMD\"" &
            PIDS+=($!)
            ;;
        lxterminal)
            lxterminal --title="$NODE_TITLE" -e "bash -c \"$CMD\"" &
            PIDS+=($!)
            ;;
        mate-terminal)
            mate-terminal --title="$NODE_TITLE" -e "bash -c \"$CMD\"" &
            PIDS+=($!)
            ;;
        tilix)
            tilix -t "$NODE_TITLE" -e "bash -c \"$CMD\"" &
            PIDS+=($!)
            ;;
    esac

    PORTS+=($PORT)
    echo -e "  ${GREEN}✓${NC} Launched Node ${BOLD}$PORT${NC} (PID: ${PIDS[$i]})"
    sleep 0.3  # Small delay to stagger startup
done

echo ""
echo -e "${GREEN}══════════════════════════════════════════════════════${NC}"
echo -e "${BOLD}  All $NUM_NODES nodes launched successfully!${NC}"
echo ""
echo -e "  Nodes running on ports: ${CYAN}${PORTS[*]}${NC}"
echo ""
echo -e "  Wait ${BOLD}3-5 seconds${NC} for leader election to complete."
echo ""
echo -e "  Then run the client in a NEW terminal:"
echo -e "  ${YELLOW}  cd $SCRIPT_DIR && $PYTHON client/client.py${NC}"
echo ""
echo -e "  Press ${BOLD}Ctrl+C${NC} HERE to stop all nodes."
echo -e "${GREEN}══════════════════════════════════════════════════════${NC}"
echo ""

# ── Keep this script alive so Ctrl+C triggers cleanup ────
wait
