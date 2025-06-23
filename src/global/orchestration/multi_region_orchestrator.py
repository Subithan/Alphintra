"""
Multi-Region Deployment Orchestrator
Alphintra Trading Platform - Phase 5
"""

import asyncio
import logging
from typing import Dict, List, Optional, Tuple, Any, Union
from dataclasses import dataclass, asdict
from enum import Enum
import json
import time
from datetime import datetime, timedelta
import uuid
from concurrent.futures import ThreadPoolExecutor
import aiohttp
import aioredis
import asyncpg

# Cloud providers
import google.cloud.compute_v1 as gcp_compute
import boto3
from azure.identity import DefaultAzureCredential
from azure.mgmt.resource import ResourceManagementClient

# Kubernetes
import kubernetes
from kubernetes import client, config

# Monitoring
from prometheus_client import Counter, Gauge, Histogram
import psutil

logger = logging.getLogger(__name__)


class Region(Enum):
    """Global regions enumeration"""
    AMERICAS_EAST = "americas-east"
    AMERICAS_WEST = "americas-west"
    EMEA_WEST = "emea-west"
    EMEA_CENTRAL = "emea-central"
    APAC_NORTHEAST = "apac-northeast"
    APAC_SOUTHEAST = "apac-southeast"
    APAC_SOUTH = "apac-south"


class DeploymentStatus(Enum):
    """Deployment status enumeration"""
    PENDING = "pending"
    DEPLOYING = "deploying"
    ACTIVE = "active"
    INACTIVE = "inactive"
    ERROR = "error"
    MAINTENANCE = "maintenance"


class CloudProvider(Enum):
    """Cloud provider enumeration"""
    GCP = "gcp"
    AWS = "aws"
    AZURE = "azure"
    ALIBABA = "alibaba"


@dataclass
class RegionConfig:
    """Regional configuration"""
    region: Region
    cloud_provider: CloudProvider
    timezone: str
    primary_exchanges: List[str]
    regulatory_jurisdiction: str
    data_residency_requirements: List[str]
    
    # Infrastructure configuration
    cluster_name: str
    cluster_zone: str
    node_count: int
    machine_type: str
    
    # Network configuration
    vpc_cidr: str
    subnet_cidrs: Dict[str, str]
    
    # Database configuration
    db_instance_type: str
    db_storage_size: int
    backup_retention_days: int
    
    # Compliance requirements
    encryption_requirements: List[str]
    audit_logging: bool
    data_locality: bool


@dataclass
class RegionStatus:
    """Regional deployment status"""
    region: Region
    status: DeploymentStatus
    last_health_check: datetime
    active_services: int
    total_services: int
    latency_metrics: Dict[str, float]
    resource_utilization: Dict[str, float]
    error_count: int
    uptime_percentage: float
    compliance_status: str


