package com.alphintra.customersupport.entity;

/**
 * Enumeration representing the current status of a support agent.
 */
public enum AgentStatus {
    AVAILABLE,    // Online and available to take new tickets
    BUSY,         // Online but busy with current tickets
    AWAY,         // Temporarily away but still online
    BREAK,        // On break
    OFFLINE       // Not currently working/logged out
}