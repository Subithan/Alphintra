package com.alphintra.trading_engine.repository;

import com.alphintra.trading_engine.model.PendingOrder;
import com.alphintra.trading_engine.model.PendingOrderStatus;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import java.util.List;

@Repository
public interface PendingOrderRepository extends JpaRepository<PendingOrder, Long> {
    
    List<PendingOrder> findByPositionIdAndStatus(Long positionId, PendingOrderStatus status);
    
    List<PendingOrder> findByStatus(PendingOrderStatus status);
    
    List<PendingOrder> findBySymbolAndStatus(String symbol, PendingOrderStatus status);
}
