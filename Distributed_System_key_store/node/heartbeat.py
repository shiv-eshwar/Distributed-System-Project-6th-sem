import threading
import time
import random
from utils.network import send_message
from config.config import NODES, HEARTBEAT_INTERVAL, LEADER_TIMEOUT, RAFT_STATE
from node.election import start_election
from utils.logger import setup_logger

logger = setup_logger(f"Node-{PORT}" if "PORT" in globals() else "Node")

last_heartbeat = time.time()
heartbeat_thread = None
stop_event = threading.Event()
state_lock = threading.Lock()

RANDOMIZED_TIMEOUT = LEADER_TIMEOUT + random.uniform(0, 2)

def start_heartbeat(host, port, is_leader):
    global heartbeat_thread, stop_event

    with state_lock:
        stop_event.set() 
        
        if heartbeat_thread and heartbeat_thread.is_alive():
            if heartbeat_thread != threading.current_thread():
                heartbeat_thread.join(timeout=1.5)
        
        stop_event.clear()

        if is_leader:
            logger.info(f"--- Node {port} acting as LEADER: Starting heartbeat emission ---")
            heartbeat_thread = threading.Thread(target=send_heartbeats, args=(host, port), daemon=True)
        else:
            logger.info(f"--- Node {port} acting as FOLLOWER: Monitoring leader ---")
            update_heartbeat() 
            heartbeat_thread = threading.Thread(target=monitor_leader, args=(host, port), daemon=True)
        
        heartbeat_thread.start()

def send_heartbeats(host, port):
    logger.info(f"[HB-SEND] Node {port} starting heartbeat emission")
    count = 0
    while not stop_event.is_set():
        term = RAFT_STATE["current_term"]
        count += 1
        sent_to = []
        for node in NODES:
            if node[1] != port:
                threading.Thread(
                    target=send_message, 
                    args=(node[0], node[1], {"command": "HEARTBEAT", "leader": port, "term": term}),
                    daemon=True
                ).start()
                sent_to.append(node[1])
        if count % 5 == 0:  
            logger.info(f"[HB-SEND] Node {port} sent heartbeat (Term {term}) to {sent_to}")
        time.sleep(HEARTBEAT_INTERVAL)

def monitor_leader(host, port):
    """Followers watch for the Leader's silence"""
    global last_heartbeat
    from node.node_server import set_leader_status

    logger.info(f"[HB-MONITOR] Node {port} starting heartbeat monitor (timeout={RANDOMIZED_TIMEOUT:.1f}s)")
    check_count = 0
    while not stop_event.is_set():
        check_count += 1
        time_since_hb = time.time() - last_heartbeat
        
        if check_count % 50 == 0:
            logger.info(f"[HB-MONITOR] Node {port} - Last heartbeat {time_since_hb:.1f}s ago (timeout in {RANDOMIZED_TIMEOUT - time_since_hb:.1f}s)")
        
        if time_since_hb > RANDOMIZED_TIMEOUT:
            logger.info(f"\n[⏱️  TIMEOUT] Node {port} detected leader timeout! ({time_since_hb:.1f}s > {RANDOMIZED_TIMEOUT:.1f}s)")
            
            is_win = start_election(host, port)

            if is_win:
                logger.info(f"[🎉 ELECTED] Node {port} WON the election!")
                set_leader_status(True)
                threading.Thread(target=start_heartbeat, args=(host, port, True), daemon=True).start()
                return 
            else:
                logger.info(f"[😞 LOST] Node {port} lost election, waiting for leader heartbeat")
                set_leader_status(False)
                update_heartbeat() 
                threading.Thread(target=start_heartbeat, args=(host, port, False), daemon=True).start()
                return 

        time.sleep(0.1) 

def update_heartbeat():
    global last_heartbeat
    last_heartbeat = time.time()
