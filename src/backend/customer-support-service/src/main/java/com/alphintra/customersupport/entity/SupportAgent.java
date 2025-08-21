package com.alphintra.customersupport.entity;

import jakarta.persistence.*;
import org.hibernate.annotations.CreationTimestamp;
import org.hibernate.annotations.UpdateTimestamp;

import java.time.LocalDateTime;
import java.util.HashSet;
import java.util.Set;

/**
 * Entity representing a support agent in the customer support system.
 */
@Entity
@Table(name = "support_agents", indexes = {
    @Index(name = "idx_agent_level", columnList = "agent_level"),
    @Index(name = "idx_agent_status", columnList = "status"),
    @Index(name = "idx_agent_department", columnList = "department")
})
public class SupportAgent {

    @Id
    @Column(name = "agent_id", length = 50)
    private String agentId;

    @Column(name = "username", nullable = false, unique = true, length = 50)
    private String username;

    @Column(name = "email", nullable = false, unique = true, length = 100)
    private String email;

    @Column(name = "first_name", nullable = false, length = 50)
    private String firstName;

    @Column(name = "last_name", nullable = false, length = 50)
    private String lastName;

    @Enumerated(EnumType.STRING)
    @Column(name = "agent_level", nullable = false)
    private AgentLevel agentLevel;

    @Enumerated(EnumType.STRING)
    @Column(name = "status", nullable = false)
    private AgentStatus status;

    @Column(name = "department", length = 50)
    private String department;

    @ElementCollection(targetClass = TicketCategory.class)
    @CollectionTable(name = "agent_specializations", 
                    joinColumns = @JoinColumn(name = "agent_id"))
    @Enumerated(EnumType.STRING)
    @Column(name = "specialization")
    private Set<TicketCategory> specializations = new HashSet<>();

    @Column(name = "max_concurrent_tickets")
    private Integer maxConcurrentTickets;

    @Column(name = "current_ticket_count")
    private Integer currentTicketCount = 0;

    @Column(name = "total_tickets_handled")
    private Long totalTicketsHandled = 0L;

    @Column(name = "average_resolution_time_hours")
    private Double averageResolutionTimeHours;

    @Column(name = "customer_satisfaction_rating")
    private Double customerSatisfactionRating;

    @Column(name = "languages", length = 200)
    private String languages; // Comma-separated list

    @Column(name = "timezone", length = 50)
    private String timezone;

    @Column(name = "work_hours_start")
    private String workHoursStart; // HH:mm format

    @Column(name = "work_hours_end")
    private String workHoursEnd; // HH:mm format

    @Column(name = "last_activity_at")
    private LocalDateTime lastActivityAt;

    @CreationTimestamp
    @Column(name = "created_at", nullable = false)
    private LocalDateTime createdAt;

    @UpdateTimestamp
    @Column(name = "updated_at", nullable = false)
    private LocalDateTime updatedAt;

    @Column(name = "is_active", nullable = false)
    private Boolean isActive = true;

    // Constructors
    public SupportAgent() {}

    public SupportAgent(String agentId, String username, String email, 
                       String firstName, String lastName, AgentLevel agentLevel) {
        this.agentId = agentId;
        this.username = username;
        this.email = email;
        this.firstName = firstName;
        this.lastName = lastName;
        this.agentLevel = agentLevel;
        this.status = AgentStatus.OFFLINE;
        this.maxConcurrentTickets = getDefaultMaxTickets(agentLevel);
    }

    // Getters and Setters
    public String getAgentId() {
        return agentId;
    }

    public void setAgentId(String agentId) {
        this.agentId = agentId;
    }

    public String getUsername() {
        return username;
    }

    public void setUsername(String username) {
        this.username = username;
    }

    public String getEmail() {
        return email;
    }

    public void setEmail(String email) {
        this.email = email;
    }

    public String getFirstName() {
        return firstName;
    }

    public void setFirstName(String firstName) {
        this.firstName = firstName;
    }

    public String getLastName() {
        return lastName;
    }

