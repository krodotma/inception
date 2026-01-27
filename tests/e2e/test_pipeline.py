"""End-to-end tests for the Inception pipeline."""

import pytest
import tempfile
from pathlib import Path

from inception.config import Config
from inception.db import InceptionDB
from inception.db.records import SourceRecord, SpanRecord, NodeRecord, Confidence, VideoAnchor
from inception.db.keys import SourceType, NodeKind, SpanType


class TestE2EGraphBuildingPipeline:
    """E2E tests for the graph building pipeline."""
    
    @pytest.fixture
    def temp_db(self):
        """Create a temporary database."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test.lmdb"
            db = InceptionDB(path=db_path)
            yield db
            db.close()
    
    def test_full_source_to_node_pipeline(self, temp_db):
        """Test creating source, spans, nodes, and edges."""
        db = temp_db
        
        # 1. Create a source
        source = SourceRecord(
            nid=db.allocate_nid(),
            source_type=SourceType.YOUTUBE_VIDEO,
            uri="https://youtube.com/watch?v=test123",
            title="Test Video",
        )
        db.put_source(source)
        
        # Verify source
        retrieved = db.get_source(source.nid)
        assert retrieved is not None
        assert retrieved.title == "Test Video"
        
        # 2. Create spans
        span1 = SpanRecord(
            nid=db.allocate_nid(),
            span_type=SpanType.VIDEO,
            source_nid=source.nid,
            anchor=VideoAnchor(t0_ms=0, t1_ms=5000),
            text="This is the first segment about Python programming.",
        )
        db.put_span(span1)
        
        span2 = SpanRecord(
            nid=db.allocate_nid(),
            span_type=SpanType.VIDEO,
            source_nid=source.nid,
            anchor=VideoAnchor(t0_ms=5000, t1_ms=10000),
            text="Python is used for many applications.",
        )
        db.put_span(span2)
        
        # 3. Create entity node
        entity_node = NodeRecord(
            nid=db.allocate_nid(),
            kind=NodeKind.ENTITY,
            payload={
                "name": "Python",
                "entity_type": "PRODUCT",
            },
            evidence_spans=[span1.nid, span2.nid],
            confidence=Confidence(aleatoric=0.9),
            source_nids=[source.nid],
        )
        db.put_node(entity_node)
        
        # 4. Create claim node
        claim_node = NodeRecord(
            nid=db.allocate_nid(),
            kind=NodeKind.CLAIM,
            payload={
                "text": "Python is used for many applications",
                "subject": "Python",
                "predicate": "is used for",
                "object": "many applications",
                "modality": "assertion",
            },
            evidence_spans=[span2.nid],
            confidence=Confidence(aleatoric=0.85),
            source_nids=[source.nid],
        )
        db.put_node(claim_node)
        
        # Verify nodes
        nodes = list(db.iter_nodes())
        assert len(nodes) == 2
        
        entity_nodes = [n for n in nodes if n.kind == NodeKind.ENTITY]
        claim_nodes = [n for n in nodes if n.kind == NodeKind.CLAIM]
        
        assert len(entity_nodes) == 1
        assert len(claim_nodes) == 1
        assert entity_nodes[0].payload["name"] == "Python"


class TestE2ESkillSynthesis:
    """E2E tests for skill synthesis."""
    
    @pytest.fixture
    def temp_db_with_procedure(self):
        """Create a temp DB with a procedure node."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test.lmdb"
            db = InceptionDB(path=db_path)
            
            # Create source
            source = SourceRecord(
                nid=db.allocate_nid(),
                source_type=SourceType.YOUTUBE_VIDEO,
                uri="https://youtube.com/watch?v=tutorial",
                title="Python Tutorial",
            )
            db.put_source(source)
            
            # Create procedure node
            procedure = NodeRecord(
                nid=db.allocate_nid(),
                kind=NodeKind.PROCEDURE,
                payload={
                    "title": "Install Python",
                    "goal": "Set up Python development environment",
                    "steps": [
                        {"index": 0, "text": "Download Python from python.org", "action_verb": "download"},
                        {"index": 1, "text": "Run the installer", "action_verb": "run"},
                        {"index": 2, "text": "Add Python to PATH", "action_verb": "add"},
                        {"index": 3, "text": "Verify installation with python --version", "action_verb": "verify"},
                    ],
                },
                source_nids=[source.nid],
            )
            db.put_node(procedure)
            
            yield db, source.nid, procedure.nid
            db.close()
    
    def test_synthesize_skill_from_procedure(self, temp_db_with_procedure):
        """Test synthesizing a skill from a procedure."""
        from inception.skills import SkillSynthesizer
        
        db, source_nid, procedure_nid = temp_db_with_procedure
        
        synthesizer = SkillSynthesizer(db)
        skills = synthesizer.synthesize_from_source(source_nid)
        
        assert len(skills) == 1
        
        skill = skills[0]
        assert skill.name == "Install Python"
        assert len(skill.steps) == 4
        assert skill.steps[0].action == "download"
    
    def test_skill_to_markdown_output(self, temp_db_with_procedure):
        """Test generating SKILL.md content."""
        from inception.skills import SkillSynthesizer
        
        db, source_nid, _ = temp_db_with_procedure
        
        synthesizer = SkillSynthesizer(db)
        skills = synthesizer.synthesize_from_source(source_nid)
        
        skill = skills[0]
        md = skill.to_skill_md()
        
        # Verify frontmatter
        assert "---" in md
        assert "name: Install Python" in md
        
        # Verify steps
        assert "### Step 1: Download" in md
        assert "### Step 2: Run" in md
        assert "python.org" in md
    
    def test_save_skill_to_file(self, temp_db_with_procedure):
        """Test saving skill to file."""
        from inception.skills import SkillSynthesizer
        
        db, source_nid, _ = temp_db_with_procedure
        
        synthesizer = SkillSynthesizer(db)
        skills = synthesizer.synthesize_from_source(source_nid)
        
        with tempfile.TemporaryDirectory() as outdir:
            output_dir = Path(outdir)
            skill_path = synthesizer.save_skill(skills[0], output_dir)
            
            assert skill_path.exists()
            assert skill_path.name == "install-python.md"
            
            content = skill_path.read_text()
            assert "Install Python" in content


