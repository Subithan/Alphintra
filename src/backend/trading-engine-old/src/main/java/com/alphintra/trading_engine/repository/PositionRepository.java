package com.alphintra.trading_engine.repository;

import com.alphintra.trading_engine.model.Position;
import com.alphintra.trading_engine.model.PositionStatus;
import org.springframework.data.jpa.repository.JpaRepository;
import java.util.Optional;

public interface PositionRepository extends JpaRepository<Position, Long> {

    // This one is used to check if we are currently IN a trade
    Optional<Position> findByUserIdAndSymbolAndStatus(Long userId, String symbol, PositionStatus status);

    // --- NEW METHOD ---
    // This one is used to find the record to reuse, regardless of its status
    Optional<Position> findFirstByUserIdAndSymbol(Long userId, String symbol);
}

