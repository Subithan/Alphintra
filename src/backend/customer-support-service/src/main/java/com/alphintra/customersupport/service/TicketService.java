package com.alphintra.customersupport.service;

import com.alphintra.customersupport.dto.*;
import com.alphintra.customersupport.entity.*;
import com.alphintra.customersupport.exception.EscalationException;
import com.alphintra.customersupport.exception.TicketNotFoundException;
import com.alphintra.customersupport.repository.SupportAgentRepository;
import com.alphintra.customersupport.repository.TicketRepository;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.PageImpl;
import org.springframework.data.domain.Pageable;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.time.LocalDateTime;
import java.util.HashSet;
import java.util.List;
import java.util.Optional;
import java.util.UUID;
import java.util.stream.Collectors;

/**
 * Service class for managing support tickets.
 */
@Service
@Transactional
public class TicketService {

    private static final Logger logger = LoggerFactory.getLogger(TicketService.class);

    @Autowired
    private TicketRepository ticketRepository;

    @Autowired
    private SupportAgentRepository supportAgentRepository;

    @Autowired
    private TicketIdGeneratorService ticketIdGeneratorService;

    @Autowired
    private SmartTicketRoutingService smartTicketRoutingService;

    @Autowired
    private NotificationService notificationService;

    @Autowired
    private AuditService auditService;

    /**
     * Create a new support ticket.
     */
    public TicketDto createTicket(CreateTicketDto createTicketDto, String createdBy) {
        logger.info("Creating new ticket for user: {}", createTicketDto.getUserId());

        // Generate unique ticket ID
        String ticketId = ticketIdGeneratorService.generateTicketId();

        // Determine priority if not provided
        TicketPriority priority = createTicketDto.getPriority();
        if (priority == null) {
            priority = determinePriority(createTicketDto);
        }

        // Create ticket entity
        Ticket ticket = new Ticket(
            ticketId,
            createTicketDto.getUserId(),
            "user@example.com", // TODO: Get actual user email from user service
            createTicketDto.getTitle(),
            createTicketDto.getDescription(),
            createTicketDto.getCategory(),
            priority
        );

        // Add tags if provided
        if (createTicketDto.getTags() != null) {
            ticket.setTags(new HashSet<>(createTicketDto.getTags()));
        }

        // Auto-assign to best available agent
        Optional<SupportAgent> assignedAgent = smartTicketRoutingService.findBestAgent(ticket);
        if (assignedAgent.isPresent()) {
            ticket.setAssignedAgentId(assignedAgent.get().getAgentId());
            ticket.setStatus(TicketStatus.ASSIGNED);
            
            // Update agent workload
            assignedAgent.get().incrementTicketCount();
            supportAgentRepository.save(assignedAgent.get());
            
            logger.info("Ticket {} assigned to agent: {}", ticketId, assignedAgent.get().getAgentId());
        } else {
            ticket.setStatus(TicketStatus.NEW);
            logger.info("No available agent found for ticket: {}", ticketId);
        }

        // Set estimated resolution time
        ticket.setEstimatedResolutionTime(calculateEstimatedResolutionTime(priority));

        // Save ticket
        ticket = ticketRepository.save(ticket);

        // Log audit event
        auditService.logTicketCreation(ticketId, createTicketDto.getUserId(), createdBy);

        // Send notifications
        notificationService.sendTicketCreatedNotification(ticket);
        if (assignedAgent.isPresent()) {
            notificationService.sendTicketAssignedNotification(ticket, assignedAgent.get());
        }

        return convertToDto(ticket);
    }

    /**
     * Get ticket by ID.
     */
    @Transactional(readOnly = true)
    public TicketDto getTicketById(String ticketId) {
        Ticket ticket = ticketRepository.findById(ticketId)
            .orElseThrow(() -> new TicketNotFoundException("Ticket not found: " + ticketId));
        
        return convertToDto(ticket);
    }

