package com.alphintra.customersupport.service;

import com.alphintra.customersupport.entity.AgentLevel;
import com.alphintra.customersupport.entity.SupportAgent;
import com.alphintra.customersupport.entity.Ticket;
import com.alphintra.customersupport.repository.SupportAgentRepository;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;

import java.util.List;
import java.util.Optional;

/**
 * Service for intelligent ticket routing to the best available agent.
 */
@Service
public class SmartTicketRoutingService {

    private static final Logger logger = LoggerFactory.getLogger(SmartTicketRoutingService.class);

    @Autowired
    private SupportAgentRepository supportAgentRepository;

    /**
     * Find the best available agent for a ticket.
     */
    public Optional<SupportAgent> findBestAgent(Ticket ticket) {
        logger.info("Finding best agent for ticket: {} with category: {}", 
                   ticket.getTicketId(), ticket.getCategory());

        // First, try to find agents with matching specialization
        List<SupportAgent> specializedAgents = supportAgentRepository
            .findAvailableAgentsWithSpecialization(ticket.getCategory());

        if (!specializedAgents.isEmpty()) {
            // Return agent with lowest workload and highest satisfaction
            return Optional.of(specializedAgents.get(0));
        }

        // If no specialized agents available, find any available agent
        List<SupportAgent> availableAgents = supportAgentRepository.findAvailableAgents();
        
        if (!availableAgents.isEmpty()) {
            // Get agent with lowest workload
            return availableAgents.stream()
                .min((a1, a2) -> Integer.compare(a1.getCurrentTicketCount(), a2.getCurrentTicketCount()));
        }

        logger.warn("No available agents found for ticket: {}", ticket.getTicketId());
        return Optional.empty();
    }

    /**
     * Find agent for escalation.
     */
    public Optional<SupportAgent> findEscalationAgent(Ticket ticket, AgentLevel targetLevel) {
        logger.info("Finding escalation agent for ticket: {} to level: {}", 
                   ticket.getTicketId(), targetLevel);

        List<AgentLevel> escalationLevels = List.of(targetLevel, AgentLevel.L4_MANAGER);
        List<SupportAgent> escalationAgents = supportAgentRepository
            .findAgentsForEscalation(escalationLevels);

        if (!escalationAgents.isEmpty()) {
            return Optional.of(escalationAgents.get(0));
        }

        logger.warn("No escalation agents available for ticket: {}", ticket.getTicketId());
        return Optional.empty();
    }

    /**
     * Check if agent can handle the ticket category.
     */
    public boolean canAgentHandleCategory(SupportAgent agent, Ticket ticket) {
        // L4 managers can handle any category
        if (agent.getAgentLevel() == AgentLevel.L4_MANAGER) {
            return true;
        }

        // Check if agent has specialization in the ticket category
        return agent.hasSpecialization(ticket.getCategory());
    }

    /**
     * Calculate agent workload score (lower is better).
     */
    public double calculateWorkloadScore(SupportAgent agent) {
        double currentLoad = (double) agent.getCurrentTicketCount() / agent.getMaxConcurrentTickets();
        double satisfactionWeight = agent.getCustomerSatisfactionRating() != null ? 
            (5.0 - agent.getCustomerSatisfactionRating()) / 5.0 : 0.5;
        
        return currentLoad + (satisfactionWeight * 0.3);
    }
}