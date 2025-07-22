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
}