#!/usr/bin/env python3
"""
18 - Distributed Systems

This example demonstrates distributed systems logging with Hydra-Logger.
Shows how to handle logging across multiple nodes and services.
"""

from hydra_logger import HydraLogger
from hydra_logger.config import LoggingConfig, LogLayer, LogDestination
import time
import uuid
import random
import threading

def generate_node_id():
    """Generate a unique node ID."""
    return f"node_{random.randint(1000, 9999)}"

def simulate_distributed_operation(logger, operation_name, nodes):
    """Simulate a distributed operation."""
    operation_id = str(uuid.uuid4())
    
    logger.info("DISTRIBUTED", f"Distributed operation started",
                operation_id=operation_id,
                operation_name=operation_name,
                participating_nodes=len(nodes),
                nodes=nodes)
    
    # Simulate operation across nodes
    for node in nodes:
        start_time = time.time()
        processing_time = random.uniform(0.1, 0.5)
        time.sleep(processing_time)
        
        logger.info("NODE", f"Node {node} completed operation",
                   operation_id=operation_id,
                   node_id=node,
                   processing_time=f"{processing_time:.3f}s",
                   status="success")
    
    logger.info("DISTRIBUTED", f"Distributed operation completed",
                operation_id=operation_id,
                operation_name=operation_name,
                total_nodes=len(nodes),
                status="success")