    /**
     * Get tickets with filtering and pagination.
     */
    @Transactional(readOnly = true)
    public Page<TicketDto> getTickets(TicketFilter filter, Pageable pageable) {
        // For now, use simple query without complex filtering to avoid parameter binding issues
        // TODO: Implement proper filtering using Specification or Criteria API
        Page<Ticket> tickets;
        
        if (filter.getUserId() != null) {
            tickets = ticketRepository.findByUserId(filter.getUserId(), pageable);
        } else if (filter.getAgentId() != null) {
            tickets = ticketRepository.findByAssignedAgentId(filter.getAgentId(), pageable);
        } else if (filter.getStatus() != null) {
            tickets = ticketRepository.findByStatus(filter.getStatus(), pageable);
        } else if (filter.getCategory() != null) {
            tickets = ticketRepository.findByCategory(filter.getCategory(), pageable);
        } else if (filter.getPriority() != null) {
            tickets = ticketRepository.findByPriority(filter.getPriority(), pageable);
        } else {
            tickets = ticketRepository.findAllTicketsOrderByCreatedAtDesc(pageable);
        }

        List<TicketDto> ticketDtos = tickets.getContent().stream()
            .map(this::convertToDto)
            .collect(Collectors.toList());

        return new PageImpl<>(ticketDtos, pageable, tickets.getTotalElements());
    }

    /**
     * Update ticket.
     */
    public TicketDto updateTicket(String ticketId, UpdateTicketDto updateDto, String updatedBy) {
        Ticket ticket = ticketRepository.findById(ticketId)
            .orElseThrow(() -> new TicketNotFoundException("Ticket not found: " + ticketId));

        TicketStatus oldStatus = ticket.getStatus();
        String oldAgentId = ticket.getAssignedAgentId();

        // Update fields
        if (updateDto.getStatus() != null) {
            ticket.setStatus(updateDto.getStatus());
            
            // Handle status-specific logic
            if (updateDto.getStatus() == TicketStatus.RESOLVED) {
                ticket.setResolvedAt(LocalDateTime.now());
            }
        }

        if (updateDto.getPriority() != null) {
            ticket.setPriority(updateDto.getPriority());
            ticket.setEstimatedResolutionTime(calculateEstimatedResolutionTime(updateDto.getPriority()));
        }

        if (updateDto.getAssignedAgentId() != null) {
            // Update agent workloads
            if (oldAgentId != null && !oldAgentId.equals(updateDto.getAssignedAgentId())) {
                supportAgentRepository.findById(oldAgentId)
                    .ifPresent(agent -> {
                        agent.decrementTicketCount();
                        supportAgentRepository.save(agent);
                    });
            }

            if (!updateDto.getAssignedAgentId().equals(oldAgentId)) {
                supportAgentRepository.findById(updateDto.getAssignedAgentId())
                    .ifPresent(agent -> {
                        agent.incrementTicketCount();
                        supportAgentRepository.save(agent);
                    });
            }

            ticket.setAssignedAgentId(updateDto.getAssignedAgentId());
        }

        if (updateDto.getTags() != null) {
            ticket.setTags(new HashSet<>(updateDto.getTags()));
        }

        ticket.setLastUpdatedBy(updatedBy);
        ticket = ticketRepository.save(ticket);

        // Log audit event
        auditService.logTicketUpdate(ticketId, updatedBy, oldStatus, ticket.getStatus());

        // Send notifications for status changes
        if (oldStatus != ticket.getStatus()) {
            notificationService.sendTicketStatusUpdateNotification(ticket);
        }

        logger.info("Ticket {} updated by {}", ticketId, updatedBy);
        return convertToDto(ticket);
    }

    /**
     * Escalate ticket.
     */
    public TicketDto escalateTicket(String ticketId, EscalationDto escalationDto, String escalatedBy) {
        Ticket ticket = ticketRepository.findById(ticketId)
            .orElseThrow(() -> new TicketNotFoundException("Ticket not found: " + ticketId));

        // Find agent for escalation
        Optional<SupportAgent> escalationAgent = smartTicketRoutingService
            .findEscalationAgent(ticket, escalationDto.getTargetLevel());

        if (escalationAgent.isEmpty()) {
            throw new EscalationException("No available agent found for escalation");
        }

        // Update current agent workload
        if (ticket.getAssignedAgentId() != null) {
            supportAgentRepository.findById(ticket.getAssignedAgentId())
                .ifPresent(agent -> {
                    agent.decrementTicketCount();
                    supportAgentRepository.save(agent);
                });
        }

        // Update ticket
        ticket.setEscalationLevel(ticket.getEscalationLevel() + 1);
        ticket.setAssignedAgentId(escalationAgent.get().getAgentId());
        ticket.setStatus(TicketStatus.ESCALATED);
        ticket.setLastUpdatedBy(escalatedBy);

        // Update new agent workload
        escalationAgent.get().incrementTicketCount();
        supportAgentRepository.save(escalationAgent.get());

        ticket = ticketRepository.save(ticket);

        // Log audit event
        auditService.logTicketEscalation(ticketId, escalatedBy, escalationDto.getReason());

        // Send notifications
        notificationService.sendTicketEscalatedNotification(ticket, escalationAgent.get(), escalationDto.getReason());

        logger.info("Ticket {} escalated to agent {} by {}", ticketId, escalationAgent.get().getAgentId(), escalatedBy);
        return convertToDto(ticket);
    }

