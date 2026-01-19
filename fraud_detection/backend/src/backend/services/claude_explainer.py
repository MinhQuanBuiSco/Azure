"""
Claude integration via Azure AI Foundry for AI-generated fraud explanations.

Uses Claude models through Azure AI Foundry (unified Azure billing and security).
"""
from typing import Dict, List, Optional
import asyncio

from backend.core.config import get_settings


class ClaudeExplainer:
    """
    Claude-based fraud explanation generator via Azure AI Foundry.

    Generates human-friendly explanations for fraud detection results.
    """

    def __init__(self):
        """Initialize Azure AI Foundry client for Claude."""
        self.settings = get_settings()
        self.client = None
        self.enabled = False

        # Initialize client if Azure AI credentials are available
        if self.settings.azure_ai_endpoint and self.settings.azure_ai_key:
            try:
                self._init_client()
                self.enabled = True
            except Exception as e:
                print(f"⚠️  Azure AI Foundry (Claude) not configured: {e}")
                print("   Continuing with basic explanations...")

    def _init_client(self):
        """Initialize the Azure AI Foundry client."""
        try:
            from azure.ai.inference import ChatCompletionsClient
            from azure.core.credentials import AzureKeyCredential

            self.client = ChatCompletionsClient(
                endpoint=self.settings.azure_ai_endpoint,
                credential=AzureKeyCredential(self.settings.azure_ai_key)
            )
            self.model_name = self.settings.azure_ai_model_name
            print(f"✅ Azure AI Foundry initialized (model: {self.model_name})")
        except ImportError:
            print("⚠️  azure-ai-inference package not installed")
            print("   Run: uv add azure-ai-inference")
            self.enabled = False
        except Exception as e:
            print(f"❌ Failed to initialize Azure AI Foundry: {e}")
            self.enabled = False

    async def generate_explanation(
        self,
        transaction: Dict,
        fraud_score: float,
        risk_level: str,
        triggered_rules: List[str],
        rule_scores: Dict[str, float],
        ml_score: float,
        azure_score: float,
        is_fraud: bool
    ) -> str:
        """
        Generate natural language explanation using Claude via Azure AI Foundry.

        Args:
            transaction: Transaction data
            fraud_score: Final fraud score (0-100)
            risk_level: low, medium, or high
            triggered_rules: List of triggered rule names
            rule_scores: Dict of rule scores
            ml_score: Isolation Forest score
            azure_score: Azure Anomaly Detector score
            is_fraud: Whether flagged as fraud

        Returns:
            Natural language explanation string
        """
        if not self.enabled or not self.client:
            return self._basic_explanation(
                fraud_score, risk_level, triggered_rules, ml_score, azure_score
            )

        try:
            prompt = self._build_prompt(
                transaction, fraud_score, risk_level, triggered_rules,
                rule_scores, ml_score, azure_score, is_fraud
            )

            # Call Azure AI Foundry asynchronously
            response = await self._call_azure_ai(prompt, max_tokens=300)

            if response:
                return response.strip()

        except Exception as e:
            print(f"Azure AI explanation error: {e}")
            return self._basic_explanation(
                fraud_score, risk_level, triggered_rules, ml_score, azure_score
            )

        return self._basic_explanation(
            fraud_score, risk_level, triggered_rules, ml_score, azure_score
        )

    async def _call_azure_ai(self, prompt: str, max_tokens: int = 300) -> Optional[str]:
        """
        Call Azure AI Foundry API asynchronously.
        """
        try:
            from azure.ai.inference.models import UserMessage, SystemMessage

            # Run sync client in executor for async compatibility
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: self.client.complete(
                    model=self.model_name,
                    messages=[
                        SystemMessage(content="You are a fraud detection analyst providing clear, concise explanations."),
                        UserMessage(content=prompt)
                    ],
                    max_tokens=max_tokens,
                    temperature=0.3
                )
            )

            if response.choices and len(response.choices) > 0:
                return response.choices[0].message.content

        except Exception as e:
            print(f"Azure AI API call failed: {e}")
            return None

        return None

    def _build_prompt(
        self,
        transaction: Dict,
        fraud_score: float,
        risk_level: str,
        triggered_rules: List[str],
        rule_scores: Dict[str, float],
        ml_score: float,
        azure_score: float,
        is_fraud: bool
    ) -> str:
        """Build prompt for Claude."""
        amount = transaction.get('amount', 0)
        merchant = transaction.get('merchant_name', 'Unknown')
        country = transaction.get('country', 'Unknown')

        prompt = f"""Generate a clear, concise explanation for this transaction analysis.

Transaction Details:
- Amount: ${amount:.2f}
- Merchant: {merchant}
- Country: {country}
- Final Fraud Score: {fraud_score:.1f}/100
- Risk Level: {risk_level.upper()}
- Flagged as Fraud: {"Yes" if is_fraud else "No"}

Detection Signals:
- Rule Engine Score: {sum(rule_scores.values()):.1f} (Rules: {', '.join(triggered_rules) if triggered_rules else 'None triggered'})
- ML Anomaly Score: {ml_score:.1f}
- Azure Anomaly Score: {azure_score:.1f}

Generate a 2-3 sentence explanation for a fraud analyst explaining:
1. Why this transaction was flagged (or not flagged)
2. The key risk indicators
3. Recommended action (approve, review, or block)

Keep it professional, clear, and actionable. Do not include headers or formatting."""

        return prompt

    def _basic_explanation(
        self,
        fraud_score: float,
        risk_level: str,
        triggered_rules: List[str],
        ml_score: float,
        azure_score: float
    ) -> str:
        """
        Generate basic explanation without AI.

        Fallback when Azure AI Foundry is unavailable.
        """
        if not triggered_rules and ml_score < 20 and azure_score < 20:
            return "Transaction appears normal. No suspicious patterns detected."

        parts = [f"Risk Level: {risk_level.upper()} (Score: {fraud_score:.1f}/100)"]

        if triggered_rules:
            parts.append(f"\nTriggered Rules: {', '.join(triggered_rules)}")

        if ml_score > 30:
            parts.append(f"\nML Anomaly Score: {ml_score:.1f}")

        if azure_score > 30:
            parts.append(f"\nAzure Anomaly Score: {azure_score:.1f}")

        # Add recommendation
        if fraud_score >= 70:
            parts.append("\nRecommendation: BLOCK transaction")
        elif fraud_score >= 30:
            parts.append("\nRecommendation: REVIEW transaction")
        else:
            parts.append("\nRecommendation: APPROVE transaction")

        return "\n".join(parts)

    async def generate_batch_summary(
        self,
        transaction_count: int,
        fraud_count: int,
        total_amount_blocked: float,
        top_rules: List[str]
    ) -> str:
        """
        Generate summary for batch of transactions.

        Used for dashboard analytics.
        """
        if not self.enabled or not self.client:
            return f"Processed {transaction_count} transactions. Blocked {fraud_count} fraudulent transactions totaling ${total_amount_blocked:,.2f}."

        try:
            prompt = f"""Summarize this fraud detection batch in 1-2 sentences:

Transactions processed: {transaction_count}
Fraudulent: {fraud_count} ({fraud_count/transaction_count*100:.1f}% if transaction_count > 0 else 0)
Total amount blocked: ${total_amount_blocked:,.2f}
Most triggered rules: {', '.join(top_rules[:3])}

Make it concise and professional."""

            response = await self._call_azure_ai(prompt, max_tokens=150)

            if response:
                return response.strip()

        except Exception as e:
            print(f"Azure AI summary error: {e}")

        return f"Processed {transaction_count} transactions. Blocked {fraud_count} fraudulent transactions totaling ${total_amount_blocked:,.2f}."
