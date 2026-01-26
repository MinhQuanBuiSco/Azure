"""LLM factory for Azure AI Foundry and direct providers."""

from langchain_anthropic import ChatAnthropic
from langchain_core.language_models import BaseChatModel
from langchain_openai import AzureChatOpenAI, ChatOpenAI

from backend.core.config import LLMProvider, Settings
from backend.core.logging import get_logger

logger = get_logger(__name__)


class LLMFactory:
    """Factory for creating LLM instances based on configuration."""

    def __init__(self, settings: Settings) -> None:
        """
        Initialize LLM factory.

        Args:
            settings: Application settings
        """
        self.settings = settings
        self._llm_cache: dict[str, BaseChatModel] = {}

    def get_llm(
        self,
        provider: LLMProvider | None = None,
        temperature: float = 0.0,
        streaming: bool = False,
    ) -> BaseChatModel:
        """
        Get an LLM instance.

        Args:
            provider: LLM provider (defaults to configured provider)
            temperature: Model temperature (default: 0.0)
            streaming: Enable streaming (default: False)

        Returns:
            Configured LLM instance
        """
        provider = provider or self.settings.llm_provider
        cache_key = f"{provider.value}_{temperature}_{streaming}"

        if cache_key in self._llm_cache:
            return self._llm_cache[cache_key]

        llm = self._create_llm(provider, temperature, streaming)
        self._llm_cache[cache_key] = llm
        return llm

    def _create_llm(
        self,
        provider: LLMProvider,
        temperature: float,
        streaming: bool,
    ) -> BaseChatModel:
        """Create a new LLM instance."""
        if provider == LLMProvider.AZURE_OPENAI:
            return self._create_azure_openai(temperature, streaming)
        elif provider == LLMProvider.AZURE_ANTHROPIC:
            return self._create_azure_anthropic(temperature, streaming)
        elif provider == LLMProvider.OPENAI:
            return self._create_openai(temperature, streaming)
        elif provider == LLMProvider.ANTHROPIC:
            return self._create_anthropic(temperature, streaming)
        else:
            raise ValueError(f"Unsupported LLM provider: {provider}")

    def _create_azure_openai(
        self,
        temperature: float,
        streaming: bool,
    ) -> AzureChatOpenAI:
        """Create Azure OpenAI instance."""
        if not self.settings.azure_openai_endpoint:
            raise ValueError("Azure OpenAI endpoint not configured")

        api_key = (
            self.settings.azure_openai_api_key.get_secret_value()
            if self.settings.azure_openai_api_key
            else None
        )

        logger.info(
            f"Creating Azure OpenAI LLM: {self.settings.azure_openai_deployment_name}"
        )

        return AzureChatOpenAI(
            azure_endpoint=self.settings.azure_openai_endpoint,
            api_key=api_key,
            azure_deployment=self.settings.azure_openai_deployment_name,
            api_version=self.settings.azure_openai_api_version,
            temperature=temperature,
            streaming=streaming,
        )

    def _create_azure_anthropic(
        self,
        temperature: float,
        streaming: bool,
    ) -> ChatAnthropic:
        """
        Create Azure AI Foundry Anthropic instance.

        Note: Azure AI Foundry hosts Anthropic models via an OpenAI-compatible API.
        """
        if not self.settings.azure_ai_foundry_endpoint:
            raise ValueError("Azure AI Foundry endpoint not configured")

        api_key = (
            self.settings.azure_ai_foundry_api_key.get_secret_value()
            if self.settings.azure_ai_foundry_api_key
            else None
        )

        logger.info(
            f"Creating Azure AI Foundry Anthropic LLM: {self.settings.azure_ai_foundry_model}"
        )

        # Azure AI Foundry uses OpenAI-compatible API for Anthropic models
        return ChatOpenAI(
            base_url=f"{self.settings.azure_ai_foundry_endpoint}/openai/deployments/{self.settings.azure_ai_foundry_model}",
            api_key=api_key,
            model=self.settings.azure_ai_foundry_model,
            temperature=temperature,
            streaming=streaming,
        )

    def _create_openai(
        self,
        temperature: float,
        streaming: bool,
    ) -> ChatOpenAI:
        """Create direct OpenAI instance."""
        if not self.settings.openai_api_key:
            raise ValueError("OpenAI API key not configured")

        logger.info(f"Creating OpenAI LLM: {self.settings.openai_model}")

        return ChatOpenAI(
            api_key=self.settings.openai_api_key.get_secret_value(),
            model=self.settings.openai_model,
            temperature=temperature,
            streaming=streaming,
        )

    def _create_anthropic(
        self,
        temperature: float,
        streaming: bool,
    ) -> ChatAnthropic:
        """Create direct Anthropic instance."""
        if not self.settings.anthropic_api_key:
            raise ValueError("Anthropic API key not configured")

        logger.info(f"Creating Anthropic LLM: {self.settings.anthropic_model}")

        return ChatAnthropic(
            api_key=self.settings.anthropic_api_key.get_secret_value(),
            model=self.settings.anthropic_model,
            temperature=temperature,
            streaming=streaming,
        )

    def get_streaming_llm(
        self,
        provider: LLMProvider | None = None,
        temperature: float = 0.0,
    ) -> BaseChatModel:
        """Get a streaming-enabled LLM instance."""
        return self.get_llm(provider, temperature, streaming=True)

    def get_available_providers(self) -> list[LLMProvider]:
        """Get list of configured/available providers."""
        available = []

        if self.settings.azure_openai_endpoint and self.settings.azure_openai_api_key:
            available.append(LLMProvider.AZURE_OPENAI)

        if (
            self.settings.azure_ai_foundry_endpoint
            and self.settings.azure_ai_foundry_api_key
        ):
            available.append(LLMProvider.AZURE_ANTHROPIC)

        if self.settings.openai_api_key:
            available.append(LLMProvider.OPENAI)

        if self.settings.anthropic_api_key:
            available.append(LLMProvider.ANTHROPIC)

        return available
