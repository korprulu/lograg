#!/usr/bin/env python3
"""
Sample log data generator for testing LogRAG
"""
import asyncio
import random
from datetime import datetime, timedelta
from pathlib import Path
import sys

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from lograg.core.similarity_engine import SimilarityEngine


# Sample log templates
LOG_TEMPLATES = [
    # Database errors
    "Database connection pool exhausted, unable to serve request",
    "MySQL connection timeout after 30 seconds",
    "PostgreSQL deadlock detected, transaction rolled back",
    "Redis cache miss for key: user_session_{user_id}",
    "Database query took {duration}ms to execute: SELECT * FROM users",
    
    # HTTP errors
    "HTTP 500 Internal Server Error in endpoint /api/users/{user_id}",
    "HTTP 404 Not Found: Resource /api/posts/{post_id} does not exist",
    "HTTP 403 Forbidden: User {user_id} lacks permission for action",
    "Rate limit exceeded for IP {ip_address}: {requests} requests in 1 minute",
    
    # Authentication errors
    "Login failed for user {username}: invalid credentials",
    "JWT token expired for user {user_id}",
    "OAuth authentication failed: invalid client_id",
    "Session timeout for user {user_id} after {duration} minutes",
    
    # System events
    "Service started successfully on port {port}",
    "Scheduled job 'data_backup' completed in {duration} seconds",
    "Memory usage: {memory_percent}% of {total_memory}GB",
    "CPU usage spike detected: {cpu_percent}% for {duration} seconds",
    
    # Application errors
    "NullPointerException in UserController.getProfile() line 45",
    "FileNotFoundException: Config file not found at /etc/app/config.yml",
    "OutOfMemoryError: Java heap space exhausted",
    "ValidationException: Email format invalid for user registration",
    
    # Network errors
    "Connection refused to external API at https://api.example.com",
    "DNS resolution failed for hostname: {hostname}",
    "SSL handshake failed with peer {peer_address}",
    "Network timeout connecting to service {service_name}",
]

LOG_LEVELS = ["DEBUG", "INFO", "WARN", "ERROR"]
SOURCES = ["user-service", "auth-service", "database", "api-gateway", "cache-service", "scheduler"]


def generate_sample_log():
    """Generate a single sample log entry"""
    template = random.choice(LOG_TEMPLATES)
    level = random.choice(LOG_LEVELS)
    source = random.choice(SOURCES)
    
    # Generate random values for template placeholders
    values = {
        "user_id": random.randint(1000, 9999),
        "post_id": random.randint(100, 999),
        "username": f"user_{random.randint(1, 100)}",
        "ip_address": f"192.168.{random.randint(1, 255)}.{random.randint(1, 255)}",
        "requests": random.randint(50, 200),
        "duration": random.randint(100, 5000),
        "port": random.choice([8080, 3000, 5432, 6379]),
        "memory_percent": random.randint(60, 95),
        "total_memory": random.choice([8, 16, 32]),
        "cpu_percent": random.randint(70, 99),
        "hostname": f"service-{random.randint(1, 10)}.example.com",
        "peer_address": f"10.0.{random.randint(1, 255)}.{random.randint(1, 255)}",
        "service_name": random.choice(SOURCES),
    }
    
    try:
        content = template.format(**values)
    except KeyError:
        content = template  # Use template as-is if formatting fails
    
    # Generate timestamp (last 24 hours)
    now = datetime.now()
    timestamp = now - timedelta(
        hours=random.randint(0, 24),
        minutes=random.randint(0, 59),
        seconds=random.randint(0, 59)
    )
    
    return {
        "content": content,
        "timestamp": timestamp.isoformat(),
        "level": level,
        "source": source
    }


async def populate_sample_data(num_logs: int = 100):
    """Populate the vector database with sample log data"""
    print(f"Generating {num_logs} sample log entries...")
    
    engine = SimilarityEngine()
    
    # Generate logs in batches
    batch_size = 20
    for i in range(0, num_logs, batch_size):
        batch_logs = []
        batch_end = min(i + batch_size, num_logs)
        
        for j in range(i, batch_end):
            log_data = generate_sample_log()
            batch_logs.append(log_data)
        
        print(f"Adding batch {i//batch_size + 1}: logs {i+1}-{batch_end}")
        result = await engine.batch_add_logs(batch_logs)
        
        if result["success"]:
            print(f"  Successfully added {result['successful']}/{result['total_processed']} logs")
        else:
            print(f"  Error: {result.get('message', 'Unknown error')}")
    
    print("\nSample data population complete!")
    
    # Show statistics
    stats_result = await engine.get_log_statistics()
    if stats_result["success"]:
        print(f"Total logs in database: {stats_result['total_logs']}")


async def demo_search():
    """Demonstrate search functionality"""
    print("\n" + "="*50)
    print("SEARCH DEMONSTRATION")
    print("="*50)
    
    engine = SimilarityEngine()
    
    # Demo searches
    demo_queries = [
        "database connection failed",
        "HTTP 500 error",
        "user authentication",
        "memory usage high",
        "timeout",
    ]
    
    for query in demo_queries:
        print(f"\nSearching for: '{query}'")
        print("-" * 40)
        
        result = await engine.search_similar_logs(
            query=query,
            limit=3,
            threshold=0.5
        )
        
        if result["success"] and result["results"]:
            for i, log in enumerate(result["results"], 1):
                print(f"{i}. [{log['similarity']:.3f}] {log['content'][:80]}...")
                print(f"   Level: {log['level']} | Source: {log['source']}")
        else:
            print("No similar logs found")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="LogRAG sample data generator")
    parser.add_argument("--populate", "-p", type=int, default=100,
                       help="Number of sample logs to generate (default: 100)")
    parser.add_argument("--demo", "-d", action="store_true",
                       help="Run search demonstration")
    parser.add_argument("--all", "-a", action="store_true",
                       help="Populate data and run demo")
    
    args = parser.parse_args()
    
    if args.all:
        asyncio.run(populate_sample_data(args.populate))
        asyncio.run(demo_search())
    elif args.demo:
        asyncio.run(demo_search())
    else:
        asyncio.run(populate_sample_data(args.populate))
