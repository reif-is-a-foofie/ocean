from dataclasses import dataclass


@dataclass
class RenderDeployPlan:
    service_name: str = "ocean-backend"
    port: int = 8000
    start_command: str = "uvicorn backend.app:app --host 0.0.0.0 --port 8000"

    def steps(self) -> list[str]:
        return [
            "Build Docker image `ocean:latest`",
            "Push to registry (configure REGISTRY_URL, REGISTRY_TOKEN)",
            "Create/Update Render service with env vars",
            f"Set start command: {self.start_command}",
            f"Expose port {self.port}, verify /healthz",
        ]

