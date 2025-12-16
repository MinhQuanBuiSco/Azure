from openai import OpenAI, AzureOpenAI
from backend.config import settings


class OpenAIService:
    """Service for interacting with OpenAI (Azure or regular)."""

    def __init__(self):
        if settings.use_azure and settings.azure_openai_key:
            # Use Azure OpenAI
            self.client = AzureOpenAI(
                api_key=settings.azure_openai_key,
                api_version=settings.azure_openai_api_version,
                azure_endpoint=settings.azure_openai_endpoint
            )
            self.model_name = settings.azure_openai_deployment
            self.is_azure = True
        else:
            # Use regular OpenAI API
            self.client = OpenAI(api_key=settings.openai_api_key)
            self.model_name = settings.openai_model
            self.is_azure = False

    async def generate_response(self, messages: list[dict]) -> str:
        """
        Generate a response from OpenAI.

        Args:
            messages: List of message dictionaries with 'role' and 'content'

        Returns:
            Generated response text
        """
        try:
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=messages,
                temperature=0.7,
                max_tokens=800,
                top_p=0.95,
            )

            return response.choices[0].message.content

        except Exception as e:
            api_type = "Azure OpenAI" if self.is_azure else "OpenAI"
            raise Exception(f"Error generating response from {api_type}: {str(e)}")

    async def generate_streaming_response(self, messages: list[dict]):
        """
        Generate a streaming response from OpenAI.

        Args:
            messages: List of message dictionaries with 'role' and 'content'

        Yields:
            Chunks of generated text
        """
        try:
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=messages,
                temperature=0.7,
                max_tokens=800,
                top_p=0.95,
                stream=True
            )

            # Important: Use synchronous iteration but yield immediately
            # OpenAI SDK returns a synchronous iterator
            for chunk in response:
                if chunk.choices and len(chunk.choices) > 0:
                    delta_content = chunk.choices[0].delta.content
                    if delta_content:
                        # Yield immediately - FastAPI will handle the async context
                        yield delta_content

        except Exception as e:
            api_type = "Azure OpenAI" if self.is_azure else "OpenAI"
            raise Exception(f"Error generating streaming response from {api_type}: {str(e)}")


# Global service instance
openai_service = OpenAIService()
