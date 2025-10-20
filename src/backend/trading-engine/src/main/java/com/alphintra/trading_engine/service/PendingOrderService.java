package com.alphintra.trading_engine.service;

import com.alphintra.trading_engine.model.*;
import com.alphintra.trading_engine.repository.PendingOrderRepository;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.math.BigDecimal;
import java.math.RoundingMode;
import java.time.LocalDateTime;
import java.util.List;

@Service
@RequiredArgsConstructor
public class PendingOrderService {

    private final PendingOrderRepository pendingOrderRepository;

    // Strategy configuration - can be moved to database later
    private static final BigDecimal TAKE_PROFIT_PERCENTAGE = new BigDecimal("1.03"); // 3% profit
    private static final BigDecimal STOP_LOSS_PERCENTAGE = new BigDecimal("0.98");   // 2% loss

    /**
     * Creates pending order (take-profit and stop-loss) for a newly opened position
     * Now creates ONE row with both prices instead of two separate rows
     */
    @Transactional
    public void createPendingOrdersForPosition(Position position, BigDecimal entryPrice) {
        System.out.println("📝 Creating pending order for position ID: " + position.getId());

        // Calculate trigger prices
        BigDecimal takeProfitPrice = entryPrice.multiply(TAKE_PROFIT_PERCENTAGE)
                .setScale(8, RoundingMode.HALF_UP);
        BigDecimal stopLossPrice = entryPrice.multiply(STOP_LOSS_PERCENTAGE)
                .setScale(8, RoundingMode.HALF_UP);

        // Create ONE pending order with both take-profit and stop-loss prices
        PendingOrder pendingOrder = new PendingOrder();
        pendingOrder.setUserId(position.getUserId());
        pendingOrder.setPositionId(position.getId());
        pendingOrder.setTakeProfitPrice(takeProfitPrice);
        pendingOrder.setStopLossPrice(stopLossPrice);
        pendingOrder.setQuantity(position.getQuantity());
        pendingOrder.setSymbol(position.getSymbol());
        pendingOrder.setStatus(PendingOrderStatus.PENDING);
        pendingOrderRepository.save(pendingOrder);

        System.out.println("   ✅ Pending order created:");
        System.out.println("      TAKE_PROFIT: " + takeProfitPrice + " (+" + 
                           entryPrice.multiply(new BigDecimal("0.03")).setScale(2, RoundingMode.HALF_UP) + ")");
        System.out.println("      STOP_LOSS: " + stopLossPrice + " (-" + 
                           entryPrice.multiply(new BigDecimal("0.02")).setScale(2, RoundingMode.HALF_UP) + ")");
    }

    /**
     * Retrieves all pending orders for monitoring
     */
    public List<PendingOrder> getAllPendingOrders() {
        return pendingOrderRepository.findByStatus(PendingOrderStatus.PENDING);
    }

    /**
     * Retrieves pending orders for a specific symbol
     */
    public List<PendingOrder> getPendingOrdersBySymbol(String symbol) {
        return pendingOrderRepository.findBySymbolAndStatus(symbol, PendingOrderStatus.PENDING);
    }

    /**
     * Marks a pending order as triggered with the trigger type
     */
    @Transactional
    public void markAsTriggered(PendingOrder order, String triggerType) {
        order.setStatus(PendingOrderStatus.TRIGGERED);
        order.setTriggeredAt(LocalDateTime.now());
        order.setTriggeredType(triggerType); // "TAKE_PROFIT" or "STOP_LOSS"
        pendingOrderRepository.save(order);
        System.out.println("   🎯 Pending order #" + order.getId() + " marked as TRIGGERED (" + triggerType + ")");
    }

    /**
     * Cancels other pending orders for the same position (OCO logic)
     * Since we now have ONE row per position, this method is no longer needed
     * but keeping it for compatibility
     */
    @Transactional
    public void cancelOtherPendingOrders(Long positionId, Long triggeredOrderId) {
        // No longer needed since we have one row with both prices
        // The order is marked as triggered with the specific type (TAKE_PROFIT or STOP_LOSS)
        System.out.println("   ✅ Order triggered - no other orders to cancel (single row design)");
    }
}
