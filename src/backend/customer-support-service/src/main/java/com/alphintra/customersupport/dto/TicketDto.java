package com.alphintra.customersupport.dto;

import com.alphintra.customersupport.entity.TicketCategory;
import com.alphintra.customersupport.entity.TicketPriority;
import com.alphintra.customersupport.entity.TicketStatus;

import java.time.LocalDateTime;
import java.util.List;
import java.util.Set;
import java.util.UUID;

/**
 * DTO for ticket information.
 */
public class TicketDto {

    private String ticketId;
    private UUID userId;
    private String title;
    private String description;
    private TicketCategory category;
    private TicketPriority priority;
    private TicketStatus status;
    private String assignedAgentId;
    private String assignedAgentName;
    private Integer escalationLevel;
    private Set<String> tags;
    private LocalDateTime createdAt;
    private LocalDateTime updatedAt;
    private LocalDateTime resolvedAt;
    private LocalDateTime estimatedResolutionTime;
    private String lastUpdatedBy;
    private Integer satisfactionRating;
    private String satisfactionFeedback;
    
    // Additional fields for enhanced ticket view
    private Long communicationCount;
    private LocalDateTime lastCommunicationAt;
    private boolean hasUnreadMessages;
    private String priorityDisplayName;
    private String statusDisplayName;
    private String categoryDisplayName;
    private List<CommunicationDto> recentCommunications;

    // User information (masked based on access level)
    private String userEmail;
    private String userFullName;
    private String userAccountType;

    // Constructors
    public TicketDto() {}

    // Getters and Setters
    public String getTicketId() {
        return ticketId;
    }

    public void setTicketId(String ticketId) {
        this.ticketId = ticketId;
    }

    public UUID getUserId() {
        return userId;
    }

    public void setUserId(UUID userId) {
        this.userId = userId;
    }

    public String getTitle() {
        return title;
    }

    public void setTitle(String title) {
        this.title = title;
    }

    public String getDescription() {
        return description;
    }

    public void setDescription(String description) {
        this.description = description;
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

    public TicketStatus getStatus() {
        return status;
    }

    public void setStatus(TicketStatus status) {
        this.status = status;
    }

    public String getAssignedAgentId() {
        return assignedAgentId;
    }

    public void setAssignedAgentId(String assignedAgentId) {
        this.assignedAgentId = assignedAgentId;
    }

    public String getAssignedAgentName() {
        return assignedAgentName;
    }

    public void setAssignedAgentName(String assignedAgentName) {
        this.assignedAgentName = assignedAgentName;
    }

    public Integer getEscalationLevel() {
        return escalationLevel;
    }

    public void setEscalationLevel(Integer escalationLevel) {
        this.escalationLevel = escalationLevel;
    }

    public Set<String> getTags() {
        return tags;
    }

    public void setTags(Set<String> tags) {
        this.tags = tags;
    }

    public LocalDateTime getCreatedAt() {
        return createdAt;
    }

    public void setCreatedAt(LocalDateTime createdAt) {
        this.createdAt = createdAt;
    }

    public LocalDateTime getUpdatedAt() {
        return updatedAt;
    }

    public void setUpdatedAt(LocalDateTime updatedAt) {
        this.updatedAt = updatedAt;
    }

    public LocalDateTime getResolvedAt() {
        return resolvedAt;
    }

    public void setResolvedAt(LocalDateTime resolvedAt) {
        this.resolvedAt = resolvedAt;
    }

    public LocalDateTime getEstimatedResolutionTime() {
        return estimatedResolutionTime;
    }

    public void setEstimatedResolutionTime(LocalDateTime estimatedResolutionTime) {
        this.estimatedResolutionTime = estimatedResolutionTime;
    }

    public String getLastUpdatedBy() {
        return lastUpdatedBy;
    }

    public void setLastUpdatedBy(String lastUpdatedBy) {
        this.lastUpdatedBy = lastUpdatedBy;
    }

    public Integer getSatisfactionRating() {
        return satisfactionRating;
    }

    public void setSatisfactionRating(Integer satisfactionRating) {
        this.satisfactionRating = satisfactionRating;
    }

    public String getSatisfactionFeedback() {
        return satisfactionFeedback;
    }

    public void setSatisfactionFeedback(String satisfactionFeedback) {
        this.satisfactionFeedback = satisfactionFeedback;
    }

    public Long getCommunicationCount() {
        return communicationCount;
    }

    public void setCommunicationCount(Long communicationCount) {
        this.communicationCount = communicationCount;
    }

    public LocalDateTime getLastCommunicationAt() {
        return lastCommunicationAt;
    }

    public void setLastCommunicationAt(LocalDateTime lastCommunicationAt) {
        this.lastCommunicationAt = lastCommunicationAt;
    }

    public boolean isHasUnreadMessages() {
        return hasUnreadMessages;
    }

    public void setHasUnreadMessages(boolean hasUnreadMessages) {
        this.hasUnreadMessages = hasUnreadMessages;
    }

    public String getPriorityDisplayName() {
        return priorityDisplayName;
    }

    public void setPriorityDisplayName(String priorityDisplayName) {
        this.priorityDisplayName = priorityDisplayName;
    }

    public String getStatusDisplayName() {
        return statusDisplayName;
    }

    public void setStatusDisplayName(String statusDisplayName) {
        this.statusDisplayName = statusDisplayName;
    }

    public String getCategoryDisplayName() {
        return categoryDisplayName;
    }

    public void setCategoryDisplayName(String categoryDisplayName) {
        this.categoryDisplayName = categoryDisplayName;
    }

    public List<CommunicationDto> getRecentCommunications() {
        return recentCommunications;
    }

    public void setRecentCommunications(List<CommunicationDto> recentCommunications) {
        this.recentCommunications = recentCommunications;
    }

    public String getUserEmail() {
        return userEmail;
    }

    public void setUserEmail(String userEmail) {
        this.userEmail = userEmail;
    }

    public String getUserFullName() {
        return userFullName;
    }

    public void setUserFullName(String userFullName) {
        this.userFullName = userFullName;
    }

    public String getUserAccountType() {
        return userAccountType;
    }

    public void setUserAccountType(String userAccountType) {
        this.userAccountType = userAccountType;
    }

    // Utility methods
    public boolean isResolved() {
        return status == TicketStatus.RESOLVED || status == TicketStatus.CLOSED;
    }

    public boolean isOpen() {
        return !isResolved();
    }

    public boolean isEscalated() {
        return escalationLevel != null && escalationLevel > 0;
    }

    public boolean isHighPriority() {
        return priority == TicketPriority.HIGH || 
               priority == TicketPriority.URGENT || 
               priority == TicketPriority.CRITICAL;
    }
}