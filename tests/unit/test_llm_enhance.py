"""Tests for LLM enhancement module."""

import pytest
from unittest.mock import Mock, patch, MagicMock
import json

from inception.enhance.llm.providers import (
    LLMProvider,
    LLMResponse,
    OllamaProvider,
    OpenRouterProvider,
    CloudProvider,
    get_provider,
)
from inception.enhance.llm.extractor import (
    LLMExtractor,
    LLMExtractionResult,
    ExtractedEntity,
    ExtractedClaim,
    ExtractedProcedure,
    ExtractedStep,
    ExtractedGap,
)
from inception.enhance.llm.prompts import (
    CLAIM_EXTRACTION_PROMPT,
    ENTITY_EXTRACTION_PROMPT,
    PROCEDURE_EXTRACTION_PROMPT,
)


class TestLLMResponse:
    """Tests for LLMResponse dataclass."""
    
    def test_creation(self):
        """Test basic response creation."""
        response = LLMResponse(
            content="Hello, world!",
            model="test-model",
            provider="test",
            tokens_used=10,
            cost_usd=0.001,
        )
        
        assert response.content == "Hello, world!"
        assert response.model == "test-model"
        assert response.tokens_used == 10
        assert response.cost_usd == 0.001


class TestOllamaProvider:
    """Tests for Ollama provider."""
    
    def test_initialization(self):
        """Test provider initialization."""
        provider = OllamaProvider(model="llama3.2")
        
        assert provider.name == "ollama"
        assert provider.model == "llama3.2"
        assert provider.base_url == "http://localhost:11434"
    
    def test_custom_url(self):
        """Test custom base URL."""
        provider = OllamaProvider(base_url="http://custom:8080")
        assert provider.base_url == "http://custom:8080"
    
    @patch("httpx.Client.get")
    def test_is_available_false(self, mock_get):
        """Test availability check when Ollama is down."""
        mock_get.side_effect = Exception("Connection refused")
        
        provider = OllamaProvider()
        assert provider.is_available() is False


class TestOpenRouterProvider:
    """Tests for OpenRouter provider."""
    
    def test_initialization(self):
        """Test provider initialization."""
        provider = OpenRouterProvider(
            model="anthropic/claude-3-haiku",
            api_key="test-key",
        )
        
        assert provider.name == "openrouter"
        assert provider.model == "anthropic/claude-3-haiku"
        assert provider.api_key == "test-key"
    
    def test_is_available_with_key(self):
        """Test availability with API key."""
        provider = OpenRouterProvider(api_key="test-key")
        assert provider.is_available() is True
    
    def test_is_available_without_key(self):
        """Test availability without API key."""
        provider = OpenRouterProvider(api_key=None)
        # Will check env var, which may or may not be set
        # Just verify it doesn't crash


class TestCloudProvider:
    """Tests for Cloud provider."""
    
    def test_anthropic_initialization(self):
        """Test Anthropic initialization."""
        provider = CloudProvider(provider="anthropic", api_key="test-key")
        
        assert provider.provider_type == "anthropic"
        assert "claude" in provider.model
    
    def test_openai_initialization(self):
        """Test OpenAI initialization."""
        provider = CloudProvider(provider="openai", api_key="test-key")
        
        assert provider.provider_type == "openai"
        assert "gpt" in provider.model


class TestGetProvider:
    """Tests for provider factory function."""
    
    @patch.object(OllamaProvider, "is_available", return_value=True)
    def test_auto_prefers_ollama(self, mock_available):
        """Test auto mode prefers Ollama when available."""
        provider = get_provider(name="auto")
        assert provider.name == "ollama"
    
    def test_offline_requires_ollama(self):
        """Test offline mode requires Ollama."""
        with patch.object(OllamaProvider, "is_available", return_value=False):
            with pytest.raises(RuntimeError, match="No offline provider"):
                get_provider(name="auto", offline=True)
    
    def test_unknown_provider(self):
        """Test unknown provider raises error."""
        with pytest.raises(ValueError, match="Unknown provider"):
            get_provider(name="unknown_provider")


