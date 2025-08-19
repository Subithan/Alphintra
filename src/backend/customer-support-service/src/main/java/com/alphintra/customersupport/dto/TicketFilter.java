package com.alphintra.customersupport.dto;

import com.alphintra.customersupport.entity.TicketCategory;
import com.alphintra.customersupport.entity.TicketPriority;
import com.alphintra.customersupport.entity.TicketStatus;

import java.time.LocalDateTime;
import java.util.UUID;

/**
 * DTO for filtering tickets in queries.
 */
public class TicketFilter {

    private UUID userId;
    private String agentId;
    private TicketStatus status;
    private TicketCategory category;
    private TicketPriority priority;
    private LocalDateTime startDate;
    private LocalDateTime endDate;
    private String searchTerm;
    private Boolean assignedToMe;
    private Integer escalationLevel;

    // Constructors
    public TicketFilter() {}

    // Getters and Setters
    public UUID getUserId() {
        return userId;
    }

    public void setUserId(UUID userId) {
        this.userId = userId;
    }

    public String getAgentId() {
        return agentId;
    }

    public void setAgentId(String agentId) {
        this.agentId = agentId;
    }

    public TicketStatus getStatus() {
        return status;
    }

    public void setStatus(TicketStatus status) {
        this.status = status;
    }

    public TicketCategory getCategory() {
        return category;
    }

    public void setCategory(TicketCategory category) {
        this.category = category;
    }

    public TicketPriority getPriority() {
        return priority;
    }

    public void setPriority(TicketPriority priority) {
        this.priority = priority;
    }

    public LocalDateTime getStartDate() {
        return startDate;
    }

    public void setStartDate(LocalDateTime startDate) {
        this.startDate = startDate;
    }

    public LocalDateTime getEndDate() {
        return endDate;
    }

    public void setEndDate(LocalDateTime endDate) {
        this.endDate = endDate;
    }

    public String getSearchTerm() {
        return searchTerm;
    }

    public void setSearchTerm(String searchTerm) {
        this.searchTerm = searchTerm;
    }

    public Boolean getAssignedToMe() {
        return assignedToMe;
    }

    public void setAssignedToMe(Boolean assignedToMe) {
        this.assignedToMe = assignedToMe;
    }

    public Integer getEscalationLevel() {
        return escalationLevel;
    }

    public void setEscalationLevel(Integer escalationLevel) {
        this.escalationLevel = escalationLevel;
    }
}