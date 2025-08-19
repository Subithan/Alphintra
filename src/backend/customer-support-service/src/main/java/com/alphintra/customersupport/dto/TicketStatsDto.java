package com.alphintra.customersupport.dto;

import java.util.Map;

/**
 * DTO for ticket statistics.
 */
public class TicketStatsDto {

    private Long totalTickets;
    private Long openTickets;
    private Long resolvedTickets;
    private Long closedTickets;
    private Double averageResolutionTimeHours;
    private Double averageSatisfactionRating;
    private Long highPriorityTickets;
    private Long escalatedTickets;
    
    // Category distribution
    private Map<String, Long> ticketsByCategory;
    
    // Priority distribution
    private Map<String, Long> ticketsByPriority;
    
    // Status distribution
    private Map<String, Long> ticketsByStatus;
    
    // Daily stats
    private Map<String, Long> dailyTicketCreation;

    // Constructors
    public TicketStatsDto() {}

    // Getters and Setters
    public Long getTotalTickets() {
        return totalTickets;
    }

    public void setTotalTickets(Long totalTickets) {
        this.totalTickets = totalTickets;
    }

    public Long getOpenTickets() {
        return openTickets;
    }

    public void setOpenTickets(Long openTickets) {
        this.openTickets = openTickets;
    }

    public Long getResolvedTickets() {
        return resolvedTickets;
    }

    public void setResolvedTickets(Long resolvedTickets) {
        this.resolvedTickets = resolvedTickets;
    }

    public Long getClosedTickets() {
        return closedTickets;
    }

    public void setClosedTickets(Long closedTickets) {
        this.closedTickets = closedTickets;
    }

    public Double getAverageResolutionTimeHours() {
        return averageResolutionTimeHours;
    }

    public void setAverageResolutionTimeHours(Double averageResolutionTimeHours) {
        this.averageResolutionTimeHours = averageResolutionTimeHours;
    }

    public Double getAverageSatisfactionRating() {
        return averageSatisfactionRating;
    }

    public void setAverageSatisfactionRating(Double averageSatisfactionRating) {
        this.averageSatisfactionRating = averageSatisfactionRating;
    }

    public Long getHighPriorityTickets() {
        return highPriorityTickets;
    }

    public void setHighPriorityTickets(Long highPriorityTickets) {
        this.highPriorityTickets = highPriorityTickets;
    }

    public Long getEscalatedTickets() {
        return escalatedTickets;
    }

    public void setEscalatedTickets(Long escalatedTickets) {
        this.escalatedTickets = escalatedTickets;
    }

    public Map<String, Long> getTicketsByCategory() {
        return ticketsByCategory;
    }

    public void setTicketsByCategory(Map<String, Long> ticketsByCategory) {
        this.ticketsByCategory = ticketsByCategory;
    }

    public Map<String, Long> getTicketsByPriority() {
        return ticketsByPriority;
    }

    public void setTicketsByPriority(Map<String, Long> ticketsByPriority) {
        this.ticketsByPriority = ticketsByPriority;
    }

    public Map<String, Long> getTicketsByStatus() {
        return ticketsByStatus;
    }

    public void setTicketsByStatus(Map<String, Long> ticketsByStatus) {
        this.ticketsByStatus = ticketsByStatus;
    }

    public Map<String, Long> getDailyTicketCreation() {
        return dailyTicketCreation;
    }

    public void setDailyTicketCreation(Map<String, Long> dailyTicketCreation) {
        this.dailyTicketCreation = dailyTicketCreation;
    }
}