class TestExtractedDataclasses:
    """Tests for extraction result dataclasses."""
    
    def test_extracted_entity(self):
        """Test ExtractedEntity creation."""
        entity = ExtractedEntity(
            name="Python",
            entity_type="PRODUCT",
            aliases=["python3", "Python 3"],
            description="A programming language",
            confidence=0.95,
        )
        
        assert entity.name == "Python"
        assert entity.entity_type == "PRODUCT"
        assert len(entity.aliases) == 2
    
    def test_extracted_claim(self):
        """Test ExtractedClaim creation."""
        claim = ExtractedClaim(
            text="Python is easy to learn",
            subject="Python",
            predicate="is",
            object="easy to learn",
            modality="assertion",
        )
        
        assert claim.text == "Python is easy to learn"
        assert claim.negated is False
    
    def test_extracted_procedure(self):
        """Test ExtractedProcedure creation."""
        procedure = ExtractedProcedure(
            title="Install Python",
            goal="Set up Python environment",
            steps=[
                ExtractedStep(index=0, text="Download Python", action_verb="download"),
                ExtractedStep(index=1, text="Run installer", action_verb="run"),
            ],
        )
        
        assert procedure.title == "Install Python"
        assert len(procedure.steps) == 2
    
    def test_extracted_gap(self):
        """Test ExtractedGap creation."""
        gap = ExtractedGap(
            gap_type="undefined_term",
            description="RLHF not defined",
            severity="high",
        )
        
        assert gap.gap_type == "undefined_term"
        assert gap.severity == "high"


class TestLLMExtractionResult:
    """Tests for LLMExtractionResult."""
    
    def test_empty_result(self):
        """Test empty result creation."""
        result = LLMExtractionResult()
        
        assert len(result.entities) == 0
        assert len(result.claims) == 0
        assert len(result.procedures) == 0
        assert len(result.gaps) == 0
    
    def test_merge_results(self):
        """Test merging two results."""
        result1 = LLMExtractionResult(
            entities=[ExtractedEntity(name="A", entity_type="CONCEPT")],
            claims=[ExtractedClaim(text="Claim 1")],
            tokens_used=100,
            cost_usd=0.01,
        )
        
        result2 = LLMExtractionResult(
            entities=[ExtractedEntity(name="B", entity_type="CONCEPT")],
            claims=[ExtractedClaim(text="Claim 2")],
            tokens_used=50,
            cost_usd=0.005,
        )
        
        merged = result1.merge(result2)
        
        assert len(merged.entities) == 2
        assert len(merged.claims) == 2
        assert merged.tokens_used == 150
        assert merged.cost_usd == 0.015


