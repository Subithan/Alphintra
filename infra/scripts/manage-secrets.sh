#!/bin/bash

# Kubernetes Secrets Management Script for Alphintra Platform
# This script helps view, update, and delete secrets

set -e

# Color codes for output
RED='\033[31m'
GREEN='\033[32m'
YELLOW='\033[33m'
BLUE='\033[34m'
CYAN='\033[36m'
RESET='\033[0m'

show_help() {
    echo -e "${CYAN}🔐 Alphintra Secrets Management${RESET}"
    echo -e "${BLUE}===============================${RESET}"
    echo ""
    echo "Usage: $0 [COMMAND]"
    echo ""
    echo "Commands:"
    echo "  list           List all secrets"
    echo "  view SECRET    View secret details (without values)"
    echo "  export SECRET  Export secret values (be careful!)"
    echo "  delete SECRET  Delete a secret"
    echo "  reset          Reset all secrets (interactive setup)"
    echo "  backup         Backup secrets to encrypted file"
    echo "  help           Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0 list"
    echo "  $0 view alphintra-secrets"
    echo "  $0 export alphintra-secrets"
    echo "  $0 delete api-keys"
    echo ""
}

list_secrets() {
    echo -e "${CYAN}📋 All Kubernetes Secrets${RESET}"
    echo ""
    echo -e "${YELLOW}Alphintra Namespace:${RESET}"
    kubectl get secrets -n alphintra --no-headers | while read secret type data age; do
        echo "  🔑 $secret ($data keys, $age old)"
    done
    echo ""
    echo -e "${YELLOW}Monitoring Namespace:${RESET}"
    kubectl get secrets -n monitoring --no-headers | while read secret type data age; do
        echo "  📊 $secret ($data keys, $age old)"
    done
    echo ""
}

view_secret() {
    local secret_name="$1"
    local namespace="$2"
    
    if [ -z "$secret_name" ]; then
        echo -e "${RED}❌ Secret name is required${RESET}"
        echo "Usage: $0 view SECRET [NAMESPACE]"
        return 1
    fi
    
    # Try to find the secret in common namespaces if namespace not specified
    if [ -z "$namespace" ]; then
        if kubectl get secret "$secret_name" -n alphintra > /dev/null 2>&1; then
            namespace="alphintra"
        elif kubectl get secret "$secret_name" -n monitoring > /dev/null 2>&1; then
            namespace="monitoring"
        else
            echo -e "${RED}❌ Secret '$secret_name' not found in alphintra or monitoring namespaces${RESET}"
            return 1
        fi
    fi
    
    echo -e "${CYAN}🔍 Secret Details: $secret_name${RESET}"
    echo -e "${YELLOW}Namespace: $namespace${RESET}"
    echo ""
    kubectl describe secret "$secret_name" -n "$namespace"
}

export_secret() {
    local secret_name="$1"
    local namespace="$2"
    
    if [ -z "$secret_name" ]; then
        echo -e "${RED}❌ Secret name is required${RESET}"
        echo "Usage: $0 export SECRET [NAMESPACE]"
        return 1
    fi
    
    # Try to find the secret in common namespaces if namespace not specified
    if [ -z "$namespace" ]; then
        if kubectl get secret "$secret_name" -n alphintra > /dev/null 2>&1; then
            namespace="alphintra"
        elif kubectl get secret "$secret_name" -n monitoring > /dev/null 2>&1; then
            namespace="monitoring"
        else
            echo -e "${RED}❌ Secret '$secret_name' not found in alphintra or monitoring namespaces${RESET}"
            return 1
        fi
    fi
    
    echo -e "${RED}⚠️  WARNING: This will display sensitive secret values!${RESET}"
    read -p "Are you sure you want to export secret '$secret_name'? (y/N): " confirm
    
    if [[ "$confirm" =~ ^[Yy]$ ]]; then
        echo -e "${CYAN}🔓 Secret Values: $secret_name${RESET}"
        echo -e "${YELLOW}Namespace: $namespace${RESET}"
        echo ""
        kubectl get secret "$secret_name" -n "$namespace" -o jsonpath='{.data}' | jq -r 'to_entries[] | "\(.key): \(.value | @base64d)"'
    else
        echo "Export cancelled."
    fi
}

