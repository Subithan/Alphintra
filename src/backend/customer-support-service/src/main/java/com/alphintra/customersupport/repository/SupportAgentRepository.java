package com.alphintra.customersupport.repository;

import com.alphintra.customersupport.entity.AgentLevel;
import com.alphintra.customersupport.entity.AgentStatus;
import com.alphintra.customersupport.entity.SupportAgent;
import com.alphintra.customersupport.entity.TicketCategory;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;
import org.springframework.stereotype.Repository;

import java.time.LocalDateTime;
import java.util.List;
import java.util.Optional;

/**
 * Repository interface for managing SupportAgent entities.
 */
@Repository
public interface SupportAgentRepository extends JpaRepository<SupportAgent, String> {

    /**
     * Find agent by username.
     */
    Optional<SupportAgent> findByUsername(String username);

    /**
     * Find agent by email.
     */
    Optional<SupportAgent> findByEmail(String email);

    /**
     * Find agents by status.
     */
    List<SupportAgent> findByStatus(AgentStatus status);

    /**
     * Find agents by level.
     */
    List<SupportAgent> findByAgentLevel(AgentLevel agentLevel);

    /**
     * Find active agents by department.
     */
    List<SupportAgent> findByDepartmentAndIsActiveTrue(String department);

    /**
     * Find available agents who can take new tickets.
     */
    @Query("SELECT a FROM SupportAgent a WHERE a.status = 'AVAILABLE' AND a.isActive = true " +
           "AND a.currentTicketCount < a.maxConcurrentTickets")
    List<SupportAgent> findAvailableAgents();

    /**
     * Find agents with specific specialization.
     */
    @Query("SELECT a FROM SupportAgent a JOIN a.specializations s WHERE s = :specialization " +
           "AND a.isActive = true")
    List<SupportAgent> findAgentsWithSpecialization(@Param("specialization") TicketCategory specialization);

    /**
     * Find available agents with specific specialization.
     */
    @Query("SELECT a FROM SupportAgent a JOIN a.specializations s WHERE s = :specialization " +
           "AND a.status = 'AVAILABLE' AND a.isActive = true " +
           "AND a.currentTicketCount < a.maxConcurrentTickets " +
           "ORDER BY a.currentTicketCount ASC, a.customerSatisfactionRating DESC")
    List<SupportAgent> findAvailableAgentsWithSpecialization(@Param("specialization") TicketCategory specialization);

    /**
     * Find agents with lowest workload for load balancing.
     */
    @Query("SELECT a FROM SupportAgent a WHERE a.status IN ('AVAILABLE', 'BUSY') AND a.isActive = true " +
           "ORDER BY a.currentTicketCount ASC, a.averageResolutionTimeHours ASC")
    List<SupportAgent> findAgentsOrderedByWorkload();

    /**
     * Find agents who haven't been active recently.
     */
    @Query("SELECT a FROM SupportAgent a WHERE a.lastActivityAt < :threshold AND a.status != 'OFFLINE'")
    List<SupportAgent> findInactiveAgents(@Param("threshold") LocalDateTime threshold);

    /**
     * Get agent performance statistics.
     */
    @Query("SELECT a.agentId, a.totalTicketsHandled, a.averageResolutionTimeHours, " +
           "a.customerSatisfactionRating, a.currentTicketCount FROM SupportAgent a " +
           "WHERE a.isActive = true ORDER BY a.customerSatisfactionRating DESC")
    List<Object[]> getAgentPerformanceStats();

    /**
     * Find agents by level and status.
     */
    List<SupportAgent> findByAgentLevelAndStatus(AgentLevel agentLevel, AgentStatus status);

    /**
     * Count active agents by level.
     */
    @Query("SELECT COUNT(a) FROM SupportAgent a WHERE a.agentLevel = :level AND a.isActive = true")
    Long countActiveAgentsByLevel(@Param("level") AgentLevel level);

    /**
     * Find agents with high satisfaction rating.
     */
    @Query("SELECT a FROM SupportAgent a WHERE a.customerSatisfactionRating >= :minRating " +
           "AND a.isActive = true ORDER BY a.customerSatisfactionRating DESC")
    List<SupportAgent> findHighRatedAgents(@Param("minRating") Double minRating);

    /**
     * Find overloaded agents (exceeding workload threshold).
     */
    @Query("SELECT a FROM SupportAgent a WHERE a.currentTicketCount >= :threshold AND a.isActive = true")
    List<SupportAgent> findOverloadedAgents(@Param("threshold") Integer threshold);

    /**
     * Find agents available for escalation (higher levels).
     */
    @Query("SELECT a FROM SupportAgent a WHERE a.agentLevel IN :levels AND a.status = 'AVAILABLE' " +
           "AND a.isActive = true AND a.currentTicketCount < a.maxConcurrentTickets " +
           "ORDER BY a.agentLevel DESC, a.currentTicketCount ASC")
    List<SupportAgent> findAgentsForEscalation(@Param("levels") List<AgentLevel> levels);

    /**
     * Get workload distribution.
     */
    @Query("SELECT a.agentLevel, AVG(a.currentTicketCount), COUNT(a) FROM SupportAgent a " +
           "WHERE a.isActive = true GROUP BY a.agentLevel")
    List<Object[]> getWorkloadDistribution();

    /**
     * Find agents in specific timezone.
     */
    List<SupportAgent> findByTimezoneAndIsActiveTrue(String timezone);

    /**
     * Get team statistics by department.
     */
    @Query("SELECT a.department, COUNT(a), AVG(a.customerSatisfactionRating), " +
           "AVG(a.averageResolutionTimeHours) FROM SupportAgent a " +
           "WHERE a.isActive = true GROUP BY a.department")
    List<Object[]> getTeamStatsByDepartment();
}