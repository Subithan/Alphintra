package com.alphintra.trading_engine.controller;

import com.alphintra.trading_engine.model.Position;
import com.alphintra.trading_engine.model.PositionStatus;
import com.alphintra.trading_engine.repository.PositionRepository;
import lombok.RequiredArgsConstructor;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.List;

@RestController
@RequestMapping("/api/trading/positions")
@RequiredArgsConstructor
public class PositionController {

    private final PositionRepository positionRepository;

    /**
     * Get all open positions for a user
     */
    @GetMapping
    public ResponseEntity<List<Position>> getAllPositions(
            @RequestParam(required = false) Long userId,
            @RequestParam(required = false) String status) {
        
        if (userId != null && status != null) {
            PositionStatus positionStatus = PositionStatus.valueOf(status.toUpperCase());
            return ResponseEntity.ok(positionRepository.findByUserIdAndStatus(userId, positionStatus));
        } else if (userId != null) {
            return ResponseEntity.ok(positionRepository.findByUserId(userId));
        } else if (status != null) {
            PositionStatus positionStatus = PositionStatus.valueOf(status.toUpperCase());
            return ResponseEntity.ok(positionRepository.findByStatus(positionStatus));
        }
        
        return ResponseEntity.ok(positionRepository.findAll());
    }

    /**
     * Get open positions for a specific user
     */
    @GetMapping("/open")
    public ResponseEntity<List<Position>> getOpenPositions(@RequestParam Long userId) {
        List<Position> positions = positionRepository.findByUserIdAndStatus(userId, PositionStatus.OPEN);
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
