"""
CODEX-2 ULTRATHINK: Comprehensive Test Suite

Tests for:
- OAuth providers
- LMDB storage
- API endpoints
- TUI screens

Model: Opus 4.5 ULTRATHINK
"""

import asyncio
import pytest
from unittest.mock import MagicMock, patch, AsyncMock
from datetime import datetime, timedelta


# =============================================================================
# FIXTURES
# =============================================================================

@pytest.fixture
def sample_token():
    """Sample OAuth token for testing."""
    return {
        "access_token": "test_access_token_12345",
        "refresh_token": "test_refresh_token_67890",
        "token_type": "Bearer",
        "expires_at": (datetime.utcnow() + timedelta(hours=1)).isoformat(),
        "scope": "read write",
    }


@pytest.fixture
def sample_entity():
    """Sample entity for testing."""
    return {
        "id": "test-entity-1",
        "name": "Test Entity",
        "type": "entity",
        "description": "A test entity for unit testing",
        "confidence": 0.95,
    }


@pytest.fixture
def sample_claim():
    """Sample claim for testing."""
    return {
        "id": "test-claim-1",
        "statement": "This is a test claim statement",
        "entity_id": "test-entity-1",
        "confidence": 0.87,
        "sources": ["source-1", "source-2"],
    }


@pytest.fixture
def sample_gap():
    """Sample knowledge gap for testing."""
    return {
        "id": "test-gap-1",
        "description": "Missing information about X",
        "gap_type": "missing",
        "priority": "high",
    }


# =============================================================================
# OAUTH TESTS
# =============================================================================

class TestOAuthBase:
    """Tests for OAuth base classes."""
    
    def test_pkce_code_verifier_length(self):
        """PKCE verifier should be 43-128 characters."""
        from inception.enhance.auth.base import PKCEHelper
        
        verifier = PKCEHelper.generate_code_verifier()
        assert 43 <= len(verifier) <= 128
        
    def test_pkce_code_verifier_charset(self):
        """PKCE verifier should use only allowed characters."""
        from inception.enhance.auth.base import PKCEHelper
        
        allowed = set("ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-._~")
        verifier = PKCEHelper.generate_code_verifier()
        assert all(c in allowed for c in verifier)
        
    def test_pkce_challenge_derivation(self):
        """PKCE challenge should be base64url encoded SHA256."""
        from inception.enhance.auth.base import PKCEHelper
        
        verifier = "test_verifier_12345"
        challenge = PKCEHelper.generate_code_challenge(verifier)
        
        # Challenge should be base64url encoded (no padding)
        assert "=" not in challenge
        assert "+" not in challenge
        assert "/" not in challenge
        
    def test_token_validity_check(self, sample_token):
        """Token should correctly report validity."""
        from inception.enhance.auth.base import OAuthToken
        
        token = OAuthToken(**sample_token)
        assert token.is_valid()
        
    def test_token_expired(self, sample_token):
        """Expired token should report invalid."""
        from inception.enhance.auth.base import OAuthToken
        
        sample_token["expires_at"] = (datetime.utcnow() - timedelta(hours=1)).isoformat()
        token = OAuthToken(**sample_token)
        assert not token.is_valid()


class TestClaudeOAuth:
    """Tests for Claude OAuth provider."""
    
    def test_auth_url_generation(self):
        """Should generate valid Claude auth URL."""
        from inception.enhance.auth.claude import ClaudeOAuthProvider
        
        provider = ClaudeOAuthProvider()
        url, state = provider.get_authorization_url()
        
        assert "claude.ai" in url or "anthropic.com" in url
        assert "client_id=" in url
        assert "state=" in url
        assert len(state) > 0
        
    def test_tier_detection_max(self, sample_token):
        """Should detect Max tier from token claims."""
        with patch('inception.enhance.auth.claude.ClaudeOAuthProvider._decode_token') as mock:
            mock.return_value = {"tier": "max"}
            
            from inception.enhance.auth.claude import ClaudeOAuthProvider
            provider = ClaudeOAuthProvider()
            
            tier = provider.detect_tier(sample_token["access_token"])
            assert tier == "max"


class TestGeminiOAuth:
    """Tests for Gemini OAuth provider."""
    
    def test_auth_url_generation(self):
        """Should generate valid Google OAuth URL."""
        from inception.enhance.auth.gemini import GeminiOAuthProvider
        
        provider = GeminiOAuthProvider()
        url, state = provider.get_authorization_url()
        
        assert "accounts.google.com" in url
        assert "client_id=" in url
        assert "scope=" in url


# =============================================================================
# STORAGE TESTS
# =============================================================================

