package com.alphintra.customersupport.exception;

/**
 * Exception thrown when ticket escalation fails.
 */
public class EscalationException extends RuntimeException {

    public EscalationException(String message) {
        super(message);
    }

    public EscalationException(String message, Throwable cause) {
        super(message, cause);
    }
}