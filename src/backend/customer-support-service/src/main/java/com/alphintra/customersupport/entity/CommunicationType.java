package com.alphintra.customersupport.entity;

/**
 * Enumeration representing different types of communication within a ticket.
 */
public enum CommunicationType {
    MESSAGE,       // Regular text message/chat
    EMAIL,         // Email communication
    PHONE_LOG,     // Phone call log/notes
    VIDEO_CALL,    // Video call session
    SCREEN_SHARE,  // Screen sharing session
    INTERNAL_NOTE, // Internal agent note (not visible to user)
    SYSTEM_LOG,    // System-generated log entry
    FILE_UPLOAD,   // File attachment/upload
    STATUS_UPDATE, // Ticket status change notification
    ESCALATION,    // Escalation note
    RESOLUTION     // Resolution summary
}