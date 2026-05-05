# # #  config/config.py

# # # # List of all nodes in the system
# # # NODES = [
# # #     ("localhost", 5001),
# # #     ("localhost", 5002),
# # #     ("localhost", 5003),
# # # ]



# # # # Leader node (initial leader)
# # # LEADER = ("localhost", 5001)

# # # # Heartbeat interval (seconds)
# # # HEARTBEAT_INTERVAL = 3

# # # # Leader timeout (seconds)
# # # LEADER_TIMEOUT = 6




# # # config/config.py

# # NODES = [
# #     ("localhost", 5001),
# #     ("localhost", 5002),
# #     ("localhost", 5003),
# # ]


# # # NODES = [("localhost", 5000 + i) for i in range(1, 101)]

# # CURRENT_LEADER = ["localhost", 5001]

# # HEARTBEAT_INTERVAL = 3
# # LEADER_TIMEOUT = 6

# # # Replication settings
# # REPLICATION_FACTOR = 2
# # ADAPTIVE_REPLICATION = True





# # config/config.py

# NODES = [
#     ("localhost", 5001),
#     ("localhost", 5002),
#     ("localhost", 5003),
#     ("localhost", 5004),
# ]

# # Keep this as a list so it can be updated in memory if needed
# CURRENT_LEADER = ["localhost", 5004]

# # --- STABILITY TWEAKS ---
# # Faster heartbeats (1 second) mean followers know the leader is alive more frequently
# HEARTBEAT_INTERVAL = 1.0

# # Longer timeout (3-5 seconds) gives the system "breathing room" 
# # This prevents accidental elections if a node is just slightly slow
# LEADER_TIMEOUT = 5.0

# # Replication settings
# REPLICATION_FACTOR = 2


# ADAPTIVE_REPLICATION = True




NODES = [
    ("localhost", 5001),
    ("localhost", 5002),
    ("localhost", 5003),
    ("localhost", 5004),
]

# Raft State
RAFT_STATE = {
    "current_term": 0,
    "voted_for": None,
}

HEARTBEAT_INTERVAL = 1.0
LEADER_TIMEOUT = 5.0  # Followers wait this long before starting election
ADAPTIVE_REPLICATION = True

# When True, election majority is computed from currently reachable nodes.
# This allows the cluster to continue with partial availability (for example,
# when 2 out of 4 configured nodes are offline).
DYNAMIC_QUORUM = True