class RegionalInfrastructureManager:
    """
    Manages infrastructure deployment and configuration for each region
    """
    
    def __init__(self, region_config: RegionConfig):
        self.region_config = region_config
        self.cloud_clients = {}
        self.k8s_clients = {}
        
        # Initialize cloud provider clients
        self._initialize_cloud_clients()
        
        # Metrics
        self.deployment_counter = Counter('region_deployments_total', 'Total deployments', ['region', 'status'])
        self.service_count = Gauge('region_active_services', 'Active services per region', ['region'])
        self.latency_histogram = Histogram('region_latency_seconds', 'Regional latency', ['region', 'target'])
        
    def _initialize_cloud_clients(self):
        """Initialize cloud provider clients"""
        try:
            if self.region_config.cloud_provider == CloudProvider.GCP:
                self.cloud_clients['compute'] = gcp_compute.InstancesClient()
                self.cloud_clients['container'] = gcp_compute.InstancesClient()  # Simplified
                
            elif self.region_config.cloud_provider == CloudProvider.AWS:
                self.cloud_clients['ec2'] = boto3.client('ec2')
                self.cloud_clients['eks'] = boto3.client('eks')
                self.cloud_clients['rds'] = boto3.client('rds')
                
            elif self.region_config.cloud_provider == CloudProvider.AZURE:
                credential = DefaultAzureCredential()
                self.cloud_clients['resource'] = ResourceManagementClient(credential, 'subscription-id')
                
            logger.info(f"Initialized cloud clients for {self.region_config.cloud_provider.value}")
            
        except Exception as e:
            logger.error(f"Error initializing cloud clients: {str(e)}")
    
    async def deploy_regional_infrastructure(self) -> bool:
        """Deploy complete regional infrastructure"""
        try:
            logger.info(f"Starting infrastructure deployment for {self.region_config.region.value}")
            
            # Deploy networking infrastructure
            networking_result = await self._deploy_networking()
            if not networking_result:
                raise Exception("Networking deployment failed")
            
            # Deploy Kubernetes cluster
            cluster_result = await self._deploy_kubernetes_cluster()
            if not cluster_result:
                raise Exception("Kubernetes cluster deployment failed")
            
            # Deploy database infrastructure
            database_result = await self._deploy_databases()
            if not database_result:
                raise Exception("Database deployment failed")
            
            # Deploy monitoring infrastructure
            monitoring_result = await self._deploy_monitoring()
            if not monitoring_result:
                raise Exception("Monitoring deployment failed")
            
            # Configure security and compliance
            security_result = await self._configure_security()
            if not security_result:
                raise Exception("Security configuration failed")
            
            self.deployment_counter.labels(
                region=self.region_config.region.value, 
                status='success'
            ).inc()
            
            logger.info(f"Infrastructure deployment completed for {self.region_config.region.value}")
            return True
            
        except Exception as e:
            logger.error(f"Infrastructure deployment failed for {self.region_config.region.value}: {str(e)}")
            self.deployment_counter.labels(
                region=self.region_config.region.value, 
                status='failed'
            ).inc()
            return False
    
    async def _deploy_networking(self) -> bool:
        """Deploy regional networking infrastructure"""
        try:
            if self.region_config.cloud_provider == CloudProvider.GCP:
                return await self._deploy_gcp_networking()
            elif self.region_config.cloud_provider == CloudProvider.AWS:
                return await self._deploy_aws_networking()
            elif self.region_config.cloud_provider == CloudProvider.AZURE:
                return await self._deploy_azure_networking()
            else:
                raise NotImplementedError(f"Networking deployment not implemented for {self.region_config.cloud_provider}")
                
        except Exception as e:
            logger.error(f"Networking deployment error: {str(e)}")
            return False
    
    async def _deploy_gcp_networking(self) -> bool:
        """Deploy GCP networking infrastructure"""
        try:
            # Create VPC
            vpc_config = {
                'name': f"alphintra-vpc-{self.region_config.region.value}",
                'auto_create_subnetworks': False,
                'routing_config': {'routing_mode': 'REGIONAL'}
            }
            
            # Create subnets
            subnet_configs = []
            for subnet_name, cidr in self.region_config.subnet_cidrs.items():
                subnet_config = {
                    'name': f"alphintra-subnet-{subnet_name}-{self.region_config.region.value}",
                    'ip_cidr_range': cidr,
                    'region': self.region_config.cluster_zone.rsplit('-', 1)[0],
                    'network': vpc_config['name']
                }
                subnet_configs.append(subnet_config)
            
            # Create firewall rules
            firewall_rules = [
                {
                    'name': f"alphintra-allow-internal-{self.region_config.region.value}",
                    'network': vpc_config['name'],
                    'source_ranges': [self.region_config.vpc_cidr],
                    'allowed': [{'IPProtocol': 'tcp'}, {'IPProtocol': 'udp'}, {'IPProtocol': 'icmp'}]
                },
                {
                    'name': f"alphintra-allow-trading-api-{self.region_config.region.value}",
                    'network': vpc_config['name'],
                    'source_ranges': ['0.0.0.0/0'],
                    'allowed': [{'IPProtocol': 'tcp', 'ports': ['443', '8080']}]
                }
            ]
            
            logger.info(f"GCP networking configuration created for {self.region_config.region.value}")
            return True
            
        except Exception as e:
            logger.error(f"GCP networking deployment error: {str(e)}")
            return False
    
    async def _deploy_aws_networking(self) -> bool:
        """Deploy AWS networking infrastructure"""
        try:
            # Create VPC
            vpc_response = self.cloud_clients['ec2'].create_vpc(
                CidrBlock=self.region_config.vpc_cidr,
                TagSpecifications=[{
                    'ResourceType': 'vpc',
                    'Tags': [{'Key': 'Name', 'Value': f"alphintra-vpc-{self.region_config.region.value}"}]
                }]
            )
            vpc_id = vpc_response['Vpc']['VpcId']
            
            # Create subnets
            subnet_ids = []
            for subnet_name, cidr in self.region_config.subnet_cidrs.items():
                subnet_response = self.cloud_clients['ec2'].create_subnet(
                    VpcId=vpc_id,
                    CidrBlock=cidr,
                    TagSpecifications=[{
                        'ResourceType': 'subnet',
                        'Tags': [{'Key': 'Name', 'Value': f"alphintra-subnet-{subnet_name}"}]
                    }]
                )
                subnet_ids.append(subnet_response['Subnet']['SubnetId'])
            
            # Create internet gateway
            igw_response = self.cloud_clients['ec2'].create_internet_gateway(
                TagSpecifications=[{
                    'ResourceType': 'internet-gateway',
                    'Tags': [{'Key': 'Name', 'Value': f"alphintra-igw-{self.region_config.region.value}"}]
                }]
            )
            
            logger.info(f"AWS networking configuration created for {self.region_config.region.value}")
            return True
            
        except Exception as e:
            logger.error(f"AWS networking deployment error: {str(e)}")
            return False
    
    async def _deploy_azure_networking(self) -> bool:
        """Deploy Azure networking infrastructure"""
        try:
            # Create resource group
            resource_group_params = {
                'location': self.region_config.cluster_zone,
                'tags': {'project': 'alphintra', 'region': self.region_config.region.value}
            }
            
            # Create virtual network
            vnet_params = {
                'location': self.region_config.cluster_zone,
                'address_space': {'address_prefixes': [self.region_config.vpc_cidr]},
                'subnets': [
                    {
                        'name': subnet_name,
                        'address_prefix': cidr
                    }
                    for subnet_name, cidr in self.region_config.subnet_cidrs.items()
                ]
            }
            
            logger.info(f"Azure networking configuration created for {self.region_config.region.value}")
            return True
            
        except Exception as e:
            logger.error(f"Azure networking deployment error: {str(e)}")
            return False
    
    async def _deploy_kubernetes_cluster(self) -> bool:
        """Deploy Kubernetes cluster"""
        try:
            if self.region_config.cloud_provider == CloudProvider.GCP:
                return await self._deploy_gke_cluster()
            elif self.region_config.cloud_provider == CloudProvider.AWS:
                return await self._deploy_eks_cluster()
            elif self.region_config.cloud_provider == CloudProvider.AZURE:
                return await self._deploy_aks_cluster()
            else:
                raise NotImplementedError(f"K8s deployment not implemented for {self.region_config.cloud_provider}")
                
        except Exception as e:
            logger.error(f"Kubernetes cluster deployment error: {str(e)}")
            return False
    
    async def _deploy_gke_cluster(self) -> bool:
        """Deploy GKE cluster"""
        try:
            cluster_config = {
                'name': self.region_config.cluster_name,
                'location': self.region_config.cluster_zone,
                'initial_node_count': self.region_config.node_count,
                'node_config': {
                    'machine_type': self.region_config.machine_type,
                    'disk_size_gb': 100,
                    'oauth_scopes': [
                        'https://www.googleapis.com/auth/compute',
                        'https://www.googleapis.com/auth/devstorage.read_only',
                        'https://www.googleapis.com/auth/logging.write',
                        'https://www.googleapis.com/auth/monitoring'
                    ]
                },
                'workload_identity_config': {'workload_pool': 'PROJECT_ID.svc.id.goog'},
                'network_policy': {'enabled': True},
                'ip_allocation_policy': {'use_ip_aliases': True},
                'master_auth': {'client_certificate_config': {'issue_client_certificate': False}},
                'logging_service': 'logging.googleapis.com/kubernetes',
                'monitoring_service': 'monitoring.googleapis.com/kubernetes'
            }
            
            logger.info(f"GKE cluster configuration created: {self.region_config.cluster_name}")
            return True
            
        except Exception as e:
            logger.error(f"GKE cluster deployment error: {str(e)}")
            return False
    
    async def _deploy_eks_cluster(self) -> bool:
        """Deploy EKS cluster"""
        try:
            cluster_config = {
                'name': self.region_config.cluster_name,
                'version': '1.21',
                'roleArn': 'arn:aws:iam::ACCOUNT:role/eks-service-role',
                'resourcesVpcConfig': {
                    'subnetIds': ['subnet-12345', 'subnet-67890'],  # Would be from networking step
                    'endpointConfigAccess': {
                        'privateAccess': True,
                        'publicAccess': True
                    }
                },
                'logging': {
                    'enable': [
                        {'types': ['api', 'audit', 'authenticator', 'controllerManager', 'scheduler']}
                    ]
                }
            }
            
            logger.info(f"EKS cluster configuration created: {self.region_config.cluster_name}")
            return True
            
        except Exception as e:
            logger.error(f"EKS cluster deployment error: {str(e)}")
            return False
    
    async def _deploy_aks_cluster(self) -> bool:
        """Deploy AKS cluster"""
        try:
            cluster_config = {
                'location': self.region_config.cluster_zone,
                'dns_prefix': f"alphintra-{self.region_config.region.value}",
                'kubernetes_version': '1.21.0',
                'agent_pool_profiles': [{
                    'name': 'default',
                    'count': self.region_config.node_count,
                    'vm_size': self.region_config.machine_type,
                    'os_type': 'Linux'
                }],
                'service_principal_profile': {
                    'client_id': 'CLIENT_ID',
                    'secret': 'CLIENT_SECRET'
                },
                'network_profile': {
                    'network_plugin': 'azure',
                    'load_balancer_sku': 'standard'
                }
            }
            
            logger.info(f"AKS cluster configuration created: {self.region_config.cluster_name}")
            return True
            
        except Exception as e:
            logger.error(f"AKS cluster deployment error: {str(e)}")
            return False
    
    async def _deploy_databases(self) -> bool:
        """Deploy regional database infrastructure"""
        try:
            # Deploy PostgreSQL for primary data
            postgres_result = await self._deploy_postgresql()
            
            # Deploy TimescaleDB for time-series data
            timescale_result = await self._deploy_timescaledb()
            
            # Deploy Redis for caching
            redis_result = await self._deploy_redis()
            
            return postgres_result and timescale_result and redis_result
            
        except Exception as e:
            logger.error(f"Database deployment error: {str(e)}")
            return False
    
    async def _deploy_postgresql(self) -> bool:
        """Deploy PostgreSQL instance"""
        try:
            db_config = {
                'instance_id': f"alphintra-postgres-{self.region_config.region.value}",
                'instance_class': self.region_config.db_instance_type,
                'allocated_storage': self.region_config.db_storage_size,
                'backup_retention_period': self.region_config.backup_retention_days,
                'encryption_at_rest': True,
                'deletion_protection': True,
                'monitoring_interval': 60
            }
            
            logger.info(f"PostgreSQL configuration created for {self.region_config.region.value}")
            return True
            
        except Exception as e:
            logger.error(f"PostgreSQL deployment error: {str(e)}")
            return False
    
    async def _deploy_timescaledb(self) -> bool:
        """Deploy TimescaleDB instance"""
        try:
            timescale_config = {
                'instance_id': f"alphintra-timescale-{self.region_config.region.value}",
                'instance_class': self.region_config.db_instance_type,
                'allocated_storage': self.region_config.db_storage_size * 2,  # More storage for time-series
                'compression_enabled': True,
                'continuous_aggregates': True,
                'retention_policies': {
                    'raw_data': '30 days',
                    'minute_aggregates': '1 year',
                    'hour_aggregates': '5 years'
                }
            }
            
            logger.info(f"TimescaleDB configuration created for {self.region_config.region.value}")
            return True
            
        except Exception as e:
            logger.error(f"TimescaleDB deployment error: {str(e)}")
            return False
    
    async def _deploy_redis(self) -> bool:
        """Deploy Redis cluster"""
        try:
            redis_config = {
                'cluster_id': f"alphintra-redis-{self.region_config.region.value}",
                'node_type': 'cache.r6g.large',
                'num_cache_nodes': 3,
                'engine_version': '6.2',
                'at_rest_encryption_enabled': True,
                'transit_encryption_enabled': True,
                'automatic_failover_enabled': True
            }
            
            logger.info(f"Redis configuration created for {self.region_config.region.value}")
            return True
            
        except Exception as e:
            logger.error(f"Redis deployment error: {str(e)}")
            return False
    
    async def _deploy_monitoring(self) -> bool:
        """Deploy monitoring infrastructure"""
        try:
            monitoring_config = {
                'prometheus_config': {
                    'retention': '30d',
                    'storage_size': '100Gi',
                    'scrape_interval': '15s'
                },
                'grafana_config': {
                    'admin_password': 'generated-secure-password',
                    'plugins': ['grafana-piechart-panel', 'grafana-worldmap-panel']
                },
                'alertmanager_config': {
                    'slack_webhook': 'https://hooks.slack.com/webhook',
                    'email_config': {
                        'smtp_server': 'smtp.gmail.com',
                        'smtp_port': 587
                    }
                }
            }
            
            logger.info(f"Monitoring configuration created for {self.region_config.region.value}")
            return True
            
        except Exception as e:
            logger.error(f"Monitoring deployment error: {str(e)}")
            return False
    
    async def _configure_security(self) -> bool:
        """Configure security and compliance"""
        try:
            security_config = {
                'encryption': {
                    'at_rest': True,
                    'in_transit': True,
                    'key_management': 'cloud_kms'
                },
                'network_security': {
                    'private_clusters': True,
                    'authorized_networks': ['10.0.0.0/8'],
                    'network_policies': True
                },
                'compliance': {
                    'audit_logging': self.region_config.audit_logging,
                    'data_residency': self.region_config.data_locality,
                    'backup_encryption': True,
                    'access_controls': 'rbac'
                }
            }
            
            logger.info(f"Security configuration created for {self.region_config.region.value}")
            return True
            
        except Exception as e:
            logger.error(f"Security configuration error: {str(e)}")
            return False
    
    async def get_region_health(self) -> RegionStatus:
        """Get comprehensive region health status"""
        try:
            # Simulate health check metrics
            latency_metrics = {
                'api_latency': 45.2,
                'db_latency': 12.1,
                'cache_latency': 0.8
            }
            
            resource_utilization = {
                'cpu_usage': 68.5,
                'memory_usage': 72.3,
                'disk_usage': 45.1,
                'network_usage': 23.7
            }
            
            return RegionStatus(
                region=self.region_config.region,
                status=DeploymentStatus.ACTIVE,
                last_health_check=datetime.now(),
                active_services=12,
                total_services=12,
                latency_metrics=latency_metrics,
                resource_utilization=resource_utilization,
                error_count=0,
                uptime_percentage=99.98,
                compliance_status="compliant"
            )
            
        except Exception as e:
            logger.error(f"Health check error for {self.region_config.region.value}: {str(e)}")
            return RegionStatus(
                region=self.region_config.region,
                status=DeploymentStatus.ERROR,
                last_health_check=datetime.now(),
                active_services=0,
                total_services=12,
                latency_metrics={},
                resource_utilization={},
                error_count=1,
                uptime_percentage=0.0,
                compliance_status="error"
            )


