#!/usr/bin/env python3
"""
16 - Compliance Auditing

This example demonstrates compliance and auditing logging with Hydra-Logger.
Shows how to log for regulatory compliance and audit trails.
"""

from hydra_logger import HydraLogger
from hydra_logger.config import LoggingConfig, LogLayer, LogDestination
import time
import uuid
import random

def generate_audit_id():
    """Generate a unique audit ID."""
    return str(uuid.uuid4())

def simulate_compliance_check(logger, check_type, user_id, resource):
    """Simulate a compliance check."""
    audit_id = generate_audit_id()
    
    logger.info("COMPLIANCE", f"{check_type} compliance check",
                audit_id=audit_id,
                check_type=check_type,
                user_id=user_id,
                resource=resource,
                timestamp=time.time(),
                result="pass" if random.random() > 0.1 else "fail")
    
    return audit_id

def main():
    """Demonstrate compliance and auditing logging."""
    
    print("📋 Compliance Auditing Demo")
    print("=" * 40)
    
    # Create compliance configuration
    config = LoggingConfig(
        layers={
            "AUDIT": LogLayer(
                level="INFO",
                destinations=[
                    LogDestination(
                        type="file",
                        path="logs/compliance/audit_trail.log",
                        format="json"
                    )
                ]
            ),
            "COMPLIANCE": LogLayer(
                level="INFO",
                destinations=[
                    LogDestination(
                        type="file",
                        path="logs/compliance/compliance.log",
                        format="text"
                    )
                ]
            ),
            "GDPR": LogLayer(
                level="INFO",
                destinations=[
                    LogDestination(
                        type="file",
                        path="logs/compliance/gdpr.log",
                        format="json"
                    )
                ]
            ),
            "SOX": LogLayer(
                level="INFO",
                destinations=[
                    LogDestination(
                        type="file",
                        path="logs/compliance/sox.log",
                        format="text"
                    )
                ]
            ),
            "HIPAA": LogLayer(
                level="INFO",
                destinations=[
                    LogDestination(
                        type="file",
                        path="logs/compliance/hipaa.log",
                        format="json"
                    )
                ]
            )
        }
    )
    
    # Initialize logger
    logger = HydraLogger(config)
    
    print("\n🔍 GDPR Compliance")
    print("-" * 20)
    
    # Simulate GDPR compliance
    gdpr_events = [
        ("data_access", "user_123", "customer_data"),
        ("data_export", "user_456", "personal_data"),
        ("data_deletion", "user_789", "user_profile"),
        ("consent_given", "user_101", "marketing_emails"),
        ("consent_withdrawn", "user_202", "analytics_tracking")
    ]
    
    for event_type, user_id, data_type in gdpr_events:
        audit_id = generate_audit_id()
        
        logger.info("GDPR", f"GDPR {event_type} event",
                    audit_id=audit_id,
                    event_type=event_type,
                    user_id=user_id,
                    data_type=data_type,
                    timestamp=time.time(),
                    legal_basis="consent" if "consent" in event_type else "legitimate_interest",
                    data_controller="company_name",
                    data_processor="service_provider")
    
    print("\n📊 SOX Compliance")
    print("-" * 20)
    
    # Simulate SOX compliance
    sox_events = [
        ("financial_transaction", "txn_001", 10000.00),
        ("access_control", "user_admin", "financial_system"),
        ("change_management", "config_change", "accounting_software"),
        ("data_backup", "backup_001", "financial_records"),
        ("security_incident", "incident_001", "unauthorized_access")
    ]
    
    for event_type, event_id, value in sox_events:
        audit_id = generate_audit_id()
        
        logger.info("SOX", f"SOX {event_type} event",
                    audit_id=audit_id,
                    event_type=event_type,
                    event_id=event_id,
                    value=value if isinstance(value, (int, float)) else None,
                    timestamp=time.time(),
                    approver="manager_001",
                    reviewer="auditor_001")
    
    print("\n🏥 HIPAA Compliance")
    print("-" * 20)
    
    # Simulate HIPAA compliance
    hipaa_events = [
        ("patient_access", "patient_001", "medical_records"),
        ("data_breach", "breach_001", "patient_data"),
        ("access_log", "doctor_001", "patient_002"),
        ("consent_form", "patient_003", "treatment_consent"),
        ("data_disclosure", "hospital_001", "insurance_company")
    ]
    
    for event_type, subject_id, data_type in hipaa_events:
        audit_id = generate_audit_id()
        
        logger.info("HIPAA", f"HIPAA {event_type} event",
                    audit_id=audit_id,
                    event_type=event_type,
                    subject_id=subject_id,
                    data_type=data_type,
                    timestamp=time.time(),
                    covered_entity="hospital_name",
                    business_associate="service_provider",
                    purpose="treatment" if "treatment" in event_type else "payment" if "insurance" in event_type else "operations")
    
    print("\n🔐 Access Control Auditing")
    print("-" * 25)
    
    # Simulate access control auditing
    access_events = [
        ("login", "user_001", "web_application"),
        ("logout", "user_001", "web_application"),
        ("permission_granted", "user_002", "admin_panel"),
        ("permission_revoked", "user_003", "sensitive_data"),
        ("failed_login", "unknown_user", "web_application")
    ]
    
    for event_type, user_id, resource in access_events:
        audit_id = generate_audit_id()
        
        logger.info("AUDIT", f"Access control {event_type}",
                    audit_id=audit_id,
                    event_type=event_type,
                    user_id=user_id,
                    resource=resource,
                    ip_address="192.168.1.100",
                    user_agent="Mozilla/5.0",
                    timestamp=time.time(),
                    session_id="session_123" if "login" in event_type else None)
    
    print("\n📝 Data Lifecycle Auditing")
    print("-" * 25)
    
    # Simulate data lifecycle auditing
    lifecycle_events = [
        ("data_created", "record_001", "customer_profile"),
        ("data_modified", "record_001", "customer_profile"),
        ("data_archived", "record_002", "old_transactions"),
        ("data_restored", "record_003", "archived_data"),
        ("data_deleted", "record_004", "expired_data")
    ]
    
    for event_type, record_id, data_type in lifecycle_events:
        audit_id = generate_audit_id()
        
        logger.info("AUDIT", f"Data lifecycle {event_type}",
                    audit_id=audit_id,
                    event_type=event_type,
                    record_id=record_id,
                    data_type=data_type,
                    timestamp=time.time(),
                    user_id="system_user",
                    reason="automated_process" if "archived" in event_type else "user_request")
    
    print("\n⚖️ Regulatory Reporting")
    print("-" * 25)
    
    # Simulate regulatory reporting
    regulatory_reports = [
        ("quarterly_report", "Q1_2025", "financial_data"),
        ("annual_report", "2024", "compliance_summary"),
        ("incident_report", "incident_001", "security_breach"),
        ("audit_report", "audit_001", "internal_audit"),
        ("compliance_report", "compliance_001", "gdpr_compliance")
    ]
    
    for report_type, report_id, data_scope in regulatory_reports:
        audit_id = generate_audit_id()
        
        logger.info("COMPLIANCE", f"Regulatory report generated",
                    audit_id=audit_id,
                    report_type=report_type,
                    report_id=report_id,
                    data_scope=data_scope,
                    timestamp=time.time(),
                    generated_by="compliance_system",
                    reviewed_by="compliance_officer",
                    status="approved")
    
    print("\n🔍 Compliance Monitoring")
    print("-" * 25)
    
    # Simulate compliance monitoring
    compliance_checks = [
        ("data_retention", "customer_data", 7),
        ("access_controls", "sensitive_data", 100),
        ("encryption_status", "personal_data", 95),
        ("backup_status", "critical_data", 99.9),
        ("audit_log_retention", "audit_data", 7)
    ]
    
    for check_type, data_category, compliance_rate in compliance_checks:
        audit_id = generate_audit_id()
        
        logger.info("COMPLIANCE", f"Compliance check completed",
                    audit_id=audit_id,
                    check_type=check_type,
                    data_category=data_category,
                    compliance_rate=f"{compliance_rate}%",
                    timestamp=time.time(),
                    status="pass" if compliance_rate >= 95 else "fail",
                    action_required="none" if compliance_rate >= 95 else "remediation")
    
    print("\n📊 Audit Trail Summary")
    print("-" * 25)
    
    # Generate audit summary
    total_events = len(gdpr_events) + len(sox_events) + len(hipaa_events) + len(access_events) + len(lifecycle_events) + len(regulatory_reports) + len(compliance_checks)
    
    logger.info("AUDIT", "Audit trail summary",
                total_events=total_events,
                gdpr_events=len(gdpr_events),
                sox_events=len(sox_events),
                hipaa_events=len(hipaa_events),
                access_events=len(access_events),
                lifecycle_events=len(lifecycle_events),
                regulatory_reports=len(regulatory_reports),
                compliance_checks=len(compliance_checks),
                timestamp=time.time(),
                retention_period="7_years",
                encryption_status="enabled")
    
    print("\n✅ Compliance auditing demo completed!")
    print("📝 Check the logs/compliance/ directory for audit logs")
    
    # Show compliance summary
    print("\n📊 Compliance Summary:")
    print("-" * 25)
    print(f"• GDPR events: {len(gdpr_events)}")
    print(f"• SOX events: {len(sox_events)}")
    print(f"• HIPAA events: {len(hipaa_events)}")
    print(f"• Access events: {len(access_events)}")
    print(f"• Lifecycle events: {len(lifecycle_events)}")
    print(f"• Regulatory reports: {len(regulatory_reports)}")
    print(f"• Compliance checks: {len(compliance_checks)}")
    print(f"• Total audit events: {total_events}")

if __name__ == "__main__":
    main() 