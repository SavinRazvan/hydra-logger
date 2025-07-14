#!/usr/bin/env python3
"""
Log Analysis Demo

This example demonstrates how to read and analyze the log files generated
by the advanced multi-layer logging example. It shows:
- Reading different log formats (JSON, CSV, Plain-text, Syslog, GELF)
- Analyzing log data from multiple layers
- Extracting insights from structured logging
- Comparing data across different formats
"""

import os
import json
import csv
import re
from datetime import datetime
from collections import defaultdict, Counter

def read_json_logs(file_path):
    """Read and parse JSON log files."""
    logs = []
    if os.path.exists(file_path):
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        log_entry = json.loads(line)
                        logs.append(log_entry)
                    except json.JSONDecodeError:
                        continue
    return logs

def read_csv_logs(file_path):
    """Read and parse CSV log files."""
    logs = []
    if os.path.exists(file_path):
        with open(file_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                logs.append(row)
    return logs

def read_plain_text_logs(file_path):
    """Read and parse plain text log files."""
    logs = []
    if os.path.exists(file_path):
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line:
                    logs.append(line)
    return logs

def read_syslog_logs(file_path):
    """Read and parse syslog format log files."""
    logs = []
    if os.path.exists(file_path):
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line:
                    logs.append(line)
    return logs

def read_gelf_logs(file_path):
    """Read and parse GELF format log files."""
    logs = []
    if os.path.exists(file_path):
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        log_entry = json.loads(line)
                        logs.append(log_entry)
                    except json.JSONDecodeError:
                        continue
    return logs

def analyze_frontend_logs():
    """Analyze frontend logs from different formats."""
    print("=== Frontend Logs Analysis ===")
    
    # Read JSON logs
    json_logs = read_json_logs("examples/logs/advanced/frontend.json")
    print(f"JSON logs: {len(json_logs)} entries")
    
    # Read CSV logs
    csv_logs = read_csv_logs("examples/logs/advanced/frontend.csv")
    print(f"CSV logs: {len(csv_logs)} entries")
    
    # Analyze user interactions
    user_actions = []
    for log in json_logs:
        if 'extra' in log:
            extra = log['extra']
            if 'user_id' in extra:
                user_actions.append({
                    'user_id': extra['user_id'],
                    'action': log['message'],
                    'timestamp': log.get('timestamp', '')
                })
    
    print(f"User interactions tracked: {len(user_actions)}")
    
    # Count actions by user
    user_action_counts = Counter(action['user_id'] for action in user_actions)
    print("Actions by user:")
    for user_id, count in user_action_counts.most_common():
        print(f"  User {user_id}: {count} actions")

def analyze_backend_logs():
    """Analyze backend logs."""
    print("\n=== Backend Logs Analysis ===")
    
    # Read backend logs
    backend_logs = read_plain_text_logs("examples/logs/advanced/backend.log")
    print(f"Backend logs: {len(backend_logs)} entries")
    
    # Analyze API calls
    api_calls = []
    for log in backend_logs:
        if "API request received" in log:
            api_calls.append(log)
        elif "External API call" in log:
            api_calls.append(log)
    
    print(f"API calls: {len(api_calls)}")
    
    # Analyze errors
    errors = [log for log in backend_logs if "ERROR" in log]
    print(f"Errors: {len(errors)}")
    
    # Show sample logs
    if backend_logs:
        print("Sample backend logs:")
        for log in backend_logs[:3]:
            print(f"  {log}")

def analyze_database_logs():
    """Analyze database logs."""
    print("\n=== Database Logs Analysis ===")
    
    # Read syslog format logs
    db_logs = read_syslog_logs("examples/logs/advanced/database.syslog")
    print(f"Database logs: {len(db_logs)} entries")
    
    # Analyze query performance
    query_logs = [log for log in db_logs if "Query executed" in log]
    print(f"Database queries: {len(query_logs)}")
    
    # Show sample logs
    if db_logs:
        print("Sample database logs:")
        for log in db_logs[:3]:
            print(f"  {log}")

def analyze_payment_logs():
    """Analyze payment logs."""
    print("\n=== Payment Logs Analysis ===")
    
    # Read JSON logs
    json_logs = read_json_logs("examples/logs/advanced/payment.json")
    print(f"Payment JSON logs: {len(json_logs)} entries")
    
    # Read GELF logs
    gelf_logs = read_gelf_logs("examples/logs/advanced/payment.gelf")
    print(f"Payment GELF logs: {len(gelf_logs)} entries")
    
    # Analyze payment status
    payment_statuses = []
    for log in json_logs:
        if 'extra' in log:
            extra = log['extra']
            if 'status' in extra:
                payment_statuses.append(extra['status'])
    
    status_counts = Counter(payment_statuses)
    print("Payment statuses:")
    for status, count in status_counts.items():
        print(f"  {status}: {count}")
    
    # Analyze amounts
    amounts = []
    for log in json_logs:
        if 'extra' in log:
            extra = log['extra']
            if 'amount' in extra:
                amounts.append(float(extra['amount']))
    
    if amounts:
        print(f"Payment amounts - Total: ${sum(amounts):.2f}, Average: ${sum(amounts)/len(amounts):.2f}")

def analyze_security_logs():
    """Analyze security logs."""
    print("\n=== Security Logs Analysis ===")
    
    # Read JSON logs
    security_logs = read_json_logs("examples/logs/advanced/security.json")
    print(f"Security logs: {len(security_logs)} entries")
    
    # Analyze login attempts
    login_attempts = []
    failed_logins = []
    
    for log in security_logs:
        if 'extra' in log:
            extra = log['extra']
            if 'success' in extra:
                if extra['success']:
                    login_attempts.append(extra)
                else:
                    failed_logins.append(extra)
    
    print(f"Successful logins: {len(login_attempts)}")
    print(f"Failed logins: {len(failed_logins)}")
    
    # Analyze IP addresses
    ip_addresses = []
    for log in security_logs:
        if 'extra' in log:
            extra = log['extra']
            if 'ip' in extra:
                ip_addresses.append(extra['ip'])
    
    ip_counts = Counter(ip_addresses)
    print("Login attempts by IP:")
    for ip, count in ip_counts.most_common():
        print(f"  {ip}: {count} attempts")

def analyze_performance_logs():
    """Analyze performance logs."""
    print("\n=== Performance Logs Analysis ===")
    
    # Read CSV logs
    csv_logs = read_csv_logs("examples/logs/advanced/performance.csv")
    print(f"Performance CSV logs: {len(csv_logs)} entries")
    
    # Read JSON logs
    json_logs = read_json_logs("examples/logs/advanced/performance.json")
    print(f"Performance JSON logs: {len(json_logs)} entries")
    
    # Analyze memory usage
    memory_values = []
    for log in csv_logs:
        if 'memory_mb' in log:
            try:
                memory_values.append(float(log['memory_mb']))
            except (ValueError, KeyError):
                continue
    
    if memory_values:
        print(f"Memory usage - Average: {sum(memory_values)/len(memory_values):.1f} MB")
        print(f"Memory usage - Max: {max(memory_values):.1f} MB")
    
    # Analyze response times
    response_times = []
    for log in json_logs:
        if 'extra' in log:
            extra = log['extra']
            if 'avg_time' in extra:
                try:
                    response_times.append(float(extra['avg_time']))
                except (ValueError, KeyError):
                    continue
    
    if response_times:
        print(f"Response times - Average: {sum(response_times)/len(response_times):.3f}s")

def analyze_combined_logs():
    """Analyze the combined log file with multiple layers."""
    print("\n=== Combined Logs Analysis ===")
    
    # Read combined logs
    combined_logs = read_plain_text_logs("examples/logs/advanced/combined.log")
    print(f"Combined logs: {len(combined_logs)} entries")
    
    # Analyze by layer
    layer_counts = defaultdict(int)
    for log in combined_logs:
        # Extract layer from log message
        if "FRONTEND" in log:
            layer_counts["FRONTEND"] += 1
        elif "BACKEND" in log:
            layer_counts["BACKEND"] += 1
        elif "DATABASE" in log:
            layer_counts["DATABASE"] += 1
        elif "SECURITY" in log:
            layer_counts["SECURITY"] += 1
    
    print("Logs by layer in combined file:")
    for layer, count in layer_counts.items():
        print(f"  {layer}: {count} entries")
    
    # Show sample combined logs
    if combined_logs:
        print("Sample combined logs:")
        for log in combined_logs[:5]:
            print(f"  {log}")

def compare_formats():
    """Compare different log formats for the same data."""
    print("\n=== Format Comparison ===")
    
    # Compare frontend logs in different formats
    json_logs = read_json_logs("examples/logs/advanced/frontend.json")
    csv_logs = read_csv_logs("examples/logs/advanced/frontend.csv")
    
    print(f"Frontend logs - JSON: {len(json_logs)} entries, CSV: {len(csv_logs)} entries")
    
    # Show how the same data looks in different formats
    if json_logs and csv_logs:
        print("\nSame data in different formats:")
        print("JSON format (first entry):")
        print(f"  {json.dumps(json_logs[0], indent=2)}")
        
        print("\nCSV format (first entry):")
        if csv_logs:
            for key, value in csv_logs[0].items():
                print(f"  {key}: {value}")

def demonstrate_log_analysis():
    """Demonstrate comprehensive log analysis."""
    
    print("Log Analysis Demo")
    print("=" * 60)
    print("This example demonstrates how to read and analyze log files")
    print("generated by the advanced multi-layer logging example.")
    print()
    
    # Check if log files exist
    log_dir = "examples/logs/advanced"
    if not os.path.exists(log_dir):
        print("❌ Log files not found!")
        print("Please run the advanced multi-layer logging example first:")
        print("  python examples/10_advanced_multi_layer/01_advanced_multi_layer_demo.py")
        return
    
    # Analyze logs from different layers and formats
    analyze_frontend_logs()
    analyze_backend_logs()
    analyze_database_logs()
    analyze_payment_logs()
    analyze_security_logs()
    analyze_performance_logs()
    analyze_combined_logs()
    compare_formats()
    
    print("\n" + "=" * 60)
    print("Log analysis demo completed!")
    print("\nKey insights demonstrated:")
    print("  ✅ Reading different log formats (JSON, CSV, Plain-text, Syslog, GELF)")
    print("  ✅ Extracting structured data from logs")
    print("  ✅ Analyzing patterns across different layers")
    print("  ✅ Comparing data in different formats")
    print("  ✅ Identifying trends and anomalies")
    print("  ✅ Cross-referencing data from multiple sources")

if __name__ == "__main__":
    demonstrate_log_analysis() 