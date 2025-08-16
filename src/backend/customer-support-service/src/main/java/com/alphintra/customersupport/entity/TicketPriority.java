package com.alphintra.customersupport.entity;

/**
 * Enumeration representing ticket priority levels.
 */
public enum TicketPriority {
    LOW,       // Non-urgent issues, can wait 24-48 hours
    MEDIUM,    // Standard priority, should be addressed within 8-24 hours
    HIGH,      // Important issues, needs attention within 2-8 hours
    URGENT,    // Critical issues affecting trading, immediate attention required
    CRITICAL   // System-wide issues or security concerns, highest priority
}