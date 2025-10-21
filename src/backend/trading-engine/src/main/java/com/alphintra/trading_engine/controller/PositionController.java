package com.alphintra.trading_engine.controller;

import com.alphintra.trading_engine.dto.PositionWithPnLDTO;
import com.alphintra.trading_engine.model.Position;
import com.alphintra.trading_engine.model.PositionStatus;
import com.alphintra.trading_engine.repository.PositionRepository;
import com.alphintra.trading_engine.service.PositionService;
import lombok.RequiredArgsConstructor;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.List;

@RestController
@RequestMapping("/api/trading/positions")
@RequiredArgsConstructor
public class PositionController {

    private final PositionRepository positionRepository;
    private final PositionService positionService;

    /**
     * Get all positions with real-time PNL calculation
     */
    @GetMapping
    public ResponseEntity<List<PositionWithPnLDTO>> getAllPositions(
            @RequestParam(required = false) Long userId,
            @RequestParam(required = false) String status) {
        
        PositionStatus positionStatus = status != null ? PositionStatus.valueOf(status.toUpperCase()) : null;
        List<PositionWithPnLDTO> positions = positionService.getPositionsWithPnL(userId, positionStatus);
        
        return ResponseEntity.ok(positions);
    }

    /**
     * Get open positions with real-time PNL for a specific user
     */
    @GetMapping("/open")
    public ResponseEntity<List<PositionWithPnLDTO>> getOpenPositions(@RequestParam Long userId) {
        List<PositionWithPnLDTO> positions = positionService.getPositionsWithPnL(userId, PositionStatus.OPEN);
        return ResponseEntity.ok(positions);
    }

    /**
     * Get a specific position by ID
     */
    @GetMapping("/{id}")
    public ResponseEntity<Position> getPosition(@PathVariable Long id) {
        return positionRepository.findById(id)
                .map(ResponseEntity::ok)
                .orElse(ResponseEntity.notFound().build());
    }
}
