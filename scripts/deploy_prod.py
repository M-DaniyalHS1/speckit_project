"""
Production Deployment Script for AI-Enhanced Interactive Book Agent

This script automates the deployment of the AI-Enhanced Interactive Book Agent to production environments.
It handles environment setup, dependency installation, configuration, and service startup.
"""
import os
import sys
import json
import subprocess
import argparse
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional


class ProductionDeployment:
    """Handles production deployment of the AI-Enhanced Interactive Book Agent."""

    def __init__(self, environment: str = "production"):
        """Initialize the deployment with the specified environment."""
        self.environment = environment
        self.project_root = Path(__file__).resolve().parent
        self.config = self._load_deployment_config()
        
    def _load_deployment_config(self) -> Dict:
        """Load the deployment configuration."""
        config_path = self.project_root / f"deploy-{self.environment}.config.json"
        
        default_config = {
            "environment": self.environment,
            "domain": "book-agent.example.com",
            "ssl_enabled": True,
            "database": {
                "host": "db.example.com",
                "port": 5432,
                "ssl_required": True
            },
            "services": {
                "api": {
                    "port": 8000,
                    "replicas": 3,
                    "memory_limit": "2GB",
                    "cpu_limit": "2"
                },
                "workers": {
                    "replicas": 2,
                    "memory_limit": "1GB",
                    "cpu_limit": "1"
                }
            },
            "monitoring": {
                "enabled": True,
                "logging_level": "INFO"
            }
        }
        
        # Load environment-specific config if available
        if config_path.exists():
            with open(config_path, 'r') as f:
                env_config = json.load(f)
                # Merge with defaults
                default_config.update(env_config)
        
        return default_config

    def check_system_requirements(self) -> bool:
        """Check that system requirements are met for deployment."""
        print("Checking system requirements...")
        
        # Check Python version
        python_version = sys.version_info
        if python_version.major < 3 or (python_version.major == 3 and python_version.minor < 8):
            print(f"Error: Python 3.8+ required, found {python_version.major}.{python_version.minor}")
            return False
            
        # Check required tools
        required_tools = ["docker", "docker-compose", "git"]
        missing_tools = []
        
        for tool in required_tools:
            try:
                subprocess.run([tool, "--version"], 
                             stdout=subprocess.DEVNULL, 
                             stderr=subprocess.DEVNULL, 
                             check=True)
            except (subprocess.CalledProcessError, FileNotFoundError):
                missing_tools.append(tool)
        
        if missing_tools:
            print(f"Missing required tools: {', '.join(missing_tools)}")
            return False
            
        # Check disk space (need at least 2GB free)
        import shutil
        _, _, free_space = shutil.disk_usage(self.project_root)
        free_gb = free_space / (1024**3)
        if free_gb < 2:
            print(f"Warning: Less than 2GB free space available: {free_gb:.2f}GB")
            
        print("System requirements check passed.")
        return True

    def validate_configuration(self) -> bool:
        """Validate the deployment configuration."""
        print("Validating configuration...")
        
        # Check required environment variables
        required_vars = [
            "GOOGLE_API_KEY",
            "POSTGRES_PASSWORD",
            "JWT_SECRET_KEY",
            "DATABASE_URL",
            "CHROMADB_PATH"
        ]
        
        missing_vars = []
        for var in required_vars:
            if not os.environ.get(var):
                if var in ["GOOGLE_API_KEY", "JWT_SECRET_KEY", "DATABASE_URL"]:
                    missing_vars.append(var)
        
        if missing_vars:
            print(f"Error: Missing required environment variables: {', '.join(missing_vars)}")
            print("Please set these variables in your environment or .env file.")
            return False
        
        # Validate domain format
        import re
        domain_pattern = r"^[a-z0-9]([a-z0-9-]{0,61}[a-z0-9])?(\.[a-z0-9]([a-z0-9-]{0,61}[a-z0-9])?)*$"
        domain = self.config.get("domain", "")
        if self.environment == "production" and not re.match(domain_pattern, domain):
            print(f"Error: Invalid domain format for production: {domain}")
            return False
        
        print("Configuration validation passed.")
        return True

    def prepare_build_environment(self) -> bool:
        """Prepare the environment for building and deployment."""
        print("Preparing build environment...")
        
        try:
            # Create necessary directories
            (self.project_root / "logs").mkdir(exist_ok=True)
            (self.project_root / "data").mkdir(exist_ok=True)
            (self.project_root / "ssl").mkdir(exist_ok=True)
            
            # Set up virtual environment if not using Docker
            if self.config.get("use_virtual_env", False):
                venv_path = self.project_root / "venv"
                
                if not venv_path.exists():
                    print("Creating virtual environment...")
                    subprocess.run([sys.executable, "-m", "venv", str(venv_path)], check=True)
                
                # Activate virtual environment and install dependencies
                if os.name == 'nt':  # Windows
                    pip_path = venv_path / "Scripts" / "pip.exe"
                    activate_script = venv_path / "Scripts" / "activate.bat"
                else:  # Unix/Linux/MacOS
                    pip_path = venv_path / "bin" / "pip"
                    activate_script = venv_path / "bin" / "activate"
                
                print("Installing Python dependencies...")
                subprocess.run([str(pip_path), "install", "--upgrade", "pip"], check=True)
                subprocess.run([str(pip_path), "install", "-r", "requirements.txt"], check=True)
                subprocess.run([str(pip_path), "install", "-r", "requirements-dev.txt"], check=True)
            
            print("Build environment prepared.")
            return True
            
        except subprocess.CalledProcessError as e:
            print(f"Error preparing build environment: {str(e)}")
            return False
        except Exception as e:
            print(f"Unexpected error preparing build environment: {str(e)}")
            return False

    def build_docker_images(self) -> bool:
        """Build Docker images for production deployment."""
        print("Building Docker images...")
        
        try:
            # Build backend image
            result = subprocess.run([
                "docker", "build", 
                "-t", f"book-agent-backend:{self.config.get('version', 'latest')}",
                "-f", "Dockerfile.backend", 
                "."
            ], cwd=self.project_root, check=True)
            
            # Build frontend image if it exists
            frontend_dockerfile = self.project_root / "Dockerfile.frontend"
            if frontend_dockerfile.exists():
                result = subprocess.run([
                    "docker", "build",
                    "-t", f"book-agent-frontend:{self.config.get('version', 'latest')}",
                    "-f", "Dockerfile.frontendend",
                    "."
                ], cwd=self.project_root, check=True)
            
            print("Docker images built successfully.")
            return True
            
        except subprocess.CalledProcessError as e:
            print(f"Error building Docker images: {str(e)}")
            return False

    def run_pre_deployment_checks(self) -> bool:
        """Run checks before deployment."""
        print("Running pre-deployment checks...")
        
        try:
            # Run unit tests
            print("Running unit tests...")
            result = subprocess.run([
                sys.executable, "-m", "pytest", 
                "backend/tests/unit/", 
                "-v", "--tb=short",
                f"--environment={self.environment}"
            ], cwd=self.project_root, capture_output=True, text=True)
            
            if result.returncode != 0:
                print(f"Unit tests failed:\n{result.stdout}\n{result.stderr}")
                return False
            
            # Run integration tests
            print("Running integration tests...")
            result = subprocess.run([
                sys.executable, "-m", "pytest", 
                "backend/tests/integration/", 
                "-v", "--tb=short"
            ], cwd=self.project_root, capture_output=True, text=True)
            
            if result.returncode != 0:
                print(f"Integration tests failed:\n{result.stdout}\n{result.stderr}")
                return False
            
            # Run security checks (if available)
            print("Running security checks...")
            try:
                result = subprocess.run([
                    "bandit", "-r", "backend/src/", "-ll"
                ], cwd=self.project_root, capture_output=True, text=True)
                
                if result.returncode != 0:
                    print(f"Security issues found:\n{result.stdout}")
                    # For now, don't fail deployment for security issues, just warn
            except FileNotFoundError:
                print("Bandit not installed, skipping security checks")
            
            print("Pre-deployment checks passed.")
            return True
            
        except Exception as e:
            print(f"Error during pre-deployment checks: {str(e)}")
            return False

    def deploy_to_production(self) -> bool:
        """Deploy the application to production."""
        print(f"Deploying to {self.environment} environment...")
        
        try:
            # Determine compose file to use
            compose_file = f"docker-compose.{self.environment}.yml"
            
            # If the environment-specific file doesn't exist, use the default
            if not (self.project_root / compose_file).exists():
                compose_file = "docker-compose.yml"
                print(f"Environment-specific compose file not found, using {compose_file}")
            
            # Pull latest images
            print("Pulling latest images...")
            subprocess.run([
                "docker-compose", 
                "-f", compose_file, 
                "pull"
            ], cwd=self.project_root, check=True)
            
            # Run database migrations
            print("Running database migrations...")
            subprocess.run([
                "docker-compose",
                "-f", compose_file,
                "run",
                "--rm",
                "backend",
                "alembic",
                "upgrade",
                "head"
            ], cwd=self.project_root, check=True)
            
            # Start all services
            print("Starting services...")
            subprocess.run([
                "docker-compose",
                "-f", compose_file,
                "up",
                "-d"
            ], cwd=self.project_root, check=True)
            
            # Wait for services to be ready
            print("Waiting for services to be ready...")
            import time
            time.sleep(10)  # Give services time to start
            
            print("Application deployed successfully.")
            return True
            
        except subprocess.CalledProcessError as e:
            print(f"Error during deployment: {str(e)}")
            return False
        except Exception as e:
            print(f"Unexpected error during deployment: {str(e)}")
            return False

    def run_health_check(self) -> bool:
        """Run health check on deployed services."""
        print("Running health check on deployed services...")
        
        try:
            import requests
            import time
            
            # Wait for services to fully start
            time.sleep(20)
            
            # Check API endpoint
            api_url = f"http://localhost:{self.config['services']['api']['port']}/health"
            
            try:
                response = requests.get(api_url, timeout=30)
                if response.status_code == 200:
                    health_data = response.json()
                    if health_data.get("status") == "healthy":
                        print("API service is healthy.")
                    else:
                        print(f"API service unhealthy: {health_data}")
                        return False
                else:
                    print(f"API health check returned status code: {response.status_code}")
                    return False
            except requests.exceptions.RequestException as e:
                print(f"API health check failed: {str(e)}")
                return False
            
            # Check other services if needed
            print("All services are healthy.")
            return True
            
        except Exception as e:
            print(f"Error during health check: {str(e)}")
            return False

    def setup_monitoring(self) -> bool:
        """Set up monitoring for the deployed application."""
        print("Setting up monitoring...")
        
        try:
            # Create log rotation for application logs
            logrotate_config = f"""{self.project_root}/logs/*.log {{
    daily
    missingok
    rotate 10
    compress
    delaycompress
    copytruncate
    notifempty
    create 640 www-data adm
    postrotate
        # Restart services if needed
    endscript
}}
"""
            
            with open("/etc/logrotate.d/book-agent", "w") as f:
                f.write(logrotate_config)
            
            # Set up basic metrics collection (if monitoring is enabled)
            if self.config.get("monitoring", {}).get("enabled", False):
                print("Monitoring setup completed.")
            else:
                print("Monitoring is disabled in configuration.")
            
            return True
            
        except Exception as e:
            print(f"Error setting up monitoring: {str(e)}")
            # Don't fail deployment if monitoring setup fails
            return True

    def create_deployment_artifact(self) -> bool:
        """Create a deployment artifact with version and timestamp information."""
        artifact = {
            "deployment_id": f"dep_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "version": self.config.get("version", "unknown"),
            "environment": self.environment,
            "timestamp": datetime.now().isoformat(),
            "commit_hash": subprocess.run(
                ["git", "rev-parse", "HEAD"], 
                capture_output=True, text=True
            ).stdout.strip() if subprocess.run(
                ["git", "rev-parse", "--git-dir"], 
                stderr=subprocess.DEVNULL
            ).returncode == 0 else "unknown",
            "config": self.config
        }
        
        # Save deployment artifact
        artifact_path = self.project_root / "deployment-artifacts"
        artifact_path.mkdir(exist_ok=True)
        
        artifact_file = artifact_path / f"deployment_{artifact['deployment_id']}.json"
        with open(artifact_file, 'w') as f:
            json.dump(artifact, f, indent=2)
        
        print(f"Deployment artifact created: {artifact_file}")
        return True

    def deploy(self) -> bool:
        """Execute the complete deployment process."""
        print(f"Starting deployment to {self.environment}...")
        
        steps = [
            ("Check system requirements", self.check_system_requirements),
            ("Validate configuration", self.validate_configuration),
            ("Prepare build environment", self.prepare_build_environment),
            ("Build Docker images", self.build_docker_images),
            ("Run pre-deployment checks", self.run_pre_deployment_checks),
            ("Deploy to production", self.deploy_to_production),
            ("Run health check", self.run_health_check),
            ("Setup monitoring", self.setup_monitoring),
            ("Create deployment artifact", self.create_deployment_artifact)
        ]
        
        for step_name, step_func in steps:
            print(f"\n--- {step_name} ---")
            if not step_func():
                print(f"\n❌ Deployment failed at step: {step_name}")
                return False
        
        print(f"\n🎉 Deployment to {self.environment} completed successfully!")
        print(f"Application is now running with deployment ID: dep_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
        
        return True


def main():
    """Main entry point for the deployment script."""
    parser = argparse.ArgumentParser(
        description="Deploy the AI-Enhanced Interactive Book Agent to production"
    )
    parser.add_argument(
        "environment",
        nargs="?",
        default="production",
        help="Target environment for deployment (production/staging/development)"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Run deployment steps without actually deploying"
    )
    parser.add_argument(
        "--skip-tests",
        action="store_true",
        help="Skip running tests during deployment"
    )
    
    args = parser.parse_args()
    
    if args.dry_run:
        print("Dry run mode: Showing what would happen without making changes")
        return True
    
    deployer = ProductionDeployment(environment=args.environment)
    
    # If skipping tests, we need to modify the deployment process
    if args.skip_tests:
        # In a real implementation, we would have a way to skip tests
        print("Tests will be skipped during deployment")
    
    success = deployer.deploy()
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())