# Quick Setup & Testing Guide

## Prerequisites
- Python 3.6+ (already configured in your `.venv`)
- 4 terminal windows or use the provided `start_system.py`

---

## Option 1: Automated System Start (RECOMMENDED)

### Start All Nodes at Once
```bash
cd c:\Users\Pritam Gupta\OneDrive - Amrita vishwa vidyapeetham\Distributed_System_key_store
python start_system.py
```

This will:
- Open 4 terminal windows (one per node)
- Start nodes on ports 5001, 5002, 5003, 5004
- Display the election process in each terminal
- Automatically shut down all nodes when you press Ctrl+C

---

## Option 2: Manual Startup (If auto-start fails)

### Terminal 1: Node 5001
```bash
python node/node_server.py 5001
```
Expected output:
```
Node 5001 listening on localhost:5001
--- Node 5001 acting as FOLLOWER: Monitoring leader ---
[!] Leader timeout at 5001! Starting election...
--- Election Started by Node 5001 ---
RESULT: I (5001) am the new Leader!
```

### Terminal 2: Node 5002
```bash
python node/node_server.py 5002
```

### Terminal 3: Node 5003
```bash
python node/node_server.py 5003
```

### Terminal 4: Node 5004
```bash
python node/node_server.py 5004
```

**Wait 2-3 seconds for election to complete before running tests.**

---

## Running Tests

### Terminal 5: Run Automated Tests
```bash
python test_system.py
```

Expected output:
```
============================================================
Testing Distributed Key-Value Store System
============================================================

[Waiting] Giving system time to elect leader (2 seconds)...

[Test 1/8] Store alice
   Command: PUT user:1 = alice
   ✓ Response from localhost:5001 -> Stored in leader and replicated

[Test 2/8] Retrieve alice
   Command: GET user:1
   Response from localhost:5001 -> alice

[Test 3/8] Store bob
   Command: PUT user:2 = bob
   ✓ Response from localhost:5001 -> Stored in leader and replicated
...
```

All 8 tests should say ✓ or show successful responses.

---

## Manual Interactive Testing

### Terminal 5: Interactive Client
```bash
python client/client.py
```

Example session:
```
--- Distributed Key-Value Store Client ---

Enter command (PUT/GET/EXIT): PUT
Key: name
Value: pritam
✓ Response from localhost:5001 -> Stored in leader and replicated

Enter command (PUT/GET/EXIT): GET
Key: name
Response from localhost:5001 -> pritam

Enter command (PUT/GET/EXIT): PUT
Key: age
Value: 21
✓ Response from localhost:5001 -> Stored in leader and replicated

Enter command (PUT/GET/EXIT): EXIT
```

---

## Failover Testing (Advanced)

### Test 1: Kill the Leader
1. After running tests, go to the Terminal running Node 5001 (the leader)
2. Press **Ctrl+C** to stop it
3. Watch the other nodes - one will say "Leader timeout! Starting election..."
4. The highest-numbered surviving node becomes the new leader
5. Try running tests again - they should still work!

### Test 2: Restart a Node
1. After killing a node, restart it:
   ```bash
   python node/node_server.py 5001
   ```
2. The node will join as a FOLLOWER
3. It will receive replicated data from the leader
4. Watch for `Replicated:` messages showing data sync

---

## Troubleshooting

### "Address already in use" Error
**Cause:** Port still in use from previous run
**Solution:** 
```bash
# Windows
netstat -ano | findstr 5001
taskkill /PID <PID> /F

# Or wait 60 seconds for OS to release port
```

### "Connection refused" from client
**Cause:** Nodes aren't started yet
**Fix:** Make sure you see all 4 nodes printing "listening on localhost:5001" etc.

### Tests timeout or fail
**Cause:** Leader election not complete
**Fix:** Wait 3-5 seconds after starting nodes before running tests. The timing is:
- Node starts → Waits for heartbeat → 4 second timeout → Triggers election → 0.5 seconds → Ready

### Incorrect replication
**Cause:** Not all nodes started
**Fix:** Ensure all 4 nodes are listening before putting data

---

## What to Expect During Normal Operation

### Node Startup Sequence (First 5 seconds)
```
Node 5001 listening
--- Node 5001 acting as FOLLOWER: Monitoring leader ---

Node 5002 listening  
--- Node 5002 acting as FOLLOWER: Monitoring leader ---

[!] Leader timeout at 5001! (one node does this after 4 seconds)
--- Election Started by Node 5001 ---
RESULT: I (5001) am the new Leader!
[STATE CHANGE] Node 5001 - Leader Status: True
--- Node 5001 acting as LEADER: Starting heartbeat emission ---
```

### During Normal Operation
```
[Node 5003 only sees heartbeats, nothing printed]
[PUT creates this in leader terminal]
[ADAPTIVE LOGIC] Active Followers: 3
[ADAPTIVE LOGIC] Target Nodes: [5002, 5003]

[Follower terminals show]
Replicated: key=value
```

---

## Files Overview

| File | Purpose |
|------|---------|
| `config/config.py` | Cluster configuration (nodes, timeouts) |
| `node/node_server.py` | Main server logic |
| `node/heartbeat.py` | Leader heartbeat & election triggers |
| `node/election.py` | Bully algorithm for leader election |
| `node/storage.py` | In-memory key-value store |
| `client/client.py` | Client to send PUT/GET requests |
| `utils/network.py` | Socket communication utilities |
| `start_system.py` | **NEW** - Auto-start all nodes |
| `test_system.py` | **NEW** - Automated test suite |
| `ISSUES_AND_FIXES.md` | **NEW** - Detailed issue report |

---

## Key Metrics to Monitor

- **Leader**: Port number of current leader
- **Response Time**: Should be <100ms for GET, <200ms for PUT
- **Replication**: Check that followers receive updates
- **Election Time**: Should complete in 5-7 seconds when leader dies

---

## Ready to Test?

```bash
# Quick start
python start_system.py

# In another terminal (after 3 seconds)
python test_system.py
```

All tests should pass! ✅

---

**Last Updated:** April 15, 2026  
**Tested On:** Python 3.8+ (Windows/Linux/Mac compatible)
