# Distributed Key-Value Store: End-to-End Comprehensive Guide

This document is your ultimate resource for understanding the Distributed Key-Value Store project from top to bottom. It is specifically designed to help you ace your final presentation and answer any Viva questions confidently.

---

## 1. Project Overview

**What is it?**
It's a distributed key-value database built in Python from scratch. Instead of storing data on a single machine (which is a single point of failure), the system distributes data across multiple nodes (servers) running concurrently. 

**Why build it?**
To achieve **High Availability** (if one node goes down, others keep serving) and **Fault Tolerance** (data is not lost if a server crashes).

**How does it work at a high level?**
- The system consists of multiple identical **Nodes** (e.g., 4 nodes running on ports 5001, 5002, 5003, 5004).
- One node is elected as the **Leader**, and the rest become **Followers**.
- The **Client** sends `PUT` (write) or `GET` (read) requests.
- **Writes (`PUT`)** must go to the Leader. The Leader then replicates this data to the Followers.
- **Reads (`GET`)** can be served by the Leader or any Follower (though usually handled by whatever node the client hits first).
- If the Leader crashes, the Followers detect the silence (lack of heartbeats) and hold an **Election** to choose a new Leader.

---

## 2. Architecture & File Breakdown

The project is structured modularly. Here is what each file does:

### `config/config.py` (The Settings)
- **`NODES`**: A list of all server addresses and ports (e.g., `localhost:5001` to `5004`).
- **`RAFT_STATE`**: Keeps track of the current election term (`current_term`) and who the node voted for (`voted_for`). This borrows concepts from the Raft Consensus Algorithm.
- **`HEARTBEAT_INTERVAL` (1.0s)**: How often the Leader says "I'm alive" to the followers.
- **`LEADER_TIMEOUT` (5.0s)**: How long a Follower waits without hearing from the Leader before assuming the Leader is dead and starting an election.
- **`ADAPTIVE_REPLICATION` / `DYNAMIC_QUORUM`**: Settings to dynamically adjust how many nodes need to agree based on how many are currently alive.

### `node/node_server.py` (The Core Engine)
This is the main brain of each node. When you run a node, this file executes.
- **State Management**: Keeps track of whether it is `I_AM_LEADER` or a Follower.
- **Client Handling (`handle_client`)**: It listens for incoming JSON messages.
  - If it receives `REQUEST_VOTE`, it decides whether to vote for a candidate.
  - If it receives `HEARTBEAT`, it acknowledges the leader is alive and updates its internal timer.
  - If it receives `PUT`, it checks if it's the leader. If yes, it stores the data and triggers `replicate_to_followers()`. If not, it rejects it.
  - If it receives `GET`, it fetches the data from its local `storage.py`.
- **Replication**: It finds active followers and sends them a `REPLICATE` command to keep their data in sync with the leader.

### `node/election.py` (The Democracy)
Handles the process of choosing a new leader when the old one fails.
- **`start_election()`**: 
  1. The node increments its `current_term` and votes for itself.
  2. It sends a `REQUEST_VOTE` message to all other nodes.
  3. It waits for `VOTE_GRANTED` responses.
  4. If it receives a **Majority** (Quorum) of votes, it declares itself the Leader and returns `True`.

### `node/heartbeat.py` (The Pulse)
Runs background threads to monitor cluster health.
- **`send_heartbeats()`**: If the node is the Leader, it runs a loop sending a `HEARTBEAT` message to all other nodes every second.
- **`monitor_leader()`**: If the node is a Follower, it constantly checks the time since the last heartbeat. If `time_since_hb > RANDOMIZED_TIMEOUT`, it triggers `start_election()` from `election.py`.
- *Note on Randomized Timeout*: Timeouts are randomized (e.g., 5.0s + up to 2.0s) so that multiple followers don't wake up at the exact same millisecond and tie an election.

### `node/storage.py` (The Database)
- A very simple wrapper around a Python dictionary (`self.store = {}`). Data is kept in RAM (In-Memory). If the node completely shuts down, this data is lost (unless replicated to surviving nodes).

