package com.alphintra.customersupport.controller;

import com.alphintra.customersupport.dto.*;
import com.alphintra.customersupport.entity.TicketCategory;
import com.alphintra.customersupport.entity.TicketPriority;
import com.alphintra.customersupport.entity.TicketStatus;
import com.alphintra.customersupport.service.TicketService;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.Parameter;
import io.swagger.v3.oas.annotations.responses.ApiResponse;
import io.swagger.v3.oas.annotations.responses.ApiResponses;
import io.swagger.v3.oas.annotations.tags.Tag;
import jakarta.validation.Valid;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.PageRequest;
import org.springframework.data.domain.Pageable;
import org.springframework.data.domain.Sort;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.time.LocalDateTime;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

/**
 * REST Controller for managing support tickets.
 */
@RestController
@RequestMapping("/tickets")
@Tag(name = "Tickets", description = "Support ticket management operations")
public class TicketController {

    private static final Logger logger = LoggerFactory.getLogger(TicketController.class);

    @Autowired
    private TicketService ticketService;

    /**
     * Create a new support ticket.
     */
    @PostMapping
    @Operation(
        summary = "Create a new support ticket",
        description = "Creates a new support ticket and automatically assigns it to the best available agent"
    )
    @ApiResponses({
        @ApiResponse(responseCode = "201", description = "Ticket created successfully"),
        @ApiResponse(responseCode = "400", description = "Invalid ticket data")
    })
    public ResponseEntity<TicketDto> createTicket(
            @Valid @RequestBody CreateTicketDto createTicketDto) {
        
        logger.info("Creating ticket for user: {}", createTicketDto.getUserId());
        
        String createdBy = getAgentId();
        TicketDto ticket = ticketService.createTicket(createTicketDto, createdBy);
        
        return ResponseEntity.status(HttpStatus.CREATED).body(ticket);
    }

    /**
     * Get all tickets with filtering and pagination.
     */
    @GetMapping
    @Operation(
        summary = "Get support tickets",
        description = "Retrieve paginated list of support tickets with optional filtering"
    )
    // @PreAuthorize("hasRole('SUPPORT_AGENT')") // Disabled for development
    public ResponseEntity<Page<TicketDto>> getTickets(
            @Parameter(description = "Page number") @RequestParam(defaultValue = "0") int page,
            @Parameter(description = "Page size") @RequestParam(defaultValue = "20") int size,
            @Parameter(description = "Sort field") @RequestParam(defaultValue = "createdAt") String sort,
            @Parameter(description = "Sort direction") @RequestParam(defaultValue = "desc") String direction,
            @Parameter(description = "Filter by user ID") @RequestParam(required = false) String userId,
            @Parameter(description = "Filter by assigned agent") @RequestParam(required = false) String agentId,
            @Parameter(description = "Filter by status") @RequestParam(required = false) TicketStatus status,
            @Parameter(description = "Filter by category") @RequestParam(required = false) TicketCategory category,
            @Parameter(description = "Filter by priority") @RequestParam(required = false) TicketPriority priority,
            @Parameter(description = "Filter tickets assigned to me") @RequestParam(required = false) Boolean assignedToMe,
            @Parameter(description = "Start date for filtering") @RequestParam(required = false) LocalDateTime startDate,
            @Parameter(description = "End date for filtering") @RequestParam(required = false) LocalDateTime endDate) {

        Sort.Direction sortDirection = direction.equalsIgnoreCase("desc") ? 
            Sort.Direction.DESC : Sort.Direction.ASC;
        Pageable pageable = PageRequest.of(page, size, Sort.by(sortDirection, sort));

        TicketFilter filter = new TicketFilter();
        
        // Set userId filter directly (now accepts String)
        if (userId != null) {
            filter.setUserId(userId);
        }
        
        filter.setAgentId(assignedToMe != null && assignedToMe ? getAgentId() : agentId);
        filter.setStatus(status);
        filter.setCategory(category);
        filter.setPriority(priority);
        filter.setStartDate(startDate);
        filter.setEndDate(endDate);

        Page<TicketDto> tickets = ticketService.getTickets(filter, pageable);
        return ResponseEntity.ok(tickets);
    }