    /**
     * Close ticket.
     */
    public TicketDto closeTicket(String ticketId, String closedBy, String closureReason) {
        Ticket ticket = ticketRepository.findById(ticketId)
            .orElseThrow(() -> new TicketNotFoundException("Ticket not found: " + ticketId));

        ticket.setStatus(TicketStatus.CLOSED);
        ticket.setLastUpdatedBy(closedBy);

        if (ticket.getResolvedAt() == null) {
            ticket.setResolvedAt(LocalDateTime.now());
        }

        // Update agent workload
        if (ticket.getAssignedAgentId() != null) {
            supportAgentRepository.findById(ticket.getAssignedAgentId())
                .ifPresent(agent -> {
                    agent.decrementTicketCount();
                    supportAgentRepository.save(agent);
                });
        }

        ticket = ticketRepository.save(ticket);

        // Log audit event
        auditService.logTicketClosure(ticketId, closedBy, closureReason);

        // Send notification
        notificationService.sendTicketClosedNotification(ticket);

        logger.info("Ticket {} closed by {}", ticketId, closedBy);
        return convertToDto(ticket);
    }

    /**
     * Add satisfaction rating to ticket.
     */
    public TicketDto addSatisfactionRating(String ticketId, int rating, String feedback) {
        if (rating < 1 || rating > 5) {
            throw new IllegalArgumentException("Rating must be between 1 and 5");
        }

        Ticket ticket = ticketRepository.findById(ticketId)
            .orElseThrow(() -> new TicketNotFoundException("Ticket not found: " + ticketId));

        ticket.setSatisfactionRating(rating);
        ticket.setSatisfactionFeedback(feedback);
        ticket = ticketRepository.save(ticket);

        // Update agent satisfaction rating
        if (ticket.getAssignedAgentId() != null) {
            updateAgentSatisfactionRating(ticket.getAssignedAgentId());
        }

        logger.info("Satisfaction rating {} added to ticket {}", rating, ticketId);
        return convertToDto(ticket);
    }

    /**
     * Get tickets assigned to agent.
     */
    @Transactional(readOnly = true)
    public Page<TicketDto> getAgentTickets(String agentId, List<TicketStatus> statuses, Pageable pageable) {
        Page<Ticket> tickets;
        
        if (statuses != null && !statuses.isEmpty()) {
            tickets = ticketRepository.findByAssignedAgentIdAndStatusIn(agentId, statuses, pageable);
        } else {
            tickets = ticketRepository.findByAssignedAgentId(agentId, pageable);
        }

        List<TicketDto> ticketDtos = tickets.getContent().stream()
            .map(this::convertToDto)
            .collect(Collectors.toList());

        return new PageImpl<>(ticketDtos, pageable, tickets.getTotalElements());
    }

    // Private helper methods

    private TicketPriority determinePriority(CreateTicketDto createTicketDto) {
        // AI-based priority determination logic
        String description = createTicketDto.getDescription().toLowerCase();
        String title = createTicketDto.getTitle().toLowerCase();
        
        // Check for urgent keywords
        if (containsUrgentKeywords(description + " " + title)) {
            return TicketPriority.URGENT;
        }
        
        // Check for high priority categories
        if (createTicketDto.getCategory() == TicketCategory.SECURITY ||
            createTicketDto.getCategory() == TicketCategory.LIVE_TRADING) {
            return TicketPriority.HIGH;
        }
        
        // Check for medium priority categories
        if (createTicketDto.getCategory() == TicketCategory.ACCOUNT_BILLING ||
            createTicketDto.getCategory() == TicketCategory.BROKER_INTEGRATION) {
            return TicketPriority.MEDIUM;
        }
        
        return TicketPriority.LOW;
    }

    private boolean containsUrgentKeywords(String text) {
        String[] urgentKeywords = {
            "urgent", "emergency", "critical", "down", "broken", "not working",
            "lost money", "unauthorized", "hacked", "cannot login", "can't access",
            "system crash", "data loss", "security breach"
        };
        
        for (String keyword : urgentKeywords) {
            if (text.contains(keyword)) {
                return true;
            }
        }
        return false;
    }