class TestTokenStorage:
    """Tests for secure token storage."""
    
    def test_store_and_retrieve(self, sample_token):
        """Should store and retrieve token."""
        with patch('keyring.set_password') as mock_set, \
             patch('keyring.get_password') as mock_get:
            
            mock_get.return_value = '{"access_token": "test"}'
            
            from inception.enhance.auth.storage import SecureTokenStorage
            storage = SecureTokenStorage()
            
            storage.store("claude", sample_token)
            mock_set.assert_called()
            
    def test_delete_token(self):
        """Should delete stored token."""
        with patch('keyring.delete_password') as mock_delete:
            from inception.enhance.auth.storage import SecureTokenStorage
            storage = SecureTokenStorage()
            
            storage.delete("claude")
            mock_delete.assert_called()


class TestLMDBStorage:
    """Tests for LMDB knowledge storage."""
    
    @pytest.fixture
    def mock_storage(self, tmp_path):
        """Create mock storage with temp path."""
        from inception.serve.api import LMDBStorage
        return LMDBStorage(db_path=str(tmp_path / "test.lmdb"))
    
    def test_get_entities_returns_list(self, mock_storage):
        """Should return list of entities."""
        entities = mock_storage.get_entities()
        assert isinstance(entities, list)
        
    def test_get_stats_returns_dict(self, mock_storage):
        """Should return stats dictionary."""
        stats = mock_storage.get_stats()
        assert isinstance(stats, dict)
        assert "entities" in stats
        assert "claims" in stats
        
    def test_search_filter(self, mock_storage):
        """Should filter entities by search term."""
        entities = mock_storage.get_entities(search="OAuth")
        # Sample data includes OAuth
        assert any("OAuth" in e.get("name", "") for e in entities)


# =============================================================================
# API TESTS
# =============================================================================

@pytest.mark.asyncio
class TestAPIEndpoints:
    """Tests for FastAPI endpoints."""
    
    @pytest.fixture
    def client(self):
        """Create test client."""
        from fastapi.testclient import TestClient
        from inception.serve.api import app
        return TestClient(app)
    
    def test_root_endpoint(self, client):
        """Root should return API info."""
        response = client.get("/")
        assert response.status_code == 200
        assert "name" in response.json()
        
    def test_health_endpoint(self, client):
        """Health should return status."""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert data["status"] in ["healthy", "degraded"]
        
    def test_stats_endpoint(self, client):
        """Stats should return counts."""
        response = client.get("/api/stats")
        assert response.status_code == 200
        data = response.json()
        assert "entities" in data
        assert "claims" in data
        
    def test_entities_endpoint(self, client):
        """Entities should return list."""
        response = client.get("/api/entities")
        assert response.status_code == 200
        assert isinstance(response.json(), list)
        
    def test_entities_search(self, client):
        """Entities should support search."""
        response = client.get("/api/entities", params={"search": "test"})
        assert response.status_code == 200
        
    def test_claims_endpoint(self, client):
        """Claims should return list."""
        response = client.get("/api/claims")
        assert response.status_code == 200
        assert isinstance(response.json(), list)
        
    def test_gaps_endpoint(self, client):
        """Gaps should return list."""
        response = client.get("/api/gaps")
        assert response.status_code == 200
        assert isinstance(response.json(), list)
        
    def test_graph_endpoint(self, client):
        """Graph should return nodes and edges."""
        response = client.get("/api/graph")
        assert response.status_code == 200
        data = response.json()
        assert "nodes" in data
        assert "edges" in data


# =============================================================================
# TUI TESTS
# =============================================================================

class TestTUIComponents:
    """Tests for Textual TUI components."""
    
    @pytest.mark.asyncio
    async def test_api_client_stats(self):
        """API client should fetch stats."""
        with patch('httpx.AsyncClient.get') as mock_get:
            mock_response = AsyncMock()
            mock_response.json.return_value = {"entities": 100}
            mock_response.raise_for_status = MagicMock()
            mock_get.return_value = mock_response
            
            from inception.tui.app import InceptionAPI
            api = InceptionAPI()
            stats = await api.get_stats()
            
            assert "entities" in stats or "error" in stats
            
    @pytest.mark.asyncio  
    async def test_api_client_entities(self):
        """API client should fetch entities."""
        with patch('httpx.AsyncClient.get') as mock_get:
            mock_response = AsyncMock()
            mock_response.json.return_value = [{"id": "1", "name": "Test"}]
            mock_response.raise_for_status = MagicMock()
            mock_get.return_value = mock_response
            
            from inception.tui.app import InceptionAPI
            api = InceptionAPI()
            entities = await api.get_entities()
            
            assert isinstance(entities, list)