### `utils/network.py` (The Postman)
- Contains `send_message()`, a utility function that opens a socket connection, sends a JSON message, waits for a response, and handles network errors (like Connection Refused or Timeouts) gracefully without crashing the app.

### `client/client.py` (The User Interface)
- A terminal-based client that allows a human user to type `PUT key value` or `GET key`.
- **Intelligent Routing**: If it sends a `PUT` to a Follower, the Follower replies "Error: Not the leader". The client code catches this and tries the next node in the list until it finds the actual Leader.

---

## 3. Step-by-Step Workflows

### Workflow A: Node Startup
1. You run `python node/node_server.py 5001`.
2. The node binds to port 5001 and starts listening.
3. It starts as a **Follower** by default and runs `start_heartbeat(is_leader=False)`, which starts the `monitor_leader()` thread.
4. It waits for heartbeats. If no leader exists (e.g., it's the first node), the timeout will expire, and it will start an election.

### Workflow B: The Election Process (Leader Dies)
1. Leader (Node 5004) crashes. Heartbeats stop.
2. Follower (Node 5001) realizes `time_since_last_heartbeat > 5.0s`.
3. Node 5001 becomes a Candidate: increments its Term, votes for itself.
4. Node 5001 asks Node 5002 and 5003 for votes.
5. Nodes 5002 and 5003 grant the vote because Node 5001's Term is higher than theirs.
6. Node 5001 gets majority votes -> Becomes Leader.
7. Node 5001 immediately starts sending heartbeats. Nodes 5002 and 5003 see the new Leader's heartbeats and reset their timers.

### Workflow C: Writing Data (`PUT`)
1. Client types `PUT user Alice`.
2. Client sends this to Node 5002 (Follower).
3. Node 5002 says "I'm not the leader".
4. Client automatically tries Node 5001 (Leader).
5. Node 5001 accepts it, saves `{ "user": "Alice" }` in its memory.
6. Node 5001 loops through active followers (5002, 5003) and sends a `REPLICATE` command with the data.
7. Node 5001 replies to the client: "Stored in leader and replicated".

---

## 4. Top 15 Viva Questions & Perfect Answers

**Q1. What consensus algorithm did you use for leader election?**
*Answer:* I implemented a customized version inspired by the **Raft Consensus Algorithm**. It uses concepts like "Terms" (epochs), randomized timeouts to prevent split votes, and requires a majority quorum to elect a leader. (Note: Originally it looked like a Bully algorithm, but the implementation using `REQUEST_VOTE` and `Terms` is fundamentally Raft-based).

**Q2. Why do you use randomized timeouts in the heartbeat monitor?**
*Answer:* If the leader dies, and all followers have the exact same timeout (e.g., exactly 5.0 seconds), they will all wake up at the exact same time, become candidates, vote for themselves, and no one will get a majority. Randomizing the timeout (e.g., 5.0s to 7.0s) ensures one node wakes up first and wins the election before others start.

**Q3. How does your system handle replication?**
*Answer:* When the Leader receives a `PUT` request, it first saves the data in its own storage. Then, it spins up background threads to send a `REPLICATE` command to the active followers. I also implemented `ADAPTIVE_REPLICATION`, which means the leader checks which followers are actually alive before trying to replicate, saving network overhead.

**Q4. What is a "Quorum" and why is it important?**
*Answer:* A Quorum is the minimum number of nodes that must agree to elect a leader. Usually, it is a simple majority `(N/2) + 1`. It prevents "Split Brain" scenarios. If a network partition happens and the network splits in half, only the half with the majority can elect a leader, preventing two leaders from accepting conflicting writes simultaneously.

**Q5. Is your data storage persistent?**
*Answer:* In the current implementation, it is **In-Memory** using Python dictionaries. If a single node crashes and restarts, it loses its data but can be re-synced from the leader. If the *entire* cluster shuts down simultaneously, data is lost. For production, I would add Disk Persistence (like writing the dictionary to a JSON file or using an SQLite database).

**Q6. What happens if a client sends a write (`PUT`) to a follower?**
*Answer:* The follower rejects the request and sends back a message saying "Error: Not the leader". My client script is designed to catch this error and intelligently retry the request on other nodes until it successfully locates the actual leader.

**Q7. What happens if a client sends a read (`GET`) to a follower?**
*Answer:* The follower will serve the read directly from its local storage. This improves read scalability because any node can answer a read. However, it means our system provides **Eventual Consistency**—if a client reads from a follower right after writing to the leader, there's a tiny window where the replication might not have finished yet.

**Q8. Explain the CAP Theorem in the context of your project.**
*Answer:* CAP theorem states a distributed system can only provide 2 out of 3 guarantees: Consistency, Availability, and Partition Tolerance. My system leans towards **AP (Availability and Partition Tolerance)**. Because any node can serve a `GET` request, the system is highly available, but it might return slightly stale data (Eventual Consistency) if a network partition delays replication. 

**Q9. How does the Leader know a follower has died?**
*Answer:* The Leader sends heartbeats, but it doesn't strictly track follower deaths to demote them. However, when replicating data, my code uses a helper function `is_node_alive()` which attempts a quick socket connection to the follower. If it fails, the leader knows the follower is dead and skips replicating to it.

**Q10. What is "Split Brain"?**
*Answer:* Split brain occurs when a network failure causes the cluster to split into two groups that cannot communicate with each other, and both groups elect a leader, resulting in two leaders. By requiring a majority vote (`(N/2) + 1`) to become a leader, my system prevents this. The group with the minority of nodes will never be able to elect a leader.

**Q11. Why do you use Daemon Threads for heartbeats?**
*Answer:* Daemon threads automatically shut down when the main Python program exits. If I used regular threads, pressing Ctrl+C on the terminal wouldn't kill the node because the heartbeat threads would keep running in the background, requiring a hard kill of the terminal.

**Q12. What role does `utils/network.py` play?**
*Answer:* It abstracts the complex socket programming. It handles creating the socket, setting timeouts (so the app doesn't hang forever if a node is slow), encoding/decoding JSON, and catching network errors like `ConnectionRefusedError`.

**Q13. How did you resolve the "Address already in use" error during development?**
*Answer:* I added the socket option `socket.SO_REUSEADDR` in `node_server.py`. When a node crashes, the OS puts the port in a `TIME_WAIT` state. This socket option tells the OS to allow us to reuse the port immediately upon restart.

**Q14. What would you improve in this project if you had more time?**
*Answer:* 
1. **Log replication/Persistence:** Saving data to a file so it survives a total cluster shutdown.
2. **Dynamic node joining:** Allowing new nodes to join on the fly without hardcoding their IPs in `config.py`.
3. **Strong Consistency:** Ensuring reads only happen from the leader or requiring a read quorum.

**Q15. Can you walk me through the lifecycle of a `HEARTBEAT` message?**
*Answer:* 
1. Leader's `send_heartbeats` thread creates a JSON: `{"command": "HEARTBEAT", "leader": 5004, "term": 1}`.
2. It sends this to port 5001.
3. Follower 5001's `handle_client` function receives it.
4. Follower 5001 extracts the Term. If the Term is valid, it calls `update_heartbeat()`, which resets `last_heartbeat = time.time()`.
5. Follower replies "OK".
6. Follower's `monitor_leader` thread sees that `time.time() - last_heartbeat` is now very small, so it resets its countdown and does not trigger an election.

---

## Final Presentation Advice

- **Be Confident:** You understand every line of code here. It's a solid implementation of fundamental distributed system concepts (Raft-like leader election, Heartbeats, Replication).
- **Run the Demo Live:** Use `python start_system.py` to open all 4 terminals. Kill the leader terminal with `Ctrl+C` and let the examiners watch the other terminals detect the timeout and automatically elect a new leader. That is the "wow" factor of this project.
- **Show the Client Routing:** Run the client, type a `PUT` command, and show how the client finds the leader even if it initially hits a follower.
- **Relate to real-world:** Mention that this is how real databases like Redis Cluster, MongoDB (Replica Sets), and Apache Kafka handle fault tolerance behind the scenes.
