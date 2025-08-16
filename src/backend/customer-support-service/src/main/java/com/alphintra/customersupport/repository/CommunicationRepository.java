package com.alphintra.customersupport.repository;

import com.alphintra.customersupport.entity.Communication;
import com.alphintra.customersupport.entity.CommunicationType;
import com.alphintra.customersupport.entity.SenderType;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;
import org.springframework.stereotype.Repository;

import java.time.LocalDateTime;
import java.util.List;

/**
 * Repository interface for managing Communication entities.
 */
@Repository
public interface CommunicationRepository extends JpaRepository<Communication, Long> {

    /**
     * Find communications by ticket ID ordered by creation time.
     */
    List<Communication> findByTicketTicketIdOrderByCreatedAtAsc(String ticketId);

    /**
     * Find communications by ticket ID with pagination.
     */
    Page<Communication> findByTicketTicketId(String ticketId, Pageable pageable);

    /**
     * Find non-internal communications for a ticket (visible to user).
     */
    List<Communication> findByTicketTicketIdAndIsInternalFalseOrderByCreatedAtAsc(String ticketId);

    /**
     * Find communications by sender.
     */
    List<Communication> findBySenderId(String senderId);

    /**
     * Find communications by sender type.
     */
    List<Communication> findBySenderType(SenderType senderType);

    /**
     * Find communications by type.
     */
    List<Communication> findByCommunicationType(CommunicationType communicationType);

    /**
     * Find unread communications for a specific recipient.
     */
    @Query("SELECT c FROM Communication c WHERE c.ticket.ticketId = :ticketId " +
           "AND c.readAt IS NULL AND c.senderType != :excludeSenderType")
    List<Communication> findUnreadCommunications(
        @Param("ticketId") String ticketId,
        @Param("excludeSenderType") SenderType excludeSenderType
    );

    /**
     * Find recent communications for agent activity tracking.
     */
    @Query("SELECT c FROM Communication c WHERE c.senderId = :agentId " +
           "AND c.senderType = 'AGENT' AND c.createdAt >= :since " +
           "ORDER BY c.createdAt DESC")
    List<Communication> findRecentAgentCommunications(
        @Param("agentId") String agentId,
        @Param("since") LocalDateTime since
    );

    /**
     * Count communications by ticket and sender type.
     */
    @Query("SELECT COUNT(c) FROM Communication c WHERE c.ticket.ticketId = :ticketId " +
           "AND c.senderType = :senderType")
    Long countByTicketAndSenderType(
        @Param("ticketId") String ticketId,
        @Param("senderType") SenderType senderType
    );

    /**
     * Find communications with attachments.
     */
    @Query("SELECT c FROM Communication c WHERE SIZE(c.attachments) > 0")
    List<Communication> findCommunicationsWithAttachments();

    /**
     * Find communications between two dates.
     */
    List<Communication> findByCreatedAtBetween(LocalDateTime startDate, LocalDateTime endDate);

    /**
     * Get communication statistics by type.
     */
    @Query("SELECT c.communicationType, COUNT(c) FROM Communication c " +
           "WHERE c.createdAt >= :since GROUP BY c.communicationType")
    List<Object[]> getCommunicationStatsByType(@Param("since") LocalDateTime since);

    /**
     * Find latest communication for each ticket.
     */
    @Query("SELECT c FROM Communication c WHERE c.createdAt = " +
           "(SELECT MAX(c2.createdAt) FROM Communication c2 WHERE c2.ticket.ticketId = c.ticket.ticketId)")
    List<Communication> findLatestCommunicationPerTicket();

    /**
     * Find phone call logs.
     */
    @Query("SELECT c FROM Communication c WHERE c.communicationType = 'PHONE_LOG' " +
           "AND c.phoneCallDuration IS NOT NULL ORDER BY c.createdAt DESC")
    List<Communication> findPhoneCallLogs();

    /**
     * Find video call recordings.
     */
    @Query("SELECT c FROM Communication c WHERE c.communicationType = 'VIDEO_CALL' " +
           "AND c.videoCallRecordingUrl IS NOT NULL ORDER BY c.createdAt DESC")
    List<Communication> findVideoCallRecordings();

    /**
     * Get response time statistics for agents.
     */
    @Query("SELECT c1.ticket.assignedAgentId, " +
           "AVG(EXTRACT(EPOCH FROM (c2.createdAt - c1.createdAt))/60) as avgResponseMinutes " +
           "FROM Communication c1 JOIN Communication c2 ON c1.ticket.ticketId = c2.ticket.ticketId " +
           "WHERE c1.senderType = 'USER' AND c2.senderType = 'AGENT' " +
           "AND c2.createdAt > c1.createdAt " +
           "AND c2.createdAt = (SELECT MIN(c3.createdAt) FROM Communication c3 " +
           "WHERE c3.ticket.ticketId = c1.ticket.ticketId AND c3.senderType = 'AGENT' " +
           "AND c3.createdAt > c1.createdAt) " +
           "GROUP BY c1.ticket.assignedAgentId")
    List<Object[]> getAgentResponseTimeStats();

    /**
     * Find communications that need follow-up.
     */
    @Query("SELECT c FROM Communication c WHERE c.communicationType = 'MESSAGE' " +
           "AND c.senderType = 'USER' AND c.createdAt < :threshold " +
           "AND NOT EXISTS (SELECT c2 FROM Communication c2 WHERE c2.ticket.ticketId = c.ticket.ticketId " +
           "AND c2.senderType = 'AGENT' AND c2.createdAt > c.createdAt)")
    List<Communication> findCommunicationsNeedingFollowUp(@Param("threshold") LocalDateTime threshold);

    /**
     * Search communications by content.
     */
    @Query("SELECT c FROM Communication c WHERE LOWER(c.content) LIKE LOWER(CONCAT('%', :searchTerm, '%'))")
    Page<Communication> searchByContent(@Param("searchTerm") String searchTerm, Pageable pageable);

    /**
     * Get daily communication volume.
     */
    @Query("SELECT DATE(c.createdAt), COUNT(c) FROM Communication c " +
           "WHERE c.createdAt >= :startDate GROUP BY DATE(c.createdAt) ORDER BY DATE(c.createdAt)")
    List<Object[]> getDailyCommunicationVolume(@Param("startDate") LocalDateTime startDate);
}