def main():
    """Demonstrate distributed systems logging."""
    
    print("🌐 Distributed Systems Demo")
    print("=" * 40)
    
    # Create distributed systems configuration
    config = LoggingConfig(
        layers={
            "DISTRIBUTED": LogLayer(
                level="INFO",
                destinations=[
                    LogDestination(
                        type="file",
                        path="logs/distributed/operations.log",
                        format="json"
                    )
                ]
            ),
            "NODE": LogLayer(
                level="INFO",
                destinations=[
                    LogDestination(
                        type="file",
                        path="logs/distributed/nodes.log",
                        format="text"
                    )
                ]
            ),
            "CLUSTER": LogLayer(
                level="INFO",
                destinations=[
                    LogDestination(
                        type="file",
                        path="logs/distributed/cluster.log",
                        format="json"
                    )
                ]
            ),
            "SYNC": LogLayer(
                level="DEBUG",
                destinations=[
                    LogDestination(
                        type="file",
                        path="logs/distributed/sync.log",
                        format="text"
                    )
                ]
            ),
            "CONSENSUS": LogLayer(
                level="INFO",
                destinations=[
                    LogDestination(
                        type="file",
                        path="logs/distributed/consensus.log",
                        format="json"
                    )
                ]
            )
        }
    )
    
    # Initialize logger
    logger = HydraLogger(config)
    
    print("\n🏗️ Cluster Formation")
    print("-" * 20)
    
    # Simulate cluster formation
    nodes = [generate_node_id() for _ in range(5)]
    cluster_id = str(uuid.uuid4())
    
    logger.info("CLUSTER", "Cluster formation started",
                cluster_id=cluster_id,
                total_nodes=len(nodes),
                nodes=nodes)
    
    for i, node in enumerate(nodes):
        logger.info("NODE", f"Node {node} joining cluster",
                   cluster_id=cluster_id,
                   node_id=node,
                   node_index=i,
                   timestamp=time.time())
    
    logger.info("CLUSTER", "Cluster formation completed",
                cluster_id=cluster_id,
                active_nodes=len(nodes),
                status="healthy")
    
    print("\n🔄 Distributed Operations")
    print("-" * 25)
    
    # Simulate distributed operations
    operations = [
        ("data_replication", nodes[:3]),
        ("load_balancing", nodes),
        ("consensus_voting", nodes),
        ("distributed_computation", nodes[:4]),
        ("fault_tolerance", nodes)
    ]
    
    for operation_name, participating_nodes in operations:
        simulate_distributed_operation(logger, operation_name, participating_nodes)
    
    print("\n⚖️ Load Balancing")
    print("-" * 20)
    
    # Simulate load balancing
    for i in range(10):
        request_id = str(uuid.uuid4())
        selected_node = random.choice(nodes)
        
        logger.info("NODE", f"Request {i+1} routed to node",
                   request_id=request_id,
                   node_id=selected_node,
                   load_factor=random.uniform(0.1, 0.9),
                   response_time=random.uniform(10, 100))
    
    print("\n🤝 Consensus Protocol")
    print("-" * 25)
    
    # Simulate consensus protocol
    consensus_rounds = 3
    for round_num in range(consensus_rounds):
        round_id = str(uuid.uuid4())
        
        logger.info("CONSENSUS", f"Consensus round {round_num + 1} started",
                    round_id=round_id,
                    round_number=round_num + 1,
                    participating_nodes=len(nodes))
        
        # Simulate voting
        votes = {}
        for node in nodes:
            vote = random.choice(["agree", "disagree"])
            votes[node] = vote
            
            logger.debug("SYNC", f"Node {node} voted",
                        round_id=round_id,
                        node_id=node,
                        vote=vote,
                        timestamp=time.time())
        
        # Determine consensus
        agree_count = sum(1 for vote in votes.values() if vote == "agree")
        consensus_reached = agree_count > len(nodes) / 2
        
        logger.info("CONSENSUS", f"Consensus round {round_num + 1} completed",
                    round_id=round_id,
                    agree_votes=agree_count,
                    total_votes=len(nodes),
                    consensus_reached=consensus_reached,
                    decision="approved" if consensus_reached else "rejected")
    
    print("\n🔄 Data Synchronization")
    print("-" * 25)
    
    # Simulate data synchronization
    sync_operations = [
        ("database_sync", "master", "slave"),
        ("cache_invalidation", "primary", "secondary"),
        ("config_sync", "leader", "follower"),
        ("state_replication", "active", "standby")
    ]
    
    for sync_type, source, target in sync_operations:
        sync_id = str(uuid.uuid4())
        
        logger.info("SYNC", f"{sync_type} started",
                    sync_id=sync_id,
                    sync_type=sync_type,
                    source=source,
                    target=target,
                    timestamp=time.time())
        
        # Simulate sync process
        sync_time = random.uniform(0.5, 2.0)
        time.sleep(sync_time)
        
        logger.info("SYNC", f"{sync_type} completed",
                    sync_id=sync_id,
                    sync_type=sync_type,
                    duration=f"{sync_time:.3f}s",
                    status="success")
    
    print("\n🛡️ Fault Tolerance")
    print("-" * 20)
    
    # Simulate fault tolerance scenarios
    fault_scenarios = [
        ("node_failure", "node_1234"),
        ("network_partition", "node_5678"),
        ("data_corruption", "node_9012"),
        ("service_degradation", "node_3456")
    ]
    
    for scenario, affected_node in fault_scenarios:
        fault_id = str(uuid.uuid4())
        
        logger.warning("NODE", f"Fault detected: {scenario}",
                      fault_id=fault_id,
                      scenario=scenario,
                      affected_node=affected_node,
                      timestamp=time.time())
        
        # Simulate recovery
        recovery_time = random.uniform(1.0, 5.0)
        time.sleep(recovery_time)
        
        logger.info("NODE", f"Recovery completed: {scenario}",
                   fault_id=fault_id,
                   scenario=scenario,
                   affected_node=affected_node,
                   recovery_time=f"{recovery_time:.3f}s",
                   status="recovered")
    
    print("\n📊 Cluster Monitoring")
    print("-" * 25)
    
    # Simulate cluster monitoring
    for node in nodes:
        node_metrics = {
            "cpu_usage": random.uniform(20, 80),
            "memory_usage": random.uniform(30, 90),
            "disk_usage": random.uniform(40, 95),
            "network_io": random.uniform(10, 100),
            "active_connections": random.randint(10, 100)
        }
        
        logger.info("NODE", f"Node {node} metrics",
                   node_id=node,
                   cpu_usage=f"{node_metrics['cpu_usage']:.1f}%",
                   memory_usage=f"{node_metrics['memory_usage']:.1f}%",
                   disk_usage=f"{node_metrics['disk_usage']:.1f}%",
                   network_io=f"{node_metrics['network_io']:.1f} MB/s",
                   active_connections=node_metrics['active_connections'])
    
    print("\n🔍 Service Discovery")
    print("-" * 20)
    
    # Simulate service discovery
    services = [
        ("api_gateway", "node_1000", 8080),
        ("database", "node_2000", 5432),
        ("cache", "node_3000", 6379),
        ("message_queue", "node_4000", 5672),
        ("monitoring", "node_5000", 9090)
    ]
    
    for service_name, node_id, port in services:
        logger.info("CLUSTER", f"Service {service_name} discovered",
                   service_name=service_name,
                   node_id=node_id,
                   port=port,
                   health_status="healthy",
                   load_factor=random.uniform(0.1, 0.9))
    
    print("\n🔄 Distributed Transactions")
    print("-" * 30)
    
    # Simulate distributed transactions
    for i in range(3):
        transaction_id = str(uuid.uuid4())
        participating_nodes = random.sample(nodes, 3)
        
        logger.info("DISTRIBUTED", f"Distributed transaction {i+1} started",
                    transaction_id=transaction_id,
                    participating_nodes=participating_nodes,
                    phase="prepare")
        
        # Simulate two-phase commit
        for node in participating_nodes:
            logger.debug("SYNC", f"Node {node} prepared transaction",
                        transaction_id=transaction_id,
                        node_id=node,
                        phase="prepare",
                        status="ready")
        
        logger.info("DISTRIBUTED", f"Distributed transaction {i+1} committed",
                    transaction_id=transaction_id,
                    participating_nodes=participating_nodes,
                    phase="commit",
                    status="committed")
    
    print("\n✅ Distributed systems demo completed!")
    print("📝 Check the logs/distributed/ directory for distributed logs")
    
    # Show distributed systems summary
    print("\n📊 Distributed Systems Summary:")
    print("-" * 35)
    print(f"• Cluster nodes: {len(nodes)}")
    print(f"• Distributed operations: {len(operations)}")
    print(f"• Consensus rounds: {consensus_rounds}")
    print(f"• Sync operations: {len(sync_operations)}")
    print(f"• Fault scenarios: {len(fault_scenarios)}")
    print(f"• Services discovered: {len(services)}")
    print(f"• Distributed transactions: 3")

if __name__ == "__main__":
    main() 