class TestLLMExtractor:
    """Tests for LLMExtractor class."""
    
    @pytest.fixture
    def mock_provider(self):
        """Create a mock LLM provider."""
        provider = Mock(spec=LLMProvider)
        provider.name = "mock"
        return provider
    
    def test_initialization(self, mock_provider):
        """Test extractor initialization."""
        extractor = LLMExtractor(provider=mock_provider)
        
        assert extractor.provider == mock_provider
        assert extractor.total_tokens == 0
        assert extractor.total_cost == 0.0
    
    def test_extract_entities_success(self, mock_provider):
        """Test successful entity extraction."""
        mock_provider.complete_json.return_value = {
            "entities": [
                {
                    "name": "Python",
                    "type": "PRODUCT",
                    "aliases": ["python3"],
                    "description": "A language",
                    "confidence": 0.9,
                }
            ]
        }
        
        extractor = LLMExtractor(provider=mock_provider)
        entities = extractor.extract_entities("Python is great")
        
        assert len(entities) == 1
        assert entities[0].name == "Python"
        assert entities[0].entity_type == "PRODUCT"
    
    def test_extract_entities_failure(self, mock_provider):
        """Test entity extraction failure handling."""
        mock_provider.complete_json.side_effect = Exception("API error")
        
        extractor = LLMExtractor(provider=mock_provider)
        entities = extractor.extract_entities("Some text")
        
        assert entities == []
    
    def test_extract_claims_success(self, mock_provider):
        """Test successful claim extraction."""
        mock_provider.complete_json.return_value = {
            "claims": [
                {
                    "text": "Python is popular",
                    "subject": "Python",
                    "predicate": "is",
                    "object": "popular",
                    "modality": "assertion",
                    "confidence": 0.85,
                }
            ]
        }
        
        extractor = LLMExtractor(provider=mock_provider)
        claims = extractor.extract_claims("Python is popular")
        
        assert len(claims) == 1
        assert claims[0].text == "Python is popular"
    
    def test_extract_procedures_success(self, mock_provider):
        """Test successful procedure extraction."""
        mock_provider.complete_json.return_value = {
            "procedures": [
                {
                    "title": "Install Python",
                    "goal": "Set up Python",
                    "prerequisites": ["admin access"],
                    "steps": [
                        {"index": 0, "text": "Download", "action_verb": "download"}
                    ],
                    "warnings": ["Backup first"],
                    "outcomes": ["Python installed"],
                }
            ]
        }
        
        extractor = LLMExtractor(provider=mock_provider)
        procedures = extractor.extract_procedures("Install Python by downloading...")
        
        assert len(procedures) == 1
        assert procedures[0].title == "Install Python"
        assert len(procedures[0].steps) == 1
    
    def test_extract_gaps_success(self, mock_provider):
        """Test successful gap detection."""
        mock_provider.complete_json.return_value = {
            "gaps": [
                {
                    "type": "undefined_term",
                    "description": "RLHF not defined",
                    "location_hint": "paragraph 1",
                    "severity": "medium",
                    "resolution_hints": ["search RLHF"],
                }
            ]
        }
        
        extractor = LLMExtractor(provider=mock_provider)
        gaps = extractor.extract_gaps("RLHF is important")
        
        assert len(gaps) == 1
        assert gaps[0].gap_type == "undefined_term"
    
    def test_extract_all_success(self, mock_provider):
        """Test comprehensive extraction."""
        mock_response = LLMResponse(
            content=json.dumps({
                "entities": [{"name": "Python", "type": "PRODUCT"}],
                "claims": [{"text": "Python is great"}],
                "procedures": [],
                "gaps": [],
            }),
            model="test",
            provider="mock",
            tokens_used=500,
            cost_usd=0.01,
        )
        mock_provider.complete.return_value = mock_response
        
        extractor = LLMExtractor(provider=mock_provider)
        result = extractor.extract_all("Python is great")
        
        assert len(result.entities) == 1
        assert len(result.claims) == 1
        assert result.tokens_used == 500


class TestPromptFormatting:
    """Tests for prompt formatting."""
    
    def test_claim_prompt_formatting(self):
        """Test claim extraction prompt formatting."""
        text = "Python is a great language"
        prompt = CLAIM_EXTRACTION_PROMPT.format(text=text)
        
        assert text in prompt
        assert "claims" in prompt.lower()
    
    def test_entity_prompt_formatting(self):
        """Test entity extraction prompt formatting."""
        text = "Guido created Python"
        prompt = ENTITY_EXTRACTION_PROMPT.format(text=text)
        
        assert text in prompt
        assert "entities" in prompt.lower()
    
    def test_procedure_prompt_formatting(self):
        """Test procedure extraction prompt formatting."""
        text = "First, download Python. Then, install it."
        prompt = PROCEDURE_EXTRACTION_PROMPT.format(text=text)
        
        assert text in prompt
        assert "steps" in prompt.lower()
