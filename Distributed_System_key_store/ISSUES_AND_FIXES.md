# Distributed Key-Value Store - Issues Found & Fixed

## Summary
Your distributed key-value store project has a solid foundation with proper leader election (Bully algorithm) and heartbeat monitoring. However, there were **11 issues** preventing reliable operation. Most have been fixed.

---

## ✅ FIXED ISSUES

### 1. **Client Logic Flaw** (CRITICAL)
**Problem:** Client wasn't properly handling leader responses. It would end PUT requests prematurely or return GET results from non-leaders.

**Root Cause:** 
```python
# OLD - flawed logic
if command == "PUT" and "Not the leader" in response:
    continue
print(f"Response from {host}:{port} -> {response}")
return  # Returns on ANY non-timeout response
```

**Fix Applied:**
```python
# NEW - strict validation
if command == "PUT":
    if "Stored in leader" in response:  # Only accept leader responses
        print(f"✓ Response from {host}:{port} -> {response}")
        return
```

**Impact:** PUT operations now reliably reach the leader; GET operations still work from any node.

---

### 2. **Network Error Handling** (HIGH)
**Problem:** Silent failures in `network.py` made debugging impossible.
```python
# OLD
except:
    return None  # Swallows all errors!
```

**Fix Applied:**
```python
# NEW
except socket.timeout:
    logger.debug(f"Timeout connecting to {host}:{port}")
    return None
except ConnectionRefusedError:
    logger.debug(f"Connection refused by {host}:{port}")
    return None
except Exception as e:
    logger.debug(f"Error sending message to {host}:{port}: {e}")
    return None
```

**Impact:** Now can diagnose connection issues.

---

### 3. **Socket Resource Cleanup** (MEDIUM)
**Problem:** Sockets not properly closed in error cases, leading to resource exhaustion.

**Fix Applied in `node_server.py`:**
```python
finally:
    try:
        conn.close()
    except:
        pass
```

**Impact:** Prevents "too many open files" errors under load.

---

### 4. **Socket Reuse Address** (MEDIUM)
**Problem:** After a node crashes, the port is in TIME_WAIT state and can't be reused immediately.

**Fix Applied:**
```python
server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
```

**Impact:** Can restart nodes without waiting 60+ seconds.

---

### 5. **Socket Timeouts** (MEDIUM)
**Problem:** Socket operations could hang indefinitely if the other side disappeared.

**Fix Applied:**
```python
client.settimeout(2)  # 2 second timeout for all socket operations
conn.settimeout(3)    # 3 second timeout for receiving data
```

**Impact:** System stays responsive even when nodes fail.

---

### 6. **Improved Error Messages** (LOW)
**Problem:** Generic error messages made troubleshooting hard.

**Fix Applied:**
```python
except OSError as e:
    print(f"\n[ERROR] Could not bind to port {PORT}. Is another node running on this port?")
    print(f"Details: {e}")
    sys.exit(1)
```

**Impact:** Users immediately know what went wrong.

---

## ⚠️ REMAINING ISSUES (Not Yet Fixed)

### 7. **Empty `replication.py`** (LOW)
**Status:** File exists but is empty.
**Recommendation:** Delete it or add replication logic placeholder.

```bash
rm node/replication.py
```

---

### 8. **Empty `run_nodes.txt`** (LOW)
**Status:** No documentation on how to start the system.
**Recommendation:** Use the new `start_system.py` script instead.

---

### 9. **No Data Persistence** (MEDIUM)
**Problem:** `KeyValueStore` is in-memory only. Data is lost on node restart.
**Solution Option 1 (Simple):**
```python
import json

class KeyValueStore:
    def __init__(self, filepath="store.json"):
        self.filepath = filepath
        self.store = self._load()
    
    def put(self, key, value):
        self.store[key] = value
        self._save()
    
    def _save(self):
        with open(self.filepath, 'w') as f:
            json.dump(self.store, f)
    
    def _load(self):
        try:
            with open(self.filepath, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            return {}
```

---

### 10. **No Logging Framework** (MEDIUM)
**Problem:** Uses `print()` instead of `logging` module. Hard to filter/redirect output.
**Solution:**
```python
import logging

logger = logging.getLogger(__name__)
logger.info(f"Node {PORT} listening on {HOST}:{PORT}")
logger.error(f"Error: {e}")
```

---

### 11. **Heartbeat Quorum Issue** (MEDIUM)
**Problem:** No quorum-based election. A single node can become leader with no consensus.
**Risk:** Works fine locally but unreliable in actual distributed scenarios.
**Solution:** Implement quorum-based leader election (requires more refactoring).

---

## 📝 QUICK START GUIDE

### Step 1: Start the System
```bash
cd "c:\Users\Pritam Gupta\OneDrive - Amrita vishwa vidyapeetham\Distributed_System_key_store"
python start_system.py
```

This opens 4 terminal windows with nodes on ports 5001-5004.

### Step 2: Run Tests (in another terminal)
```bash
python test_system.py
```

### Step 3: Manual Testing
```bash
python client/client.py
```

---

## 📊 Architecture Overview

```
Client
  ↓
[send_request() - tries all nodes until leader responds]
  ↓ (on PUT, waits for "Stored in leader" response)
  ↓
Leader Node (Port 5001/5002/5003/5004)
  ├→ PUT/GET operations
  ├→ Sends HEARTBEAT to followers every 1 second
  ├→ Replicates data to followers
  └→ Exposed to replace if away >4 seconds
  
Follower Nodes
  ├→ Monitor heartbeat from leader
  ├→ Timeout after 4 seconds of silence
  ├→ Trigger election (Bully algorithm)
  ├→ GET requests ok (eventual consistency)
  └→ Cannot accept PUT (redirect to leader)
```

---

## ✨ What's Working Well

✅ **Leader Election** - Bully algorithm correctly picks highest-port node  
✅ **Heartbeat Mechanism** - 1-second interval keeps followers in sync  
✅ **Adaptive Replication** - Replicates to 50% of active followers  
✅ **Error Recovery** - Proper exception handling and cleanup  
✅ **Timeout Handling** - System stays responsive under failures  

---

## 🔧 Configuration (config/config.py)

```python
NODES = [
    ("localhost", 5001),  # 4 nodes configured
    ("localhost", 5002),
    ("localhost", 5003),
    ("localhost", 5004),
]

HEARTBEAT_INTERVAL = 1        # Leader sends heartbeat every 1 sec
LEADER_TIMEOUT = 4            # Follower waits 4 secs before election
REPLICATION_FACTOR = 2         # Replicates to N followers
ADAPTIVE_REPLICATION = True    # Only replicates to active followers
```

---

## 🚀 Next Steps (Optional Improvements)

1. **Persistence** - Implement JSON-based storage (see issue #9 above)
2. **Logging** - Switch to Python `logging` module
3. **Metrics** - Add counters for PUT/GET/election operations
4. **Consistency** - Add versioning for concurrent write handling
5. **Quorum** - Implement majority-based leader election
6. **UI** - Add web dashboard to visualize cluster state

---

## 📞 Testing Checklist

- [ ] Start system with `python start_system.py`
- [ ] Wait 2-3 seconds for initial election
- [ ] Run `python test_system.py` - all 8 tests should pass
- [ ] Run `python client/client.py` - manual tests
- [ ] Kill a node (Ctrl+C), system should re-elect
- [ ] Add back the node with `python node/node_server.py 5001`
- [ ] Data should be replicated to the new node

---

**Last Updated:** April 15, 2026  
**Status:** ✅ Core functionality fixed, system ready for testing