class TestE2EQueryPipeline:
    """E2E tests for the query pipeline."""
    
    @pytest.fixture
    def populated_db(self):
        """Create a populated database."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test.lmdb"
            db = InceptionDB(path=db_path)
            
            # Create source
            source = SourceRecord(
                nid=db.allocate_nid(),
                source_type=SourceType.WEB_PAGE,
                uri="https://example.com/article",
                title="Test Article",
            )
            db.put_source(source)
            
            # Create entities
            for name, etype in [("Python", "PRODUCT"), ("Guido", "PERSON"), ("Google", "ORG")]:
                node = NodeRecord(
                    nid=db.allocate_nid(),
                    kind=NodeKind.ENTITY,
                    payload={"name": name, "entity_type": etype},
                    source_nids=[source.nid],
                )
                db.put_node(node)
            
            # Create claims
            for text in ["Python is popular", "Python was created by Guido"]:
                node = NodeRecord(
                    nid=db.allocate_nid(),
                    kind=NodeKind.CLAIM,
                    payload={"text": text, "modality": "assertion"},
                    source_nids=[source.nid],
                )
                db.put_node(node)
            
            yield db, source.nid
            db.close()
    
    def test_query_entities(self, populated_db):
        """Test querying entities."""
        from inception.query import QueryEngine
        
        db, source_nid = populated_db
        engine = QueryEngine(db)
        
        # Query all entities
        result = engine.query_entities()
        assert result.total_count == 3
        
        # Query by type
        result = engine.query_entities(entity_type="PERSON")
        assert result.total_count == 1
        assert result.nodes[0].payload["name"] == "Guido"
    
    def test_query_claims(self, populated_db):
        """Test querying claims."""
        from inception.query import QueryEngine
        
        db, source_nid = populated_db
        engine = QueryEngine(db)
        
        result = engine.query_claims()
        assert result.total_count == 2
    
    def test_full_text_search(self, populated_db):
        """Test full-text search."""
        from inception.query import QueryEngine
        
        db, source_nid = populated_db
        engine = QueryEngine(db)
        
        result = engine.full_text_search("Guido")
        assert result.total_count >= 1


class TestE2EOutputGeneration:
    """E2E tests for output generation."""
    
    @pytest.fixture
    def db_with_content(self):
        """Create a DB with varied content."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test.lmdb"
            db = InceptionDB(path=db_path)
            
            source = SourceRecord(
                nid=db.allocate_nid(),
                source_type=SourceType.YOUTUBE_VIDEO,
                uri="https://youtube.com/watch?v=demo",
                title="Demo Video",
            )
            db.put_source(source)
            
            # Add entities, claims, procedures, gaps
            db.put_node(NodeRecord(
                nid=db.allocate_nid(),
                kind=NodeKind.ENTITY,
                payload={"name": "Python", "entity_type": "PRODUCT"},
                source_nids=[source.nid],
            ))
            
            db.put_node(NodeRecord(
                nid=db.allocate_nid(),
                kind=NodeKind.CLAIM,
                payload={"text": "Python is great for beginners", "modality": "assertion"},
                source_nids=[source.nid],
            ))
            
            db.put_node(NodeRecord(
                nid=db.allocate_nid(),
                kind=NodeKind.PROCEDURE,
                payload={
                    "title": "Getting Started",
                    "goal": "Start coding in Python",
                    "steps": [{"index": 0, "text": "Install Python"}],
                },
                source_nids=[source.nid],
            ))
            
            db.put_node(NodeRecord(
                nid=db.allocate_nid(),
                kind=NodeKind.GAP,
                payload={"gap_type": "undefined_term", "description": "IDE not explained"},
                source_nids=[source.nid],
            ))
            
            yield db, source.nid
            db.close()
    
    def test_generate_action_pack(self, db_with_content):
        """Test generating an action pack."""
        from inception.output import ActionPackGenerator, RheoLevel
        
        db, source_nid = db_with_content
        
        generator = ActionPackGenerator(db)
        pack = generator.generate(source_nid, level=RheoLevel.FULL)
        
        assert pack.source_nid == source_nid
        assert len(pack.entities) == 1
        assert len(pack.claims) == 1
        assert len(pack.procedures) == 1
        assert len(pack.gaps) == 1
    
    def test_action_pack_markdown(self, db_with_content):
        """Test action pack markdown output."""
        from inception.output import ActionPackGenerator, RheoLevel
        
        db, source_nid = db_with_content
        
        generator = ActionPackGenerator(db)
        pack = generator.generate(source_nid, level=RheoLevel.FULL)
        
        md = pack.to_markdown(RheoLevel.FULL)
        
        assert "Key Entities" in md or "Claims" in md or "Uncertainties" in md
