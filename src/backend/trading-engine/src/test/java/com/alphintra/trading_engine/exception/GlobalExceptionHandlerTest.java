package com.alphintra.trading_engine.exception;

import com.alphintra.trading_engine.dto.ErrorResponse;
import org.junit.jupiter.api.Test;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;

import static org.assertj.core.api.Assertions.assertThat;

class GlobalExceptionHandlerTest {

    private final GlobalExceptionHandler handler = new GlobalExceptionHandler();

    @Test
    void handleWalletServiceReturnsServiceUnavailable() {
        WalletServiceException exception = new WalletServiceException("Could not fetch Coinbase credentials from wallet service.");

        ResponseEntity<ErrorResponse> response = handler.handleWalletService(exception);

        assertThat(response.getStatusCode()).isEqualTo(HttpStatus.SERVICE_UNAVAILABLE);
        assertThat(response.getBody()).isNotNull();
        assertThat(response.getBody().error()).isEqualTo("WALLET_SERVICE_UNAVAILABLE");
        assertThat(response.getBody().message()).isEqualTo("Could not fetch Coinbase credentials from wallet service.");
        assertThat(response.getBody().currency()).isNull();
        assertThat(response.getBody().currentBalance()).isNull();
        assertThat(response.getBody().minimumRequired()).isNull();
    }
}