    public void setLastName(String lastName) {
        this.lastName = lastName;
    }

    public AgentLevel getAgentLevel() {
        return agentLevel;
    }

    public void setAgentLevel(AgentLevel agentLevel) {
        this.agentLevel = agentLevel;
    }

    public AgentStatus getStatus() {
        return status;
    }

    public void setStatus(AgentStatus status) {
        this.status = status;
    }

    public String getDepartment() {
        return department;
    }

    public void setDepartment(String department) {
        this.department = department;
    }

    public Set<TicketCategory> getSpecializations() {
        return specializations;
    }

    public void setSpecializations(Set<TicketCategory> specializations) {
        this.specializations = specializations;
    }

    public Integer getMaxConcurrentTickets() {
        return maxConcurrentTickets;
    }

    public void setMaxConcurrentTickets(Integer maxConcurrentTickets) {
        this.maxConcurrentTickets = maxConcurrentTickets;
    }

    public Integer getCurrentTicketCount() {
        return currentTicketCount;
    }

    public void setCurrentTicketCount(Integer currentTicketCount) {
        this.currentTicketCount = currentTicketCount;
    }

    public Long getTotalTicketsHandled() {
        return totalTicketsHandled;
    }

    public void setTotalTicketsHandled(Long totalTicketsHandled) {
        this.totalTicketsHandled = totalTicketsHandled;
    }

    public Double getAverageResolutionTimeHours() {
        return averageResolutionTimeHours;
    }

    public void setAverageResolutionTimeHours(Double averageResolutionTimeHours) {
        this.averageResolutionTimeHours = averageResolutionTimeHours;
    }

    public Double getCustomerSatisfactionRating() {
        return customerSatisfactionRating;
    }

    public void setCustomerSatisfactionRating(Double customerSatisfactionRating) {
        this.customerSatisfactionRating = customerSatisfactionRating;
    }

    public String getLanguages() {
        return languages;
    }

    public void setLanguages(String languages) {
        this.languages = languages;
    }

    public String getTimezone() {
        return timezone;
    }

    public void setTimezone(String timezone) {
        this.timezone = timezone;
    }

    public String getWorkHoursStart() {
        return workHoursStart;
    }

    public void setWorkHoursStart(String workHoursStart) {
        this.workHoursStart = workHoursStart;
    }

    public String getWorkHoursEnd() {
        return workHoursEnd;
    }

    public void setWorkHoursEnd(String workHoursEnd) {
        this.workHoursEnd = workHoursEnd;
    }

    public LocalDateTime getLastActivityAt() {
        return lastActivityAt;
    }

    public void setLastActivityAt(LocalDateTime lastActivityAt) {
        this.lastActivityAt = lastActivityAt;
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

    public Boolean getIsActive() {
        return isActive;
    }

    public void setIsActive(Boolean isActive) {
        this.isActive = isActive;
    }

    // Utility methods
    public String getFullName() {
        return firstName + " " + lastName;
    }

    public boolean hasSpecialization(TicketCategory category) {
        return specializations.contains(category);
    }

    public void addSpecialization(TicketCategory category) {
        specializations.add(category);
    }

    public void removeSpecialization(TicketCategory category) {
        specializations.remove(category);
    }

    public boolean canTakeNewTicket() {
        return isActive && status == AgentStatus.AVAILABLE && 
               currentTicketCount < maxConcurrentTickets;
    }

    public void incrementTicketCount() {
        this.currentTicketCount++;
        this.totalTicketsHandled++;
    }

    public void decrementTicketCount() {
        if (this.currentTicketCount > 0) {
            this.currentTicketCount--;
        }
    }

    public void updateLastActivity() {
        this.lastActivityAt = LocalDateTime.now();
    }

    private Integer getDefaultMaxTickets(AgentLevel level) {
        return switch (level) {
            case L1 -> 5;
            case L2 -> 8;
            case L3_SPECIALIST -> 6;
            case L4_MANAGER -> 10;
        };
    }
}