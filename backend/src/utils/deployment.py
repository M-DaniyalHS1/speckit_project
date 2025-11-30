"""
Deployment script for the AI-Enhanced Interactive Book Agent.

This module provides functionality to deploy the application to production environments
with proper configuration, environment setup, and service management.
"""
import os
import sys
import subprocess
import argparse
import json
from pathlib import Path
from typing import Dict, Any, Optional
import yaml
from datetime import datetime


class DeploymentManager:
    """Manages deployment of the AI-Enhanced Interactive Book Agent to production."""

    def __init__(self, environment: str = "production"):
        """Initialize the deployment manager with the target environment."""
        self.environment = environment
        self.project_root = Path(__file__).parent.parent
        self.config = self._load_config()
        
    def _load_config(self) -> Dict[str, Any]:
        """Load deployment configuration from environment-specific files."""
        config_path = self.project_root / "deployment" / f"config.{self.environment}.yaml"
        
        # Default configuration
        default_config = {
            "environment": self.environment,
            "domain": "book-agent.example.com",
            "ssl_enabled": True,
            "database": {
                "host": "localhost",
                "port": 5432,
                "ssl_mode": "require"
            },
            "services": {
                "backend": {
                    "replicas": 3,
                    "cpu_limit": "1000m",
                    "memory_limit": "2Gi"
                },
                "frontend": {
                    "replicas": 2,
                    "cpu_limit": "500m",
                    "memory_limit": "1Gi"
                }
            },
            "monitoring": {
                "enabled": True,
                "logging_level": "INFO"
            }
        }
        
        # Try to load environment-specific config
        if config_path.exists():
            with open(config_path, 'r') as f:
                env_config = yaml.safe_load(f)
                # Merge with defaults
                for key, value in env_config.items():
                    if isinstance(value, dict) and key in default_config:
                        default_config[key].update(value)
                    else:
                        default_config[key] = value
        
        return default_config

    def check_prerequisites(self) -> bool:
        """Check if all prerequisites are met for deployment."""
        print(f"Checking prerequisites for {self.environment} deployment...")
        
        # Check for required tools
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
        
        # Check for required environment variables
        required_vars = [
            "GOOGLE_API_KEY",
            "POSTGRES_PASSWORD",
            "JWT_SECRET_KEY",
            "DATABASE_URL"
        ]
        
        missing_vars = []
        for var in required_vars:
            if not os.environ.get(var):
                missing_vars.append(var)
        
        if missing_vars:
            print(f"Missing required environment variables: {', '.join(missing_vars)}")
            return False
        
        print("All prerequisites met.")
        return True

    def build_application(self) -> bool:
        """Build the application containers."""
        print("Building application containers...")
        
        try:
            # Build with Docker Compose
            build_result = subprocess.run(
                ["docker-compose", "-f", "docker-compose.prod.yml", "build", "--no-cache"],
                cwd=self.project_root,
                capture_output=True,
                text=True
            )
            
            if build_result.returncode != 0:
                print(f"Build failed: {build_result.stderr}")
                return False
            
            print("Application built successfully.")
            return True
            
        except Exception as e:
            print(f"Error during build: {str(e)}")
            return False

    def run_pre_deployment_tests(self) -> bool:
        """Run tests before deployment."""
        print("Running pre-deployment tests...")
        
        try:
            # Run unit tests
            unit_test_result = subprocess.run(
                [sys.executable, "-m", "pytest", "backend/tests/unit/", "-v"],
                cwd=self.project_root,
                capture_output=True,
                text=True
            )
            
            if unit_test_result.returncode != 0:
                print(f"Unit tests failed: {unit_test_result.stderr}")
                return False
            
            print("Unit tests passed.")
            
            # Run integration tests
            integration_test_result = subprocess.run(
                [sys.executable, "-m", "pytest", "backend/tests/integration/", "-v"],
                cwd=self.project_root,
                capture_output=True,
                text=True
            )
            
            if integration_test_result.returncode != 0:
                print(f"Integration tests failed: {integration_test_result.stderr}")
                return False
                
            print("Integration tests passed.")
            
            return True
            
        except Exception as e:
            print(f"Error during testing: {str(e)}")
            return False

    def deploy_services(self) -> bool:
        """Deploy services to the target environment."""
        print(f"Deploying services to {self.environment}...")
        
        try:
            # Create necessary directories
            Path(self.project_root / "deployment" / "logs").mkdir(parents=True, exist_ok=True)
            Path(self.project_root / "deployment" / "backups").mkdir(parents=True, exist_ok=True)
            
            # Set environment-specific variables
            env_vars = os.environ.copy()
            env_vars.update({
                "ENVIRONMENT": self.environment,
                "LOG_LEVEL": self.config.get("monitoring", {}).get("logging_level", "INFO"),
                "SSL_ENABLED": str(self.config.get("ssl_enabled", True))
            })
            
            # Deploy with Docker Compose
            deploy_result = subprocess.run(
                ["docker-compose", "-f", "docker-compose.prod.yml", "up", "-d"],
                cwd=self.project_root,
                env=env_vars,
                capture_output=True,
                text=True
            )
            
            if deploy_result.returncode != 0:
                print(f"Deployment failed: {deploy_result.stderr}")
                return False
            
            print("Services deployed successfully.")
            return True
            
        except Exception as e:
            print(f"Error during deployment: {str(e)}")
            return False

    def run_post_deployment_health_checks(self) -> bool:
        """Run health checks after deployment."""
        print("Running post-deployment health checks...")
        
        try:
            import requests
            import time
            
            # Wait a bit for services to start
            time.sleep(30)
            
            # Check backend health
            backend_url = f"http://localhost:8000/health"
            
            response = requests.get(backend_url, timeout=30)
            
            if response.status_code != 200:
                print(f"Backend health check failed: {response.status_code}")
                return False
            
            health_data = response.json()
            if not health_data.get("status") == "healthy":
                print(f"Backend is not healthy: {health_data}")
                return False
            
            print("Health checks passed.")
            return True
            
        except Exception as e:
            print(f"Error during health checks: {str(e)}")
            return False

    def setup_ssl_certificates(self) -> bool:
        """Set up SSL certificates for HTTPS."""
        if not self.config.get("ssl_enabled", True):
            print("SSL disabled for this environment.")
            return True
        
        print("Setting up SSL certificates...")
        
        try:
            ssl_dir = self.project_root / "ssl"
            ssl_dir.mkdir(exist_ok=True)
            
            cert_path = ssl_dir / "certificate.pem"
            key_path = ssl_dir / "private.key"
            
            # In production, you'd get certificates from a CA
            # For now, we'll warn if they don't exist
            if not cert_path.exists() or not key_path.exists():
                print("SSL certificates not found. In a production environment,")
                print("obtain proper certificates from a Certificate Authority.")
                print("For testing, you may generate self-signed certificates.")
                
                # For demo purposes, provide command for generating self-signed certs
                print("\nTo generate self-signed certificates, run:")
                print(f"openssl req -x509 -nodes -days 365 -newkey rsa:2048 \\")
                print(f"  -keyout {key_path} \\")
                print(f"  -out {cert_path} \\")
                print(f"  -subj \"/CN={self.config.get('domain', 'localhost')}\"")
                
                # Return True for testing purposes, but in production this would be required
                if self.environment == "production":
                    return False
                else:
                    return True
            
            print("SSL certificates found and configured.")
            return True
            
        except Exception as e:
            print(f"Error setting up SSL: {str(e)}")
            return False

    def create_backup(self, backup_name: Optional[str] = None) -> bool:
        """Create a backup of the current deployment."""
        print("Creating deployment backup...")
        
        try:
            if not backup_name:
                backup_name = f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            backup_path = self.project_root / "deployment" / "backups" / backup_name
            backup_path.mkdir(parents=True, exist_ok=True)
            
            # Backup important files
            important_dirs = ["backend", "frontend", "ssl", "configs"]
            important_files = ["docker-compose.prod.yml", ".env", "pyproject.toml"]
            
            for directory in important_dirs:
                dir_path = self.project_root / directory
                if dir_path.exists():
                    backup_dir_path = backup_path / directory
                    import shutil
                    shutil.copytree(dir_path, backup_dir_path, dirs_exist_ok=True)
            
            for file_name in important_files:
                file_path = self.project_root / file_name
                if file_path.exists():
                    backup_file_path = backup_path / file_name
                    import shutil
                    shutil.copy2(file_path, backup_file_path)
            
            print(f"Backup created at: {backup_path}")
            return True
            
        except Exception as e:
            print(f"Error creating backup: {str(e)}")
            return False

    def rollback(self, backup_name: str) -> bool:
        """Rollback to a previous backup."""
        print(f"Rolling back to backup: {backup_name}")
        
        try:
            backup_path = self.project_root / "deployment" / "backups" / backup_name
            
            if not backup_path.exists():
                print(f"Backup {backup_name} does not exist.")
                return False
            
            # Stop current services
            subprocess.run(["docker-compose", "-f", "docker-compose.prod.yml", "down"])
            
            # Restore backed up files
            # Implementation would depend on the nature of changes
            # For now, we'll just indicate that rollback is initiated
            
            print("Rollback operation initiated. Please restart services manually.")
            return True
            
        except Exception as e:
            print(f"Error during rollback: {str(e)}")
            return False

    def deploy(self) -> bool:
        """Execute the complete deployment process."""
        print(f"Starting deployment to {self.environment} environment...")
        
        # Create backup before deployment
        if not self.create_backup():
            print("Failed to create backup before deployment. Aborting.")
            return False
        
        # Execute deployment steps
        steps = [
            ("Check prerequisites", self.check_prerequisites),
            ("Setup SSL certificates", self.setup_ssl_certificates),
            ("Build application", self.build_application),
            ("Run pre-deployment tests", self.run_pre_deployment_tests),
            ("Deploy services", self.deploy_services),
            ("Run health checks", self.run_post_deployment_health_checks)
        ]
        
        for step_name, step_func in steps:
            print(f"\n--- {step_name} ---")
            if not step_func():
                print(f"Step '{step_name}' failed. Aborting deployment.")
                return False
        
        print(f"\n✅ Deployment to {self.environment} completed successfully!")
        print(f"Application is now running at: {self.config.get('domain', 'localhost')}")
        
        return True

    def get_deployment_status(self) -> Dict[str, Any]:
        """Get current deployment status."""
        try:
            # Get Docker compose status
            result = subprocess.run(
                ["docker-compose", "-f", "docker-compose.prod.yml", "ps", "--format", "json"],
                cwd=self.project_root,
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                services = []
                for line in result.stdout.strip().split('\n'):
                    if line:
                        try:
                            service_info = json.loads(line)
                            services.append({
                                "name": service_info.get("Name", "Unknown"),
                                "state": service_info.get("State", "Unknown"),
                                "status": service_info.get("Status", "Unknown")
                            })
                        except json.JSONDecodeError:
                            continue
                
                return {
                    "environment": self.environment,
                    "services": services,
                    "timestamp": datetime.now().isoformat()
                }
            else:
                return {
                    "error": "Could not retrieve Docker compose status",
                    "timestamp": datetime.now().isoformat()
                }
        except Exception as e:
            return {
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }


def main():
    """Main entry point for the deployment script."""
    parser = argparse.ArgumentParser(description="Deploy the AI-Enhanced Interactive Book Agent")
    parser.add_argument(
        "action", 
        choices=["deploy", "status", "backup", "rollback"], 
        help="Action to perform"
    )
    parser.add_argument(
        "--env", 
        default="production", 
        help="Target environment (default: production)"
    )
    parser.add_argument(
        "--backup-name", 
        help="Backup name for rollback operation"
    )
    
    args = parser.parse_args()
    
    manager = DeploymentManager(environment=args.env)
    
    if args.action == "deploy":
        success = manager.deploy()
        sys.exit(0 if success else 1)
    
    elif args.action == "status":
        status = manager.get_deployment_status()
        print(json.dumps(status, indent=2))
        sys.exit(0)
    
    elif args.action == "backup":
        success = manager.create_backup()
        sys.exit(0 if success else 1)
    
    elif args.action == "rollback":
        if not args.backup_name:
            print("Error: --backup-name is required for rollback operation")
            sys.exit(1)
        
        success = manager.rollback(args.backup_name)
        sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()