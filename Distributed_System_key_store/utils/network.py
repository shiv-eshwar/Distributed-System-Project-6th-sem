# utils/network.py

import socket
import json
from utils.logger import setup_logger

logger = setup_logger("network")

def send_message(host, port, message):
    """Send a message to a remote node with proper error handling and timeouts."""
    try:
        client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client.settimeout(2)  # 2 second timeout for all socket operations
        client.connect((host, port))
        client.send(json.dumps(message).encode())
        response = client.recv(4096).decode()
        return response
    except socket.timeout:
        logger.debug(f"Timeout connecting to {host}:{port}")
        return None
    except ConnectionRefusedError:
        logger.debug(f"Connection refused by {host}:{port}")
        return None
    except Exception as e:
        logger.debug(f"Error sending message to {host}:{port}: {e}")
        return None
    finally:
        try:
            client.close()
        except:
            pass