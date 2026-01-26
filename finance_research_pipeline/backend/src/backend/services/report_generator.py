"""PDF report generation service using WeasyPrint."""

import io
from datetime import datetime, UTC
from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader
from weasyprint import HTML, CSS

from backend.core.logging import get_logger

logger = get_logger(__name__)

# Template directory
TEMPLATES_DIR = Path(__file__).parent.parent / "templates"


class ReportGenerator:
    """Service for generating PDF reports from research data."""

    def __init__(self) -> None:
        """Initialize report generator."""
        # Ensure templates directory exists
        TEMPLATES_DIR.mkdir(parents=True, exist_ok=True)

        self.env = Environment(
            loader=FileSystemLoader(str(TEMPLATES_DIR)),
            autoescape=True,
        )

        # Create default template if it doesn't exist
        self._ensure_default_template()

    def _ensure_default_template(self) -> None:
        """Create default report template if it doesn't exist."""
        template_path = TEMPLATES_DIR / "report.html"
        if not template_path.exists():
            template_path.write_text(DEFAULT_REPORT_TEMPLATE)

        css_path = TEMPLATES_DIR / "report.css"
        if not css_path.exists():
            css_path.write_text(DEFAULT_REPORT_CSS)

    def generate_pdf(
        self,
        research_id: str,
        company_name: str,
        ticker_symbol: str | None,
        report_data: dict[str, Any],
    ) -> bytes:
        """
        Generate a PDF report.

        Args:
            research_id: Research session ID
            company_name: Company name
            ticker_symbol: Stock ticker
            report_data: Report content and data

        Returns:
            PDF file as bytes
        """
        try:
            # Load template
            template = self.env.get_template("report.html")

            # Prepare template context
            context = {
                "research_id": research_id,
                "company_name": company_name,
                "ticker_symbol": ticker_symbol or "N/A",
                "generated_at": datetime.now(UTC).strftime("%Y-%m-%d %H:%M UTC"),
                "executive_summary": report_data.get("executive_summary", ""),
                "market_analysis": report_data.get("market_analysis", {}),
                "financial_data": report_data.get("financial_data", {}),
                "news_analysis": report_data.get("news_analysis", {}),
                "competitor_analysis": report_data.get("competitor_analysis", {}),
                "risk_assessment": report_data.get("risk_assessment", {}),
                "recommendations": report_data.get("recommendations", []),
                "full_report": report_data.get("full_report", ""),
            }

            # Render HTML
            html_content = template.render(**context)

            # Load CSS
            css_path = TEMPLATES_DIR / "report.css"
            css = CSS(filename=str(css_path)) if css_path.exists() else None

            # Generate PDF
            pdf_buffer = io.BytesIO()
            HTML(string=html_content).write_pdf(
                pdf_buffer,
                stylesheets=[css] if css else None,
            )

            pdf_buffer.seek(0)
            logger.info(f"Generated PDF report for {company_name}")
            return pdf_buffer.getvalue()

        except Exception as e:
            logger.error(f"Failed to generate PDF report: {e}")
            raise

    def generate_html(
        self,
        research_id: str,
        company_name: str,
        ticker_symbol: str | None,
        report_data: dict[str, Any],
    ) -> str:
        """
        Generate an HTML report.

        Args:
            research_id: Research session ID
            company_name: Company name
            ticker_symbol: Stock ticker
            report_data: Report content and data

        Returns:
            HTML content as string
        """
        template = self.env.get_template("report.html")

        context = {
            "research_id": research_id,
            "company_name": company_name,
            "ticker_symbol": ticker_symbol or "N/A",
            "generated_at": datetime.now(UTC).strftime("%Y-%m-%d %H:%M UTC"),
            "executive_summary": report_data.get("executive_summary", ""),
            "market_analysis": report_data.get("market_analysis", {}),
            "financial_data": report_data.get("financial_data", {}),
            "news_analysis": report_data.get("news_analysis", {}),
            "competitor_analysis": report_data.get("competitor_analysis", {}),
            "risk_assessment": report_data.get("risk_assessment", {}),
            "recommendations": report_data.get("recommendations", []),
            "full_report": report_data.get("full_report", ""),
        }

        return template.render(**context)


# Default HTML template
DEFAULT_REPORT_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Finance Research Report - {{ company_name }}</title>
    <link rel="stylesheet" href="report.css">
