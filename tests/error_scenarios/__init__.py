"""
Error scenario tests package for Alphintra no-code to AI-ML integration.

This package contains comprehensive error scenario tests covering:
- Network failures and service unavailability 
- Malformed data handling and validation
- Authentication and authorization edge cases
- Database transaction rollbacks and recovery
- Timeout scenarios and graceful degradation

Test Categories:
1. test_network_failures.py - Connection errors, timeouts, service unavailability
2. test_malformed_data_handling.py - Invalid workflow definitions, corrupted data
3. test_authentication_authorization.py - JWT issues, permission violations, security attacks
4. test_database_transaction_rollbacks.py - Transaction failures, rollback scenarios
5. test_timeout_scenarios.py - Various timeout conditions and recovery mechanisms

Usage:
    pytest tests/error_scenarios/ -v
    pytest tests/error_scenarios/test_network_failures.py -v
"""

__version__ = "1.0.0"
__author__ = "Alphintra Development Team"