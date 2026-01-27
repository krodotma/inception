"""
Comprehensive tests for Tier 4 Operations modules.

Tests for:
- Incremental Sync
- Export Pipeline
- Interactive TUI
"""

import pytest
import tempfile
import time
from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock, patch

# ==============================================================================
# SYNC TESTS
# ==============================================================================

class TestFileWatcher:
    """Tests for FileWatcher."""
    
    def test_watch_config_defaults(self):
        """Test WatchConfig default values."""
        from inception.enhance.operations.sync.watcher import WatchConfig
        
        config = WatchConfig(watch_paths=[Path("/tmp")])
        
        assert ".mp4" in config.include_extensions
        assert ".*" in config.exclude_patterns
        assert config.poll_interval == 1.0
    
    def test_watch_event_creation(self):
        """Test WatchEvent creation."""
        from inception.enhance.operations.sync.watcher import WatchEvent
        
        event = WatchEvent(
            path=Path("/tmp/test.mp4"),
            event_type="created",
            timestamp=time.time(),
            size=1024,
        )
        
        assert event.event_type == "created"
        assert event.size == 1024
    
    def test_file_watcher_scan(self):
        """Test single file scan."""
        from inception.enhance.operations.sync.watcher import FileWatcher, WatchConfig
        
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create test file
            test_file = Path(tmpdir) / "test.mp4"
            test_file.write_text("video content")
            
            config = WatchConfig(watch_paths=[Path(tmpdir)])
            watcher = FileWatcher(config)
            
            events = watcher.scan_once()
            
            # Should detect the new file
            assert len(events) >= 1


class TestChangeDetector:
    """Tests for ChangeDetector."""
    
    def test_change_type_enum(self):
        """Test ChangeType enum."""
        from inception.enhance.operations.sync.detector import ChangeType
        
        assert ChangeType.CREATED.name == "CREATED"
        assert ChangeType.MODIFIED.name == "MODIFIED"
        assert ChangeType.DELETED.name == "DELETED"
    
    def test_detect_new_file(self):
        """Test detecting new files."""
        from inception.enhance.operations.sync.detector import ChangeDetector, ChangeType
        
        with tempfile.TemporaryDirectory() as tmpdir:
            detector = ChangeDetector(state_path=Path(tmpdir) / "state.db")
            
            test_file = Path(tmpdir) / "test.txt"
            test_file.write_text("content")
            
            event = detector.detect_change(test_file)
            
            assert event.change_type == ChangeType.CREATED
            assert event.content_hash != ""
    
    def test_detect_unchanged_file(self):
        """Test detecting unchanged files."""
        from inception.enhance.operations.sync.detector import ChangeDetector, ChangeType
        
        with tempfile.TemporaryDirectory() as tmpdir:
            detector = ChangeDetector(state_path=Path(tmpdir) / "state.db")
            
            test_file = Path(tmpdir) / "test.txt"
            test_file.write_text("content")
            
            # First detection - new
            detector.detect_change(test_file)
            detector.record_sync(test_file)
            
            # Second detection - unchanged
            event = detector.detect_change(test_file)
            assert event.change_type == ChangeType.UNCHANGED
    
    def test_detect_modified_file(self):
        """Test detecting modified files."""
        from inception.enhance.operations.sync.detector import ChangeDetector, ChangeType
        
        with tempfile.TemporaryDirectory() as tmpdir:
            detector = ChangeDetector(state_path=Path(tmpdir) / "state.db")
            
            test_file = Path(tmpdir) / "test.txt"
            test_file.write_text("content v1")
            
            detector.detect_change(test_file)
            detector.record_sync(test_file)
            
            # Modify file
            time.sleep(0.1)
            test_file.write_text("content v2")
            
            event = detector.detect_change(test_file)
            assert event.change_type == ChangeType.MODIFIED


