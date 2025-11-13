# Alphintra Cloud Architecture Documentation

## 📖 Overview

This directory contains comprehensive documentation of the Alphintra platform's cloud architecture, deployed on Google Cloud Platform (GCP). The documentation was generated through extensive analysis of the infrastructure code, Kubernetes manifests, CI/CD pipelines, and live cluster inspection.

---

## 📚 Documentation Files

### 1. [CLOUD_ARCHITECTURE.md](./CLOUD_ARCHITECTURE.md)
**The Complete Architecture Document** (65+ pages)

Comprehensive documentation covering:
- ✅ Executive summary and architecture overview
- ✅ Infrastructure components (GKE, Cloud SQL, Artifact Registry)
- ✅ Microservices architecture and service inventory
- ✅ Network architecture (VPC, subnets, firewall, egress)
- ✅ Security & identity (Workload Identity, mTLS, JWT)
- ✅ Data layer (Cloud SQL, Redis, connection patterns)
- ✅ Service mesh (Istio configuration, traffic management)
- ✅ CI/CD pipeline (Cloud Build, GitHub Actions, ArgoCD)
- ✅ Observability (Prometheus, Grafana, logging, tracing)
- ✅ Deployment strategy (environments, rollouts, health checks)
- ✅ Disaster recovery & high availability
- ✅ Infrastructure management (Terraform, Kustomize)
- ✅ Cost optimization and compliance
- ✅ Troubleshooting guide and operations manual

**Target Audience**: DevOps engineers, architects, new team members

---

### 2. [ARCHITECTURE_DIAGRAMS.md](./ARCHITECTURE_DIAGRAMS.md)
**Visual Architecture Diagrams** (10 comprehensive diagrams)

Includes Mermaid diagrams for:
1. **High-Level System Architecture** - Complete platform overview
2. **Network Architecture** - VPC, subnets, IPs, firewalls
3. **Service Mesh (Istio)** - mTLS, gateways, virtual services
4. **CI/CD Pipeline** - Build and deployment flow
5. **Data Flow** - Request sequence diagram
6. **Observability Stack** - Monitoring and alerting architecture
7. **Security Architecture** - Authentication, encryption, secrets
8. **Deployment Topology** - Multi-environment setup
9. **Infrastructure as Code** - Terraform module structure
10. **Kubernetes Resources** - Kustomize hierarchy

**Target Audience**: Visual learners, stakeholders, presentations

**How to View**:
- GitHub: Renders automatically in markdown
- VS Code: Install "Markdown Preview Mermaid Support" extension
- Export images: https://mermaid.live/

---

### 3. [ARCHITECTURE_QUICK_REFERENCE.md](./ARCHITECTURE_QUICK_REFERENCE.md)
**Quick Reference Guide** (10-15 minutes read)

Fast-access guide containing:
- 📊 Quick facts and access points
- 🏗️ Architecture layers summary
- 🔐 Security overview
- 📦 Service inventory table
- 💾 Data stores configuration
- 🚀 CI/CD pipeline summary
- 📊 Observability setup
- 🌍 Network configuration
- 🛠️ Common operations cheatsheet
- 📈 Capacity and scaling guidelines
- 💰 Cost breakdown
- 🔄 Disaster recovery status
- 📞 Troubleshooting quick guide

**Target Audience**: On-call engineers, quick lookups, incident response

---

## 🎯 How to Use This Documentation

### For New Team Members
1. Start with [ARCHITECTURE_QUICK_REFERENCE.md](./ARCHITECTURE_QUICK_REFERENCE.md) for overview
2. Review [ARCHITECTURE_DIAGRAMS.md](./ARCHITECTURE_DIAGRAMS.md) for visual understanding
3. Deep dive into [CLOUD_ARCHITECTURE.md](./CLOUD_ARCHITECTURE.md) for comprehensive details
4. Explore `infra/` directory to see actual implementation

### For Operations
1. Keep [ARCHITECTURE_QUICK_REFERENCE.md](./ARCHITECTURE_QUICK_REFERENCE.md) bookmarked
2. Use "Common Operations" section for daily tasks
3. Reference "Troubleshooting" section during incidents
4. Check service inventory for ports and endpoints

