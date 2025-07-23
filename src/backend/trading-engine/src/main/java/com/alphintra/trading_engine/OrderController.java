package com.alphintra.trading_engine;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.List;
import java.util.UUID;

@RestController
@RequestMapping("/api/orders")
public class OrderController {

    @Autowired
    private OrderService orderService;

    @PostMapping
    public ResponseEntity<OrderResponse> createOrder(@RequestBody OrderRequest request) {
        OrderResponse response = orderService.createOrder(request);
        return ResponseEntity.ok(response);
    }

    @GetMapping("/{orderUuid}")
    public ResponseEntity<OrderResponse> getOrder(@PathVariable UUID orderUuid) {
        OrderResponse response = orderService.getOrder(orderUuid);
        return ResponseEntity.ok(response);
    }

    @GetMapping("/history")
    public ResponseEntity<List<TradeResponse>> getTradeHistory() {
        List<TradeResponse> response = orderService.getTradeHistory();
        return ResponseEntity.ok(response);
    }

    @GetMapping
    public ResponseEntity<List<OrderResponse>> getOrders(@RequestParam(required = false) String status) {
        // For now, return all orders or filter by status if implemented in OrderService
        List<Order> orders = orderService.getAllOrders(); // Add this method to OrderService
        List<OrderResponse> responses = orders.stream()
                .filter(o -> status == null || o.getStatus().equalsIgnoreCase(status))
                .map(orderService::mapToResponse)
                .toList();
        return ResponseEntity.ok(responses);
    }
}