    /**
     * Get a specific ticket by ID.
     */
    @GetMapping("/{ticketId}")
    @Operation(
        summary = "Get ticket by ID",
        description = "Retrieve a specific support ticket by its ID"
    )
    // @PreAuthorize("hasRole('SUPPORT_AGENT')") // Disabled for development
    public ResponseEntity<TicketDto> getTicket(
            @Parameter(description = "Ticket ID") @PathVariable String ticketId) {
        
        TicketDto ticket = ticketService.getTicketById(ticketId);
        return ResponseEntity.ok(ticket);
    }

    /**
     * Update a ticket.
     */
    @PutMapping("/{ticketId}")
    @Operation(
        summary = "Update ticket",
        description = "Update an existing support ticket"
    )
    // @PreAuthorize("hasRole('SUPPORT_AGENT')") // Disabled for development
    public ResponseEntity<TicketDto> updateTicket(
            @Parameter(description = "Ticket ID") @PathVariable String ticketId,
            @Valid @RequestBody UpdateTicketDto updateDto) {
        
        String updatedBy = getAgentId();
        TicketDto ticket = ticketService.updateTicket(ticketId, updateDto, updatedBy);
        
        return ResponseEntity.ok(ticket);
    }

    /**
     * Escalate a ticket.
     */
    @PostMapping("/{ticketId}/escalate")
    @Operation(
        summary = "Escalate ticket",
        description = "Escalate a ticket to a higher level of support"
    )
    // @PreAuthorize("hasRole('SUPPORT_AGENT')") // Disabled for development
    public ResponseEntity<TicketDto> escalateTicket(
            @Parameter(description = "Ticket ID") @PathVariable String ticketId,
            @Valid @RequestBody EscalationDto escalationDto) {
        
        String escalatedBy = getAgentId();
        TicketDto ticket = ticketService.escalateTicket(ticketId, escalationDto, escalatedBy);
        
        return ResponseEntity.ok(ticket);
    }

    /**
     * Close a ticket.
     */
    @PostMapping("/{ticketId}/close")
    @Operation(
        summary = "Close ticket",
        description = "Close a support ticket"
    )
    // @PreAuthorize("hasRole('SUPPORT_AGENT')") // Disabled for development
    public ResponseEntity<TicketDto> closeTicket(
            @Parameter(description = "Ticket ID") @PathVariable String ticketId,
            @Parameter(description = "Closure reason") @RequestParam(required = false) String reason) {
        
        String closedBy = getAgentId();
        TicketDto ticket = ticketService.closeTicket(ticketId, closedBy, reason);
        
        return ResponseEntity.ok(ticket);
    }

    /**
     * Add satisfaction rating to a ticket.
     */
    @PostMapping("/{ticketId}/satisfaction")
    @Operation(
        summary = "Add satisfaction rating",
        description = "Add customer satisfaction rating to a resolved ticket"
    )
    public ResponseEntity<TicketDto> addSatisfactionRating(
            @Parameter(description = "Ticket ID") @PathVariable String ticketId,
            @Parameter(description = "Rating (1-5)") @RequestParam int rating,
            @Parameter(description = "Feedback") @RequestParam(required = false) String feedback) {
        
        TicketDto ticket = ticketService.addSatisfactionRating(ticketId, rating, feedback);
        return ResponseEntity.ok(ticket);
    }

