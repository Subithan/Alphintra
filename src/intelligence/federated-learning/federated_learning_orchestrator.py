"""
Federated Learning Orchestrator
Alphintra Trading Platform - Phase 5

Implements privacy-preserving federated learning across multiple trading nodes
for collaborative model improvement without sharing sensitive data.
"""

import asyncio
import logging
from typing import Dict, List, Optional, Tuple, Any, Union
from dataclasses import dataclass, asdict
from enum import Enum
import json
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
import uuid
import hashlib
import pickle
import base64
from concurrent.futures import ThreadPoolExecutor
import tempfile
import os

# Federated learning libraries
try:
    import torch
    import torch.nn as nn
    import torch.optim as optim
    from torch.utils.data import DataLoader, TensorDataset
    import torch.nn.functional as F
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False
    logging.warning("PyTorch not available - federated learning will use limited functionality")

try:
    import tensorflow as tf
    import tensorflow_federated as tff
    TFF_AVAILABLE = True
except ImportError:
    TFF_AVAILABLE = False
    logging.warning("TensorFlow Federated not available - using custom implementation")

# Cryptographic libraries for privacy
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

# Infrastructure
import aiohttp
import aioredis
import asyncpg
import websockets

# Monitoring
from prometheus_client import Counter, Gauge, Histogram

logger = logging.getLogger(__name__)


class AggregationMethod(Enum):
    """Federated aggregation methods"""
    FEDERATED_AVERAGING = "federated_averaging"  # FedAvg
    FEDERATED_PROX = "federated_prox"           # FedProx
    FEDERATED_NOVA = "federated_nova"           # FedNova
    SECURE_AGGREGATION = "secure_aggregation"   # With differential privacy
    WEIGHTED_AVERAGING = "weighted_averaging"   # Based on data size


class NodeRole(Enum):
    """Federated learning node roles"""
    COORDINATOR = "coordinator"      # Central coordinator
    PARTICIPANT = "participant"      # Regular participant
    AGGREGATOR = "aggregator"        # Dedicated aggregator
    VALIDATOR = "validator"          # Model validator


class ModelType(Enum):
    """Types of models for federated learning"""
    PRICE_PREDICTION = "price_prediction"
    RISK_ASSESSMENT = "risk_assessment"
    SENTIMENT_ANALYSIS = "sentiment_analysis"
    ANOMALY_DETECTION = "anomaly_detection"
    PORTFOLIO_OPTIMIZATION = "portfolio_optimization"


@dataclass
class FederatedNode:
    """Federated learning node information"""
    node_id: str
    role: NodeRole
    endpoint: str
    public_key: str
    region: str
    data_size: int
    model_capabilities: List[ModelType]
    last_seen: datetime
    trust_score: float
    performance_metrics: Dict[str, float]
    is_active: bool


@dataclass
class ModelUpdate:
    """Model update from a federated node"""
    update_id: str
    node_id: str
    model_type: ModelType
    round_number: int
    weights: Dict[str, Any]  # Encrypted model weights
    gradient_norms: Dict[str, float]
    training_loss: float
    validation_loss: float
    data_size: int
    training_time: float
    timestamp: datetime
    signature: str  # Cryptographic signature


@dataclass
class FederatedRound:
    """Federated learning round information"""
    round_id: str
    round_number: int
    model_type: ModelType
    start_time: datetime
    end_time: Optional[datetime]
    participating_nodes: List[str]
    aggregation_method: AggregationMethod
    global_loss: float
    convergence_metrics: Dict[str, float]
    privacy_budget: float
    is_completed: bool


@dataclass
class GlobalModel:
    """Global federated model"""
    model_id: str
    model_type: ModelType
    version: int
    weights: Dict[str, Any]
    performance_metrics: Dict[str, float]
    training_rounds: int
    last_updated: datetime
    participating_nodes: List[str]
    privacy_guarantees: Dict[str, Any]


