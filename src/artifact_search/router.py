"""Query router using Azure AI Foundry to determine which apps to search."""

import json
import logging

from azure.identity import DefaultAzureCredential, get_bearer_token_provider
from openai import AsyncAzureOpenAI

from artifact_search.config import Settings
from artifact_search.models import AppSource, ArtifactType, RoutedQuery, SearchQuery

logger = logging.getLogger(__name__)

ROUTING_SYSTEM_PROMPT = """You are a query router for a MedTech risk management artifact search system.

Your job is to analyze user queries and determine:
1. Which application(s) should be searched
2. What type of artifacts to look for
3. Key search terms to use

Available applications and their purposes:
- azure_devops: Work items, tasks, bugs, user stories, requirements tracking, test cases, sprints
- figma: UI/UX designs, wireframes, mockups, design components, visual specifications
- notion: Documentation, knowledge base, meeting notes, policies, procedures, SOPs
- icepanel: Architecture diagrams, C4 models, system components, technical architecture

Artifact types:
- requirement: Product/system requirements, user stories, features
- risk: Risk items, hazards, potential harms (ISO 14971)
- mitigation: Risk controls, mitigations, protective measures
- design: UI designs, wireframes, visual specifications
- architecture: System architecture, C4 diagrams, technical components
- work_item: Tasks, bugs, sprints, general work items
- test_case: Test cases, verification, validation
- document: General documentation, SOPs, policies

For MedTech risk management queries:
- Requirements related to risks → search azure_devops, notion
- Risk items and hazards → search azure_devops, notion
- Mitigations and controls → search azure_devops, notion
- Design specifications → search figma
- Architecture questions → search icepanel
- Documentation/SOPs → search notion
- General work tracking → search azure_devops

Respond with JSON only, no explanation:
{
  "target_apps": ["app1", "app2"],
  "artifact_types": ["type1", "type2"],
  "search_terms": ["term1", "term2", "term3"]
}
"""


async def route_query(query: SearchQuery, settings: Settings) -> RoutedQuery:
    """Use Azure AI to route a query to appropriate apps."""
    if not settings.is_azure_ai_configured():
        logger.warning("Azure AI not configured, using fallback routing")
        return _fallback_route(query)

    try:
        # Use DefaultAzureCredential (az login) or API key
        if settings.azure_ai_use_ad_auth and not settings.azure_ai_api_key:
            token_provider = get_bearer_token_provider(
                DefaultAzureCredential(),
                "https://cognitiveservices.azure.com/.default"
            )
            client = AsyncAzureOpenAI(
                azure_endpoint=settings.azure_ai_endpoint,
                azure_ad_token_provider=token_provider,
                api_version="2024-02-01",
            )
        else:
            client = AsyncAzureOpenAI(
                azure_endpoint=settings.azure_ai_endpoint,
                api_key=settings.azure_ai_api_key,
                api_version="2024-02-01",
            )

        response = await client.chat.completions.create(
            model=settings.azure_ai_deployment,
            messages=[
                {"role": "system", "content": ROUTING_SYSTEM_PROMPT},
                {"role": "user", "content": query.query},
            ],
            temperature=0.1,
            max_tokens=500,
            response_format={"type": "json_object"},
        )

        content = response.choices[0].message.content
        if not content:
            logger.warning("Empty response from Azure AI, using fallback")
            return _fallback_route(query)

        result = json.loads(content)

        target_apps = [
            AppSource(app)
            for app in result.get("target_apps", [])
            if app in [s.value for s in AppSource]
        ]
        artifact_types = [
            ArtifactType(at)
            for at in result.get("artifact_types", [])
            if at in [t.value for t in ArtifactType]
        ]
        search_terms = result.get("search_terms", [])

        # Ensure we have at least some defaults
        if not target_apps:
            target_apps = [AppSource.AZURE_DEVOPS, AppSource.NOTION]
        if not artifact_types:
            artifact_types = [ArtifactType.DOCUMENT]
        if not search_terms:
            search_terms = query.query.split()[:5]

        return RoutedQuery(
            original_query=query.query,
            target_apps=target_apps,
            artifact_types=artifact_types,
            search_terms=search_terms,
        )

    except Exception as e:
        logger.error(f"Azure AI routing failed: {e}")
        return _fallback_route(query)


def _fallback_route(query: SearchQuery) -> RoutedQuery:
    """Fallback routing when AI is not available."""
    query_lower = query.query.lower()

    target_apps = []
    artifact_types = []

    # Simple keyword-based routing
    if any(word in query_lower for word in ["design", "ui", "ux", "wireframe", "mockup"]):
        target_apps.append(AppSource.FIGMA)
        artifact_types.append(ArtifactType.DESIGN)

    if any(word in query_lower for word in ["architecture", "system", "component", "c4", "diagram"]):
        target_apps.append(AppSource.ICEPANEL)
        artifact_types.append(ArtifactType.ARCHITECTURE)

    if any(word in query_lower for word in ["risk", "hazard", "harm", "severity"]):
        target_apps.extend([AppSource.AZURE_DEVOPS, AppSource.NOTION])
        artifact_types.append(ArtifactType.RISK)

    if any(word in query_lower for word in ["mitigation", "control", "measure", "protection"]):
        target_apps.extend([AppSource.AZURE_DEVOPS, AppSource.NOTION])
        artifact_types.append(ArtifactType.MITIGATION)

    if any(word in query_lower for word in ["requirement", "req", "story", "feature"]):
        target_apps.extend([AppSource.AZURE_DEVOPS, AppSource.NOTION])
        artifact_types.append(ArtifactType.REQUIREMENT)

    if any(word in query_lower for word in ["document", "sop", "procedure", "policy"]):
        target_apps.append(AppSource.NOTION)
        artifact_types.append(ArtifactType.DOCUMENT)

    if any(word in query_lower for word in ["task", "bug", "sprint", "work item"]):
        target_apps.append(AppSource.AZURE_DEVOPS)
        artifact_types.append(ArtifactType.WORK_ITEM)

    # Default to searching everything if no matches
    if not target_apps:
        target_apps = list(AppSource)
    if not artifact_types:
        artifact_types = [ArtifactType.DOCUMENT, ArtifactType.REQUIREMENT]

    # Deduplicate
    target_apps = list(dict.fromkeys(target_apps))
    artifact_types = list(dict.fromkeys(artifact_types))

    # Extract search terms (simple word extraction)
    stop_words = {"the", "a", "an", "is", "are", "what", "where", "how", "can", "you", "get", "me", "find", "show", "related", "to", "this", "that", "for", "in", "on", "with"}
    search_terms = [
        word for word in query.query.split()
        if word.lower() not in stop_words and len(word) > 2
    ][:5]

    return RoutedQuery(
        original_query=query.query,
        target_apps=target_apps,
        artifact_types=artifact_types,
        search_terms=search_terms if search_terms else ["risk", "requirement"],
    )
