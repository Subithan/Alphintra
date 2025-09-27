package com.alphintra.trading_engine.repository;

import com.alphintra.trading_engine.model.Position;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import java.util.List;
import java.util.Optional;

@Repository
public interface PositionRepository extends JpaRepository<Position, Long> {
    Optional<Position> findByUserIdAndAsset(Long userId, String asset);
    List<Position> findByUserId(Long userId);
}