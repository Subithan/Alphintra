package com.alphintra.customersupport.service;

import com.alphintra.customersupport.dto.CreateTicketDto;
import com.alphintra.customersupport.dto.TicketDto;
import com.alphintra.customersupport.entity.*;
import com.alphintra.customersupport.repository.SupportAgentRepository;
import com.alphintra.customersupport.repository.TicketRepository;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;

import java.util.Optional;

import static org.junit.jupiter.api.Assertions.*;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.*;

/**
 * Unit tests for TicketService.
 */
@ExtendWith(MockitoExtension.class)
class TicketServiceTest {

    @Mock
    private TicketRepository ticketRepository;

    @Mock
    private SupportAgentRepository supportAgentRepository;

    @Mock
    private TicketIdGeneratorService ticketIdGeneratorService;

    @Mock
    private SmartTicketRoutingService smartTicketRoutingService;

    @Mock
    private NotificationService notificationService;

    @Mock
    private AuditService auditService;

    @InjectMocks
    private TicketService ticketService;

    private CreateTicketDto createTicketDto;
    private Ticket mockTicket;
    private SupportAgent mockAgent;

    @BeforeEach
    void setUp() {
        // Setup test data
        String userId = "user-12345";
        createTicketDto = new CreateTicketDto();
        createTicketDto.setUserId(userId);
        createTicketDto.setTitle("Test Ticket");
        createTicketDto.setDescription("This is a test ticket description");
        createTicketDto.setCategory(TicketCategory.TECHNICAL);

        mockTicket = new Ticket(
            "TKT-20241201-0001",
            userId,
            "user@example.com",
            "Test Ticket",
            "This is a test ticket description",
            TicketCategory.TECHNICAL,
            TicketPriority.MEDIUM
        );

        mockAgent = new SupportAgent(
            "agent-001",
            "test-agent",
            "agent@test.com",
            "Test",
            "Agent",
            AgentLevel.L2
        );
    }

    @Test
    void createTicket_ShouldCreateTicketSuccessfully() {
        // Arrange
        when(ticketIdGeneratorService.generateTicketId()).thenReturn("TKT-20241201-0001");
        when(smartTicketRoutingService.findBestAgent(any(Ticket.class))).thenReturn(Optional.of(mockAgent));
        when(ticketRepository.save(any(Ticket.class))).thenReturn(mockTicket);
        when(supportAgentRepository.save(any(SupportAgent.class))).thenReturn(mockAgent);

        // Act
        TicketDto result = ticketService.createTicket(createTicketDto, "test-creator");

        // Assert
        assertNotNull(result);
        assertEquals("TKT-20241201-0001", result.getTicketId());
        assertEquals("Test Ticket", result.getTitle());
        assertEquals(TicketCategory.TECHNICAL, result.getCategory());
        assertEquals(TicketStatus.ASSIGNED, result.getStatus());

        // Verify interactions
        verify(ticketIdGeneratorService).generateTicketId();
        verify(smartTicketRoutingService).findBestAgent(any(Ticket.class));
        verify(ticketRepository).save(any(Ticket.class));
        verify(supportAgentRepository).save(any(SupportAgent.class));
        verify(auditService).logTicketCreation(anyString(), anyString(), anyString());
        verify(notificationService).sendTicketCreatedNotification(any(Ticket.class));
        verify(notificationService).sendTicketAssignedNotification(any(Ticket.class), any(SupportAgent.class));
    }

