package com.alphintra.customersupport.dto;

import com.alphintra.customersupport.entity.TicketPriority;
import com.alphintra.customersupport.entity.TicketStatus;

import java.util.List;

/**
 * DTO for updating ticket information.
 */
public class UpdateTicketDto {

    private TicketStatus status;
    private TicketPriority priority;
    private String assignedAgentId;
    private List<String> tags;
    private String notes;

    // Constructors
    public UpdateTicketDto() {}

    // Getters and Setters
    public TicketStatus getStatus() {
        return status;
    }

    public void setStatus(TicketStatus status) {
        this.status = status;
    }

    public TicketPriority getPriority() {
        return priority;
    }

    public void setPriority(TicketPriority priority) {
        this.priority = priority;
    }

    public String getAssignedAgentId() {
        return assignedAgentId;
    }

    public void setAssignedAgentId(String assignedAgentId) {
        this.assignedAgentId = assignedAgentId;
    }

    public List<String> getTags() {
        return tags;
    }

    public void setTags(List<String> tags) {
        this.tags = tags;
    }

    public String getNotes() {
        return notes;
    }

    public void setNotes(String notes) {
        this.notes = notes;
    }
}