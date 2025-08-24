package com.alphintra.customersupport.repository;

import com.alphintra.customersupport.entity.Ticket;
import com.alphintra.customersupport.entity.TicketCategory;
import com.alphintra.customersupport.entity.TicketPriority;
import com.alphintra.customersupport.entity.TicketStatus;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;
import org.springframework.stereotype.Repository;

import java.time.LocalDateTime;
import java.util.List;
import java.util.Optional;
import java.util.UUID;

/**
 * Repository interface for managing Ticket entities.
 */
@Repository
public interface TicketRepository extends JpaRepository<Ticket, String> {

    /**
     * Find tickets by user ID with pagination.
     */
    Page<Ticket> findByUserId(UUID userId, Pageable pageable);

    /**
     * Find tickets assigned to a specific agent.
     */
    Page<Ticket> findByAssignedAgentId(String agentId, Pageable pageable);

    /**
     * Find tickets by status with pagination.
     */
    Page<Ticket> findByStatus(TicketStatus status, Pageable pageable);

    /**
     * Find tickets by multiple statuses.
     */
    Page<Ticket> findByStatusIn(List<TicketStatus> statuses, Pageable pageable);

    /**
     * Find tickets by category.
     */
    Page<Ticket> findByCategory(TicketCategory category, Pageable pageable);

    /**
     * Find tickets by priority.
     */
    Page<Ticket> findByPriority(TicketPriority priority, Pageable pageable);

    /**
     * Find unassigned tickets (no agent assigned).
     */
    @Query("SELECT t FROM Ticket t WHERE t.assignedAgentId IS NULL AND t.status = :status")
    List<Ticket> findUnassignedTickets(@Param("status") TicketStatus status);

    /**
     * Find tickets that need escalation (older than specified time and not resolved).
     */
    @Query("SELECT t FROM Ticket t WHERE t.createdAt < :threshold AND t.status NOT IN :excludedStatuses")
    List<Ticket> findTicketsNeedingEscalation(
        @Param("threshold") LocalDateTime threshold,
        @Param("excludedStatuses") List<TicketStatus> excludedStatuses
    );

    /**
     * Count tickets by status for an agent.
     */
    @Query("SELECT COUNT(t) FROM Ticket t WHERE t.assignedAgentId = :agentId AND t.status = :status")
    Long countByAssignedAgentIdAndStatus(@Param("agentId") String agentId, @Param("status") TicketStatus status);

    /**
     * Find tickets created between two dates.
     */
    List<Ticket> findByCreatedAtBetween(LocalDateTime startDate, LocalDateTime endDate);

    /**
     * Find resolved tickets between two dates.
     */
    @Query("SELECT t FROM Ticket t WHERE t.resolvedAt BETWEEN :startDate AND :endDate")
    List<Ticket> findResolvedTicketsBetween(
        @Param("startDate") LocalDateTime startDate,
        @Param("endDate") LocalDateTime endDate
    );

    /**
     * Find high priority open tickets.
     */
    @Query("SELECT t FROM Ticket t WHERE t.priority IN :priorities AND t.status NOT IN :closedStatuses ORDER BY t.priority DESC, t.createdAt ASC")
    List<Ticket> findHighPriorityOpenTickets(
        @Param("priorities") List<TicketPriority> priorities,
        @Param("closedStatuses") List<TicketStatus> closedStatuses
    );

    /**
     * Search tickets by title or description.
     */
    @Query("SELECT t FROM Ticket t WHERE LOWER(t.title) LIKE LOWER(CONCAT('%', :searchTerm, '%')) " +
           "OR LOWER(t.description) LIKE LOWER(CONCAT('%', :searchTerm, '%'))")
    Page<Ticket> searchTickets(@Param("searchTerm") String searchTerm, Pageable pageable);

    /**
     * Find tickets with specific tags.
     */
    @Query("SELECT DISTINCT t FROM Ticket t JOIN t.tags tag WHERE tag IN :tags")
    List<Ticket> findByTagsIn(@Param("tags") List<String> tags);

    /**
     * Get ticket statistics for agent performance.
     */
    @Query(value = "SELECT assigned_agent_id, COUNT(*), AVG(EXTRACT(EPOCH FROM (resolved_at - created_at))/3600) " +
           "FROM support_tickets WHERE resolved_at IS NOT NULL AND assigned_agent_id IS NOT NULL " +
           "GROUP BY assigned_agent_id", nativeQuery = true)
    List<Object[]> getAgentPerformanceStats();

    /**
     * Find tickets that haven't been updated for a specified time.
     */
    @Query("SELECT t FROM Ticket t WHERE t.updatedAt < :threshold AND t.status NOT IN :excludedStatuses")
    List<Ticket> findStaleTickets(
        @Param("threshold") LocalDateTime threshold,
        @Param("excludedStatuses") List<TicketStatus> excludedStatuses
    );

    /**
     * Find all tickets with pagination (fallback for complex filtering).
     */
    @Query("SELECT t FROM Ticket t ORDER BY t.createdAt DESC")
    Page<Ticket> findAllTicketsOrderByCreatedAtDesc(Pageable pageable);

    /**
     * Get daily ticket creation statistics.
     */
    @Query("SELECT DATE(t.createdAt), COUNT(t) FROM Ticket t " +
           "WHERE t.createdAt >= :startDate GROUP BY DATE(t.createdAt) ORDER BY DATE(t.createdAt)")
    List<Object[]> getDailyTicketStats(@Param("startDate") LocalDateTime startDate);

    /**
     * Get category distribution of tickets.
     */
    @Query("SELECT t.category, COUNT(t) FROM Ticket t GROUP BY t.category")
    List<Object[]> getCategoryDistribution();

    /**
     * Find tickets requiring satisfaction survey.
     */
    @Query("SELECT t FROM Ticket t WHERE t.status = 'RESOLVED' AND t.satisfactionRating IS NULL " +
           "AND t.resolvedAt < :threshold")
    List<Ticket> findTicketsNeedingSatisfactionSurvey(@Param("threshold") LocalDateTime threshold);

    /**
     * Find tickets by assigned agent and with satisfaction rating.
     */
    @Query("SELECT t FROM Ticket t WHERE t.assignedAgentId = :agentId AND t.satisfactionRating IS NOT NULL")
    List<Ticket> findByAssignedAgentIdAndSatisfactionRatingNotNull(@Param("agentId") String agentId);

    /**
     * Find tickets by assigned agent and status.
     */
    Page<Ticket> findByAssignedAgentIdAndStatusIn(String agentId, List<TicketStatus> statuses, Pageable pageable);
}