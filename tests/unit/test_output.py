"""Unit tests for output layer modules."""

import pytest
from inception.output.rheomode import (
    RheoLevel,
    ActionItem,
    KeyTakeaway,
    EvidenceLink,
    ActionPack,
    ActionPackGenerator,
)


class TestRheoLevel:
    """Tests for RheoLevel enumeration."""
    
    def test_rheo_level_values(self):
        """Test rheo level integer values."""
        assert RheoLevel.GIST == 0
        assert RheoLevel.TAKEAWAYS == 1
        assert RheoLevel.EVIDENCE == 2
        assert RheoLevel.FULL == 3
        assert RheoLevel.SKILLS == 4
    
    def test_rheo_level_comparison(self):
        """Test rheo level ordering."""
        assert RheoLevel.GIST < RheoLevel.TAKEAWAYS
        assert RheoLevel.EVIDENCE < RheoLevel.FULL
        assert RheoLevel.SKILLS > RheoLevel.EVIDENCE


class TestActionItem:
    """Tests for ActionItem dataclass."""
    
    def test_action_item_creation(self):
        """Test creating an action item."""
        item = ActionItem(
            action="Review the document",
            context="Section 3",
            priority=7,
            action_type="do",
        )
        
        assert item.action == "Review the document"
        assert item.priority == 7
        assert item.action_type == "do"
    
    def test_action_item_defaults(self):
        """Test action item default values."""
        item = ActionItem(action="Do something")
        
        assert item.context is None
        assert item.priority == 0
        assert item.action_type == "general"
        assert item.confidence == 1.0


class TestKeyTakeaway:
    """Tests for KeyTakeaway dataclass."""
    
    def test_takeaway_creation(self):
        """Test creating a key takeaway."""
        takeaway = KeyTakeaway(
            text="Important insight here",
            category="insight",
            importance=0.9,
        )
        
        assert takeaway.text == "Important insight here"
        assert takeaway.category == "insight"
        assert takeaway.importance == 0.9
    
    def test_takeaway_categories(self):
        """Test different takeaway categories."""
        insight = KeyTakeaway(text="Fact", category="insight")
        warning = KeyTakeaway(text="Be careful", category="warning")
        tip = KeyTakeaway(text="Try this", category="tip")
        
        assert insight.category == "insight"
        assert warning.category == "warning"
        assert tip.category == "tip"


class TestEvidenceLink:
    """Tests for EvidenceLink dataclass."""
    
    def test_evidence_link_creation(self):
        """Test creating an evidence link."""
        link = EvidenceLink(
            span_nid=42,
            timestamp_ms=5000,
            text_preview="...at this point...",
        )
        
        assert link.span_nid == 42
        assert link.timestamp_ms == 5000
        assert link.text_preview == "...at this point..."
    
    def test_evidence_link_page_reference(self):
        """Test evidence link with page reference."""
        link = EvidenceLink(
            span_nid=100,
            page=5,
        )
        
        assert link.page == 5
        assert link.timestamp_ms is None