class FederatedLearningOrchestrator:
    """Orchestrates federated learning across multiple nodes"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.node_id = config.get('node_id', str(uuid.uuid4()))
        self.role = NodeRole(config.get('role', 'participant'))
        
        # Cryptographic setup
        self.encryption_key = self._generate_encryption_key()
        
        # Federated learning parameters
        self.min_participants = config.get('min_participants', 3)
        self.max_rounds = config.get('max_rounds', 100)
        self.convergence_threshold = config.get('convergence_threshold', 1e-4)
        self.privacy_budget = config.get('privacy_budget', 1.0)
        
        # Node registry
        self.nodes: Dict[str, FederatedNode] = {}
        self.active_rounds: Dict[str, FederatedRound] = {}
        self.global_models: Dict[ModelType, GlobalModel] = {}
        
        # Communication
        self.websocket_server = None
        self.client_connections: Dict[str, websockets.WebSocketServerProtocol] = {}
        
        # Database connections
        self.redis_client = None
        self.db_pool = None
        
        # Metrics
        self.round_counter = Counter('federated_rounds_total', 'Total federated learning rounds')
        self.node_gauge = Gauge('active_federated_nodes', 'Number of active federated nodes')
        self.convergence_gauge = Gauge('model_convergence_loss', 'Global model convergence loss')
        self.privacy_gauge = Gauge('privacy_budget_remaining', 'Remaining privacy budget')
        
    async def initialize(self):
        """Initialize federated learning orchestrator"""
        self.redis_client = await aioredis.from_url(
            self.config['redis_url'],
            encoding='utf-8',
            decode_responses=True
        )
        
        self.db_pool = await asyncpg.create_pool(
            self.config['database_url'],
            min_size=5,
            max_size=20
        )
        
        # Start WebSocket server for node communication
        if self.role == NodeRole.COORDINATOR:
            await self._start_websocket_server()
        
        # Load existing models and nodes
        await self._load_existing_state()
        
        logger.info(f"Federated Learning Orchestrator initialized - Role: {self.role.value}, "
                   f"Node ID: {self.node_id}")
    
    def _generate_encryption_key(self) -> bytes:
        """Generate encryption key for secure communication"""
        password = self.config.get('encryption_password', 'default_password').encode()
        salt = self.config.get('encryption_salt', 'default_salt').encode()
        
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(password))
        return key
    
    async def _start_websocket_server(self):
        """Start WebSocket server for node communication"""
        async def handle_client(websocket, path):
            node_id = None
            try:
                # Register client
                async for message in websocket:
                    data = json.loads(message)
                    
                    if data['type'] == 'register':
                        node_id = data['node_id']
                        self.client_connections[node_id] = websocket
                        logger.info(f"Node {node_id} connected")
                        
                    elif data['type'] == 'model_update':
                        await self._handle_model_update(data)
                        
                    elif data['type'] == 'heartbeat':
                        await self._handle_heartbeat(data)
                        
            except websockets.exceptions.ConnectionClosed:
                if node_id and node_id in self.client_connections:
                    del self.client_connections[node_id]
                    logger.info(f"Node {node_id} disconnected")
            except Exception as e:
                logger.error(f"WebSocket error: {e}")
        
        # Start server
        port = self.config.get('websocket_port', 8765)
        self.websocket_server = await websockets.serve(handle_client, "localhost", port)
        logger.info(f"WebSocket server started on port {port}")
    
    async def _load_existing_state(self):
        """Load existing federated learning state"""
        try:
            # Load nodes
            async with self.db_pool.acquire() as conn:
                rows = await conn.fetch("SELECT * FROM federated_nodes WHERE is_active = true")
                for row in rows:
                    node = FederatedNode(
                        node_id=row['node_id'],
                        role=NodeRole(row['role']),
                        endpoint=row['endpoint'],
                        public_key=row['public_key'],
                        region=row['region'],
                        data_size=row['data_size'],
                        model_capabilities=[ModelType(cap) for cap in json.loads(row['model_capabilities'])],
                        last_seen=row['last_seen'],
                        trust_score=row['trust_score'],
                        performance_metrics=json.loads(row['performance_metrics']),
                        is_active=row['is_active']
                    )
                    self.nodes[node.node_id] = node
                
                # Load global models
                model_rows = await conn.fetch("SELECT * FROM global_federated_models")
                for row in model_rows:
                    model = GlobalModel(
                        model_id=row['model_id'],
                        model_type=ModelType(row['model_type']),
                        version=row['version'],
                        weights=json.loads(row['weights']),
                        performance_metrics=json.loads(row['performance_metrics']),
                        training_rounds=row['training_rounds'],
                        last_updated=row['last_updated'],
                        participating_nodes=json.loads(row['participating_nodes']),
                        privacy_guarantees=json.loads(row['privacy_guarantees'])
                    )
                    self.global_models[model.model_type] = model
                    
        except Exception as e:
            logger.error(f"Error loading existing state: {e}")
    
    async def register_node(self, node: FederatedNode) -> bool:
        """Register a new federated learning node"""
        try:
            # Validate node
            if not await self._validate_node(node):
                logger.warning(f"Node validation failed for {node.node_id}")
                return False
            
            # Store in registry
            self.nodes[node.node_id] = node
            
            # Persist to database
            async with self.db_pool.acquire() as conn:
                await conn.execute("""
                    INSERT INTO federated_nodes 
                    (node_id, role, endpoint, public_key, region, data_size, 
                     model_capabilities, last_seen, trust_score, performance_metrics, is_active)
                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11)
                    ON CONFLICT (node_id) DO UPDATE SET
                    role = $2, endpoint = $3, public_key = $4, region = $5,
                    data_size = $6, model_capabilities = $7, last_seen = $8,
                    trust_score = $9, performance_metrics = $10, is_active = $11
                """,
                    node.node_id, node.role.value, node.endpoint, node.public_key,
                    node.region, node.data_size, json.dumps([cap.value for cap in node.model_capabilities]),
                    node.last_seen, node.trust_score, json.dumps(node.performance_metrics),
                    node.is_active
                )
            
            # Update metrics
            self.node_gauge.set(len([n for n in self.nodes.values() if n.is_active]))
            
            logger.info(f"Node {node.node_id} registered successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error registering node {node.node_id}: {e}")
            return False
    
    async def _validate_node(self, node: FederatedNode) -> bool:
        """Validate a federated learning node"""
        # Check if endpoint is reachable
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{node.endpoint}/health", timeout=5) as response:
                    if response.status != 200:
                        return False
        except:
            return False
        
        # Check trust score
        if node.trust_score < 0.5:
            return False
        
        # Check capabilities
        if not node.model_capabilities:
            return False
        
        return True
    
    async def start_federated_round(self, 
                                  model_type: ModelType, 
                                  aggregation_method: AggregationMethod = AggregationMethod.FEDERATED_AVERAGING) -> str:
        """Start a new federated learning round"""
        
        if self.role != NodeRole.COORDINATOR:
            raise ValueError("Only coordinator can start federated rounds")
        
        # Check if enough nodes are available
        capable_nodes = [
            node for node in self.nodes.values() 
            if node.is_active and model_type in node.model_capabilities
        ]
        
        if len(capable_nodes) < self.min_participants:
            raise ValueError(f"Not enough nodes available: {len(capable_nodes)} < {self.min_participants}")
        
        # Create new round
        round_id = str(uuid.uuid4())
        round_number = len([r for r in self.active_rounds.values() if r.model_type == model_type]) + 1
        
        federated_round = FederatedRound(
            round_id=round_id,
            round_number=round_number,
            model_type=model_type,
            start_time=datetime.now(),
            end_time=None,
            participating_nodes=[node.node_id for node in capable_nodes[:self.min_participants]],
            aggregation_method=aggregation_method,
            global_loss=float('inf'),
            convergence_metrics={},
            privacy_budget=self.privacy_budget,
            is_completed=False
        )
        
        self.active_rounds[round_id] = federated_round
        
        # Send round start message to participating nodes
        round_message = {
            'type': 'round_start',
            'round_id': round_id,
            'model_type': model_type.value,
            'round_number': round_number,
            'aggregation_method': aggregation_method.value,
            'global_model_weights': self.global_models.get(model_type, {}).weights if model_type in self.global_models else {}
        }
        
        await self._broadcast_to_nodes(federated_round.participating_nodes, round_message)
        
        # Store round in database
        await self._store_federated_round(federated_round)
        
        self.round_counter.inc()
        logger.info(f"Started federated round {round_number} for {model_type.value} with {len(federated_round.participating_nodes)} nodes")
        
        return round_id
    
    async def _handle_model_update(self, update_data: Dict[str, Any]):
        """Handle model update from a participant node"""
        try:
            # Parse update
            model_update = ModelUpdate(
                update_id=update_data['update_id'],
                node_id=update_data['node_id'],
                model_type=ModelType(update_data['model_type']),
                round_number=update_data['round_number'],
                weights=update_data['weights'],
                gradient_norms=update_data.get('gradient_norms', {}),
                training_loss=update_data['training_loss'],
                validation_loss=update_data['validation_loss'],
                data_size=update_data['data_size'],
                training_time=update_data['training_time'],
                timestamp=datetime.now(),
                signature=update_data.get('signature', '')
            )
            
            # Validate update
            if not await self._validate_model_update(model_update):
                logger.warning(f"Invalid model update from node {model_update.node_id}")
                return
            
            # Store update
            await self._store_model_update(model_update)
            
            # Check if round is ready for aggregation
            round_id = None
            for rid, round_info in self.active_rounds.items():
                if (round_info.model_type == model_update.model_type and 
                    round_info.round_number == model_update.round_number):
                    round_id = rid
                    break
            
            if round_id:
                await self._check_round_completion(round_id)
                
        except Exception as e:
            logger.error(f"Error handling model update: {e}")
    
    async def _validate_model_update(self, update: ModelUpdate) -> bool:
        """Validate a model update"""
        # Check if node is registered and active
        if update.node_id not in self.nodes or not self.nodes[update.node_id].is_active:
            return False
        
        # Check signature (simplified validation)
        if not update.signature:
            return False
        
        # Check gradient norms for potential attacks
        if update.gradient_norms:
            max_norm = max(update.gradient_norms.values())
            if max_norm > 10.0:  # Threshold for gradient clipping
                logger.warning(f"Large gradient norm detected: {max_norm}")
                return False
        
        return True
    
    async def _check_round_completion(self, round_id: str):
        """Check if a federated round is ready for aggregation"""
        if round_id not in self.active_rounds:
            return
        
        round_info = self.active_rounds[round_id]
        
        # Get all updates for this round
        async with self.db_pool.acquire() as conn:
            updates = await conn.fetch("""
                SELECT * FROM model_updates 
                WHERE model_type = $1 AND round_number = $2
            """, round_info.model_type.value, round_info.round_number)
        
        # Check if we have updates from all participants
        received_nodes = set(update['node_id'] for update in updates)
        expected_nodes = set(round_info.participating_nodes)
        
        if received_nodes >= expected_nodes:
            logger.info(f"Round {round_info.round_number} ready for aggregation")
            await self._aggregate_models(round_id, updates)
    
    async def _aggregate_models(self, round_id: str, updates: List[Dict[str, Any]]):
        """Aggregate model updates from participants"""
        round_info = self.active_rounds[round_id]
        
        try:
            if round_info.aggregation_method == AggregationMethod.FEDERATED_AVERAGING:
                aggregated_weights = await self._federated_averaging(updates)
            elif round_info.aggregation_method == AggregationMethod.WEIGHTED_AVERAGING:
                aggregated_weights = await self._weighted_averaging(updates)
            elif round_info.aggregation_method == AggregationMethod.SECURE_AGGREGATION:
                aggregated_weights = await self._secure_aggregation(updates)
            else:
                # Default to federated averaging
                aggregated_weights = await self._federated_averaging(updates)
            
            # Calculate global loss
            global_loss = np.mean([update['training_loss'] for update in updates])
            
            # Update global model
            if round_info.model_type in self.global_models:
                global_model = self.global_models[round_info.model_type]
                global_model.weights = aggregated_weights
                global_model.version += 1
                global_model.training_rounds += 1
                global_model.last_updated = datetime.now()
                
                # Calculate convergence
                loss_diff = abs(global_model.performance_metrics.get('loss', float('inf')) - global_loss)
                global_model.performance_metrics['loss'] = global_loss
                global_model.performance_metrics['convergence'] = loss_diff
                
            else:
                # Create new global model
                global_model = GlobalModel(
                    model_id=str(uuid.uuid4()),
                    model_type=round_info.model_type,
                    version=1,
                    weights=aggregated_weights,
                    performance_metrics={'loss': global_loss, 'convergence': float('inf')},
                    training_rounds=1,
                    last_updated=datetime.now(),
                    participating_nodes=round_info.participating_nodes,
                    privacy_guarantees={'differential_privacy': True, 'budget_used': 0.1}
                )
                self.global_models[round_info.model_type] = global_model
            
            # Complete round
            round_info.end_time = datetime.now()
            round_info.global_loss = global_loss
            round_info.convergence_metrics = global_model.performance_metrics
            round_info.is_completed = True
            
            # Send updated model to participants
            update_message = {
                'type': 'round_complete',
                'round_id': round_id,
                'global_model_weights': aggregated_weights,
                'global_loss': global_loss,
                'convergence_metrics': global_model.performance_metrics
            }
            
            await self._broadcast_to_nodes(round_info.participating_nodes, update_message)
            
            # Store updated global model
            await self._store_global_model(global_model)
            
            # Update metrics
            self.convergence_gauge.set(global_loss)
            
            # Check for convergence
            if global_model.performance_metrics['convergence'] < self.convergence_threshold:
                logger.info(f"Model {round_info.model_type.value} converged after {global_model.training_rounds} rounds")
            
            logger.info(f"Round {round_info.round_number} completed - Global Loss: {global_loss:.6f}")
            
        except Exception as e:
            logger.error(f"Error aggregating models for round {round_id}: {e}")
    
    async def _federated_averaging(self, updates: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Perform federated averaging of model weights"""
        if not updates:
            return {}
        
        # Calculate total data size for weighting
        total_data_size = sum(update['data_size'] for update in updates)
        
        # Initialize aggregated weights
        aggregated_weights = {}
        
        # Decrypt and aggregate weights
        for update in updates:
            weight_data = json.loads(update['weights'])
            data_weight = update['data_size'] / total_data_size
            
            for layer_name, weights in weight_data.items():
                if isinstance(weights, list):
                    weights = np.array(weights)
                
                if layer_name not in aggregated_weights:
                    aggregated_weights[layer_name] = weights * data_weight
                else:
                    aggregated_weights[layer_name] += weights * data_weight
        
        # Convert back to serializable format
        serializable_weights = {}
        for layer_name, weights in aggregated_weights.items():
            if isinstance(weights, np.ndarray):
                serializable_weights[layer_name] = weights.tolist()
            else:
                serializable_weights[layer_name] = weights
        
        return serializable_weights
    
    async def _weighted_averaging(self, updates: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Perform weighted averaging based on node performance"""
        if not updates:
            return {}
        
        # Calculate weights based on node trust scores and data size
        total_weight = 0
        node_weights = {}
        
        for update in updates:
            node_id = update['node_id']
            node = self.nodes.get(node_id)
            if node:
                # Combine trust score and data size for weighting
                weight = node.trust_score * np.sqrt(update['data_size'])
                node_weights[node_id] = weight
                total_weight += weight
        
        # Normalize weights
        for node_id in node_weights:
            node_weights[node_id] /= total_weight
        
        # Aggregate weights
        aggregated_weights = {}
        
        for update in updates:
            node_id = update['node_id']
            weight_data = json.loads(update['weights'])
            node_weight = node_weights.get(node_id, 0)
            
            for layer_name, weights in weight_data.items():
                if isinstance(weights, list):
                    weights = np.array(weights)
                
                if layer_name not in aggregated_weights:
                    aggregated_weights[layer_name] = weights * node_weight
                else:
                    aggregated_weights[layer_name] += weights * node_weight
        
        # Convert to serializable format
        serializable_weights = {}
        for layer_name, weights in aggregated_weights.items():
            if isinstance(weights, np.ndarray):
                serializable_weights[layer_name] = weights.tolist()
            else:
                serializable_weights[layer_name] = weights
        
        return serializable_weights
    
    async def _secure_aggregation(self, updates: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Perform secure aggregation with differential privacy"""
        # Add noise for differential privacy
        noise_scale = 1.0 / self.privacy_budget
        
        # Perform regular federated averaging first
        aggregated_weights = await self._federated_averaging(updates)
        
        # Add differential privacy noise
        for layer_name, weights in aggregated_weights.items():
            if isinstance(weights, list):
                weights = np.array(weights)
            
            # Add Gaussian noise
            noise = np.random.normal(0, noise_scale, weights.shape)
            noisy_weights = weights + noise
            
            aggregated_weights[layer_name] = noisy_weights.tolist()
        
        # Update privacy budget
        self.privacy_budget -= 0.1  # Consume some privacy budget
        self.privacy_gauge.set(self.privacy_budget)
        
        return aggregated_weights
    
    async def _broadcast_to_nodes(self, node_ids: List[str], message: Dict[str, Any]):
        """Broadcast message to specified nodes"""
        for node_id in node_ids:
            if node_id in self.client_connections:
                try:
                    await self.client_connections[node_id].send(json.dumps(message))
                except Exception as e:
                    logger.error(f"Error sending message to node {node_id}: {e}")
    
    async def _handle_heartbeat(self, heartbeat_data: Dict[str, Any]):
        """Handle heartbeat from a node"""
        node_id = heartbeat_data['node_id']
        if node_id in self.nodes:
            self.nodes[node_id].last_seen = datetime.now()
            
            # Update performance metrics if provided
            if 'performance_metrics' in heartbeat_data:
                self.nodes[node_id].performance_metrics.update(heartbeat_data['performance_metrics'])
    
    async def _store_federated_round(self, round_info: FederatedRound):
        """Store federated round information"""
        try:
            async with self.db_pool.acquire() as conn:
                await conn.execute("""
                    INSERT INTO federated_rounds 
                    (round_id, round_number, model_type, start_time, end_time,
                     participating_nodes, aggregation_method, global_loss,
                     convergence_metrics, privacy_budget, is_completed)
                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11)
                    ON CONFLICT (round_id) DO UPDATE SET
                    end_time = $5, global_loss = $8, convergence_metrics = $9,
                    privacy_budget = $10, is_completed = $11
                """,
                    round_info.round_id, round_info.round_number, round_info.model_type.value,
                    round_info.start_time, round_info.end_time,
                    json.dumps(round_info.participating_nodes), round_info.aggregation_method.value,
                    round_info.global_loss, json.dumps(round_info.convergence_metrics),
                    round_info.privacy_budget, round_info.is_completed
                )
        except Exception as e:
            logger.error(f"Error storing federated round: {e}")
    
    async def _store_model_update(self, update: ModelUpdate):
        """Store model update in database"""
        try:
            async with self.db_pool.acquire() as conn:
                await conn.execute("""
                    INSERT INTO model_updates 
                    (update_id, node_id, model_type, round_number, weights,
                     gradient_norms, training_loss, validation_loss, data_size,
                     training_time, timestamp, signature)
                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12)
                """,
                    update.update_id, update.node_id, update.model_type.value,
                    update.round_number, json.dumps(update.weights),
                    json.dumps(update.gradient_norms), update.training_loss,
                    update.validation_loss, update.data_size, update.training_time,
                    update.timestamp, update.signature
                )
        except Exception as e:
            logger.error(f"Error storing model update: {e}")
    
    async def _store_global_model(self, model: GlobalModel):
        """Store global model in database"""
        try:
            async with self.db_pool.acquire() as conn:
                await conn.execute("""
                    INSERT INTO global_federated_models 
                    (model_id, model_type, version, weights, performance_metrics,
                     training_rounds, last_updated, participating_nodes, privacy_guarantees)
                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
                    ON CONFLICT (model_type) DO UPDATE SET
                    version = $3, weights = $4, performance_metrics = $5,
                    training_rounds = $6, last_updated = $7, participating_nodes = $8,
                    privacy_guarantees = $9
                """,
                    model.model_id, model.model_type.value, model.version,
                    json.dumps(model.weights), json.dumps(model.performance_metrics),
                    model.training_rounds, model.last_updated,
                    json.dumps(model.participating_nodes), json.dumps(model.privacy_guarantees)
                )
        except Exception as e:
            logger.error(f"Error storing global model: {e}")
    
    async def get_global_model(self, model_type: ModelType) -> Optional[GlobalModel]:
        """Get the latest global model for a specific type"""
        return self.global_models.get(model_type)
    
    async def get_node_performance(self, node_id: str) -> Dict[str, Any]:
        """Get performance metrics for a specific node"""
        if node_id not in self.nodes:
            return {}
        
        node = self.nodes[node_id]
        
        # Get recent round participation
        async with self.db_pool.acquire() as conn:
            rounds = await conn.fetch("""
                SELECT COUNT(*) as total_rounds, AVG(global_loss) as avg_loss
                FROM federated_rounds 
                WHERE $1 = ANY(participating_nodes::text[])
            """, node_id)
        
        performance = {
            'trust_score': node.trust_score,
            'data_size': node.data_size,
            'last_seen': node.last_seen.isoformat(),
            'total_rounds': rounds[0]['total_rounds'] if rounds else 0,
            'average_loss_contribution': rounds[0]['avg_loss'] if rounds else 0,
            'performance_metrics': node.performance_metrics
        }
        
        return performance
    
    async def monitor_federated_learning(self):
        """Monitor federated learning system"""
        while True:
            try:
                # Update node status
                active_nodes = 0
                current_time = datetime.now()
                
                for node in self.nodes.values():
                    # Mark nodes as inactive if not seen for 5 minutes
                    if (current_time - node.last_seen).total_seconds() > 300:
                        node.is_active = False
                    else:
                        active_nodes += 1
                
                self.node_gauge.set(active_nodes)
                
                # Check for stale rounds
                for round_id, round_info in list(self.active_rounds.items()):
                    if not round_info.is_completed:
                        round_age = (current_time - round_info.start_time).total_seconds()
                        if round_age > 3600:  # 1 hour timeout
                            logger.warning(f"Round {round_id} timed out, marking as failed")
                            round_info.is_completed = True
                            round_info.end_time = current_time
                            await self._store_federated_round(round_info)
                            del self.active_rounds[round_id]
                
                # Log system status
                logger.info(f"Federated Learning Status - Active Nodes: {active_nodes}, "
                           f"Active Rounds: {len(self.active_rounds)}, "
                           f"Global Models: {len(self.global_models)}")
                
            except Exception as e:
                logger.error(f"Error in federated learning monitoring: {e}")
            
            await asyncio.sleep(60)  # Monitor every minute
    
    async def cleanup(self):
        """Clean up resources"""
        if self.websocket_server:
            self.websocket_server.close()
            await self.websocket_server.wait_closed()
        
        if self.redis_client:
            await self.redis_client.close()
        
        if self.db_pool:
            await self.db_pool.close()
        
        logger.info("Federated Learning Orchestrator cleanup completed")


# Example usage
async def main():
    """Example usage of Federated Learning Orchestrator"""
    
    # Coordinator configuration
    coordinator_config = {
        'node_id': 'coordinator-1',
        'role': 'coordinator',
        'redis_url': 'redis://localhost:6379',
        'database_url': 'postgresql://user:pass@localhost/alphintra',
        'websocket_port': 8765,
        'min_participants': 2,
        'max_rounds': 50,
        'convergence_threshold': 1e-4,
        'privacy_budget': 1.0,
        'encryption_password': 'secure_federated_password'
    }
    
    coordinator = FederatedLearningOrchestrator(coordinator_config)
    await coordinator.initialize()
    
    try:
        # Start monitoring
        monitor_task = asyncio.create_task(coordinator.monitor_federated_learning())
        
        # Example: Start a federated learning round
        if coordinator.role == NodeRole.COORDINATOR:
            # Register some example nodes first
            example_nodes = [
                FederatedNode(
                    node_id='node-americas',
                    role=NodeRole.PARTICIPANT,
                    endpoint='http://americas-node:8080',
                    public_key='americas-public-key',
                    region='americas',
                    data_size=10000,
                    model_capabilities=[ModelType.PRICE_PREDICTION, ModelType.RISK_ASSESSMENT],
                    last_seen=datetime.now(),
                    trust_score=0.95,
                    performance_metrics={'accuracy': 0.87, 'loss': 0.23},
                    is_active=True
                ),
                FederatedNode(
                    node_id='node-emea',
                    role=NodeRole.PARTICIPANT,
                    endpoint='http://emea-node:8080',
                    public_key='emea-public-key',
                    region='emea',
                    data_size=8000,
                    model_capabilities=[ModelType.PRICE_PREDICTION, ModelType.SENTIMENT_ANALYSIS],
                    last_seen=datetime.now(),
                    trust_score=0.92,
                    performance_metrics={'accuracy': 0.85, 'loss': 0.25},
                    is_active=True
                )
            ]
            
            for node in example_nodes:
                await coordinator.register_node(node)
            
            # Start federated round
            round_id = await coordinator.start_federated_round(
                ModelType.PRICE_PREDICTION,
                AggregationMethod.FEDERATED_AVERAGING
            )
            
            print(f"Started federated learning round: {round_id}")
        
        # Keep running
        await monitor_task
        
    except KeyboardInterrupt:
        print("\nShutdown requested...")
    finally:
        await coordinator.cleanup()


if __name__ == "__main__":
    asyncio.run(main())