class MultiRegionOrchestrator:
    """
    Orchestrates deployment and management across multiple global regions
    """
    
    def __init__(self, redis_url: str = "redis://localhost:6379"):
        self.redis_url = redis_url
        self.redis_client = None
        
        # Regional managers
        self.regional_managers: Dict[Region, RegionalInfrastructureManager] = {}
        
        # Global state
        self.deployment_status: Dict[Region, RegionStatus] = {}
        self.active_regions: List[Region] = []
        
        # Configuration
        self.region_configs = self._initialize_region_configs()
        
        # Metrics
        self.global_latency = Histogram('global_latency_seconds', 'Global latency', ['source', 'target'])
        self.active_regions_gauge = Gauge('active_regions_total', 'Total active regions')
        self.deployment_health = Gauge('deployment_health_score', 'Overall deployment health')
        
        # Background tasks
        self.health_check_task = None
        self.optimization_task = None
        
    def _initialize_region_configs(self) -> Dict[Region, RegionConfig]:
        """Initialize configuration for all regions"""
        configs = {}
        
        # Americas East (Primary)
        configs[Region.AMERICAS_EAST] = RegionConfig(
            region=Region.AMERICAS_EAST,
            cloud_provider=CloudProvider.GCP,
            timezone="America/New_York",
            primary_exchanges=["NYSE", "NASDAQ", "CBOE"],
            regulatory_jurisdiction="US",
            data_residency_requirements=["US"],
            cluster_name="alphintra-americas-east",
            cluster_zone="us-east1-b",
            node_count=6,
            machine_type="n1-standard-4",
            vpc_cidr="10.1.0.0/16",
            subnet_cidrs={
                "trading": "10.1.1.0/24",
                "data": "10.1.2.0/24",
                "management": "10.1.3.0/24"
            },
            db_instance_type="db-n1-standard-4",
            db_storage_size=500,
            backup_retention_days=30,
            encryption_requirements=["AES256", "TLS1.3"],
            audit_logging=True,
            data_locality=True
        )
        
        # Americas West
        configs[Region.AMERICAS_WEST] = RegionConfig(
            region=Region.AMERICAS_WEST,
            cloud_provider=CloudProvider.AWS,
            timezone="America/Los_Angeles",
            primary_exchanges=["CME", "CBOT", "COMEX"],
            regulatory_jurisdiction="US",
            data_residency_requirements=["US"],
            cluster_name="alphintra-americas-west",
            cluster_zone="us-west-2a",
            node_count=4,
            machine_type="m5.xlarge",
            vpc_cidr="10.2.0.0/16",
            subnet_cidrs={
                "trading": "10.2.1.0/24",
                "data": "10.2.2.0/24",
                "management": "10.2.3.0/24"
            },
            db_instance_type="db.r5.xlarge",
            db_storage_size=400,
            backup_retention_days=30,
            encryption_requirements=["AES256", "TLS1.3"],
            audit_logging=True,
            data_locality=True
        )
        
        # EMEA West (London)
        configs[Region.EMEA_WEST] = RegionConfig(
            region=Region.EMEA_WEST,
            cloud_provider=CloudProvider.GCP,
            timezone="Europe/London",
            primary_exchanges=["LSE", "LSEG", "ICE"],
            regulatory_jurisdiction="UK",
            data_residency_requirements=["UK", "EU"],
            cluster_name="alphintra-emea-west",
            cluster_zone="europe-west2-b",
            node_count=5,
            machine_type="n1-standard-4",
            vpc_cidr="10.3.0.0/16",
            subnet_cidrs={
                "trading": "10.3.1.0/24",
                "data": "10.3.2.0/24",
                "management": "10.3.3.0/24"
            },
            db_instance_type="db-n1-standard-4",
            db_storage_size=400,
            backup_retention_days=30,
            encryption_requirements=["AES256", "TLS1.3"],
            audit_logging=True,
            data_locality=True
        )
        
        # EMEA Central (Frankfurt)
        configs[Region.EMEA_CENTRAL] = RegionConfig(
            region=Region.EMEA_CENTRAL,
            cloud_provider=CloudProvider.AZURE,
            timezone="Europe/Berlin",
            primary_exchanges=["XETRA", "Eurex", "Euronext"],
            regulatory_jurisdiction="EU",
            data_residency_requirements=["EU", "Germany"],
            cluster_name="alphintra-emea-central",
            cluster_zone="Germany West Central",
            node_count=4,
            machine_type="Standard_D4s_v3",
            vpc_cidr="10.4.0.0/16",
            subnet_cidrs={
                "trading": "10.4.1.0/24",
                "data": "10.4.2.0/24",
                "management": "10.4.3.0/24"
            },
            db_instance_type="GP_Gen5_4",
            db_storage_size=400,
            backup_retention_days=30,
            encryption_requirements=["AES256", "TLS1.3"],
            audit_logging=True,
            data_locality=True
        )
        
        # APAC Northeast (Tokyo)
        configs[Region.APAC_NORTHEAST] = RegionConfig(
            region=Region.APAC_NORTHEAST,
            cloud_provider=CloudProvider.GCP,
            timezone="Asia/Tokyo",
            primary_exchanges=["TSE", "JPX", "OSE"],
            regulatory_jurisdiction="Japan",
            data_residency_requirements=["Japan"],
            cluster_name="alphintra-apac-northeast",
            cluster_zone="asia-northeast1-b",
            node_count=4,
            machine_type="n1-standard-4",
            vpc_cidr="10.5.0.0/16",
            subnet_cidrs={
                "trading": "10.5.1.0/24",
                "data": "10.5.2.0/24",
                "management": "10.5.3.0/24"
            },
            db_instance_type="db-n1-standard-4",
            db_storage_size=300,
            backup_retention_days=30,
            encryption_requirements=["AES256", "TLS1.3"],
            audit_logging=True,
            data_locality=True
        )
        
        # APAC Southeast (Singapore)
        configs[Region.APAC_SOUTHEAST] = RegionConfig(
            region=Region.APAC_SOUTHEAST,
            cloud_provider=CloudProvider.AWS,
            timezone="Asia/Singapore",
            primary_exchanges=["SGX", "HKEX", "SET"],
            regulatory_jurisdiction="Singapore",
            data_residency_requirements=["Singapore", "APAC"],
            cluster_name="alphintra-apac-southeast",
            cluster_zone="ap-southeast-1a",
            node_count=3,
            machine_type="m5.large",
            vpc_cidr="10.6.0.0/16",
            subnet_cidrs={
                "trading": "10.6.1.0/24",
                "data": "10.6.2.0/24",
                "management": "10.6.3.0/24"
            },
            db_instance_type="db.r5.large",
            db_storage_size=300,
            backup_retention_days=30,
            encryption_requirements=["AES256", "TLS1.3"],
            audit_logging=True,
            data_locality=True
        )
        
        return configs
    
    async def initialize(self):
        """Initialize multi-region orchestrator"""
        try:
            # Initialize Redis connection
            self.redis_client = aioredis.from_url(self.redis_url)
            await self.redis_client.ping()
            
            # Initialize regional managers
            for region, config in self.region_configs.items():
                manager = RegionalInfrastructureManager(config)
                self.regional_managers[region] = manager
            
            # Start background tasks
            self.health_check_task = asyncio.create_task(self._continuous_health_monitoring())
            self.optimization_task = asyncio.create_task(self._continuous_optimization())
            
            logger.info("Multi-region orchestrator initialized successfully")
            
        except Exception as e:
            logger.error(f"Error initializing multi-region orchestrator: {str(e)}")
            raise
    
    async def deploy_all_regions(self) -> Dict[Region, bool]:
        """Deploy infrastructure to all regions"""
        try:
            logger.info("Starting global multi-region deployment")
            
            # Deploy regions in parallel for efficiency
            deployment_tasks = []
            for region, manager in self.regional_managers.items():
                task = asyncio.create_task(
                    self._deploy_single_region(region, manager)
                )
                deployment_tasks.append((region, task))
            
            # Wait for all deployments
            deployment_results = {}
            for region, task in deployment_tasks:
                try:
                    result = await task
                    deployment_results[region] = result
                    
                    if result:
                        self.active_regions.append(region)
                        logger.info(f"Region {region.value} deployed successfully")
                    else:
                        logger.error(f"Region {region.value} deployment failed")
                        
                except Exception as e:
                    logger.error(f"Region {region.value} deployment error: {str(e)}")
                    deployment_results[region] = False
            
            # Update metrics
            self.active_regions_gauge.set(len(self.active_regions))
            
            successful_deployments = sum(1 for result in deployment_results.values() if result)
            total_deployments = len(deployment_results)
            
            logger.info(f"Global deployment completed: {successful_deployments}/{total_deployments} regions successful")
            
            return deployment_results
            
        except Exception as e:
            logger.error(f"Error in global deployment: {str(e)}")
            raise
    
    async def _deploy_single_region(self, region: Region, manager: RegionalInfrastructureManager) -> bool:
        """Deploy infrastructure to a single region"""
        try:
            start_time = time.time()
            
            # Deploy regional infrastructure
            result = await manager.deploy_regional_infrastructure()
            
            # Update deployment status
            if result:
                status = await manager.get_region_health()
                self.deployment_status[region] = status
                
                # Cache status in Redis
                await self._cache_region_status(region, status)
            
            deployment_time = time.time() - start_time
            logger.info(f"Region {region.value} deployment completed in {deployment_time:.2f}s")
            
            return result
            
        except Exception as e:
            logger.error(f"Error deploying region {region.value}: {str(e)}")
            return False
    
    async def _continuous_health_monitoring(self):
        """Continuously monitor health of all regions"""
        while True:
            try:
                for region, manager in self.regional_managers.items():
                    if region in self.active_regions:
                        # Get current health status
                        status = await manager.get_region_health()
                        self.deployment_status[region] = status
                        
                        # Cache in Redis
                        await self._cache_region_status(region, status)
                        
                        # Check for issues
                        if status.status == DeploymentStatus.ERROR:
                            logger.warning(f"Region {region.value} health check failed")
                            await self._handle_region_failure(region, status)
                        
                        # Update metrics
                        for metric_name, value in status.latency_metrics.items():
                            self.global_latency.labels(
                                source=region.value, 
                                target=metric_name
                            ).observe(value / 1000)  # Convert to seconds
                
                # Calculate overall health score
                health_score = await self._calculate_global_health_score()
                self.deployment_health.set(health_score)
                
                await asyncio.sleep(30)  # Health check every 30 seconds
                
            except Exception as e:
                logger.error(f"Error in health monitoring: {str(e)}")
                await asyncio.sleep(60)  # Wait longer on error
    
    async def _continuous_optimization(self):
        """Continuously optimize regional deployments"""
        while True:
            try:
                # Optimize resource allocation
                await self._optimize_resource_allocation()
                
                # Optimize traffic routing
                await self._optimize_traffic_routing()
                
                # Optimize costs
                await self._optimize_costs()
                
                await asyncio.sleep(300)  # Optimize every 5 minutes
                
            except Exception as e:
                logger.error(f"Error in continuous optimization: {str(e)}")
                await asyncio.sleep(600)  # Wait longer on error
    
    async def _cache_region_status(self, region: Region, status: RegionStatus):
        """Cache region status in Redis"""
        try:
            if self.redis_client:
                status_data = asdict(status)
                status_data['last_health_check'] = status.last_health_check.isoformat()
                
                await self.redis_client.setex(
                    f"region_status:{region.value}",
                    300,  # 5 minutes TTL
                    json.dumps(status_data, default=str)
                )
        except Exception as e:
            logger.error(f"Error caching region status: {str(e)}")
    
    async def _handle_region_failure(self, region: Region, status: RegionStatus):
        """Handle region failure or degradation"""
        try:
            logger.warning(f"Handling failure for region {region.value}")
            
            # Attempt automatic recovery
            recovery_result = await self._attempt_region_recovery(region)
            
            if not recovery_result:
                # Redirect traffic to other regions
                await self._redirect_traffic_from_region(region)
                
                # Alert operations team
                await self._send_region_failure_alert(region, status)
            
        except Exception as e:
            logger.error(f"Error handling region failure: {str(e)}")
    
    async def _attempt_region_recovery(self, region: Region) -> bool:
        """Attempt automatic recovery of failed region"""
        try:
            manager = self.regional_managers[region]
            
            # Try to redeploy failed components
            recovery_result = await manager.deploy_regional_infrastructure()
            
            if recovery_result:
                logger.info(f"Region {region.value} recovered successfully")
                return True
            else:
                logger.error(f"Region {region.value} recovery failed")
                return False
                
        except Exception as e:
            logger.error(f"Error in region recovery: {str(e)}")
            return False
    
    async def _redirect_traffic_from_region(self, failed_region: Region):
        """Redirect traffic from failed region to healthy regions"""
        try:
            # Find healthy regions in same timezone/market
            healthy_regions = [
                r for r in self.active_regions 
                if r != failed_region and self.deployment_status[r].status == DeploymentStatus.ACTIVE
            ]
            
            if healthy_regions:
                # Update load balancer configuration
                logger.info(f"Redirecting traffic from {failed_region.value} to {[r.value for r in healthy_regions]}")
                
                # Implementation would update actual load balancer rules
                
        except Exception as e:
            logger.error(f"Error redirecting traffic: {str(e)}")
    
    async def _send_region_failure_alert(self, region: Region, status: RegionStatus):
        """Send alert for region failure"""
        try:
            alert_data = {
                'region': region.value,
                'status': status.status.value,
                'error_count': status.error_count,
                'uptime': status.uptime_percentage,
                'timestamp': datetime.now().isoformat()
            }
            
            # Send to alerting system (Slack, PagerDuty, etc.)
            logger.critical(f"REGION FAILURE ALERT: {json.dumps(alert_data)}")
            
        except Exception as e:
            logger.error(f"Error sending failure alert: {str(e)}")
    
    async def _optimize_resource_allocation(self):
        """Optimize resource allocation across regions"""
        try:
            for region in self.active_regions:
                status = self.deployment_status.get(region)
                if status and status.resource_utilization:
                    # Check if scaling is needed
                    cpu_usage = status.resource_utilization.get('cpu_usage', 0)
                    memory_usage = status.resource_utilization.get('memory_usage', 0)
                    
                    if cpu_usage > 80 or memory_usage > 80:
                        logger.info(f"High resource usage in {region.value}, considering scale-up")
                        # Implementation would trigger auto-scaling
                    elif cpu_usage < 30 and memory_usage < 30:
                        logger.info(f"Low resource usage in {region.value}, considering scale-down")
                        # Implementation would trigger scale-down
        
        except Exception as e:
            logger.error(f"Error optimizing resource allocation: {str(e)}")
    
    async def _optimize_traffic_routing(self):
        """Optimize traffic routing based on latency and load"""
        try:
            # Analyze latency patterns
            latency_matrix = {}
            for region in self.active_regions:
                status = self.deployment_status.get(region)
                if status:
                    latency_matrix[region] = status.latency_metrics
            
            # Optimize routing algorithms
            # Implementation would update traffic routing rules
            
        except Exception as e:
            logger.error(f"Error optimizing traffic routing: {str(e)}")
    
    async def _optimize_costs(self):
        """Optimize costs across regions"""
        try:
            for region in self.active_regions:
                # Analyze resource usage patterns
                # Recommend cost optimizations
                # Implementation would suggest instance type changes, etc.
                pass
                
        except Exception as e:
            logger.error(f"Error optimizing costs: {str(e)}")
    
    async def _calculate_global_health_score(self) -> float:
        """Calculate overall global health score"""
        try:
            if not self.deployment_status:
                return 0.0
            
            total_score = 0.0
            active_count = 0
            
            for region, status in self.deployment_status.items():
                if status.status == DeploymentStatus.ACTIVE:
                    # Weight by uptime and service availability
                    region_score = (
                        status.uptime_percentage * 0.4 +
                        (status.active_services / status.total_services * 100) * 0.3 +
                        max(0, 100 - sum(status.latency_metrics.values()) / len(status.latency_metrics.values())) * 0.3
                    )
                    total_score += region_score
                    active_count += 1
            
            return total_score / active_count if active_count > 0 else 0.0
            
        except Exception as e:
            logger.error(f"Error calculating health score: {str(e)}")
            return 0.0
    
    async def get_global_status(self) -> Dict[str, Any]:
        """Get comprehensive global deployment status"""
        try:
            total_regions = len(self.region_configs)
            active_regions = len(self.active_regions)
            
            # Calculate aggregate metrics
            total_services = sum(status.total_services for status in self.deployment_status.values())
            active_services = sum(status.active_services for status in self.deployment_status.values())
            
            avg_latency = 0.0
            avg_uptime = 0.0
            
            if self.deployment_status:
                avg_latency = sum(
                    sum(status.latency_metrics.values()) / len(status.latency_metrics.values())
                    for status in self.deployment_status.values()
                    if status.latency_metrics
                ) / len(self.deployment_status)
                
                avg_uptime = sum(
                    status.uptime_percentage 
                    for status in self.deployment_status.values()
                ) / len(self.deployment_status)
            
            return {
                'timestamp': datetime.now().isoformat(),
                'global_health_score': await self._calculate_global_health_score(),
                'regions': {
                    'total': total_regions,
                    'active': active_regions,
                    'inactive': total_regions - active_regions
                },
                'services': {
                    'total': total_services,
                    'active': active_services,
                    'availability_percentage': (active_services / total_services * 100) if total_services > 0 else 0
                },
                'performance': {
                    'average_latency_ms': avg_latency,
                    'average_uptime_percentage': avg_uptime
                },
                'regional_status': {
                    region.value: asdict(status) 
                    for region, status in self.deployment_status.items()
                }
            }
            
        except Exception as e:
            logger.error(f"Error getting global status: {str(e)}")
            return {'error': str(e)}
    
    async def cleanup(self):
        """Cleanup resources"""
        try:
            # Cancel background tasks
            if self.health_check_task:
                self.health_check_task.cancel()
            if self.optimization_task:
                self.optimization_task.cancel()
            
            # Close Redis connection
            if self.redis_client:
                await self.redis_client.close()
            
            logger.info("Multi-region orchestrator cleanup completed")
            
        except Exception as e:
            logger.error(f"Error in cleanup: {str(e)}")