### For Architecture & Planning
1. Study [CLOUD_ARCHITECTURE.md](./CLOUD_ARCHITECTURE.md) thoroughly
2. Use [ARCHITECTURE_DIAGRAMS.md](./ARCHITECTURE_DIAGRAMS.md) for presentations
3. Reference "Roadmap" and "Future Enhancements" sections
4. Review cost optimization opportunities

### For Security Review
1. Focus on "Security & Identity" section in full doc
2. Review Security Architecture diagram
3. Check Workload Identity and IAM configurations
4. Validate secret management practices

---

## 🔍 Key Findings

### Current State (as of Nov 4, 2025)

**✅ Strengths**:
- Modern cloud-native architecture on GKE
- Istio service mesh with strict mTLS
- Comprehensive CI/CD with Cloud Build + GitHub Actions
- Infrastructure as Code with Terraform
- GitOps with ArgoCD (partial)
- 9 microservices deployed and operational
- Cloud SQL with private networking
- Structured logging and monitoring foundation

**⚠️ Areas for Improvement**:
- Single-zone GKE cluster (dev) - needs regional for HA
- No Memorystore Redis yet (using in-cluster)
- Staging and production environments not fully configured
- Limited auto-scaling (only service-gateway has HPA)
- Observability incomplete (tracing planned, alerting basic)
- No formal DR plan or multi-region setup
- Cost optimization opportunities (spot VMs, committed use)

**🚀 High Priority Actions**:
1. Enable GKE regional cluster for high availability
2. Implement Cloud SQL HA with read replicas
3. Deploy Memorystore Redis (replace in-cluster)
4. Complete observability stack (tracing, comprehensive alerts)
5. Set up staging environment with proper promotion flow
6. Implement auto-scaling for all services
7. Document and test DR procedures

---

## 📊 Architecture at a Glance

```
┌─────────────────────────────────────────────────────────────┐
│                    Google Cloud Platform                     │
│                   Project: alphintra-472817                  │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌────────────────────────────────────────────────────┐    │
│  │  GKE Cluster (alphintra-cluster)                   │    │
│  │  • 5 nodes (us-central1-a)                         │    │
│  │  • Kubernetes 1.33.5                               │    │
│  │  • Istio Service Mesh (ASM 1.17.2)                │    │
│  │                                                     │    │
│  │  Namespaces:                                       │    │
│  │  ├─ alphintra (9 services)                        │    │
│  │  ├─ istio-system (service mesh)                   │    │
│  │  ├─ observability (Prometheus, Grafana)           │    │
│  │  ├─ cert-manager (TLS)                            │    │
│  │  └─ default (frontend)                            │    │
│  └────────────────────────────────────────────────────┘    │
│                                                              │
│  Data Layer:                                                 │
│  • Cloud SQL PostgreSQL (10.6.124.3)                       │
│  • Redis (in-cluster, ClusterIP)                           │
│                                                              │
│  Storage:                                                    │
│  • Artifact Registry (us-central1)                         │
│  • Cloud Storage (build caches)                            │
│  • Secret Manager (credentials)                            │
│                                                              │
│  Networking:                                                 │
│  • External LB: 34.172.120.224                             │
│  • NAT Gateway: 34.134.209.61                              │
│  • VPC: default (10.128.0.0/20)                            │
│  • Pod Network: 10.32.0.0/14                               │
└─────────────────────────────────────────────────────────────┘

External Access:
  Internet → Load Balancer → Istio Gateway → service-gateway
                                                    ↓
                                              Backend Services
                                                    ↓
                                              Cloud SQL (private)
```

---

## 🔗 Related Documentation

### Internal Documents
- [Gateway Overview](../gateway/overview.md)
- [Auth Service Runbook](../auth-service-runbook.md)
- [Istio Rollout Plan](../mesh/istio-rollout.md)
- [Observability README](../observability/README.md)
- [Rollout Strategy](./rollout-strategy.md)
- [Prerequisites](./prerequisites.md)
- [Cloud Baseline](./cloud-baseline.md)