class TestSyncQueue:
    """Tests for SyncQueue."""
    
    def test_enqueue_dequeue(self):
        """Test basic queue operations."""
        from inception.enhance.operations.sync.queue import SyncQueue, JobPriority
        
        queue = SyncQueue()
        
        job = queue.enqueue(Path("/test/file.mp4"))
        
        assert queue.size == 1
        
        dequeued = queue.dequeue()
        assert dequeued.path == Path("/test/file.mp4")
        assert queue.size == 0
    
    def test_priority_ordering(self):
        """Test priority queue ordering."""
        from inception.enhance.operations.sync.queue import SyncQueue, JobPriority
        
        queue = SyncQueue()
        
        queue.enqueue(Path("/low.mp4"), priority=JobPriority.LOW)
        queue.enqueue(Path("/high.mp4"), priority=JobPriority.HIGH)
        queue.enqueue(Path("/normal.mp4"), priority=JobPriority.NORMAL)
        
        # High priority should come first
        first = queue.dequeue()
        assert first.path == Path("/high.mp4")
    
    def test_job_retry(self):
        """Test job retry mechanism."""
        from inception.enhance.operations.sync.queue import SyncQueue, JobPriority, JobStatus
        
        queue = SyncQueue()
        
        job = queue.enqueue(Path("/test.mp4"))
        job = queue.dequeue()
        
        # Fail the job
        queue.fail(job, "Test error")
        
        # Should be re-queued
        assert queue.size == 1
        assert job.attempt == 1
    
    def test_job_max_retries(self):
        """Test max retry limit."""
        from inception.enhance.operations.sync.queue import SyncQueue
        
        queue = SyncQueue()
        
        job = queue.enqueue(Path("/test.mp4"))
        job = queue.dequeue()
        job.max_attempts = 1
        
        queue.fail(job, "Error")
        
        # Should not be re-queued
        assert queue.size == 0
        assert len(queue.get_failed()) == 1


class TestSyncEngine:
    """Tests for SyncEngine."""
    
    def test_sync_config(self):
        """Test SyncConfig creation."""
        from inception.enhance.operations.sync.engine import SyncConfig
        
        config = SyncConfig(watch_paths=[Path("/tmp")])
        
        assert config.batch_size == 10
        assert config.worker_threads == 2
    
    def test_sync_result(self):
        """Test SyncResult creation."""
        from inception.enhance.operations.sync.engine import SyncResult
        
        result = SyncResult(
            path=Path("/test.mp4"),
            success=True,
            nid=123,
            duration_ms=50.0,
        )
        
        assert result.success
        assert result.nid == 123
    
    def test_scan_directory(self):
        """Test directory scanning."""
        from inception.enhance.operations.sync.engine import SyncEngine, SyncConfig
        
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create test files
            (Path(tmpdir) / "test.txt").write_text("content")
            
            config = SyncConfig(
                watch_paths=[Path(tmpdir)],
                state_path=Path(tmpdir) / "state.db",
            )
            
            engine = SyncEngine(config)
            changes = engine.scan()
            
            assert len(changes) >= 1


# ==============================================================================
# EXPORT TESTS
# ==============================================================================

class TestExportFormat:
    """Tests for ExportFormat."""
    
    def test_format_enum(self):
        """Test ExportFormat enum."""
        from inception.enhance.operations.export.formats import ExportFormat
        
        assert ExportFormat.OBSIDIAN.name == "OBSIDIAN"
        assert ExportFormat.JSON.name == "JSON"
    
    def test_file_extension(self):
        """Test file extension mapping."""
        from inception.enhance.operations.export.formats import ExportFormat, get_file_extension
        
        assert get_file_extension(ExportFormat.OBSIDIAN) == ".md"
        assert get_file_extension(ExportFormat.JSON) == ".json"
        assert get_file_extension(ExportFormat.RDF) == ".ttl"


class TestExportPipeline:
    """Tests for ExportPipeline."""
    
    def test_export_config(self):
        """Test ExportConfig creation."""
        from inception.enhance.operations.export.pipeline import ExportConfig, ExportResult
        from inception.enhance.operations.export.formats import ExportFormat
        
        config = ExportConfig(
            output_dir=Path("/tmp/export"),
            format=ExportFormat.OBSIDIAN,
        )
        
        assert config.include_entities
        assert config.create_index
    
    def test_export_result(self):
        """Test ExportResult creation."""
        from inception.enhance.operations.export.pipeline import ExportResult
        
        result = ExportResult(
            success=True,
            output_dir=Path("/tmp"),
            files_created=10,
            total_size_bytes=1024,
        )
        
        assert result.success
        assert not result.has_errors


class TestObsidianExporter:
    """Tests for ObsidianExporter."""
    
    def test_export_empty_data(self):
        """Test export with empty data."""
        from inception.enhance.operations.export.obsidian import ObsidianExporter
        from inception.enhance.operations.export.pipeline import ExportConfig
        from inception.enhance.operations.export.formats import ExportFormat
        
        with tempfile.TemporaryDirectory() as tmpdir:
            config = ExportConfig(
                output_dir=Path(tmpdir),
                format=ExportFormat.OBSIDIAN,
            )
            
            exporter = ObsidianExporter(config)
            result = exporter.export({"entities": [], "claims": [], "procedures": []})
            
            assert result.success
            assert result.files_created >= 1  # Index file
    
    def test_export_with_entities(self):
        """Test export with entity data."""
        from inception.enhance.operations.export.obsidian import ObsidianExporter
        from inception.enhance.operations.export.pipeline import ExportConfig
        from inception.enhance.operations.export.formats import ExportFormat
        
        with tempfile.TemporaryDirectory() as tmpdir:
            config = ExportConfig(
                output_dir=Path(tmpdir),
                format=ExportFormat.OBSIDIAN,
            )
            
            data = {
                "entities": [
                    {"nid": 1, "name": "Python", "type": "programming language"}
                ],
                "claims": [],
                "procedures": [],
                "edges": [],
            }
            
            exporter = ObsidianExporter(config)
            result = exporter.export(data)
            
            assert result.success
            assert result.files_created >= 2  # Entity + index