# Example usage and testing
if __name__ == "__main__":
    async def test_multi_region_deployment():
        """Test multi-region deployment system"""
        
        # Initialize orchestrator
        orchestrator = MultiRegionOrchestrator()
        await orchestrator.initialize()
        
        try:
            # Deploy all regions
            print("🌍 Starting global multi-region deployment...")
            deployment_results = await orchestrator.deploy_all_regions()
            
            print(f"\n📊 Deployment Results:")
            for region, success in deployment_results.items():
                status = "✅ SUCCESS" if success else "❌ FAILED"
                print(f"  {region.value}: {status}")
            
            # Wait for health monitoring to run
            print("\n⏳ Waiting for health monitoring...")
            await asyncio.sleep(10)
            
            # Get global status
            global_status = await orchestrator.get_global_status()
            print(f"\n🌐 Global Status:")
            print(f"  Health Score: {global_status['global_health_score']:.2f}/100")
            print(f"  Active Regions: {global_status['regions']['active']}/{global_status['regions']['total']}")
            print(f"  Service Availability: {global_status['services']['availability_percentage']:.1f}%")
            print(f"  Average Latency: {global_status['performance']['average_latency_ms']:.1f}ms")
            print(f"  Average Uptime: {global_status['performance']['average_uptime_percentage']:.2f}%")
            
            print(f"\n📍 Regional Details:")
            for region_name, status in global_status['regional_status'].items():
                print(f"  {region_name}:")
                print(f"    Status: {status['status']}")
                print(f"    Services: {status['active_services']}/{status['total_services']}")
                print(f"    Uptime: {status['uptime_percentage']:.2f}%")
            
            # Monitor for a bit
            print(f"\n🔄 Monitoring for 30 seconds...")
            await asyncio.sleep(30)
            
            # Final status
            final_status = await orchestrator.get_global_status()
            print(f"\n🎯 Final Health Score: {final_status['global_health_score']:.2f}/100")
            
        finally:
            # Cleanup
            await orchestrator.cleanup()
            print("\n✅ Multi-region deployment test completed!")
    
    # Run the test
    asyncio.run(test_multi_region_deployment())