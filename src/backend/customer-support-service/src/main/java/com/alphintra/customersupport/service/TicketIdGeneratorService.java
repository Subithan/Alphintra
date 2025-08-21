package com.alphintra.customersupport.service;

import org.springframework.stereotype.Service;

import java.time.LocalDateTime;
import java.time.format.DateTimeFormatter;
import java.util.concurrent.atomic.AtomicLong;

/**
 * Service for generating unique ticket IDs.
 */
@Service
public class TicketIdGeneratorService {

    private static final String PREFIX = "TKT";
    private static final DateTimeFormatter DATE_FORMAT = DateTimeFormatter.ofPattern("yyyyMMdd");
    private final AtomicLong counter = new AtomicLong(1);

    /**
     * Generate a unique ticket ID.
     * Format: TKT-YYYYMMDD-NNNN
     * Example: TKT-20241201-0001
     */
    public String generateTicketId() {
        String date = LocalDateTime.now().format(DATE_FORMAT);
        long ticketNumber = counter.getAndIncrement();
        
        return String.format("%s-%s-%04d", PREFIX, date, ticketNumber);
    }

    /**
     * Reset the counter (mainly for testing purposes).
     */
    public void resetCounter() {
        counter.set(1);
    }
}