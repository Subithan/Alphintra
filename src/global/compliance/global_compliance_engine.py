"""
Global Compliance Engine
Alphintra Trading Platform - Phase 5

Manages regulatory compliance across multiple jurisdictions with real-time monitoring,
automated reporting, and intelligent compliance adaptation.
"""

import asyncio
import logging
from typing import Dict, List, Optional, Tuple, Any, Union
from dataclasses import dataclass, asdict
from enum import Enum
import json
import time
import uuid
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
from concurrent.futures import ThreadPoolExecutor

# Regulatory frameworks
import aiohttp
import aioredis
import asyncpg

# Monitoring
from prometheus_client import Counter, Gauge, Histogram

logger = logging.getLogger(__name__)


class Jurisdiction(Enum):
    """Regulatory jurisdictions"""
    US = "US"
    EU = "EU"
    UK = "UK"
    JAPAN = "JAPAN"
    SINGAPORE = "SINGAPORE"
    HONG_KONG = "HONG_KONG"
    CANADA = "CANADA"
    AUSTRALIA = "AUSTRALIA"


class RegulatoryFramework(Enum):
    """Regulatory frameworks"""
    SEC = "SEC"           # US Securities and Exchange Commission
    CFTC = "CFTC"         # US Commodity Futures Trading Commission
    FINRA = "FINRA"       # Financial Industry Regulatory Authority
    ESMA = "ESMA"         # European Securities and Markets Authority
    MIFID_II = "MIFID_II" # Markets in Financial Instruments Directive
    EMIR = "EMIR"         # European Market Infrastructure Regulation
    FCA = "FCA"           # UK Financial Conduct Authority
    PRA = "PRA"           # UK Prudential Regulation Authority
    JFSA = "JFSA"         # Japan Financial Services Agency
    MAS = "MAS"           # Monetary Authority of Singapore
    SFC = "SFC"           # Securities and Futures Commission (Hong Kong)
    IIROC = "IIROC"       # Investment Industry Regulatory Organization of Canada
    ASIC = "ASIC"         # Australian Securities and Investments Commission


class ComplianceRuleType(Enum):
    """Types of compliance rules"""
    POSITION_LIMITS = "position_limits"
    RISK_LIMITS = "risk_limits"
    REPORTING = "reporting"
    BEST_EXECUTION = "best_execution"
    MARKET_MAKING = "market_making"
    ALGO_TRADING = "algo_trading"
    DATA_PROTECTION = "data_protection"
    ANTI_MONEY_LAUNDERING = "anti_money_laundering"
    KNOW_YOUR_CUSTOMER = "know_your_customer"
    TRADE_SURVEILLANCE = "trade_surveillance"