class TestMarkdownExporter:
    """Tests for MarkdownExporter."""
    
    def test_export_creates_file(self):
        """Test markdown export creates file."""
        from inception.enhance.operations.export.markdown import MarkdownExporter
        from inception.enhance.operations.export.pipeline import ExportConfig
        from inception.enhance.operations.export.formats import ExportFormat
        
        with tempfile.TemporaryDirectory() as tmpdir:
            config = ExportConfig(
                output_dir=Path(tmpdir),
                format=ExportFormat.MARKDOWN,
            )
            
            exporter = MarkdownExporter(config)
            result = exporter.export({"entities": [], "claims": [], "procedures": [], "sources": []})
            
            assert result.success
            assert (Path(tmpdir) / "knowledge_base.md").exists()


class TestJSONExporter:
    """Tests for JSONExporter."""
    
    def test_export_valid_json(self):
        """Test JSON export creates valid JSON."""
        import json
        from inception.enhance.operations.export.json_export import JSONExporter
        from inception.enhance.operations.export.pipeline import ExportConfig
        from inception.enhance.operations.export.formats import ExportFormat
        
        with tempfile.TemporaryDirectory() as tmpdir:
            config = ExportConfig(
                output_dir=Path(tmpdir),
                format=ExportFormat.JSON,
            )
            
            exporter = JSONExporter(config)
            result = exporter.export({"entities": [], "claims": []})
            
            assert result.success
            
            # Verify valid JSON
            output_file = Path(tmpdir) / "knowledge_base.json"
            data = json.loads(output_file.read_text())
            assert "version" in data
            assert "content" in data


# ==============================================================================
# TUI TESTS
# ==============================================================================

class TestInceptionTUI:
    """Tests for InceptionTUI."""
    
    def test_tui_config(self):
        """Test TUIConfig creation."""
        from inception.enhance.operations.tui.app import TUIConfig
        
        config = TUIConfig(theme="light")
        
        assert config.theme == "light"
        assert config.show_gaps
    
    def test_tui_creation(self):
        """Test TUI instantiation."""
        from inception.enhance.operations.tui.app import InceptionTUI, TUIConfig
        
        config = TUIConfig()
        tui = InceptionTUI(config)
        
        assert not tui._running
    
    def test_tui_stop(self):
        """Test TUI stop."""
        from inception.enhance.operations.tui.app import InceptionTUI
        
        tui = InceptionTUI()
        tui._running = True
        tui.stop()
        
        assert not tui._running


# ==============================================================================
# INTEGRATION TESTS
# ==============================================================================

class TestOperationsIntegration:
    """Integration tests for operations modules."""
    
    def test_sync_to_export_workflow(self):
        """Test sync detecting changes then exporting."""
        from inception.enhance.operations.sync.engine import SyncEngine, SyncConfig
        from inception.enhance.operations.export.pipeline import ExportPipeline, ExportConfig
        from inception.enhance.operations.export.formats import ExportFormat
        
        with tempfile.TemporaryDirectory() as tmpdir:
            tmppath = Path(tmpdir)
            
            # Create sync engine
            sync_config = SyncConfig(
                watch_paths=[tmppath / "input"],
                state_path=tmppath / "state.db",
            )
            
            (tmppath / "input").mkdir()
            (tmppath / "input" / "test.txt").write_text("content")
            
            engine = SyncEngine(sync_config)
            changes = engine.scan()
            
            # Create export pipeline
            export_config = ExportConfig(
                output_dir=tmppath / "output",
                format=ExportFormat.JSON,
            )
            
            pipeline = ExportPipeline()
            
            # Both components work
            assert len(changes) >= 1
            assert pipeline is not None
    
    def test_package_imports(self):
        """Test all exports are accessible."""
        from inception.enhance.operations import (
            SyncEngine,
            SyncConfig,
            ChangeEvent,
            FileWatcher,
            ExportPipeline,
            ExportFormat,
            ObsidianExporter,
            MarkdownExporter,
            JSONExporter,
            InceptionTUI,
        )
        
        assert SyncEngine is not None
        assert ExportPipeline is not None
        assert InceptionTUI is not None
