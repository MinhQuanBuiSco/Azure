"""Model routing and load balancing."""

from typing import Any

from backend.config.settings import get_settings


class ModelRouter:
    """Routes requests to appropriate model deployments."""

    # Model aliases and their Azure deployment mappings
    MODEL_MAPPINGS = {
        "gpt-4o": "gpt-4o",
        "gpt-4o-mini": "gpt-4o-mini",
        "gpt-4": "gpt-4o",  # Alias
        "gpt-4-turbo": "gpt-4o",  # Alias
        "gpt-3.5-turbo": "gpt-4o-mini",  # Route to mini for cost savings
    }

    def __init__(self):
        self.settings = get_settings()

    def get_deployment_name(self, model: str) -> str:
        """
        Get the Azure deployment name for a given model.

        Args:
            model: The requested model name

        Returns:
            The Azure deployment name to use
        """
        # Check if it's a known model alias
        if model in self.MODEL_MAPPINGS:
            return self.MODEL_MAPPINGS[model]

        # Default to configured deployment
        return self.settings.azure_ai_deployment_name

    def get_model_info(self, model: str) -> dict[str, Any]:
        """
        Get information about a model.

        Args:
            model: The model name

        Returns:
            Dict with model information
        """
        deployment = self.get_deployment_name(model)

        # Model capabilities
        capabilities = {
            "gpt-4o": {
                "max_tokens": 128000,
                "supports_vision": True,
                "supports_functions": True,
                "supports_json_mode": True,
            },
            "gpt-4o-mini": {
                "max_tokens": 128000,
                "supports_vision": True,
                "supports_functions": True,
                "supports_json_mode": True,
            },
        }

        return {
            "requested_model": model,
            "deployment_name": deployment,
            "capabilities": capabilities.get(deployment, {}),
        }

    def validate_request(self, model: str, max_tokens: int | None = None) -> tuple[bool, str | None]:
        """
        Validate a request against model constraints.

        Args:
            model: The requested model
            max_tokens: Requested max tokens

        Returns:
            Tuple of (is_valid, error_message)
        """
        info = self.get_model_info(model)
        caps = info.get("capabilities", {})

        if max_tokens and caps.get("max_tokens"):
            if max_tokens > caps["max_tokens"]:
                return False, f"max_tokens ({max_tokens}) exceeds model limit ({caps['max_tokens']})"

        return True, None


# Global router instance
_router: ModelRouter | None = None


def get_model_router() -> ModelRouter:
    """Get or create the model router."""
    global _router
    if _router is None:
        _router = ModelRouter()
    return _router