class ViolationSeverity(Enum):
    """Compliance violation severity levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class ComplianceRule:
    """Compliance rule definition"""
    rule_id: str
    jurisdiction: Jurisdiction
    framework: RegulatoryFramework
    rule_type: ComplianceRuleType
    description: str
    parameters: Dict[str, Any]
    effective_date: datetime
    expiry_date: Optional[datetime]
    is_active: bool
    created_at: datetime
    updated_at: datetime


@dataclass
class TradeComplianceCheck:
    """Trade compliance check result"""
    check_id: str
    trade_id: str
    rule_id: str
    jurisdiction: Jurisdiction
    framework: RegulatoryFramework
    is_compliant: bool
    violation_details: Optional[str]
    severity: Optional[ViolationSeverity]
    timestamp: datetime
    remediation_required: bool
    remediation_steps: List[str]


@dataclass
class ComplianceReport:
    """Compliance report data structure"""
    report_id: str
    jurisdiction: Jurisdiction
    framework: RegulatoryFramework
    report_type: str
    reporting_period_start: datetime
    reporting_period_end: datetime
    data: Dict[str, Any]
    generated_at: datetime
    submitted_at: Optional[datetime]
    submission_reference: Optional[str]
    status: str


@dataclass
class RegulatoryUpdate:
    """Regulatory framework update"""
    update_id: str
    jurisdiction: Jurisdiction
    framework: RegulatoryFramework
    update_type: str
    title: str
    description: str
    effective_date: datetime
    impact_assessment: str
    implementation_required: bool
    created_at: datetime


class RegulatoryDataProvider:
    """
    Provides real-time regulatory data and updates from multiple sources
    """
    
    def __init__(self):
        self.data_sources = {
            'sec': 'https://www.sec.gov/files/rules/',
            'cftc': 'https://www.cftc.gov/LawRegulation/',
            'esma': 'https://www.esma.europa.eu/policy-rules/',
            'fca': 'https://www.fca.org.uk/publications/',
            'jfsa': 'https://www.fsa.go.jp/en/',
            'mas': 'https://www.mas.gov.sg/regulation/',
            'regulatory_news': 'https://api.regulatorynews.com/v1/'
        }
        
        self.update_cache = {}
        self.cache_duration = timedelta(hours=1)
        
        # Metrics
        self.regulatory_updates = Counter('regulatory_updates_total', 'Regulatory updates', ['jurisdiction', 'framework'])
        self.compliance_checks = Counter('compliance_checks_total', 'Compliance checks', ['jurisdiction', 'result'])
        
    async def get_regulatory_updates(self, jurisdiction: Jurisdiction = None) -> List[RegulatoryUpdate]:
        """Get latest regulatory updates"""
        try:
            updates = []
            
            # Check cache first
            cache_key = f"updates_{jurisdiction.value if jurisdiction else 'all'}"
            if cache_key in self.update_cache:
                cached_data, cache_time = self.update_cache[cache_key]
                if datetime.now() - cache_time < self.cache_duration:
                    return cached_data
            
            # Fetch updates from various sources
            if jurisdiction == Jurisdiction.US or jurisdiction is None:
                sec_updates = await self._fetch_sec_updates()
                updates.extend(sec_updates)
                
                cftc_updates = await self._fetch_cftc_updates()
                updates.extend(cftc_updates)
            
            if jurisdiction == Jurisdiction.EU or jurisdiction is None:
                esma_updates = await self._fetch_esma_updates()
                updates.extend(esma_updates)
            
            if jurisdiction == Jurisdiction.UK or jurisdiction is None:
                fca_updates = await self._fetch_fca_updates()
                updates.extend(fca_updates)
            
            # Cache results
            self.update_cache[cache_key] = (updates, datetime.now())
            
            # Update metrics
            for update in updates:
                self.regulatory_updates.labels(
                    jurisdiction=update.jurisdiction.value,
                    framework=update.framework.value
                ).inc()
            
            return updates
            
        except Exception as e:
            logger.error(f"Error getting regulatory updates: {str(e)}")
            return []
    
    async def _fetch_sec_updates(self) -> List[RegulatoryUpdate]:
        """Fetch SEC regulatory updates"""
        try:
            # Mock implementation - would integrate with actual SEC APIs/feeds
            updates = [
                RegulatoryUpdate(
                    update_id=str(uuid.uuid4()),
                    jurisdiction=Jurisdiction.US,
                    framework=RegulatoryFramework.SEC,
                    update_type="rule_proposal",
                    title="Enhanced Risk Management for Algorithmic Trading",
                    description="Proposed amendments to risk management requirements for algorithmic trading systems",
                    effective_date=datetime.now() + timedelta(days=90),
                    impact_assessment="Medium - requires system updates for risk controls",
                    implementation_required=True,
                    created_at=datetime.now()
                )
            ]
            return updates
            
        except Exception as e:
            logger.error(f"Error fetching SEC updates: {str(e)}")
            return []
    
    async def _fetch_cftc_updates(self) -> List[RegulatoryUpdate]:
        """Fetch CFTC regulatory updates"""
        try:
            # Mock implementation
            updates = [
                RegulatoryUpdate(
                    update_id=str(uuid.uuid4()),
                    jurisdiction=Jurisdiction.US,
                    framework=RegulatoryFramework.CFTC,
                    update_type="guidance",
                    title="Margin Requirements for Uncleared Swaps",
                    description="Updated guidance on margin requirements for uncleared derivatives",
                    effective_date=datetime.now() + timedelta(days=60),
                    impact_assessment="High - affects derivatives trading operations",
                    implementation_required=True,
                    created_at=datetime.now()
                )
            ]
            return updates
            
        except Exception as e:
            logger.error(f"Error fetching CFTC updates: {str(e)}")
            return []
    
    async def _fetch_esma_updates(self) -> List[RegulatoryUpdate]:
        """Fetch ESMA regulatory updates"""
        try:
            # Mock implementation
            updates = [
                RegulatoryUpdate(
                    update_id=str(uuid.uuid4()),
                    jurisdiction=Jurisdiction.EU,
                    framework=RegulatoryFramework.MIFID_II,
                    update_type="technical_standard",
                    title="Transaction Reporting Updates for MiFID II",
                    description="Technical standards for transaction reporting under MiFID II",
                    effective_date=datetime.now() + timedelta(days=120),
                    impact_assessment="Medium - updates to reporting systems required",
                    implementation_required=True,
                    created_at=datetime.now()
                )
            ]
            return updates
            
        except Exception as e:
            logger.error(f"Error fetching ESMA updates: {str(e)}")
            return []
    
    async def _fetch_fca_updates(self) -> List[RegulatoryUpdate]:
        """Fetch FCA regulatory updates"""
        try:
            # Mock implementation
            updates = [
                RegulatoryUpdate(
                    update_id=str(uuid.uuid4()),
                    jurisdiction=Jurisdiction.UK,
                    framework=RegulatoryFramework.FCA,
                    update_type="policy_statement",
                    title="Algorithmic Trading Disclosure Requirements",
                    description="New disclosure requirements for algorithmic trading strategies",
                    effective_date=datetime.now() + timedelta(days=75),
                    impact_assessment="Low - documentation updates required",
                    implementation_required=False,
                    created_at=datetime.now()
                )
            ]
            return updates
            
        except Exception as e:
            logger.error(f"Error fetching FCA updates: {str(e)}")
            return []


class ComplianceRuleEngine:
    """
    Manages and enforces compliance rules across jurisdictions
    """
    
    def __init__(self):
        self.rules_db = {}  # In production, this would be a proper database
        self.rule_cache = {}
        
        # Initialize default rules
        asyncio.create_task(self._initialize_default_rules())
        
    async def _initialize_default_rules(self):
        """Initialize default compliance rules for major jurisdictions"""
        try:
            default_rules = [
                # US SEC Rules
                ComplianceRule(
                    rule_id="SEC_POSITION_LIMIT_001",
                    jurisdiction=Jurisdiction.US,
                    framework=RegulatoryFramework.SEC,
                    rule_type=ComplianceRuleType.POSITION_LIMITS,
                    description="Single position cannot exceed 10% of total portfolio value",
                    parameters={"max_position_pct": 0.10, "calculation_method": "market_value"},
                    effective_date=datetime(2020, 1, 1),
                    expiry_date=None,
                    is_active=True,
                    created_at=datetime.now(),
                    updated_at=datetime.now()
                ),
                
                ComplianceRule(
                    rule_id="SEC_RISK_LIMIT_001",
                    jurisdiction=Jurisdiction.US,
                    framework=RegulatoryFramework.SEC,
                    rule_type=ComplianceRuleType.RISK_LIMITS,
                    description="Daily VaR cannot exceed 2% of portfolio value",
                    parameters={"max_var_pct": 0.02, "confidence_level": 0.95, "holding_period": 1},
                    effective_date=datetime(2020, 1, 1),
                    expiry_date=None,
                    is_active=True,
                    created_at=datetime.now(),
                    updated_at=datetime.now()
                ),
                
                # EU MiFID II Rules
                ComplianceRule(
                    rule_id="MIFID_REPORTING_001",
                    jurisdiction=Jurisdiction.EU,
                    framework=RegulatoryFramework.MIFID_II,
                    rule_type=ComplianceRuleType.REPORTING,
                    description="All transactions must be reported within T+1",
                    parameters={"reporting_deadline_hours": 24, "include_derivatives": True},
                    effective_date=datetime(2018, 1, 3),
                    expiry_date=None,
                    is_active=True,
                    created_at=datetime.now(),
                    updated_at=datetime.now()
                ),
                
                ComplianceRule(
                    rule_id="MIFID_BEST_EXECUTION_001",
                    jurisdiction=Jurisdiction.EU,
                    framework=RegulatoryFramework.MIFID_II,
                    rule_type=ComplianceRuleType.BEST_EXECUTION,
                    description="Must demonstrate best execution for client orders",
                    parameters={"execution_factors": ["price", "costs", "speed", "likelihood"], "monitoring_required": True},
                    effective_date=datetime(2018, 1, 3),
                    expiry_date=None,
                    is_active=True,
                    created_at=datetime.now(),
                    updated_at=datetime.now()
                ),
                
                # UK FCA Rules
                ComplianceRule(
                    rule_id="FCA_ALGO_TRADING_001",
                    jurisdiction=Jurisdiction.UK,
                    framework=RegulatoryFramework.FCA,
                    rule_type=ComplianceRuleType.ALGO_TRADING,
                    description="Algorithmic trading systems must have adequate risk controls",
                    parameters={"risk_controls_required": True, "testing_required": True, "monitoring_required": True},
                    effective_date=datetime(2021, 1, 1),
                    expiry_date=None,
                    is_active=True,
                    created_at=datetime.now(),
                    updated_at=datetime.now()
                ),
                
                # Japan JFSA Rules
                ComplianceRule(
                    rule_id="JFSA_POSITION_LIMIT_001",
                    jurisdiction=Jurisdiction.JAPAN,
                    framework=RegulatoryFramework.JFSA,
                    rule_type=ComplianceRuleType.POSITION_LIMITS,
                    description="Single equity position cannot exceed 5% of issued shares",
                    parameters={"max_ownership_pct": 0.05, "notification_threshold": 0.03},
                    effective_date=datetime(2020, 1, 1),
                    expiry_date=None,
                    is_active=True,
                    created_at=datetime.now(),
                    updated_at=datetime.now()
                )
            ]
            
            # Store rules
            for rule in default_rules:
                self.rules_db[rule.rule_id] = rule
                
            logger.info(f"Initialized {len(default_rules)} default compliance rules")
            
        except Exception as e:
            logger.error(f"Error initializing default rules: {str(e)}")
    
    async def get_applicable_rules(self, jurisdiction: Jurisdiction, 
                                 trade_data: Dict[str, Any]) -> List[ComplianceRule]:
        """Get applicable compliance rules for a trade"""
        try:
            applicable_rules = []
            
            for rule in self.rules_db.values():
                if rule.jurisdiction == jurisdiction and rule.is_active:
                    # Check if rule applies to this trade type
                    if self._rule_applies_to_trade(rule, trade_data):
                        applicable_rules.append(rule)
            
            return applicable_rules
            
        except Exception as e:
            logger.error(f"Error getting applicable rules: {str(e)}")
            return []
    
    def _rule_applies_to_trade(self, rule: ComplianceRule, trade_data: Dict[str, Any]) -> bool:
        """Determine if a rule applies to a specific trade"""
        try:
            # Basic applicability logic - in practice this would be more sophisticated
            if rule.rule_type == ComplianceRuleType.POSITION_LIMITS:
                return trade_data.get('asset_class') in ['equity', 'bond', 'derivative']
            elif rule.rule_type == ComplianceRuleType.RISK_LIMITS:
                return True  # Risk limits apply to all trades
            elif rule.rule_type == ComplianceRuleType.REPORTING:
                return trade_data.get('requires_reporting', True)
            elif rule.rule_type == ComplianceRuleType.ALGO_TRADING:
                return trade_data.get('is_algorithmic', False)
            else:
                return True
                
        except Exception as e:
            logger.error(f"Error checking rule applicability: {str(e)}")
            return False
    
    async def add_rule(self, rule: ComplianceRule) -> bool:
        """Add new compliance rule"""
        try:
            self.rules_db[rule.rule_id] = rule
            logger.info(f"Added compliance rule: {rule.rule_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error adding compliance rule: {str(e)}")
            return False
    
    async def update_rule(self, rule_id: str, updates: Dict[str, Any]) -> bool:
        """Update existing compliance rule"""
        try:
            if rule_id in self.rules_db:
                rule = self.rules_db[rule_id]
                
                # Update rule attributes
                for key, value in updates.items():
                    if hasattr(rule, key):
                        setattr(rule, key, value)
                
                rule.updated_at = datetime.now()
                logger.info(f"Updated compliance rule: {rule_id}")
                return True
            else:
                logger.warning(f"Rule not found for update: {rule_id}")
                return False
                
        except Exception as e:
            logger.error(f"Error updating compliance rule: {str(e)}")
            return False


class ComplianceValidator:
    """
    Validates trades and portfolios against compliance rules
    """
    
    def __init__(self, rule_engine: ComplianceRuleEngine):
        self.rule_engine = rule_engine
        
        # Metrics
        self.validations_performed = Counter('compliance_validations_total', 'Compliance validations', ['jurisdiction', 'result'])
        self.validation_latency = Histogram('compliance_validation_duration_seconds', 'Validation duration')
        
    async def validate_trade(self, trade_data: Dict[str, Any], 
                           portfolio_data: Dict[str, Any] = None) -> List[TradeComplianceCheck]:
        """Validate a trade against all applicable compliance rules"""
        try:
            start_time = time.time()
            compliance_checks = []
            
            # Determine applicable jurisdictions
            jurisdictions = self._determine_applicable_jurisdictions(trade_data)
            
            for jurisdiction in jurisdictions:
                # Get applicable rules
                applicable_rules = await self.rule_engine.get_applicable_rules(jurisdiction, trade_data)
                
                # Check each rule
                for rule in applicable_rules:
                    check_result = await self._check_rule_compliance(rule, trade_data, portfolio_data)
                    compliance_checks.append(check_result)
                    
                    # Update metrics
                    self.validations_performed.labels(
                        jurisdiction=jurisdiction.value,
                        result='compliant' if check_result.is_compliant else 'violation'
                    ).inc()
            
            # Update latency metric
            validation_time = time.time() - start_time
            self.validation_latency.observe(validation_time)
            
            return compliance_checks
            
        except Exception as e:
            logger.error(f"Error validating trade: {str(e)}")
            return []
    
    def _determine_applicable_jurisdictions(self, trade_data: Dict[str, Any]) -> List[Jurisdiction]:
        """Determine which jurisdictions apply to a trade"""
        try:
            jurisdictions = []
            
            # Based on trading venue
            venue = trade_data.get('venue', '').upper()
            if venue in ['NYSE', 'NASDAQ']:
                jurisdictions.append(Jurisdiction.US)
            elif venue in ['LSE']:
                jurisdictions.append(Jurisdiction.UK)
            elif venue in ['XETRA', 'EURONEXT']:
                jurisdictions.append(Jurisdiction.EU)
            elif venue in ['TSE']:
                jurisdictions.append(Jurisdiction.JAPAN)
            
            # Based on instrument type and domicile
            instrument_domicile = trade_data.get('instrument_domicile', '').upper()
            if instrument_domicile == 'US':
                if Jurisdiction.US not in jurisdictions:
                    jurisdictions.append(Jurisdiction.US)
            elif instrument_domicile == 'EU':
                if Jurisdiction.EU not in jurisdictions:
                    jurisdictions.append(Jurisdiction.EU)
            
            # Default to US if no specific jurisdiction identified
            if not jurisdictions:
                jurisdictions.append(Jurisdiction.US)
            
            return jurisdictions
            
        except Exception as e:
            logger.error(f"Error determining applicable jurisdictions: {str(e)}")
            return [Jurisdiction.US]  # Default fallback
    
    async def _check_rule_compliance(self, rule: ComplianceRule, trade_data: Dict[str, Any], 
                                   portfolio_data: Dict[str, Any] = None) -> TradeComplianceCheck:
        """Check compliance against a specific rule"""
        try:
            trade_id = trade_data.get('trade_id', str(uuid.uuid4()))
            is_compliant = True
            violation_details = None
            severity = None
            remediation_steps = []
            
            if rule.rule_type == ComplianceRuleType.POSITION_LIMITS:
                is_compliant, violation_details, severity = await self._check_position_limits(
                    rule, trade_data, portfolio_data
                )
                if not is_compliant:
                    remediation_steps = ["Reduce position size", "Seek regulatory approval for larger position"]
                    
            elif rule.rule_type == ComplianceRuleType.RISK_LIMITS:
                is_compliant, violation_details, severity = await self._check_risk_limits(
                    rule, trade_data, portfolio_data
                )
                if not is_compliant:
                    remediation_steps = ["Reduce portfolio risk", "Implement additional hedging"]
                    
            elif rule.rule_type == ComplianceRuleType.REPORTING:
                is_compliant, violation_details, severity = await self._check_reporting_requirements(
                    rule, trade_data
                )
                if not is_compliant:
                    remediation_steps = ["Submit required reports", "Update reporting systems"]
                    
            elif rule.rule_type == ComplianceRuleType.BEST_EXECUTION:
                is_compliant, violation_details, severity = await self._check_best_execution(
                    rule, trade_data
                )
                if not is_compliant:
                    remediation_steps = ["Review execution venues", "Improve execution algorithms"]
                    
            elif rule.rule_type == ComplianceRuleType.ALGO_TRADING:
                is_compliant, violation_details, severity = await self._check_algo_trading_controls(
                    rule, trade_data
                )
                if not is_compliant:
                    remediation_steps = ["Implement required risk controls", "Update system documentation"]
            
            return TradeComplianceCheck(
                check_id=str(uuid.uuid4()),
                trade_id=trade_id,
                rule_id=rule.rule_id,
                jurisdiction=rule.jurisdiction,
                framework=rule.framework,
                is_compliant=is_compliant,
                violation_details=violation_details,
                severity=severity,
                timestamp=datetime.now(),
                remediation_required=not is_compliant,
                remediation_steps=remediation_steps
            )
            
        except Exception as e:
            logger.error(f"Error checking rule compliance: {str(e)}")
            return TradeComplianceCheck(
                check_id=str(uuid.uuid4()),
                trade_id=trade_data.get('trade_id', 'unknown'),
                rule_id=rule.rule_id,
                jurisdiction=rule.jurisdiction,
                framework=rule.framework,
                is_compliant=False,
                violation_details=f"Compliance check error: {str(e)}",
                severity=ViolationSeverity.HIGH,
                timestamp=datetime.now(),
                remediation_required=True,
                remediation_steps=["Investigate compliance check error"]
            )
    
    async def _check_position_limits(self, rule: ComplianceRule, trade_data: Dict[str, Any], 
                                   portfolio_data: Dict[str, Any]) -> Tuple[bool, Optional[str], Optional[ViolationSeverity]]:
        """Check position limit compliance"""
        try:
            if not portfolio_data:
                return True, None, None
            
            max_position_pct = rule.parameters.get('max_position_pct', 0.10)
            
            # Calculate position size after trade
            current_position = portfolio_data.get('positions', {}).get(trade_data.get('symbol', ''), 0)
            trade_quantity = trade_data.get('quantity', 0)
            if trade_data.get('side') == 'sell':
                trade_quantity = -trade_quantity
            
            new_position = current_position + trade_quantity
            position_value = new_position * trade_data.get('price', 0)
            portfolio_value = portfolio_data.get('total_value', 0)
            
            if portfolio_value > 0:
                position_pct = abs(position_value) / portfolio_value
                
                if position_pct > max_position_pct:
                    violation_details = f"Position limit exceeded: {position_pct:.2%} > {max_position_pct:.2%}"
                    severity = ViolationSeverity.HIGH if position_pct > max_position_pct * 1.5 else ViolationSeverity.MEDIUM
                    return False, violation_details, severity
            
            return True, None, None
            
        except Exception as e:
            logger.error(f"Error checking position limits: {str(e)}")
            return False, f"Position limit check error: {str(e)}", ViolationSeverity.HIGH
    
    async def _check_risk_limits(self, rule: ComplianceRule, trade_data: Dict[str, Any], 
                               portfolio_data: Dict[str, Any]) -> Tuple[bool, Optional[str], Optional[ViolationSeverity]]:
        """Check risk limit compliance"""
        try:
            if not portfolio_data:
                return True, None, None
            
            max_var_pct = rule.parameters.get('max_var_pct', 0.02)
            
            # Simplified VaR calculation
            portfolio_value = portfolio_data.get('total_value', 0)
            estimated_var = portfolio_data.get('estimated_var', 0)
            
            if portfolio_value > 0:
                var_pct = estimated_var / portfolio_value
                
                if var_pct > max_var_pct:
                    violation_details = f"VaR limit exceeded: {var_pct:.2%} > {max_var_pct:.2%}"
                    severity = ViolationSeverity.CRITICAL if var_pct > max_var_pct * 2 else ViolationSeverity.HIGH
                    return False, violation_details, severity
            
            return True, None, None
            
        except Exception as e:
            logger.error(f"Error checking risk limits: {str(e)}")
            return False, f"Risk limit check error: {str(e)}", ViolationSeverity.HIGH
    
    async def _check_reporting_requirements(self, rule: ComplianceRule, 
                                          trade_data: Dict[str, Any]) -> Tuple[bool, Optional[str], Optional[ViolationSeverity]]:
        """Check reporting requirement compliance"""
        try:
            # Check if trade requires reporting
            if not trade_data.get('requires_reporting', True):
                return True, None, None
            
            reporting_deadline_hours = rule.parameters.get('reporting_deadline_hours', 24)
            trade_time = trade_data.get('trade_time', datetime.now())
            
            if isinstance(trade_time, str):
                trade_time = datetime.fromisoformat(trade_time)
            
            hours_since_trade = (datetime.now() - trade_time).total_seconds() / 3600
            
            if hours_since_trade > reporting_deadline_hours:
                violation_details = f"Reporting deadline missed: {hours_since_trade:.1f}h > {reporting_deadline_hours}h"
                severity = ViolationSeverity.MEDIUM
                return False, violation_details, severity
            
            return True, None, None
            
        except Exception as e:
            logger.error(f"Error checking reporting requirements: {str(e)}")
            return False, f"Reporting check error: {str(e)}", ViolationSeverity.MEDIUM
    
    async def _check_best_execution(self, rule: ComplianceRule, 
                                  trade_data: Dict[str, Any]) -> Tuple[bool, Optional[str], Optional[ViolationSeverity]]:
        """Check best execution compliance"""
        try:
            # Simplified best execution check
            execution_price = trade_data.get('execution_price', 0)
            benchmark_price = trade_data.get('benchmark_price', execution_price)
            
            if benchmark_price > 0:
                price_deviation = abs(execution_price - benchmark_price) / benchmark_price
                max_deviation = 0.001  # 10 bps tolerance
                
                if price_deviation > max_deviation:
                    violation_details = f"Best execution deviation: {price_deviation:.4f} > {max_deviation:.4f}"
                    severity = ViolationSeverity.LOW
                    return False, violation_details, severity
            
            return True, None, None
            
        except Exception as e:
            logger.error(f"Error checking best execution: {str(e)}")
            return False, f"Best execution check error: {str(e)}", ViolationSeverity.LOW
    
    async def _check_algo_trading_controls(self, rule: ComplianceRule, 
                                         trade_data: Dict[str, Any]) -> Tuple[bool, Optional[str], Optional[ViolationSeverity]]:
        """Check algorithmic trading controls compliance"""
        try:
            if not trade_data.get('is_algorithmic', False):
                return True, None, None
            
            # Check required controls
            required_controls = rule.parameters.get('risk_controls_required', True)
            has_risk_controls = trade_data.get('has_risk_controls', False)
            
            if required_controls and not has_risk_controls:
                violation_details = "Required risk controls not implemented for algorithmic trade"
                severity = ViolationSeverity.HIGH
                return False, violation_details, severity
            
            return True, None, None
            
        except Exception as e:
            logger.error(f"Error checking algo trading controls: {str(e)}")
            return False, f"Algo trading check error: {str(e)}", ViolationSeverity.HIGH


class ComplianceReportingEngine:
    """
    Generates and submits regulatory reports
    """
    
    def __init__(self):
        self.report_templates = {}
        self.submission_apis = {}
        self.report_history = {}
        
        # Initialize report templates
        asyncio.create_task(self._initialize_report_templates())
        
        # Metrics
        self.reports_generated = Counter('compliance_reports_generated_total', 'Reports generated', ['jurisdiction', 'report_type'])
        self.reports_submitted = Counter('compliance_reports_submitted_total', 'Reports submitted', ['jurisdiction', 'status'])
    
    async def _initialize_report_templates(self):
        """Initialize regulatory report templates"""
        try:
            # MiFID II Transaction Reporting Template
            self.report_templates['MIFID_TRANSACTION'] = {
                'jurisdiction': Jurisdiction.EU,
                'framework': RegulatoryFramework.MIFID_II,
                'required_fields': [
                    'trading_venue', 'instrument_id', 'price', 'quantity', 'trade_time',
                    'buyer_id', 'seller_id', 'transaction_type', 'settlement_date'
                ],
                'format': 'XML',
                'submission_endpoint': 'https://api.esma.europa.eu/mifid/transactions'
            }
            
            # SEC Institutional Investment Manager Report (13F)
            self.report_templates['SEC_13F'] = {
                'jurisdiction': Jurisdiction.US,
                'framework': RegulatoryFramework.SEC,
                'required_fields': [
                    'manager_name', 'report_date', 'holdings', 'total_value',
                    'confidential_treatment', 'amendment_flag'
                ],
                'format': 'XML',
                'submission_endpoint': 'https://www.sec.gov/edgar/forms'
            }
            
            # CFTC Swap Data Repository Report
            self.report_templates['CFTC_SDR'] = {
                'jurisdiction': Jurisdiction.US,
                'framework': RegulatoryFramework.CFTC,
                'required_fields': [
                    'swap_id', 'counterparty_1', 'counterparty_2', 'notional_amount',
                    'effective_date', 'maturity_date', 'product_type', 'clearing_status'
                ],
                'format': 'XML',
                'submission_endpoint': 'https://www.cftc.gov/sdr/api'
            }
            
            logger.info("Initialized regulatory report templates")
            
        except Exception as e:
            logger.error(f"Error initializing report templates: {str(e)}")
    
    async def generate_regulatory_report(self, jurisdiction: Jurisdiction, report_type: str,
                                       period_start: datetime, period_end: datetime,
                                       data: Dict[str, Any]) -> ComplianceReport:
        """Generate regulatory report"""
        try:
            report_id = str(uuid.uuid4())
            
            # Get appropriate template
            template_key = f"{jurisdiction.value}_{report_type}"
            if template_key not in self.report_templates:
                template_key = report_type
            
            template = self.report_templates.get(template_key)
            if not template:
                raise ValueError(f"No template found for report type: {report_type}")
            
            # Validate required fields
            required_fields = template.get('required_fields', [])
            missing_fields = [field for field in required_fields if field not in data]
            
            if missing_fields:
                raise ValueError(f"Missing required fields: {missing_fields}")
            
            # Generate report data
            report_data = await self._generate_report_data(template, data, period_start, period_end)
            
            # Create report object
            report = ComplianceReport(
                report_id=report_id,
                jurisdiction=jurisdiction,
                framework=RegulatoryFramework(template.get('framework', 'SEC')),
                report_type=report_type,
                reporting_period_start=period_start,
                reporting_period_end=period_end,
                data=report_data,
                generated_at=datetime.now(),
                submitted_at=None,
                submission_reference=None,
                status='generated'
            )
            
            # Store report
            self.report_history[report_id] = report
            
            # Update metrics
            self.reports_generated.labels(
                jurisdiction=jurisdiction.value,
                report_type=report_type
            ).inc()
            
            logger.info(f"Generated regulatory report: {report_id} ({report_type})")
            return report
            
        except Exception as e:
            logger.error(f"Error generating regulatory report: {str(e)}")
            raise
    
    async def _generate_report_data(self, template: Dict[str, Any], data: Dict[str, Any],
                                  period_start: datetime, period_end: datetime) -> Dict[str, Any]:
        """Generate formatted report data based on template"""
        try:
            report_data = {
                'header': {
                    'report_type': template.get('report_type', 'TRANSACTION_REPORT'),
                    'period_start': period_start.isoformat(),
                    'period_end': period_end.isoformat(),
                    'generated_at': datetime.now().isoformat(),
                    'format_version': '1.0'
                },
                'data': data
            }
            
            # Add jurisdiction-specific formatting
            if template.get('format') == 'XML':
                report_data['format'] = 'XML'
                # Would convert to actual XML format in production
            
            return report_data
            
        except Exception as e:
            logger.error(f"Error generating report data: {str(e)}")
            raise
    
    async def submit_report(self, report_id: str) -> bool:
        """Submit regulatory report to authorities"""
        try:
            if report_id not in self.report_history:
                raise ValueError(f"Report not found: {report_id}")
            
            report = self.report_history[report_id]
            
            # Get submission endpoint
            template_key = f"{report.jurisdiction.value}_{report.report_type}"
            template = self.report_templates.get(template_key, {})
            submission_endpoint = template.get('submission_endpoint')
            
            if not submission_endpoint:
                raise ValueError(f"No submission endpoint configured for {template_key}")
            
            # Submit report (mock implementation)
            submission_result = await self._submit_to_regulator(submission_endpoint, report)
            
            if submission_result['success']:
                # Update report status
                report.submitted_at = datetime.now()
                report.submission_reference = submission_result['reference']
                report.status = 'submitted'
                
                # Update metrics
                self.reports_submitted.labels(
                    jurisdiction=report.jurisdiction.value,
                    status='success'
                ).inc()
                
                logger.info(f"Successfully submitted report: {report_id}")
                return True
            else:
                report.status = 'submission_failed'
                
                # Update metrics
                self.reports_submitted.labels(
                    jurisdiction=report.jurisdiction.value,
                    status='failed'
                ).inc()
                
                logger.error(f"Failed to submit report: {report_id} - {submission_result['error']}")
                return False
                
        except Exception as e:
            logger.error(f"Error submitting report: {str(e)}")
            return False
    
    async def _submit_to_regulator(self, endpoint: str, report: ComplianceReport) -> Dict[str, Any]:
        """Submit report to regulatory authority (mock implementation)"""
        try:
            # Mock implementation - would integrate with actual regulatory APIs
            await asyncio.sleep(0.1)  # Simulate network delay
            
            # Simulate 95% success rate
            import random
            success = random.random() < 0.95
            
            if success:
                return {
                    'success': True,
                    'reference': f"REF_{uuid.uuid4().hex[:8].upper()}",
                    'submitted_at': datetime.now().isoformat()
                }
            else:
                return {
                    'success': False,
                    'error': 'Simulated submission failure',
                    'retry_after': 3600  # Retry after 1 hour
                }
                
        except Exception as e:
            logger.error(f"Error submitting to regulator: {str(e)}")
            return {'success': False, 'error': str(e)}


class GlobalComplianceEngine:
    """
    Main global compliance engine coordinating all compliance activities
    """
    
    def __init__(self, redis_url: str = "redis://localhost:6379"):
        self.redis_url = redis_url
        self.redis_client = None
        
        # Core components
        self.regulatory_data_provider = RegulatoryDataProvider()
        self.rule_engine = ComplianceRuleEngine()
        self.validator = ComplianceValidator(self.rule_engine)
        self.reporting_engine = ComplianceReportingEngine()
        
        # State tracking
        self.active_violations = {}
        self.pending_reports = {}
        
        # Configuration
        self.monitoring_interval = timedelta(minutes=5)
        self.reporting_schedule = {
            'daily': ['TRANSACTION_REPORTS'],
            'weekly': ['POSITION_REPORTS'],
            'monthly': ['RISK_REPORTS'],
            'quarterly': ['13F_REPORTS']
        }
        
        # Metrics
        self.compliance_violations = Counter('compliance_violations_total', 'Compliance violations', ['jurisdiction', 'severity'])
        self.regulatory_updates_processed = Counter('regulatory_updates_processed_total', 'Regulatory updates processed')
        self.compliance_score = Gauge('compliance_score', 'Overall compliance score', ['jurisdiction'])
        
        # Background tasks
        self.monitoring_task = None
        self.reporting_task = None
        self.update_monitoring_task = None
        
        logger.info("Global Compliance Engine initialized")
    
    async def initialize(self):
        """Initialize the global compliance engine"""
        try:
            # Initialize Redis connection
            self.redis_client = aioredis.from_url(self.redis_url)
            await self.redis_client.ping()
            
            # Start background tasks
            self.monitoring_task = asyncio.create_task(self._continuous_compliance_monitoring())
            self.reporting_task = asyncio.create_task(self._automated_reporting())
            self.update_monitoring_task = asyncio.create_task(self._monitor_regulatory_updates())
            
            logger.info("Global compliance engine initialized successfully")
            
        except Exception as e:
            logger.error(f"Error initializing global compliance engine: {str(e)}")
            raise
    
    async def validate_trade_compliance(self, trade_data: Dict[str, Any], 
                                      portfolio_data: Dict[str, Any] = None) -> Dict[str, Any]:
        """Main method to validate trade compliance across all jurisdictions"""
        try:
            start_time = time.time()
            
            logger.info(f"Validating trade compliance: {trade_data.get('trade_id', 'unknown')}")
            
            # Perform compliance validation
            compliance_checks = await self.validator.validate_trade(trade_data, portfolio_data)
            
            # Analyze results
            violations = [check for check in compliance_checks if not check.is_compliant]
            all_compliant = len(violations) == 0
            
            # Handle violations
            if violations:
                await self._handle_compliance_violations(violations)
            
            # Calculate compliance scores by jurisdiction
            jurisdiction_scores = self._calculate_jurisdiction_compliance_scores(compliance_checks)
            
            # Update metrics
            for violation in violations:
                self.compliance_violations.labels(
                    jurisdiction=violation.jurisdiction.value,
                    severity=violation.severity.value if violation.severity else 'unknown'
                ).inc()
            
            for jurisdiction, score in jurisdiction_scores.items():
                self.compliance_score.labels(jurisdiction=jurisdiction).set(score)
            
            processing_time = time.time() - start_time
            
            result = {
                'trade_id': trade_data.get('trade_id', 'unknown'),
                'is_compliant': all_compliant,
                'processing_time': processing_time,
                'total_checks': len(compliance_checks),
                'violations_count': len(violations),
                'compliance_checks': [asdict(check) for check in compliance_checks],
                'violations': [asdict(violation) for violation in violations],
                'jurisdiction_scores': jurisdiction_scores,
                'remediation_required': any(check.remediation_required for check in compliance_checks),
                'timestamp': datetime.now().isoformat()
            }
            
            # Cache result
            await self._cache_compliance_result(result)
            
            logger.info(f"Trade compliance validation completed: {all_compliant} ({processing_time:.3f}s)")
            return result
            
        except Exception as e:
            logger.error(f"Error validating trade compliance: {str(e)}")
            return {
                'trade_id': trade_data.get('trade_id', 'unknown'),
                'is_compliant': False,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    async def generate_compliance_report(self, jurisdiction: Jurisdiction, report_type: str,
                                       period_start: datetime, period_end: datetime,
                                       auto_submit: bool = False) -> Dict[str, Any]:
        """Generate compliance report for specific jurisdiction"""
        try:
            logger.info(f"Generating compliance report: {jurisdiction.value} - {report_type}")
            
            # Collect data for the reporting period
            report_data = await self._collect_report_data(jurisdiction, report_type, period_start, period_end)
            
            # Generate report
            report = await self.reporting_engine.generate_regulatory_report(
                jurisdiction, report_type, period_start, period_end, report_data
            )
            
            # Auto-submit if requested
            if auto_submit:
                submission_success = await self.reporting_engine.submit_report(report.report_id)
                
                return {
                    'success': True,
                    'report_id': report.report_id,
                    'submitted': submission_success,
                    'submission_reference': report.submission_reference,
                    'generated_at': report.generated_at.isoformat()
                }
            else:
                return {
                    'success': True,
                    'report_id': report.report_id,
                    'submitted': False,
                    'generated_at': report.generated_at.isoformat()
                }
                
        except Exception as e:
            logger.error(f"Error generating compliance report: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    async def get_compliance_status(self, jurisdiction: Jurisdiction = None) -> Dict[str, Any]:
        """Get comprehensive compliance status"""
        try:
            if jurisdiction:
                # Status for specific jurisdiction
                status = await self._get_jurisdiction_status(jurisdiction)
            else:
                # Global compliance status
                status = await self._get_global_compliance_status()
            
            return status
            
        except Exception as e:
            logger.error(f"Error getting compliance status: {str(e)}")
            return {'error': str(e)}
    
    async def _handle_compliance_violations(self, violations: List[TradeComplianceCheck]):
        """Handle compliance violations"""
        try:
            for violation in violations:
                violation_key = f"{violation.jurisdiction.value}_{violation.rule_id}_{violation.trade_id}"
                
                # Store violation
                self.active_violations[violation_key] = violation
                
                # Create alerts based on severity
                if violation.severity in [ViolationSeverity.HIGH, ViolationSeverity.CRITICAL]:
                    await self._create_compliance_alert(violation)
                
                # Log violation
                logger.warning(f"Compliance violation: {violation.jurisdiction.value} - {violation.violation_details}")
                
        except Exception as e:
            logger.error(f"Error handling compliance violations: {str(e)}")
    
    async def _create_compliance_alert(self, violation: TradeComplianceCheck):
        """Create compliance alert for high-severity violations"""
        try:
            alert = {
                'alert_id': str(uuid.uuid4()),
                'violation_id': violation.check_id,
                'jurisdiction': violation.jurisdiction.value,
                'framework': violation.framework.value,
                'severity': violation.severity.value,
                'trade_id': violation.trade_id,
                'details': violation.violation_details,
                'remediation_steps': violation.remediation_steps,
                'created_at': datetime.now().isoformat(),
                'status': 'active'
            }
            
            # Store alert in Redis for real-time notifications
            if self.redis_client:
                await self.redis_client.lpush('compliance_alerts', json.dumps(alert))
                await self.redis_client.expire('compliance_alerts', 86400)  # 24 hour TTL
            
            logger.warning(f"Compliance alert created: {alert['alert_id']}")
            
        except Exception as e:
            logger.error(f"Error creating compliance alert: {str(e)}")
    
    def _calculate_jurisdiction_compliance_scores(self, compliance_checks: List[TradeComplianceCheck]) -> Dict[str, float]:
        """Calculate compliance scores by jurisdiction"""
        try:
            jurisdiction_scores = {}
            
            # Group checks by jurisdiction
            by_jurisdiction = {}
            for check in compliance_checks:
                jurisdiction = check.jurisdiction.value
                if jurisdiction not in by_jurisdiction:
                    by_jurisdiction[jurisdiction] = []
                by_jurisdiction[jurisdiction].append(check)
            
            # Calculate scores
            for jurisdiction, checks in by_jurisdiction.items():
                total_checks = len(checks)
                compliant_checks = len([c for c in checks if c.is_compliant])
                
                if total_checks > 0:
                    base_score = compliant_checks / total_checks
                    
                    # Apply severity penalties
                    severity_penalty = 0
                    for check in checks:
                        if not check.is_compliant and check.severity:
                            if check.severity == ViolationSeverity.CRITICAL:
                                severity_penalty += 0.2
                            elif check.severity == ViolationSeverity.HIGH:
                                severity_penalty += 0.1
                            elif check.severity == ViolationSeverity.MEDIUM:
                                severity_penalty += 0.05
                    
                    final_score = max(0, base_score - severity_penalty)
                    jurisdiction_scores[jurisdiction] = round(final_score, 3)
                else:
                    jurisdiction_scores[jurisdiction] = 1.0
            
            return jurisdiction_scores
            
        except Exception as e:
            logger.error(f"Error calculating jurisdiction compliance scores: {str(e)}")
            return {}
    
    async def _continuous_compliance_monitoring(self):
        """Continuously monitor compliance status"""
        while True:
            try:
                logger.debug("Running compliance monitoring cycle")
                
                # Check for expired violations
                await self._cleanup_expired_violations()
                
                # Monitor regulatory deadlines
                await self._check_regulatory_deadlines()
                
                # Update compliance metrics
                await self._update_compliance_metrics()
                
                await asyncio.sleep(self.monitoring_interval.total_seconds())
                
            except Exception as e:
                logger.error(f"Error in compliance monitoring: {str(e)}")
                await asyncio.sleep(300)  # Wait 5 minutes on error
    
    async def _automated_reporting(self):
        """Handle automated regulatory reporting"""
        while True:
            try:
                now = datetime.now()
                
                # Check daily reports
                if now.hour == 18:  # 6 PM daily
                    for report_type in self.reporting_schedule['daily']:
                        await self._generate_scheduled_report('daily', report_type)
                
                # Check weekly reports (Sunday)
                if now.weekday() == 6 and now.hour == 20:  # Sunday 8 PM
                    for report_type in self.reporting_schedule['weekly']:
                        await self._generate_scheduled_report('weekly', report_type)
                
                # Check monthly reports (last day of month)
                tomorrow = now + timedelta(days=1)
                if tomorrow.day == 1 and now.hour == 22:  # Last day 10 PM
                    for report_type in self.reporting_schedule['monthly']:
                        await self._generate_scheduled_report('monthly', report_type)
                
                await asyncio.sleep(3600)  # Check every hour
                
            except Exception as e:
                logger.error(f"Error in automated reporting: {str(e)}")
                await asyncio.sleep(3600)
    
    async def _monitor_regulatory_updates(self):
        """Monitor for regulatory updates"""
        while True:
            try:
                logger.debug("Checking for regulatory updates")
                
                # Get updates for all jurisdictions
                updates = await self.regulatory_data_provider.get_regulatory_updates()
                
                for update in updates:
                    await self._process_regulatory_update(update)
                    self.regulatory_updates_processed.inc()
                
                await asyncio.sleep(3600)  # Check every hour
                
            except Exception as e:
                logger.error(f"Error monitoring regulatory updates: {str(e)}")
                await asyncio.sleep(1800)  # Wait 30 minutes on error
    
    async def _process_regulatory_update(self, update: RegulatoryUpdate):
        """Process regulatory update and adapt compliance rules"""
        try:
            logger.info(f"Processing regulatory update: {update.title}")
            
            # Store update
            update_key = f"regulatory_update:{update.update_id}"
            if self.redis_client:
                await self.redis_client.setex(
                    update_key,
                    86400 * 30,  # 30 days TTL
                    json.dumps(asdict(update), default=str)
                )
            
            # Assess if implementation is required
            if update.implementation_required:
                # Create implementation task
                implementation_task = {
                    'task_id': str(uuid.uuid4()),
                    'update_id': update.update_id,
                    'jurisdiction': update.jurisdiction.value,
                    'effective_date': update.effective_date.isoformat(),
                    'status': 'pending',
                    'created_at': datetime.now().isoformat()
                }
                
                # Queue for implementation
                if self.redis_client:
                    await self.redis_client.lpush('implementation_tasks', json.dumps(implementation_task))
                
                logger.info(f"Queued implementation task for update: {update.update_id}")
            
        except Exception as e:
            logger.error(f"Error processing regulatory update: {str(e)}")
    
    async def _collect_report_data(self, jurisdiction: Jurisdiction, report_type: str,
                                 period_start: datetime, period_end: datetime) -> Dict[str, Any]:
        """Collect data for regulatory report"""
        try:
            # Mock implementation - would collect actual trading data
            report_data = {
                'reporting_entity': 'Alphintra Trading Platform',
                'jurisdiction': jurisdiction.value,
                'report_type': report_type,
                'period_start': period_start.isoformat(),
                'period_end': period_end.isoformat(),
                'transaction_count': 1250,
                'total_volume': 125000000,
                'largest_position': 5000000,
                'compliance_violations': len([v for v in self.active_violations.values() 
                                            if v.jurisdiction == jurisdiction])
            }
            
            return report_data
            
        except Exception as e:
            logger.error(f"Error collecting report data: {str(e)}")
            return {}
    
    async def _cache_compliance_result(self, result: Dict[str, Any]):
        """Cache compliance result in Redis"""
        try:
            if self.redis_client:
                cache_key = f"compliance_result:{result['trade_id']}"
                await self.redis_client.setex(
                    cache_key,
                    3600,  # 1 hour TTL
                    json.dumps(result, default=str)
                )
        except Exception as e:
            logger.error(f"Error caching compliance result: {str(e)}")
    
    async def _get_global_compliance_status(self) -> Dict[str, Any]:
        """Get global compliance status across all jurisdictions"""
        try:
            status = {
                'timestamp': datetime.now().isoformat(),
                'jurisdictions': {},
                'overall_compliance_score': 0.0,
                'active_violations': len(self.active_violations),
                'pending_reports': len(self.pending_reports),
                'regulatory_updates_pending': 0
            }
            
            # Get status for each jurisdiction
            for jurisdiction in Jurisdiction:
                jurisdiction_status = await self._get_jurisdiction_status(jurisdiction)
                status['jurisdictions'][jurisdiction.value] = jurisdiction_status
            
            # Calculate overall score
            jurisdiction_scores = [j['compliance_score'] for j in status['jurisdictions'].values() 
                                 if 'compliance_score' in j]
            if jurisdiction_scores:
                status['overall_compliance_score'] = sum(jurisdiction_scores) / len(jurisdiction_scores)
            
            return status
            
        except Exception as e:
            logger.error(f"Error getting global compliance status: {str(e)}")
            return {'error': str(e)}
    
    async def _get_jurisdiction_status(self, jurisdiction: Jurisdiction) -> Dict[str, Any]:
        """Get compliance status for specific jurisdiction"""
        try:
            # Count violations for this jurisdiction
            jurisdiction_violations = [
                v for v in self.active_violations.values() 
                if v.jurisdiction == jurisdiction
            ]
            
            # Get applicable rules count
            applicable_rules = [
                rule for rule in self.rule_engine.rules_db.values()
                if rule.jurisdiction == jurisdiction and rule.is_active
            ]
            
            return {
                'jurisdiction': jurisdiction.value,
                'compliance_score': 0.95,  # Mock score
                'active_rules': len(applicable_rules),
                'active_violations': len(jurisdiction_violations),
                'high_severity_violations': len([v for v in jurisdiction_violations 
                                               if v.severity == ViolationSeverity.HIGH]),
                'critical_violations': len([v for v in jurisdiction_violations 
                                          if v.severity == ViolationSeverity.CRITICAL]),
                'last_updated': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting jurisdiction status: {str(e)}")
            return {'jurisdiction': jurisdiction.value, 'error': str(e)}
    
    async def cleanup(self):
        """Cleanup resources"""
        try:
            # Cancel background tasks
            if self.monitoring_task:
                self.monitoring_task.cancel()
            if self.reporting_task:
                self.reporting_task.cancel()
            if self.update_monitoring_task:
                self.update_monitoring_task.cancel()
            
            # Close Redis connection
            if self.redis_client:
                await self.redis_client.close()
            
            logger.info("Global compliance engine cleanup completed")
            
        except Exception as e:
            logger.error(f"Error in cleanup: {str(e)}")


# Example usage and testing
if __name__ == "__main__":
    async def test_global_compliance_engine():
        """Test global compliance engine"""
        
        # Initialize engine
        engine = GlobalComplianceEngine()
        await engine.initialize()
        
        try:
            # Sample trade data
            sample_trade = {
                'trade_id': 'TRADE_001',
                'symbol': 'AAPL',
                'side': 'buy',
                'quantity': 10000,
                'price': 150.0,
                'venue': 'NYSE',
                'trade_time': datetime.now(),
                'instrument_domicile': 'US',
                'requires_reporting': True,
                'is_algorithmic': True,
                'has_risk_controls': True
            }
            
            # Sample portfolio data
            sample_portfolio = {
                'total_value': 10000000,
                'positions': {
                    'AAPL': 5000
                },
                'estimated_var': 150000
            }
            
            print("🏛️ Testing Global Compliance Engine...")
            
            # Validate trade compliance
            print("\n📋 Validating trade compliance...")
            compliance_result = await engine.validate_trade_compliance(sample_trade, sample_portfolio)
            
            print(f"✅ Compliance Result:")
            print(f"  Is Compliant: {compliance_result['is_compliant']}")
            print(f"  Total Checks: {compliance_result['total_checks']}")
            print(f"  Violations: {compliance_result['violations_count']}")
            print(f"  Processing Time: {compliance_result['processing_time']:.3f}s")
            
            if compliance_result['violations']:
                print(f"\n⚠️ Violations Found:")
                for violation in compliance_result['violations']:
                    print(f"  - {violation['jurisdiction']} ({violation['framework']}): {violation['violation_details']}")
            
            print(f"\n📊 Jurisdiction Scores:")
            for jurisdiction, score in compliance_result['jurisdiction_scores'].items():
                print(f"  {jurisdiction}: {score:.1%}")
            
            # Generate compliance report
            print(f"\n📝 Generating compliance report...")
            period_start = datetime.now() - timedelta(days=30)
            period_end = datetime.now()
            
            report_result = await engine.generate_compliance_report(
                Jurisdiction.US, 'TRANSACTION_REPORT', period_start, period_end
            )
            
            print(f"📋 Report Result:")
            print(f"  Success: {report_result['success']}")
            print(f"  Report ID: {report_result.get('report_id', 'N/A')}")
            print(f"  Generated At: {report_result.get('generated_at', 'N/A')}")
            
            # Get compliance status
            print(f"\n🔍 Getting compliance status...")
            status = await engine.get_compliance_status()
            
            print(f"📈 Compliance Status:")
            print(f"  Overall Score: {status['overall_compliance_score']:.1%}")
            print(f"  Active Violations: {status['active_violations']}")
            print(f"  Pending Reports: {status['pending_reports']}")
            
            print(f"\n🌍 Jurisdiction Status:")
            for jurisdiction, jurisdiction_status in status['jurisdictions'].items():
                if 'compliance_score' in jurisdiction_status:
                    print(f"  {jurisdiction}: {jurisdiction_status['compliance_score']:.1%} "
                          f"({jurisdiction_status['active_violations']} violations)")
            
            # Monitor for a bit
            print(f"\n⏳ Monitoring for 10 seconds...")
            await asyncio.sleep(10)
            
            print(f"\n✅ Global compliance engine test completed!")
            
        finally:
            # Cleanup
            await engine.cleanup()
    
    # Run the test
    asyncio.run(test_global_compliance_engine())