class TestActionPack:
    """Tests for ActionPack dataclass."""
    
    def test_action_pack_creation(self):
        """Test creating an action pack."""
        pack = ActionPack(
            source_nid=1,
            title="Test Content",
            gist="A quick summary",
            why_it_matters="It helps you learn",
        )
        
        assert pack.source_nid == 1
        assert pack.title == "Test Content"
        assert pack.gist == "A quick summary"
    
    def test_action_pack_with_takeaways(self):
        """Test action pack with takeaways and actions."""
        pack = ActionPack(
            source_nid=1,
            key_takeaways=[
                KeyTakeaway(text="Point 1", category="insight"),
                KeyTakeaway(text="Point 2", category="tip"),
            ],
            action_items=[
                ActionItem(action="Do this", priority=5),
                ActionItem(action="Do that", priority=3),
            ],
        )
        
        assert len(pack.key_takeaways) == 2
        assert len(pack.action_items) == 2
    
    def test_action_pack_at_level_gist(self):
        """Test getting action pack at gist level."""
        pack = ActionPack(
            source_nid=1,
            title="Test",
            gist="Summary",
            why_it_matters="Important",
            key_takeaways=[KeyTakeaway(text="T1")],
            claims=[{"text": "Claim 1"}],
        )
        
        result = pack.at_level(RheoLevel.GIST)
        
        assert "gist" in result
        assert "why_it_matters" in result
        assert "key_takeaways" not in result
    
    def test_action_pack_at_level_takeaways(self):
        """Test getting action pack at takeaways level."""
        pack = ActionPack(
            source_nid=1,
            gist="Summary",
            key_takeaways=[KeyTakeaway(text="T1")],
            action_items=[ActionItem(action="A1")],
            claims=[{"text": "C1"}],
        )
        
        result = pack.at_level(RheoLevel.TAKEAWAYS)
        
        assert "gist" in result
        assert "key_takeaways" in result
        assert "action_items" in result
        assert "claims" not in result
    
    def test_action_pack_at_level_full(self):
        """Test getting action pack at full level."""
        pack = ActionPack(
            source_nid=1,
            gist="Summary",
            key_takeaways=[KeyTakeaway(text="T1")],
            claims=[{"text": "C1"}],
            entities=[{"name": "E1"}],
            gaps=[{"description": "G1"}],
        )
        
        result = pack.at_level(RheoLevel.FULL)
        
        assert "entities" in result
        assert "gaps" in result
    
    def test_action_pack_to_markdown(self):
        """Test markdown rendering of action pack."""
        pack = ActionPack(
            source_nid=1,
            title="Test Document",
            gist="This is a test document about testing.",
            why_it_matters="Testing is important.",
            key_takeaways=[
                KeyTakeaway(text="Testing catches bugs", category="insight"),
                KeyTakeaway(text="Always test edge cases", category="tip"),
            ],
            action_items=[
                ActionItem(action="Write more tests", priority=8),
            ],
            claims=[{"text": "Unit tests improve code quality."}],
        )
        
        md = pack.to_markdown(RheoLevel.EVIDENCE)
        
        assert "# Test Document" in md
        assert "TL;DR" in md
        assert "Key Takeaways" in md
        assert "Action Items" in md
        assert "- [ ] Write more tests" in md
    
    def test_action_pack_markdown_with_procedures(self):
        """Test markdown with procedures."""
        pack = ActionPack(
            source_nid=1,
            title="How-To Guide",
            procedures=[{
                "title": "Setup Process",
                "steps": [
                    {"index": 0, "text": "Install dependencies"},
                    {"index": 1, "text": "Configure settings"},
                ],
            }],
        )
        
        md = pack.to_markdown(RheoLevel.EVIDENCE)
        
        assert "### Setup Process" in md
        assert "1. Install dependencies" in md
        assert "2. Configure settings" in md
    
    def test_action_pack_markdown_with_gaps(self):
        """Test markdown with gaps/uncertainties."""
        pack = ActionPack(
            source_nid=1,
            gaps=[
                {"description": "Missing version info"},
                {"description": "Unclear requirements"},
            ],
        )
        
        md = pack.to_markdown(RheoLevel.FULL)
        
        assert "Uncertainties & Gaps" in md
        assert "❓" in md


class TestActionPackWithCategories:
    """Tests for action pack category rendering."""
    
    def test_warning_category_display(self):
        """Test warning category in markdown."""
        pack = ActionPack(
            source_nid=1,
            key_takeaways=[
                KeyTakeaway(text="Be careful here", category="warning"),
            ],
        )
        
        md = pack.to_markdown()
        assert "⚠️" in md
    
    def test_tip_category_display(self):
        """Test tip category in markdown."""
        pack = ActionPack(
            source_nid=1,
            key_takeaways=[
                KeyTakeaway(text="Pro tip", category="tip"),
            ],
        )
        
        md = pack.to_markdown()
        assert "💡" in md
    
    def test_entity_grouping(self):
        """Test entity grouping by type in markdown."""
        pack = ActionPack(
            source_nid=1,
            entities=[
                {"name": "Python", "entity_type": "PRODUCT"},
                {"name": "JavaScript", "entity_type": "PRODUCT"},
                {"name": "Google", "entity_type": "ORG"},
            ],
        )
        
        md = pack.to_markdown(RheoLevel.FULL)
        
        assert "PRODUCT" in md
        assert "ORG" in md
