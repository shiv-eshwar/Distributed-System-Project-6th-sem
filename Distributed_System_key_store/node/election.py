import socket
import json
import config.config as config
from utils.logger import setup_logger

logger = setup_logger(f"Node-{PORT}" if "PORT" in globals() else "Node")

def start_election(current_host, current_port):
    config.RAFT_STATE["current_term"] += 1
    config.RAFT_STATE["voted_for"] = current_port
    
    term = config.RAFT_STATE["current_term"]
    logger.info(f"\n[RAFT ELECTION] Starting Term {term}")
    
    votes = 1  
    reachable_nodes = 1  
    
    for host, port in config.NODES:
        if int(port) == int(current_port): continue
        
        try:
            with socket.create_connection((host, port), timeout=0.3) as sock:
                reachable_nodes += 1
                msg = {
                    "command": "REQUEST_VOTE",
                    "term": term,
                    "candidate": current_port
                }
                sock.sendall(json.dumps(msg).encode())
                resp = sock.recv(1024).decode()
                if resp == "VOTE_GRANTED":
                    votes += 1
        except:
            continue

    if getattr(config, "DYNAMIC_QUORUM", False):
        majority = (reachable_nodes // 2) + 1
        logger.info(f"[ELECTION] Dynamic quorum enabled: reachable={reachable_nodes}, majority={majority}")
    else:
        majority = (len(config.NODES) // 2) + 1
        logger.info(f"[ELECTION] Static quorum: cluster={len(config.NODES)}, majority={majority}")

    logger.info(f"[ELECTION] Received {votes}/{len(config.NODES)} votes.")
    
    if votes >= majority:
        logger.info(f"--- RESULT: I ({current_port}) am the Leader for Term {term} ---")
        return True
    return False

def is_node_alive(host, port):
    """Check if a node is alive by attempting a quick connection"""
    try:
        with socket.create_connection((host, port), timeout=0.5) as sock:
            return True
    except:
        return False