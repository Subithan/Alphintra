package com.alphintra.trading_engine.repository;

import com.alphintra.trading_engine.model.UserBalance;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import java.util.List;
import java.util.Optional;

@Repository
public interface UserBalanceRepository extends JpaRepository<UserBalance, Long> {
    
    /**
     * Find all balances for a specific user
     */
    List<UserBalance> findByUserId(Long userId);
    
    /**
     * Find a specific balance for a user and asset
     */
    Optional<UserBalance> findByUserIdAndAsset(Long userId, String asset);
}
