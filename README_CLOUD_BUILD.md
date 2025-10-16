# Cloud Build Deployment Scripts

This directory contains scripts to simplify building and deploying Alphintra services to Google Cloud Build.

## Available Scripts

### 1. Shell Script (cloud_build.sh)

A bash script that allows you to build and deploy specific services.

#### Usage

```bash
./cloud_build.sh [service-name]
```

#### Available Services

- `no-code-service`
- `auth-service`
- `service-gateway`
- `frontend`

#### Examples

```bash
# Deploy auth-service
./cloud_build.sh auth-service

# Deploy frontend
./cloud_build.sh frontend

# Deploy no-code-service
./cloud_build.sh no-code-service

# Deploy service-gateway
./cloud_build.sh service-gateway
```

### 2. Makefile

A Makefile that provides the same functionality using `make` commands.

#### Usage

```bash
make [service-name]
```

#### Available Targets

- `no-code-service` - Build and deploy no-code-service
- `auth-service` - Build and deploy auth-service
- `service-gateway` - Build and deploy service-gateway
- `frontend` - Build and deploy frontend
- `all` - Build and deploy all services
- `help` - Show usage information

#### Examples

```bash
# Deploy auth-service
make auth-service

# Deploy frontend
make frontend

# Deploy all services
make all

# Show help
make help
```

## How It Works

Both scripts:

1. Get the current Git commit SHA using `git rev-parse HEAD`
2. Execute the appropriate `gcloud builds submit` command with:
   - The correct cloudbuild.yaml configuration file
   - Substitutions for commit SHA and service name
   - The project ID: `alphintra-472817`

## Prerequisites

1. Ensure you have the Google Cloud SDK installed and authenticated
2. Make sure you have the necessary permissions to deploy to the project
3. The scripts should be run from the root directory of the project

## Notes

- The frontend service uses `_BUILD_TAG` instead of `_COMMIT_SHA` for the substitution variable
- All scripts include error handling to ensure they exit if a command fails
- The shell script will display usage information if no service name is provided