delete_secret() {
    local secret_name="$1"
    local namespace="$2"
    
    if [ -z "$secret_name" ]; then
        echo -e "${RED}❌ Secret name is required${RESET}"
        echo "Usage: $0 delete SECRET [NAMESPACE]"
        return 1
    fi
    
    # Try to find the secret in common namespaces if namespace not specified
    if [ -z "$namespace" ]; then
        if kubectl get secret "$secret_name" -n alphintra > /dev/null 2>&1; then
            namespace="alphintra"
        elif kubectl get secret "$secret_name" -n monitoring > /dev/null 2>&1; then
            namespace="monitoring"
        else
            echo -e "${RED}❌ Secret '$secret_name' not found in alphintra or monitoring namespaces${RESET}"
            return 1
        fi
    fi
    
    echo -e "${RED}⚠️  WARNING: This will permanently delete the secret!${RESET}"
    echo -e "${YELLOW}Secret: $secret_name (namespace: $namespace)${RESET}"
    read -p "Are you sure you want to delete this secret? (y/N): " confirm
    
    if [[ "$confirm" =~ ^[Yy]$ ]]; then
        kubectl delete secret "$secret_name" -n "$namespace"
        echo -e "${GREEN}✓ Secret '$secret_name' deleted successfully${RESET}"
    else
        echo "Deletion cancelled."
    fi
}

reset_secrets() {
    echo -e "${RED}⚠️  WARNING: This will delete all existing secrets and create new ones!${RESET}"
    read -p "Are you sure you want to reset all secrets? (y/N): " confirm
    
    if [[ "$confirm" =~ ^[Yy]$ ]]; then
        echo -e "${YELLOW}Deleting existing secrets...${RESET}"
        
        # Delete alphintra namespace secrets
        kubectl delete secrets --all -n alphintra || true
        
        # Delete monitoring namespace secrets  
        kubectl delete secrets --all -n monitoring || true
        
        echo -e "${GREEN}✓ All secrets deleted${RESET}"
        echo ""
        echo -e "${BLUE}🚀 Starting interactive secrets setup...${RESET}"
        ./setup-secrets.sh
    else
        echo "Reset cancelled."
    fi
}

backup_secrets() {
    local backup_file="secrets-backup-$(date +%Y%m%d-%H%M%S).yaml"
    
    echo -e "${CYAN}💾 Creating encrypted secrets backup...${RESET}"
    
    # Create backup directory
    mkdir -p ../backups
    
    # Export all secrets to YAML
    echo "# Alphintra Secrets Backup - $(date)" > "../backups/$backup_file"
    echo "# WARNING: This file contains sensitive information!" >> "../backups/$backup_file"
    echo "" >> "../backups/$backup_file"
    
    echo "# Alphintra Namespace Secrets" >> "../backups/$backup_file"
    kubectl get secrets -n alphintra -o yaml >> "../backups/$backup_file"
    
    echo "" >> "../backups/$backup_file"
    echo "# Monitoring Namespace Secrets" >> "../backups/$backup_file"
    kubectl get secrets -n monitoring -o yaml >> "../backups/$backup_file"
    
    # Encrypt the backup file
    if command -v gpg > /dev/null 2>&1; then
        echo -e "${YELLOW}Encrypting backup with GPG...${RESET}"
        gpg --symmetric --cipher-algo AES256 "../backups/$backup_file"
        rm "../backups/$backup_file"
        backup_file="${backup_file}.gpg"
        echo -e "${GREEN}✓ Encrypted backup created: ../backups/$backup_file${RESET}"
        echo -e "${YELLOW}To restore: gpg --decrypt ../backups/$backup_file | kubectl apply -f -${RESET}"
    else
        echo -e "${YELLOW}⚠️  GPG not found. Backup is unencrypted!${RESET}"
        echo -e "${GREEN}✓ Backup created: ../backups/$backup_file${RESET}"
        echo -e "${RED}Please encrypt this file manually before storing!${RESET}"
    fi
}

# Main script logic
case "${1:-help}" in
    "list")
        list_secrets
        ;;
    "view")
        view_secret "$2" "$3"
        ;;
    "export")
        export_secret "$2" "$3"
        ;;
    "delete")
        delete_secret "$2" "$3"
        ;;
    "reset")
        reset_secrets
        ;;
    "backup")
        backup_secrets
        ;;
    "help"|*)
        show_help
        ;;
esac