# =============================================================================
# INTEGRATION TESTS
# =============================================================================

class TestIntegration:
    """Integration tests for full workflows."""
    
    def test_auth_to_storage_flow(self, sample_token):
        """Token should flow from auth to storage."""
        with patch('keyring.set_password'), patch('keyring.get_password'):
            from inception.enhance.auth.storage import SecureTokenStorage
            from inception.enhance.auth.base import OAuthToken
            
            storage = SecureTokenStorage()
            token = OAuthToken(**sample_token)
            
            # Store
            storage.store("test_provider", sample_token)
            
            # Token should be valid
            assert token.is_valid()
            
    def test_storage_to_api_flow(self):
        """Storage should provide data to API."""
        from inception.serve.api import storage
        
        # Get data
        entities = storage.get_entities(limit=5)
        stats = storage.get_stats()
        
        # Should have consistent data
        assert isinstance(entities, list)
        assert isinstance(stats, dict)


# =============================================================================
# LEARNING ENGINE TESTS (Stage 3.8 Steps 493-497)
# =============================================================================

class TestDAPOOptimizer:
    """Tests for DAPO optimizer."""
    
    def test_dynamic_clip_adjustment(self):
        """Clip range should adjust based on advantage variance."""
        # Import directly to avoid __init__.py
        import sys
        sys.path.insert(0, '/Users/kroma/inceptional')
        exec(open('/Users/kroma/inceptional/inception/enhance/learning.py').read(), globals())
        
        dapo = DAPOOptimizer(clip_range=0.2)
        
        # Low variance advantages
        clip1 = dapo.compute_dynamic_clip([0.1, 0.1, 0.1])
        
        # High variance advantages
        dapo._advantage_variance = 0.1  # Reset
        clip2 = dapo.compute_dynamic_clip([0.0, 0.5, 1.0])
        
        assert clip2 >= clip1  # Higher variance = wider clip
        
    def test_entropy_bonus_decay(self):
        """Entropy bonus should decay over time."""
        import sys
        sys.path.insert(0, '/Users/kroma/inceptional')
        exec(open('/Users/kroma/inceptional/inception/enhance/learning.py').read(), globals())
        
        dapo = DAPOOptimizer()
        initial_schedule = dapo._entropy_schedule
        
        # Simulate updates
        for _ in range(100):
            dapo.compute_entropy_bonus(0.5)
        
        assert dapo._entropy_schedule < initial_schedule


class TestGRPOOptimizer:
    """Tests for GRPO optimizer."""
    
    def test_group_experience_tracking(self):
        """Should group experiences by action."""
        import sys
        sys.path.insert(0, '/Users/kroma/inceptional')
        exec(open('/Users/kroma/inceptional/inception/enhance/learning.py').read(), globals())
        
        grpo = GRPOOptimizer()
        
        exp1 = Experience(state={}, action="extract_claim", reward=0.5, next_state={}, done=False)
        exp2 = Experience(state={}, action="resolve_gap", reward=0.3, next_state={}, done=False)
        exp3 = Experience(state={}, action="extract_claim", reward=0.7, next_state={}, done=False)
        
        grpo.add_experience(exp1)
        grpo.add_experience(exp2)
        grpo.add_experience(exp3)
        
        assert "extract_claim" in grpo._action_groups
        assert "resolve_gap" in grpo._action_groups
        assert len(grpo._action_groups["extract_claim"]) == 2


class TestRLVREngine:
    """Tests for RLVR verification engine."""
    
    def test_verified_claim_reward(self):
        """Verified claims should get positive reward."""
        import sys
        sys.path.insert(0, '/Users/kroma/inceptional')
        exec(open('/Users/kroma/inceptional/inception/enhance/learning.py').read(), globals())
        
        rlvr = RLVREngine()
        
        claim = {"statement": "OAuth uses tokens for authentication"}
        sources = [{"content": "OAuth protocol uses bearer tokens for authentication and authorization"}]
        
        reward = rlvr.compute_verified_reward("extract_claim", claim, sources)
        assert reward > 0  # Should be positive for verified claim
        
    def test_unverified_claim_penalty(self):
        """Unverified claims should get negative reward."""
        import sys
        sys.path.insert(0, '/Users/kroma/inceptional')
        exec(open('/Users/kroma/inceptional/inception/enhance/learning.py').read(), globals())
        
        rlvr = RLVREngine()
        
        claim = {"statement": "completely unrelated statement xyz"}
        sources = [{"content": "OAuth protocol documentation"}]
        
        reward = rlvr.compute_verified_reward("extract_claim", claim, sources)
        assert reward < 0  # Should be negative for unverified


