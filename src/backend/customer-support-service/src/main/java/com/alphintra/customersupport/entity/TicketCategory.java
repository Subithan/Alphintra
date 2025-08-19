package com.alphintra.customersupport.entity;

/**
 * Enumeration representing different categories of support tickets.
 */
public enum TicketCategory {
    TECHNICAL,              // Technical issues with platform
    STRATEGY_DEVELOPMENT,   // Help with strategy creation (no-code/code)
    LIVE_TRADING,          // Issues with live trading execution
    PAPER_TRADING,         // Issues with paper trading
    BROKER_INTEGRATION,    // Broker connectivity problems
    MODEL_TRAINING,        // ML model training issues
    BACKTESTING,           // Backtesting problems
    ACCOUNT_BILLING,       // Account and billing issues
    KYC_VERIFICATION,      // KYC/AML verification help
    API_SDK,               // API and SDK usage help
    MARKETPLACE,           // Marketplace-related issues
    SECURITY,              // Security concerns
    DATA_PRIVACY,          // Data privacy requests
    FEATURE_REQUEST,       // New feature requests
    BUG_REPORT,            // Bug reports
    GENERAL_INQUIRY,       // General questions
    OTHER                  // Other issues
}