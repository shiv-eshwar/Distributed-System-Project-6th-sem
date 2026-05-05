import socket, threading, json, sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# When launched as a script (`python node/node_server.py ...`), expose this
# module under its package name so imports in other modules share the same
# globals (notably leader state).
if __name__ == "__main__":
    sys.modules["node.node_server"] = sys.modules[__name__]

from utils.logger import setup_logger
from config.config import ADAPTIVE_REPLICATION, NODES, RAFT_STATE
from node.storage import KeyValueStore
from utils.network import send_message
from node.heartbeat import start_heartbeat, update_heartbeat

store = KeyValueStore()
HOST = "localhost"
PORT = int(sys.argv[1])

logger = setup_logger(f"Node-{PORT}" if "PORT" in globals() else "Node")
I_AM_LEADER = False
leader_lock = threading.Lock()

def set_leader_status(status):
    global I_AM_LEADER
    with leader_lock:
        old_status = I_AM_LEADER
        I_AM_LEADER = status
        if not status: RAFT_STATE["voted_for"] = None # Reset vote on demotion
        status_str = "LEADER" if status else "FOLLOWER"
        logger.info(f"[SET-LEADER] Node {PORT} set_leader_status({status}): {old_status}->{status}")
        if old_status != status:
            logger.info(f"\n[⚡ STATE CHANGE] Node {PORT} -> {status_str} (Term {RAFT_STATE['current_term']})")
        
def is_leader():
    with leader_lock:
        return I_AM_LEADER

def handle_client(conn):
    try:
        conn.settimeout(2.0)
        data = conn.recv(4096).decode()
        if not data: return
        msg = json.loads(data)
        cmd = msg.get("command")

        # --- RAFT LOGIC: VOTE REQUEST ---
        if cmd == "REQUEST_VOTE":
            c_term = msg.get("term")
            candidate = msg.get("candidate")
            
            # Grant vote if candidate term is higher
            if c_term > RAFT_STATE["current_term"]:
                RAFT_STATE["current_term"] = c_term
                RAFT_STATE["voted_for"] = candidate
                
                # CRITICAL: Reset timer so we don't start a conflicting election
                update_heartbeat() 
                
                logger.info(f"[VOTE] Node {PORT} voting for candidate {candidate} in Term {c_term}")
                conn.sendall(b"VOTE_GRANTED")
                if is_leader():
                    set_leader_status(False)
                    threading.Thread(target=start_heartbeat, args=(HOST, PORT, False), daemon=True).start()
            else:
                conn.sendall(b"VOTE_DENIED")
            return

        # --- RAFT LOGIC: HEARTBEAT ---
        if cmd == "HEARTBEAT":
            l_term = msg.get("term")
            leader = msg.get("leader")
            if l_term >= RAFT_STATE["current_term"]:
                # If we're a leader with a lower term, step down BEFORE updating term
                if is_leader() and l_term > RAFT_STATE["current_term"]:
                    logger.info(f"[HB] Node {PORT} stepping down: received higher term {l_term} from leader {leader}")
                    set_leader_status(False)
                
                update_heartbeat()
                RAFT_STATE["current_term"] = l_term
            conn.sendall(b"OK")
            return

        # --- STANDARD COMMANDS ---
        if cmd == "PUT":
            leader_status = is_leader()
            logger.info(f"[PUT-REQ] Node {PORT} received PUT: is_leader={leader_status}, I_AM_LEADER={I_AM_LEADER}")
            if leader_status:
                store.put(msg["key"], msg["value"])
                threading.Thread(target=replicate_to_followers, args=(msg["key"], msg["value"])).start()
                conn.sendall(b"Stored in leader and replicated")
                logger.info(f"[PUT] Node {PORT} stored key={msg['key']}")
            else:
                conn.sendall(b"Error: Not the leader")
        elif cmd == "GET":
            result = store.get(msg["key"])
            conn.sendall(str(result).encode())
        elif cmd == "REPLICATE":
            store.put(msg["key"], msg["value"])
            conn.sendall(b"Replicated")

    except Exception as e: 
        pass
    finally: conn.close()

def replicate_to_followers(key, value):
    all_potential_followers = [node for node in NODES if node != (HOST, PORT)]
    
    # Import locally to avoid circular dependency
    from node.election import is_node_alive
    active_followers = [n for n in all_potential_followers if is_node_alive(n[0], n[1])]
    
    total_active = len(active_followers)

    if ADAPTIVE_REPLICATION:
        if total_active <= 1:
            replication_nodes = active_followers
        else:
            count = max(1, total_active // 2)
            replication_nodes = active_followers[:count]
    else:
        replication_nodes = active_followers

    logger.info(f"\n[ADAPTIVE LOGIC] Active Followers: {total_active}")
    logger.info(f"[ADAPTIVE LOGIC] Target Nodes: {[n[1] for n in replication_nodes]}")

    for node in replication_nodes:
        message = {"command": "REPLICATE", "key": key, "value": value}
        # Use daemon threads so they exit when the main node stops
        threading.Thread(target=send_message, args=(node[0], node[1], message), daemon=True).start()

if __name__ == "__main__":
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    
    try:
        server.bind((HOST, PORT))
    except OSError as e:
        logger.info(f"Error: Could not bind to port {PORT}. {e}")
        sys.exit(1)

    server.listen(5)
    logger.info(f"Node {PORT} listening on {HOST}:{PORT}")
    
    # Start heartbeat/monitor thread
    start_heartbeat(HOST, PORT, I_AM_LEADER)
    
    while True:
        try:
            conn, addr = server.accept()
            threading.Thread(target=handle_client, args=(conn,), daemon=True).start()
        except KeyboardInterrupt:
            logger.info("\nShutting down node...")
            break