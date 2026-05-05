import sys
import os
import socket
import json
import time

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.logger import setup_logger
logger = setup_logger("client")

from config.config import NODES
from utils.network import send_message
from node.election import start_election

def send_request(command, key, value=None):
    message = {"command": command, "key": key, "value": value}
    
    max_retries = 5 
    
    for attempt in range(max_retries):
        last_error = None
        leader_found = False

        for host, port in NODES:
            try:
                client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                client.settimeout(1.5) 
                client.connect((host, port))
                client.send(json.dumps(message).encode())

                response = client.recv(4096).decode()
                client.close()

                if "Stored in leader" in response:
                    logger.info(f"✓ Success! Leader found at {port}: {response}")
                    return 
                elif "Error: Not the leader" in response:
                    continue 
                else:
                    logger.info(f"Response from {host}:{port} -> {response}")
                    return

            except (socket.timeout, ConnectionRefusedError, Exception) as e:
                last_error = str(e)
                continue

        if attempt < max_retries - 1:
            logger.info(f"Attempt {attempt + 1} failed. Cluster might be electing a leader... Retrying in 3s.")
            time.sleep(3) 
        else:
            logger.info("Request failed: All retries exhausted. No leader found.")

if __name__ == "__main__":
    logger.info("--- Distributed Key-Value Store Client ---")
    while True:
        try:
            cmd = input("\nEnter command (PUT/GET/EXIT): ").upper()
            if cmd == "EXIT": break
            if cmd not in ["PUT", "GET"]: continue
            
            key = input("Key: ")
            value = input("Value: ") if cmd == "PUT" else None
            send_request(cmd, key, value)
        except KeyboardInterrupt:
            break