</head>
<body>
    <header class="report-header">
        <h1>Finance Research Report</h1>
        <div class="company-info">
            <h2>{{ company_name }}</h2>
            <p class="ticker">Ticker: {{ ticker_symbol }}</p>
            <p class="date">Generated: {{ generated_at }}</p>
            <p class="research-id">Report ID: {{ research_id }}</p>
        </div>
    </header>

    <main class="report-content">
        {% if executive_summary %}
        <section class="executive-summary">
            <h2>Executive Summary</h2>
            <div class="content">{{ executive_summary }}</div>
        </section>
        {% endif %}

        {% if financial_data %}
        <section class="financial-data">
            <h2>Financial Data</h2>
            {% if financial_data.price %}
            <div class="subsection">
                <h3>Stock Price</h3>
                <table>
                    <tr><td>Current Price</td><td>${{ financial_data.price.current or 'N/A' }}</td></tr>
                    <tr><td>52-Week High</td><td>${{ financial_data.price.fifty_two_week_high or 'N/A' }}</td></tr>
                    <tr><td>52-Week Low</td><td>${{ financial_data.price.fifty_two_week_low or 'N/A' }}</td></tr>
                </table>
            </div>
            {% endif %}
            {% if financial_data.valuation %}
            <div class="subsection">
                <h3>Valuation Metrics</h3>
                <table>
                    <tr><td>P/E Ratio</td><td>{{ financial_data.valuation.pe_ratio or 'N/A' }}</td></tr>
                    <tr><td>Forward P/E</td><td>{{ financial_data.valuation.forward_pe or 'N/A' }}</td></tr>
                    <tr><td>PEG Ratio</td><td>{{ financial_data.valuation.peg_ratio or 'N/A' }}</td></tr>
                </table>
            </div>
            {% endif %}
        </section>
        {% endif %}

        {% if market_analysis %}
        <section class="market-analysis">
            <h2>Market Analysis</h2>
            <div class="content">{{ market_analysis.summary or market_analysis }}</div>
        </section>
        {% endif %}

        {% if news_analysis %}
        <section class="news-analysis">
            <h2>News Analysis</h2>
            {% if news_analysis.sentiment_distribution %}
            <div class="sentiment-summary">
                <p>Overall Sentiment: <strong>{{ news_analysis.overall_sentiment or 'Neutral' }}</strong></p>
                <p>Sentiment Score: {{ news_analysis.sentiment_score or 0 }}</p>
            </div>
            {% endif %}
            <div class="content">{{ news_analysis.summary or '' }}</div>
        </section>
        {% endif %}

        {% if competitor_analysis %}
        <section class="competitor-analysis">
            <h2>Competitor Analysis</h2>
            <div class="content">{{ competitor_analysis.summary or competitor_analysis }}</div>
        </section>
        {% endif %}

        {% if risk_assessment %}
        <section class="risk-assessment">
            <h2>Risk Assessment</h2>
            <div class="content">{{ risk_assessment.summary or risk_assessment }}</div>
        </section>
        {% endif %}

        {% if recommendations %}
        <section class="recommendations">
            <h2>Recommendations</h2>
            <ul>
            {% for rec in recommendations %}
                <li>{{ rec }}</li>
            {% endfor %}
            </ul>
        </section>
        {% endif %}

        {% if full_report %}
        <section class="full-report">
            <h2>Detailed Analysis</h2>
            <div class="content">{{ full_report }}</div>
        </section>
        {% endif %}
    </main>

    <footer class="report-footer">
        <p>This report was generated automatically by the Finance Research Pipeline.</p>
        <p>Disclaimer: This report is for informational purposes only and does not constitute financial advice.</p>
    </footer>
</body>
</html>
"""

# Default CSS styles
DEFAULT_REPORT_CSS = """/* Finance Research Report Styles */
@page {
    size: A4;
    margin: 2cm;
}

* {
    box-sizing: border-box;
}

body {
    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    line-height: 1.6;
    color: #333;
    max-width: 210mm;
    margin: 0 auto;
    padding: 20px;
}

.report-header {
    text-align: center;
    border-bottom: 3px solid #2563eb;
    padding-bottom: 20px;
    margin-bottom: 30px;
}

.report-header h1 {
    color: #1e40af;
    font-size: 28px;
    margin-bottom: 10px;
}

.company-info h2 {
    color: #1f2937;
    font-size: 24px;
    margin: 10px 0;
}

.ticker {
    font-size: 18px;
    color: #4b5563;
    font-weight: 600;
}

.date, .research-id {
    font-size: 12px;
    color: #6b7280;
}

section {
    margin-bottom: 30px;
    page-break-inside: avoid;
}

section h2 {
    color: #1e40af;
    border-bottom: 2px solid #dbeafe;
    padding-bottom: 8px;
    margin-bottom: 15px;
}

section h3 {
    color: #374151;
    font-size: 16px;
    margin: 15px 0 10px;
}

.subsection {
    margin-bottom: 20px;
}

table {
    width: 100%;
    border-collapse: collapse;
    margin: 10px 0;
}

table td {
    padding: 8px 12px;
    border: 1px solid #e5e7eb;
}

table td:first-child {
    background-color: #f9fafb;
    font-weight: 500;
    width: 40%;
}

.content {
    text-align: justify;
}

.sentiment-summary {
    background-color: #f0f9ff;
    padding: 15px;
    border-radius: 8px;
    margin-bottom: 15px;
}

.recommendations ul {
    list-style-type: none;
    padding: 0;
}

.recommendations li {
    padding: 10px 15px;
    margin: 8px 0;
    background-color: #f0fdf4;
    border-left: 4px solid #22c55e;
    border-radius: 4px;
}

.report-footer {
    margin-top: 40px;
    padding-top: 20px;
    border-top: 1px solid #e5e7eb;
    text-align: center;
    font-size: 11px;
    color: #6b7280;
}

@media print {
    body {
        padding: 0;
    }

    section {
        page-break-inside: avoid;
    }
}
"""