    private LocalDateTime calculateEstimatedResolutionTime(TicketPriority priority) {
        LocalDateTime now = LocalDateTime.now();
        
        return switch (priority) {
            case CRITICAL -> now.plusMinutes(30);
            case URGENT -> now.plusHours(2);
            case HIGH -> now.plusHours(8);
            case MEDIUM -> now.plusHours(24);
            case LOW -> now.plusHours(48);
        };
    }

    private void updateAgentSatisfactionRating(String agentId) {
        // Calculate average satisfaction rating for the agent
        List<Ticket> agentTickets = ticketRepository.findByAssignedAgentIdAndSatisfactionRatingNotNull(agentId);
        
        if (!agentTickets.isEmpty()) {
            double averageRating = agentTickets.stream()
                .mapToInt(Ticket::getSatisfactionRating)
                .average()
                .orElse(0.0);
            
            supportAgentRepository.findById(agentId)
                .ifPresent(agent -> {
                    agent.setCustomerSatisfactionRating(averageRating);
                    supportAgentRepository.save(agent);
                });
        }
    }

    private TicketDto convertToDto(Ticket ticket) {
        TicketDto dto = new TicketDto();
        dto.setTicketId(ticket.getTicketId());
        dto.setUserId(ticket.getUserId());
        dto.setTitle(ticket.getTitle());
        dto.setDescription(ticket.getDescription());
        dto.setCategory(ticket.getCategory());
        dto.setPriority(ticket.getPriority());
        dto.setStatus(ticket.getStatus());
        dto.setAssignedAgentId(ticket.getAssignedAgentId());
        dto.setEscalationLevel(ticket.getEscalationLevel());
        dto.setTags(ticket.getTags());
        dto.setCreatedAt(ticket.getCreatedAt());
        dto.setUpdatedAt(ticket.getUpdatedAt());
        dto.setResolvedAt(ticket.getResolvedAt());
        dto.setEstimatedResolutionTime(ticket.getEstimatedResolutionTime());
        dto.setLastUpdatedBy(ticket.getLastUpdatedBy());
        dto.setSatisfactionRating(ticket.getSatisfactionRating());
        dto.setSatisfactionFeedback(ticket.getSatisfactionFeedback());

        // Set assigned agent name
        if (ticket.getAssignedAgentId() != null) {
            supportAgentRepository.findById(ticket.getAssignedAgentId())
                .ifPresent(agent -> dto.setAssignedAgentName(agent.getFullName()));
        }

        // Set display names
        dto.setPriorityDisplayName(formatPriority(ticket.getPriority()));
        dto.setStatusDisplayName(formatStatus(ticket.getStatus()));
        dto.setCategoryDisplayName(formatCategory(ticket.getCategory()));

        return dto;
    }

    private String formatPriority(TicketPriority priority) {
        return switch (priority) {
            case CRITICAL -> "Critical";
            case URGENT -> "Urgent";
            case HIGH -> "High";
            case MEDIUM -> "Medium";
            case LOW -> "Low";
        };
    }

    private String formatStatus(TicketStatus status) {
        return switch (status) {
            case NEW -> "New";
            case ASSIGNED -> "Assigned";
            case IN_PROGRESS -> "In Progress";
            case PENDING_USER -> "Pending User";
            case PENDING_INTERNAL -> "Pending Internal";
            case ESCALATED -> "Escalated";
            case RESOLVED -> "Resolved";
            case CLOSED -> "Closed";
            case REOPENED -> "Reopened";
        };
    }

    private String formatCategory(TicketCategory category) {
        return switch (category) {
            case TECHNICAL -> "Technical";
            case STRATEGY_DEVELOPMENT -> "Strategy Development";
            case LIVE_TRADING -> "Live Trading";
            case PAPER_TRADING -> "Paper Trading";
            case BROKER_INTEGRATION -> "Broker Integration";
            case MODEL_TRAINING -> "Model Training";
            case BACKTESTING -> "Backtesting";
            case ACCOUNT_BILLING -> "Account & Billing";
            case KYC_VERIFICATION -> "KYC Verification";
            case API_SDK -> "API & SDK";
            case MARKETPLACE -> "Marketplace";
            case SECURITY -> "Security";
            case DATA_PRIVACY -> "Data Privacy";
            case FEATURE_REQUEST -> "Feature Request";
            case BUG_REPORT -> "Bug Report";
            case GENERAL_INQUIRY -> "General Inquiry";
            case OTHER -> "Other";
        };
    }
}