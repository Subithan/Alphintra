package com.alphintra.trading_engine.controller;

import com.alphintra.trading_engine.model.PendingOrder;
import com.alphintra.trading_engine.model.PendingOrderStatus;
import com.alphintra.trading_engine.repository.PendingOrderRepository;
import lombok.RequiredArgsConstructor;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.List;

@RestController
@RequestMapping("/api/trading/pending-orders")
@RequiredArgsConstructor
public class PendingOrderController {

    private final PendingOrderRepository pendingOrderRepository;

    /**
     * Get all pending orders
     */
    @GetMapping
    public ResponseEntity<List<PendingOrder>> getAllPendingOrders(
            @RequestParam(required = false) Long userId,
            @RequestParam(required = false) String status,
            @RequestParam(required = false) String symbol) {
        
        // Filter by userId and status
        if (userId != null && status != null) {
            PendingOrderStatus orderStatus = PendingOrderStatus.valueOf(status.toUpperCase());
            return ResponseEntity.ok(pendingOrderRepository.findByUserIdAndStatus(userId, orderStatus));
        }
        // Filter by userId only
        else if (userId != null) {
            return ResponseEntity.ok(pendingOrderRepository.findByUserId(userId));
        }
        // Filter by status and symbol
        else if (status != null && symbol != null) {
            PendingOrderStatus orderStatus = PendingOrderStatus.valueOf(status.toUpperCase());
            return ResponseEntity.ok(pendingOrderRepository.findBySymbolAndStatus(symbol, orderStatus));
        }
        // Filter by status only
        else if (status != null) {
            PendingOrderStatus orderStatus = PendingOrderStatus.valueOf(status.toUpperCase());
            return ResponseEntity.ok(pendingOrderRepository.findByStatus(orderStatus));
        }
        // Filter by symbol only
        else if (symbol != null) {
            return ResponseEntity.ok(pendingOrderRepository.findBySymbol(symbol));
        }
        
        return ResponseEntity.ok(pendingOrderRepository.findAll());
    }

    /**
     * Get pending orders for a specific position
     */
    @GetMapping("/position/{positionId}")
    public ResponseEntity<List<PendingOrder>> getPendingOrdersByPosition(@PathVariable Long positionId) {
        List<PendingOrder> orders = pendingOrderRepository.findByPositionId(positionId);
        return ResponseEntity.ok(orders);
    }

    /**
     * Get a specific pending order by ID
     */
    @GetMapping("/{id}")
    public ResponseEntity<PendingOrder> getPendingOrder(@PathVariable Long id) {
        return pendingOrderRepository.findById(id)
                .map(ResponseEntity::ok)
                .orElse(ResponseEntity.notFound().build());
    }
}
