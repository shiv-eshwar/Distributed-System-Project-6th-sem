# Distributed Key-Value Store

A fault-tolerant, highly available distributed key-value database built entirely from scratch in Python. This project demonstrates core distributed systems concepts including leader election, data replication, and consensus, heavily inspired by the **Raft Consensus Algorithm**.

## 🚀 Features

- **Raft-like Leader Election:** Uses randomized timeouts, terms (epochs), and majority quorums to ensure a single, stable leader.
- **High Availability & Fault Tolerance:** If the leader crashes, followers automatically detect the failure via heartbeat timeouts and elect a new leader.
- **Data Replication:** Write operations (`PUT`) are sent to the leader and automatically replicated to active followers.
- **Smart Client Routing:** The client intelligently routes requests, automatically finding the new leader if the node it contacts is a follower or has crashed.
- **Eventual Consistency:** Reads (`GET`) can be served by any node, providing high availability and partition tolerance (AP system in the CAP theorem).
- **Adaptive Replication:** Dynamically adjusts to the number of alive nodes to reduce network overhead.

## 🏗️ Architecture

The system consists of multiple identical nodes (e.g., 4 nodes) and a client interface.
- **Leader:** Handles all write requests and replicates data to followers. Sends periodic heartbeats.
- **Followers:** Monitor the leader's heartbeats. If heartbeats stop, they transition to candidates and start an election. Serve read requests.
- **In-Memory Storage:** Data is stored in-memory using Python dictionaries for fast access.

## 📂 Project Structure

- `node_server.py`: The core engine running on each node, handling client requests and replication.
- `election.py`: Manages the democracy process of choosing a new leader.
- `heartbeat.py`: Runs daemon threads for sending heartbeats (leader) and monitoring heartbeats (followers).
- `storage.py`: Handles the in-memory key-value storage.
- `client.py`: A terminal-based client for sending `PUT` and `GET` requests with intelligent retry logic.
- `config.py`: Contains cluster configuration, timeouts, and port settings.
- `network.py`: Abstraction for socket programming, JSON encoding, and network error handling.

## 🛠️ Getting Started

### Prerequisites
- Python 3.x

### Running the Cluster

You can start the cluster nodes individually using the start script or manually:

```bash
# Start the cluster (starts 4 nodes locally)
./start_cluster.sh
```

Or manually start individual nodes in separate terminals:
```bash
python3 node/node_server.py 5001
python3 node/node_server.py 5002
python3 node/node_server.py 5003
python3 node/node_server.py 5004
```

### Using the Client

Run the client to interact with the database:

```bash
python3 client/client.py
```

**Commands:**
- `PUT <key> <value>`: Store a value. (e.g., `PUT name Alice`)
- `GET <key>`: Retrieve a value. (e.g., `GET name`)

## 💡 How it Works (Election Demo)

1. Start all 4 nodes. Node 5001 (or the fastest one to timeout) will become the Leader.
2. The Leader will start sending `HEARTBEAT` messages.
3. Open the client and `PUT` some data. See it replicated across terminals.
4. **Kill the Leader** (Ctrl+C on its terminal).
5. Watch the other terminals: a follower's timeout will expire, it will request votes, and a **new Leader will be elected** automatically.
6. Continue using the client—it will automatically find the new leader and operations will succeed without data loss!

---
*Developed as a 6th Semester Distributed Systems Project.*
