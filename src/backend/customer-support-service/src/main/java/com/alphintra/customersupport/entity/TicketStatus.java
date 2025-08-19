package com.alphintra.customersupport.entity;

/**
 * Enumeration representing the status of a support ticket.
 */
public enum TicketStatus {
    NEW,              // Newly created ticket, not yet assigned
    ASSIGNED,         // Assigned to an agent but not yet being worked on
    IN_PROGRESS,      // Currently being worked on by an agent
    PENDING_USER,     // Waiting for user response or action
    PENDING_INTERNAL, // Waiting for internal team response
    ESCALATED,        // Escalated to higher level support or specialist
    RESOLVED,         // Issue has been resolved, waiting for user confirmation
    CLOSED,           // Ticket closed, issue confirmed resolved
    REOPENED          // Previously closed ticket that has been reopened
}