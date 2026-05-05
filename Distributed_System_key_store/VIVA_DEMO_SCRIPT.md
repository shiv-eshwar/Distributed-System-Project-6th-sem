# The "Wow Factor" Demo Script

This is your step-by-step script for your live presentation. Follow this sequence exactly to demonstrate the power, resilience, and fault-tolerance of your distributed system.

## Preparation Before the Professor Watches
1. Have your VS Code or terminal open.
2. Make sure you don't have any dangling nodes running in the background.
3. Have your `PROJECT_COMPREHENSIVE_GUIDE.md` open on another screen or printed out just in case.

---

## Phase 1: The Launch (The Setup)

**What to do:**
1. Open a terminal in your project directory.
2. Run the cluster launcher:
   ```bash
   ./start_cluster.sh
   ```
3. **What to say:**
   > *"Professor, I've built an automated bash script that dynamically updates the configuration and launches 4 separate nodes, each in its own terminal. Let's wait a few seconds for them to initialize and hold their first election to elect a Leader."*

4. **Point out:** Look at the 4 terminals. Point out the one that says `RESULT: I (... ) am the Leader for Term 1`. Tell the professor which port is the current leader (e.g., Node 5004).

---

## Phase 2: The Happy Path (Data Storage & Replication)

**What to do:**
1. Open a **5th terminal window**.
2. Start the interactive client:
   ```bash
   python3 client/client.py
   ```
3. Type `PUT`, then key: `secret_code`, value: `12345`.
4. **What to say:**
   > *"Now I'm acting as a client. I just sent a PUT request. My client script is smart enough to find the Leader. If you look at the Leader's terminal, it received the data, and if you look at the Follower terminals, you'll see they received a `REPLICATE` command. The data is now safely copied across the cluster."*
5. Type `GET`, then key: `secret_code` to prove it works.

---

## Phase 3: Chaos Engineering (Killing the Leader)

This is the most impressive part. You will simulate a catastrophic server crash.

**What to do:**
1. Identify which terminal window belongs to the **Leader**.
2. Click on that terminal window.
3. Press **`Ctrl + C`** on your keyboard to instantly kill the server. The terminal window will show it has exited.
4. **What to say:**
   > *"Now for the failover test. I have just completely killed the Leader node. In a traditional database, the system would now be down. Let's watch the followers."*

---

## Phase 4: The Recovery (Auto-Election)

**What to do:**
1. Keep your hands off the keyboard and let the professor watch the remaining 3 follower terminals.
2. After about 3 to 5 seconds, one of the followers will print: `[⏱️ TIMEOUT] Node XXXX detected leader timeout!`
3. Then you will see: `[RAFT ELECTION] Starting Term 2`
4. Finally, one of the surviving nodes will say: `[🎉 ELECTED] Node XXXX WON the election!`

5. **What to say:**
   > *"Because the Leader stopped sending heartbeats, the followers' randomized timeout timers expired. They automatically initiated a Raft-based election for Term 2, gathered a majority quorum of votes, and we now have a brand new Leader, completely automatically."*

---

## Phase 5: Proof of Resilience

**What to do:**
1. Go back to your Client terminal (the 5th window).
2. Type `GET`, then key: `secret_code`.
   - It will return `12345`.
3. Type `PUT`, then key: `new_leader`, value: `works`.
4. **What to say:**
   > *"To prove the system is fully functional, I'll retrieve the data we stored earlier. As you can see, no data was lost because of the replication. Furthermore, the client can still write new data, proving the new Leader is actively accepting writes and replicating to the remaining followers."*

---

## Phase 6: The Revival (Bringing the dead node back)

**What to do:**
1. Go to the terminal window of the node you killed (it should say "Press Enter to close"). Press Enter to close it.
2. Open a new terminal window.
3. Manually restart that specific node. (For example, if you killed 5004, run:)
   ```bash
   python3 node/node_server.py 5004
   ```
4. **What to say:**
   > *"If the crashed server is repaired and comes back online, it doesn't cause a conflict. It recognizes there is an active leader with a higher term, and peacefully joins the cluster as a Follower, ready to receive new replicated data."*

---

## Bonus Tips for the Viva

- **If asked about "How does the client find the leader?":** Tell them, "If the client hits a follower with a PUT request, the follower replies 'Error: Not the leader'. The client catches this error and loops through the other nodes until it finds the actual leader."
- **If asked "What happens if a network partition splits 4 nodes into 2 and 2?":** Confidently answer: "Because my system requires a strict majority `(N/2) + 1` to elect a leader, a partition of 2 nodes will only get 2 votes, which is not a majority of 4. Neither side will elect a leader. This prioritizes Consistency over Availability (preventing Split Brain), though I have a dynamic quorum flag that can be toggled."
- **Take your time:** When you kill the leader, don't rush. The 3-5 second pause where nothing happens builds suspense before the election triggers. Let the professor see the timeout happen naturally!
