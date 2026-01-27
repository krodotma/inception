"""Tests for vision enhancement module."""

import pytest
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path
import tempfile
import os

from inception.enhance.vision.providers import (
    VLMProvider,
    VLMResponse,
    LLaVAProvider,
    OpenAIVisionProvider,
    AnthropicVisionProvider,
    get_vlm_provider,
)
from inception.enhance.vision.analyzer import (
    VisionAnalyzer,
    ImageAnalysis,
    PROMPTS,
)


class TestVLMResponse:
    """Tests for VLMResponse dataclass."""
    
    def test_creation(self):
        """Test basic response creation."""
        response = VLMResponse(
            description="A flowchart showing the data pipeline",
            model="llava:7b",
            provider="llava",
            tokens_used=500,
            cost_usd=0.0,
        )
        
        assert response.description == "A flowchart showing the data pipeline"
        assert response.model == "llava:7b"
        assert response.provider == "llava"
        assert response.cost_usd == 0.0


class TestLLaVAProvider:
    """Tests for LLaVA provider."""
    
    def test_initialization(self):
        """Test provider initialization."""
        provider = LLaVAProvider(model="llava:7b")
        
        assert provider.name == "llava"
        assert provider.model == "llava:7b"
        assert provider.base_url == "http://localhost:11434"
    
    def test_custom_url(self):
        """Test custom base URL."""
        provider = LLaVAProvider(base_url="http://custom:8080")
        assert provider.base_url == "http://custom:8080"
    
    @patch("httpx.Client.get")
    def test_is_available_false(self, mock_get):
        """Test availability check when Ollama is down."""
        mock_get.side_effect = Exception("Connection refused")
        
        provider = LLaVAProvider()
        assert provider.is_available() is False
    
    @patch("httpx.Client.get")
    def test_is_available_no_llava(self, mock_get):
        """Test availability when LLaVA model not present."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "models": [{"name": "llama3:8b"}]  # No llava
        }
        mock_get.return_value = mock_response
        
        provider = LLaVAProvider()
        assert provider.is_available() is False


class TestOpenAIVisionProvider:
    """Tests for OpenAI Vision provider."""
    
    def test_initialization(self):
        """Test provider initialization."""
        provider = OpenAIVisionProvider(
            model="gpt-4o",
            api_key="test-key",
        )
        
        assert provider.name == "openai"
        assert provider.model == "gpt-4o"
        assert provider.api_key == "test-key"
    
    def test_is_available_with_key(self):
        """Test availability with API key."""
        provider = OpenAIVisionProvider(api_key="test-key")
        assert provider.is_available() is True
    
    def test_is_available_without_key(self):
        """Test availability without API key."""
        # Clear env var for test
        old_key = os.environ.pop("OPENAI_API_KEY", None)
        try:
            provider = OpenAIVisionProvider(api_key=None)
            assert provider.is_available() is False
        finally:
            if old_key:
                os.environ["OPENAI_API_KEY"] = old_key


class TestAnthropicVisionProvider:
    """Tests for Anthropic Vision provider."""
    
    def test_initialization(self):
        """Test provider initialization."""
        provider = AnthropicVisionProvider(
            model="claude-3-5-sonnet-20241022",
            api_key="test-key",
        )
        
        assert provider.name == "anthropic"
        assert "claude" in provider.model
        assert provider.api_key == "test-key"
    
    def test_is_available_with_key(self):
        """Test availability with API key."""
        provider = AnthropicVisionProvider(api_key="test-key")
        assert provider.is_available() is True


class TestGetVLMProvider:
    """Tests for VLM provider factory function."""
    
    @patch.object(LLaVAProvider, "is_available", return_value=True)
    def test_auto_prefers_llava(self, mock_available):
        """Test auto mode prefers LLaVA when available."""
        provider = get_vlm_provider(name="auto")
        assert provider.name == "llava"
    
    def test_offline_requires_llava(self):
        """Test offline mode requires LLaVA."""
        with patch.object(LLaVAProvider, "is_available", return_value=False):
            with pytest.raises(RuntimeError, match="No offline VLM"):
                get_vlm_provider(name="auto", offline=True)
    
    def test_unknown_provider(self):
        """Test unknown provider raises error."""
        with pytest.raises(ValueError, match="Unknown VLM provider"):
            get_vlm_provider(name="unknown_provider")


class TestImageAnalysis:
    """Tests for ImageAnalysis dataclass."""
    
    def test_creation(self):
        """Test basic analysis creation."""
        analysis = ImageAnalysis(
            image_path="/path/to/image.png",
            content_type="diagram",
            description="A flowchart showing data flow",
            entities=["Database", "API", "Frontend"],
        )
        
        assert analysis.content_type == "diagram"
        assert len(analysis.entities) == 3
    
    def test_default_values(self):
        """Test default values."""
        analysis = ImageAnalysis(
            image_path="test.png",
            content_type="unknown",
            description="Test",
        )
        
        assert analysis.entities == []
        assert analysis.relationships == []
        assert analysis.provider == ""


class TestVisionAnalyzer:
    """Tests for VisionAnalyzer."""
    
    @pytest.fixture
    def mock_provider(self):
        """Create a mock VLM provider."""
        provider = Mock(spec=VLMProvider)
        provider.name = "mock"
        provider.analyze_image.return_value = VLMResponse(
            description="This is a flowchart showing the data pipeline with Database, API, and Frontend components.",
            model="mock",
            provider="mock",
            tokens_used=100,
            cost_usd=0.001,
        )
        return provider
    
    @pytest.fixture
    def analyzer(self, mock_provider):
        """Create an analyzer with mock provider."""
        return VisionAnalyzer(provider=mock_provider)
    
    @pytest.fixture
    def temp_image(self):
        """Create a temporary image file."""
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
            # Write minimal PNG data
            f.write(b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde\x00\x00\x00\x0cIDATx\x9cc\xf8\x0f\x00\x00\x01\x01\x00\x05\x18\xd8N\x00\x00\x00\x00IEND\xaeB`\x82')
            return Path(f.name)
    
    def test_initialization(self, analyzer, mock_provider):
        """Test analyzer initialization."""
        assert analyzer.provider == mock_provider
        assert analyzer.total_tokens == 0
        assert analyzer.total_cost == 0.0
    
    def test_analyze_success(self, analyzer, mock_provider, temp_image):
        """Test successful image analysis."""
        result = analyzer.analyze(temp_image)
        
        assert result.image_path == str(temp_image)
        assert result.description != ""
        assert result.tokens_used == 100
        mock_provider.analyze_image.assert_called_once()
        
        # Clean up
        temp_image.unlink()
    
    def test_analyze_updates_totals(self, analyzer, mock_provider, temp_image):
        """Test that analysis updates token/cost totals."""
        analyzer.analyze(temp_image)
        
        assert analyzer.total_tokens == 100
        assert analyzer.total_cost == 0.001
        
        temp_image.unlink()
    
    def test_analyze_file_not_found(self, analyzer):
        """Test error handling for missing file."""
        with pytest.raises(FileNotFoundError):
            analyzer.analyze("/nonexistent/image.png")
    
    def test_detect_content_type_diagram(self, analyzer):
        """Test content type detection for diagrams."""
        detected = analyzer._detect_content_type(
            "This is a flowchart showing the architecture..."
        )
        assert detected == "diagram"
    
    def test_detect_content_type_code(self, analyzer):
        """Test content type detection for code."""
        detected = analyzer._detect_content_type(
            "This Python code shows a function definition..."
        )
        assert detected == "code"
    
    def test_detect_content_type_chart(self, analyzer):
        """Test content type detection for charts."""
        detected = analyzer._detect_content_type(
            "A bar chart showing sales data over time..."
        )
        assert detected == "chart"
    
    def test_extract_entities(self, analyzer):
        """Test entity extraction from description."""
        entities = analyzer._extract_entities(
            "The diagram shows Database connected to API which serves the Frontend."
        )
        
        assert "Database" in entities
        assert "API" in entities
        assert "Frontend" in entities


class TestPrompts:
    """Tests for specialized prompts."""
    
    def test_all_prompts_defined(self):
        """Test that all expected prompts are defined."""
        expected = ["default", "diagram", "code", "chart", "ui"]
        
        for prompt_type in expected:
            assert prompt_type in PROMPTS
            assert len(PROMPTS[prompt_type]) > 50  # Non-trivial prompt
    
    def test_default_prompt(self):
        """Test default prompt contains key instructions."""
        prompt = PROMPTS["default"]
        
        assert "describe" in prompt.lower()
        assert "elements" in prompt.lower()