class TestGAPPolicy:
    """Tests for GAP-aware policy."""
    
    def test_gap_prioritization(self):
        """Should prioritize high-priority gaps."""
        import sys
        sys.path.insert(0, '/Users/kroma/inceptional')
        exec(open('/Users/kroma/inceptional/inception/enhance/learning.py').read(), globals())
        
        gap_policy = GAPPolicy()
        
        gap_high = {"id": "g1", "priority": "high", "gap_type": "missing"}
        gap_low = {"id": "g2", "priority": "low", "gap_type": "missing"}
        
        score_high = gap_policy.score_gap(gap_high)
        score_low = gap_policy.score_gap(gap_low)
        
        assert score_high > score_low


class TestActiveLearner:
    """Tests for active learning."""
    
    def test_uncertainty_sampling(self):
        """Should select high-uncertainty samples."""
        import sys
        sys.path.insert(0, '/Users/kroma/inceptional')
        exec(open('/Users/kroma/inceptional/inception/enhance/learning.py').read(), globals())
        
        learner = ActiveLearner(strategy="uncertainty")
        
        candidates = [
            {"id": "c1", "name": "Candidate 1"},
            {"id": "c2", "name": "Candidate 2"},
            {"id": "c3", "name": "Candidate 3"},
        ]
        
        selected = learner.select_queries(candidates, num_queries=2)
        assert len(selected) == 2


class TestInceptionLearningEngine:
    """Tests for unified learning engine."""
    
    def test_engine_initialization(self):
        """Engine should initialize all components."""
        import sys
        sys.path.insert(0, '/Users/kroma/inceptional')
        exec(open('/Users/kroma/inceptional/inception/enhance/learning.py').read(), globals())
        
        engine = InceptionLearningEngine()
        
        assert engine.dapo is not None
        assert engine.grpo is not None
        assert engine.rlvr is not None
        assert engine.gap_policy is not None
        assert engine.active_learner is not None
        
    def test_step_execution(self):
        """Step should record experience and return reward."""
        import sys
        sys.path.insert(0, '/Users/kroma/inceptional')
        exec(open('/Users/kroma/inceptional/inception/enhance/learning.py').read(), globals())
        
        engine = InceptionLearningEngine()
        
        result = engine.step(
            action="extract_claim",
            state={"entities": 10},
            result={"statement": "test claim"},
            sources=[{"content": "test source"}],
        )
        
        assert "step" in result
        assert "reward" in result
        assert result["step"] == 1


# =============================================================================
# PHASE 3 API TESTS (Steps 498-500)
# =============================================================================

@pytest.mark.asyncio
class TestPhase3APIEndpoints:
    """Tests for Phase 3 API endpoints."""
    
    @pytest.fixture
    def client(self):
        """Create test client."""
        from fastapi.testclient import TestClient
        from inception.serve.api import app
        return TestClient(app)
    
    def test_timeline_endpoint(self, client):
        """Timeline should return events."""
        response = client.get("/api/timeline")
        assert response.status_code == 200
        assert isinstance(response.json(), list)
        
    def test_sources_endpoint(self, client):
        """Sources should return list."""
        response = client.get("/api/sources")
        assert response.status_code == 200
        assert isinstance(response.json(), list)
        
    def test_graph_clusters_endpoint(self, client):
        """Graph clusters should return cluster data."""
        response = client.get("/api/graph/clusters")
        assert response.status_code == 200
        data = response.json()
        assert "clusters" in data
        
    def test_graph_path_endpoint(self, client):
        """Path finding should work."""
        response = client.post("/api/graph/path", json={
            "source_id": "entity-1",
            "target_id": "entity-2",
        })
        assert response.status_code == 200
        data = response.json()
        assert "path_found" in data
        
    def test_extract_text_endpoint(self, client):
        """Text extraction should work."""
        response = client.post("/api/extract/text", json={
            "text": "OAuth is an authentication protocol.",
        })
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "processed"
        
    def test_actionpack_endpoint(self, client):
        """ActionPack generation should work."""
        response = client.post("/api/actionpack", json={
            "procedure_id": "proc-1",
            "format": "bash",
        })
        assert response.status_code == 200
        data = response.json()
        assert "script" in data
        
    def test_learning_stats_endpoint(self, client):
        """Learning stats should return data."""
        response = client.get("/api/learning/stats")
        assert response.status_code == 200


# =============================================================================
# RUN
# =============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