    /**
     * Get tickets assigned to the current agent.
     */
    @GetMapping("/my-tickets")
    @Operation(
        summary = "Get my assigned tickets",
        description = "Get tickets assigned to the authenticated agent"
    )
    // @PreAuthorize("hasRole('SUPPORT_AGENT')") // Disabled for development
    public ResponseEntity<Page<TicketDto>> getMyTickets(
            @Parameter(description = "Page number") @RequestParam(defaultValue = "0") int page,
            @Parameter(description = "Page size") @RequestParam(defaultValue = "20") int size,
            @Parameter(description = "Filter by status") @RequestParam(required = false) List<TicketStatus> statuses) {
        
        Pageable pageable = PageRequest.of(page, size, Sort.by(Sort.Direction.DESC, "updatedAt"));
        String agentId = getAgentId();
        
        Page<TicketDto> tickets = ticketService.getAgentTickets(agentId, statuses, pageable);
        return ResponseEntity.ok(tickets);
    }

    /**
     * Search tickets by title or description.
     */
    @GetMapping("/search")
    @Operation(
        summary = "Search tickets",
        description = "Search tickets by title or description"
    )
    // @PreAuthorize("hasRole('SUPPORT_AGENT')") // Disabled for development
    public ResponseEntity<Page<TicketDto>> searchTickets(
            @Parameter(description = "Search term") @RequestParam String q,
            @Parameter(description = "Page number") @RequestParam(defaultValue = "0") int page,
            @Parameter(description = "Page size") @RequestParam(defaultValue = "20") int size) {
        
        // TODO: Implement search functionality
        // This would use the search repository method or Elasticsearch
        
        return ResponseEntity.ok(Page.empty());
    }

    /**
     * Get ticket statistics.
     */
    @GetMapping("/stats")
    @Operation(
        summary = "Get ticket statistics",
        description = "Get various statistics about support tickets"
    )
    // @PreAuthorize("hasRole('SUPPORT_AGENT')") // Disabled for development
    public ResponseEntity<TicketStatsDto> getTicketStats(
            @Parameter(description = "Start date") @RequestParam(required = false) LocalDateTime startDate,
            @Parameter(description = "End date") @RequestParam(required = false) LocalDateTime endDate) {
        
        // TODO: Implement ticket statistics
        TicketStatsDto stats = new TicketStatsDto();
        
        return ResponseEntity.ok(stats);
    }

    /**
     * Get available ticket categories.
     */
    @GetMapping("/categories")
    @Operation(
        summary = "Get ticket categories",
        description = "Get list of available ticket categories"
    )
    public ResponseEntity<List<TicketCategory>> getTicketCategories() {
        List<TicketCategory> categories = List.of(TicketCategory.values());
        return ResponseEntity.ok(categories);
    }

    /**
     * Get available ticket priorities.
     */
    @GetMapping("/priorities")
    @Operation(
        summary = "Get ticket priorities",
        description = "Get list of available ticket priorities"
    )
    public ResponseEntity<List<TicketPriority>> getTicketPriorities() {
        List<TicketPriority> priorities = List.of(TicketPriority.values());
        return ResponseEntity.ok(priorities);
    }

    /**
     * Get available ticket statuses.
     */
    @GetMapping("/statuses")
    @Operation(
        summary = "Get ticket statuses",
        description = "Get list of available ticket statuses"
    )
    public ResponseEntity<List<TicketStatus>> getTicketStatuses() {
        List<TicketStatus> statuses = List.of(TicketStatus.values());
        return ResponseEntity.ok(statuses);
    }

    // Private helper methods

    private String getAgentId() {
        // Placeholder agent identifier while authentication is disabled
        return "dev-agent-001";
    }

    /**
     * Get all agents - temporary endpoint for testing.
     */
    @GetMapping("/agents")
    @CrossOrigin(originPatterns = "*", allowCredentials = "false")
    public ResponseEntity<Map<String, Object>> getAllAgents() {
        Map<String, Object> response = new HashMap<>();
        response.put("message", "Agents endpoint is working via tickets controller");
        response.put("data", new Object[0]);
        return ResponseEntity.ok(response);
    }
}