### Infrastructure Code
- Terraform: `infra/terraform/`
- Kubernetes: `infra/kubernetes/`
- GitOps: `infra/gitops/`
- Scripts: `infra/scripts/`

### CI/CD
- GitHub Workflows: `.github/workflows/`
- Cloud Build configs: `src/*/cloudbuild.yaml`

---

## 🛠️ Maintenance

### Updating Documentation

This documentation should be updated when:
- ✏️ New services are added or removed
- ✏️ Infrastructure changes (new GCP services, configuration)
- ✏️ Network topology changes
- ✏️ Security policies change
- ✏️ Deployment strategies evolve
- ✏️ Major version upgrades (K8s, Istio, etc.)

**Review Frequency**: Monthly (or after major changes)

### How to Update
1. Make changes to the relevant markdown file
2. Update version number and date in document footer
3. Regenerate diagrams if architecture changes
4. Commit with descriptive message: `docs: Update architecture for [change]`
5. Create PR for team review

### Diagram Updates
- Edit Mermaid code directly in ARCHITECTURE_DIAGRAMS.md
- Test rendering at https://mermaid.live/
- Ensure all new services/components are represented
- Update color coding legend if needed

---

## 🤝 Contributing

### Documentation Standards
- Use clear, concise language
- Include code examples where helpful
- Keep tables and lists for easy scanning
- Use emoji sparingly for section headers
- Maintain consistent formatting
- Link to related docs

### Diagram Standards
- Follow established color coding
- Use descriptive labels
- Keep complexity manageable
- Group related components in subgraphs
- Test rendering in multiple viewers

---

## 📝 Change Log

### Version 1.0 (November 4, 2025)
- ✅ Initial comprehensive documentation created
- ✅ 10 architecture diagrams developed
- ✅ Quick reference guide completed
- ✅ Analysis of live cluster (kubectl/gcloud commands)
- ✅ Terraform and Kubernetes manifest analysis
- ✅ CI/CD pipeline documentation
- ✅ Security and network architecture documented

### Planned Updates
- 📋 Add TimescaleDB architecture (when deployed)
- 📋 Document Kafka integration (planned)
- 📋 Multi-region DR architecture
- 📋 Production environment details
- 📋 Performance benchmarking results
- 📋 Cost optimization case studies

---

## 📞 Support

### Questions or Clarifications
For questions about this documentation:
1. Check existing docs in `docs/` directory
2. Review inline comments in infrastructure code
3. Search GitHub issues for related discussions
4. Contact platform team via Slack #platform-team

### Reporting Issues
Found an error or outdated information?
1. Create GitHub issue with label `documentation`
2. Include page/section reference
3. Suggest correction or update
4. Tag platform team members

---

## 📜 License & Ownership

**Owner**: Alphintra Platform Team  
**Repository**: Subithan/Alphintra  
**Confidentiality**: Internal Use Only  

This documentation contains proprietary information about Alphintra's infrastructure and should not be shared externally.

---

## 🎓 Additional Learning Resources

### GCP & Kubernetes
- [GKE Documentation](https://cloud.google.com/kubernetes-engine/docs)
- [GKE Best Practices](https://cloud.google.com/kubernetes-engine/docs/best-practices)
- [Kubernetes Documentation](https://kubernetes.io/docs/)

### Service Mesh
- [Istio Documentation](https://istio.io/latest/docs/)
- [Istio Best Practices](https://istio.io/latest/docs/ops/best-practices/)
- [Service Mesh Comparison](https://servicemesh.es/)

### Spring & Java
- [Spring Cloud Gateway](https://spring.io/projects/spring-cloud-gateway)
- [Spring Boot on GKE](https://cloud.google.com/java/spring)

### Infrastructure as Code
- [Terraform Best Practices](https://www.terraform-best-practices.com/)
- [Kustomize Documentation](https://kustomize.io/)

### GitOps
- [ArgoCD Documentation](https://argo-cd.readthedocs.io/)
- [GitOps Principles](https://opengitops.dev/)

---

**Last Updated**: November 4, 2025  
**Next Review**: December 4, 2025  
**Maintained By**: Alphintra Platform Team
