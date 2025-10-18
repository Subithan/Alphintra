package com.alphintra.trading_engine.exception;

import com.alphintra.trading_engine.dto.ErrorResponse;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.ExceptionHandler;
import org.springframework.web.bind.annotation.RestControllerAdvice;

@RestControllerAdvice
public class GlobalExceptionHandler {

    @ExceptionHandler(InsufficientBalanceException.class)
    public ResponseEntity<ErrorResponse> handleInsufficientBalance(InsufficientBalanceException ex) {
        System.err.println("❌ INSUFFICIENT BALANCE ERROR: " + ex.getMessage());
        
        ErrorResponse error = new ErrorResponse(
            "INSUFFICIENT_BALANCE",
            ex.getMessage(),
            ex.getCurrency(),
            ex.getCurrentBalance(),
            ex.getMinimumRequired()
        );
        
        return ResponseEntity
            .status(HttpStatus.BAD_REQUEST)
            .body(error);
    }
}