    @Test
    void createTicket_WhenNoAgentAvailable_ShouldCreateUnassignedTicket() {
        // Arrange
        when(ticketIdGeneratorService.generateTicketId()).thenReturn("TKT-20241201-0002");
        when(smartTicketRoutingService.findBestAgent(any(Ticket.class))).thenReturn(Optional.empty());
        
        Ticket unassignedTicket = new Ticket(
            "TKT-20241201-0002",
            createTicketDto.getUserId(),
            "user@example.com",
            createTicketDto.getTitle(),
            createTicketDto.getDescription(),
            createTicketDto.getCategory(),
            TicketPriority.MEDIUM
        );
        unassignedTicket.setStatus(TicketStatus.NEW);
        
        when(ticketRepository.save(any(Ticket.class))).thenReturn(unassignedTicket);

        // Act
        TicketDto result = ticketService.createTicket(createTicketDto, "test-creator");

        // Assert
        assertNotNull(result);
        assertEquals("TKT-20241201-0002", result.getTicketId());
        assertEquals(TicketStatus.NEW, result.getStatus());
        assertNull(result.getAssignedAgentId());

        // Verify no agent assignment notifications
        verify(notificationService, never()).sendTicketAssignedNotification(any(Ticket.class), any(SupportAgent.class));
    }

    @Test
    void createTicket_ShouldDeterminePriorityAutomatically() {
        // Arrange
        createTicketDto.setPriority(null); // No priority specified
        createTicketDto.setDescription("URGENT: System is down and not working");
        
        when(ticketIdGeneratorService.generateTicketId()).thenReturn("TKT-20241201-0003");
        when(smartTicketRoutingService.findBestAgent(any(Ticket.class))).thenReturn(Optional.empty());
        when(ticketRepository.save(any(Ticket.class))).thenAnswer(invocation -> {
            Ticket ticket = invocation.getArgument(0);
            return ticket;
        });

        // Act
        TicketDto result = ticketService.createTicket(createTicketDto, "test-creator");

        // Assert
        assertNotNull(result);
        // The priority should be determined automatically based on keywords
        verify(ticketRepository).save(argThat(ticket -> 
            ticket.getPriority() == TicketPriority.URGENT || 
            ticket.getPriority() == TicketPriority.HIGH
        ));
    }

    @Test
    void getTicketById_ShouldReturnTicketWhenExists() {
        // Arrange
        String ticketId = "TKT-20241201-0001";
        when(ticketRepository.findById(ticketId)).thenReturn(Optional.of(mockTicket));

        // Act
        TicketDto result = ticketService.getTicketById(ticketId);

        // Assert
        assertNotNull(result);
        assertEquals(ticketId, result.getTicketId());
        assertEquals("Test Ticket", result.getTitle());
    }

    @Test
    void getTicketById_ShouldThrowExceptionWhenNotFound() {
        // Arrange
        String ticketId = "TKT-NONEXISTENT";
        when(ticketRepository.findById(ticketId)).thenReturn(Optional.empty());

        // Act & Assert
        assertThrows(RuntimeException.class, () -> ticketService.getTicketById(ticketId));
    }

    @Test
    void addSatisfactionRating_ShouldUpdateTicketAndAgentRating() {
        // Arrange
        String ticketId = "TKT-20241201-0001";
        int rating = 5;
        String feedback = "Excellent service!";
        
        mockTicket.setAssignedAgentId("agent-001");
        when(ticketRepository.findById(ticketId)).thenReturn(Optional.of(mockTicket));
        when(ticketRepository.save(any(Ticket.class))).thenReturn(mockTicket);
        when(ticketRepository.findByAssignedAgentIdAndSatisfactionRatingNotNull("agent-001"))
            .thenReturn(java.util.List.of(mockTicket));
        when(supportAgentRepository.findById("agent-001")).thenReturn(Optional.of(mockAgent));

        // Act
        TicketDto result = ticketService.addSatisfactionRating(ticketId, rating, feedback);

        // Assert
        assertNotNull(result);
        verify(ticketRepository).save(argThat(ticket -> 
            ticket.getSatisfactionRating() == 5 && 
            "Excellent service!".equals(ticket.getSatisfactionFeedback())
        ));
        verify(supportAgentRepository).save(any(SupportAgent.class));
    }

    @Test
    void addSatisfactionRating_ShouldThrowExceptionForInvalidRating() {
        // Arrange
        String ticketId = "TKT-20241201-0001";
        int invalidRating = 6; // Rating should be 1-5

        // Act & Assert
        assertThrows(IllegalArgumentException.class, 
            () -> ticketService.addSatisfactionRating(ticketId, invalidRating, "feedback"));
    }
}