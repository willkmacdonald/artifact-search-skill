"""Configuration settings for artifact search skill."""

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Azure DevOps
    azure_devops_org_url: str = Field(default="")
    azure_devops_pat: str = Field(default="")
    azure_devops_project: str = Field(default="RiskManagement")

    # Figma
    figma_access_token: str = Field(default="")
    figma_file_key: str = Field(default="")

    # Notion
    notion_api_key: str = Field(default="")
    notion_database_id: str = Field(default="")

    # Ice Panel
    icepanel_api_key: str = Field(default="")
    icepanel_landscape_id: str = Field(default="")

    # Azure AI Foundry
    azure_ai_endpoint: str = Field(default="")
    azure_ai_api_key: str = Field(default="")  # Optional if using az login
    azure_ai_deployment: str = Field(default="gpt-4o")
    azure_ai_use_ad_auth: bool = Field(default=True)  # Use DefaultAzureCredential

    def is_azure_devops_configured(self) -> bool:
        """Check if Azure DevOps is configured."""
        return bool(self.azure_devops_org_url and self.azure_devops_pat)

    def is_figma_configured(self) -> bool:
        """Check if Figma is configured."""
        return bool(self.figma_access_token and self.figma_file_key)

    def is_notion_configured(self) -> bool:
        """Check if Notion is configured."""
        return bool(self.notion_api_key and self.notion_database_id)

    def is_icepanel_configured(self) -> bool:
        """Check if Ice Panel is configured."""
        return bool(self.icepanel_api_key and self.icepanel_landscape_id)

    def is_azure_ai_configured(self) -> bool:
        """Check if Azure AI Foundry is configured."""
        # Either API key or AD auth (az login) works
        return bool(self.azure_ai_endpoint and (self.azure_ai_api_key or self.azure_ai_use_ad_auth))


def get_settings() -> Settings:
    """Get application settings singleton."""
    return Settings()
