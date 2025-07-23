package com.alphintra.trading_engine;

import org.springframework.data.jpa.repository.JpaRepository;

public interface AssetBalanceRepository extends JpaRepository<AssetBalance, Long> {
    AssetBalance findByAccountAccountIdAndAsset(Long accountId, String asset);
}