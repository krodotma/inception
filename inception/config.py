"""
Configuration system for Inception.

Supports YAML configuration files and environment variable overrides.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

# Default paths
DEFAULT_DATA_DIR = Path.home() / ".inception"
DEFAULT_DB_PATH = DEFAULT_DATA_DIR / "db"
DEFAULT_ARTIFACTS_PATH = DEFAULT_DATA_DIR / "artifacts"
DEFAULT_CACHE_PATH = DEFAULT_DATA_DIR / "cache"


@dataclass
class LMDBConfig:
    """LMDB database configuration."""
    
    path: Path = field(default_factory=lambda: DEFAULT_DB_PATH)
    map_size: int = 10 * 1024 * 1024 * 1024  # 10GB default
    max_dbs: int = 16
    
    def __post_init__(self) -> None:
        if isinstance(self.path, str):
            self.path = Path(self.path)


@dataclass
class WhisperConfig:
    """Whisper ASR configuration."""
    
    model_size: str = "base"  # tiny, base, small, medium, large
    device: str = "auto"  # auto, cpu, cuda
    compute_type: str = "float16"
    language: str | None = None  # None for auto-detect


@dataclass
class OCRConfig:
    """OCR configuration."""
    
    engine: str = "paddleocr"  # paddleocr, tesseract
    languages: list[str] = field(default_factory=lambda: ["en"])
    use_gpu: bool = True


@dataclass
class PipelineConfig:
    """Pipeline processing configuration."""
    
    offline_mode: bool = False
    cache_enabled: bool = True
    max_workers: int = 4
    seed: int | None = None  # For reproducibility


@dataclass
class VectorConfig:
    """Vector embedding configuration."""
    
    model: str = "all-MiniLM-L6-v2"  # sentence-transformers model
    dimension: int = 384
    index_type: str = "hnsw"  # hnsw, flat, ivf
    normalize: bool = True
    batch_size: int = 32
    ef_construction: int = 200  # HNSW parameter
    ef_search: int = 50  # HNSW search parameter
    m: int = 16  # HNSW connections per layer


@dataclass
class LLMConfig:
    """LLM provider configuration."""
    
    provider: str = "anthropic"  # anthropic, openai, local
    model: str = "claude-sonnet-4-20250514"  # model identifier
    temperature: float = 0.7
    max_tokens: int = 4096
    api_key_env: str = "ANTHROPIC_API_KEY"  # env var for API key
    base_url: str | None = None  # custom endpoint
    timeout_seconds: int = 30


@dataclass
class Config:
    """Main configuration for Inception."""
    
    data_dir: Path = field(default_factory=lambda: DEFAULT_DATA_DIR)
    artifacts_dir: Path = field(default_factory=lambda: DEFAULT_ARTIFACTS_PATH)
    cache_dir: Path = field(default_factory=lambda: DEFAULT_CACHE_PATH)
    
    lmdb: LMDBConfig = field(default_factory=LMDBConfig)
    whisper: WhisperConfig = field(default_factory=WhisperConfig)
    ocr: OCRConfig = field(default_factory=OCRConfig)
    pipeline: PipelineConfig = field(default_factory=PipelineConfig)
    vector: VectorConfig = field(default_factory=VectorConfig)
    llm: LLMConfig = field(default_factory=LLMConfig)
    
    # Schema and pipeline versions for determinism
    schema_version: str = "0.1.0"
    pipeline_version: str = "0.1.0"
    
    def __post_init__(self) -> None:
        # Convert string paths to Path objects
        if isinstance(self.data_dir, str):
            self.data_dir = Path(self.data_dir)
        if isinstance(self.artifacts_dir, str):
            self.artifacts_dir = Path(self.artifacts_dir)
        if isinstance(self.cache_dir, str):
            self.cache_dir = Path(self.cache_dir)
    
    @classmethod
    def from_yaml(cls, path: Path | str) -> Config:
        """Load configuration from a YAML file."""
        path = Path(path)
        if not path.exists():
            return cls()
        
        with open(path) as f:
            data = yaml.safe_load(f) or {}
        
        return cls.from_dict(data)
    
    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Config:
        """Create configuration from a dictionary."""
        config = cls()
        
        # Top-level paths
        if "data_dir" in data:
            config.data_dir = Path(data["data_dir"])
        if "artifacts_dir" in data:
            config.artifacts_dir = Path(data["artifacts_dir"])
        if "cache_dir" in data:
            config.cache_dir = Path(data["cache_dir"])
        
        # LMDB config
        if "lmdb" in data:
            lmdb_data = data["lmdb"]
            config.lmdb = LMDBConfig(
                path=Path(lmdb_data.get("path", config.lmdb.path)),
                map_size=lmdb_data.get("map_size", config.lmdb.map_size),
                max_dbs=lmdb_data.get("max_dbs", config.lmdb.max_dbs),
            )
        
        # Whisper config
        if "whisper" in data:
            w_data = data["whisper"]
            config.whisper = WhisperConfig(
                model_size=w_data.get("model_size", config.whisper.model_size),
                device=w_data.get("device", config.whisper.device),
                compute_type=w_data.get("compute_type", config.whisper.compute_type),
                language=w_data.get("language"),
            )
        
        # OCR config
        if "ocr" in data:
            ocr_data = data["ocr"]
            config.ocr = OCRConfig(
                engine=ocr_data.get("engine", config.ocr.engine),
                languages=ocr_data.get("languages", config.ocr.languages),
                use_gpu=ocr_data.get("use_gpu", config.ocr.use_gpu),
            )
        
        # Pipeline config
        if "pipeline" in data:
            p_data = data["pipeline"]
            config.pipeline = PipelineConfig(
                offline_mode=p_data.get("offline_mode", config.pipeline.offline_mode),
                cache_enabled=p_data.get("cache_enabled", config.pipeline.cache_enabled),
                max_workers=p_data.get("max_workers", config.pipeline.max_workers),
                seed=p_data.get("seed"),
            )
        
        return config
    
    def to_dict(self) -> dict[str, Any]:
        """Convert configuration to a dictionary."""
        return {
            "data_dir": str(self.data_dir),
            "artifacts_dir": str(self.artifacts_dir),
            "cache_dir": str(self.cache_dir),
            "schema_version": self.schema_version,
            "pipeline_version": self.pipeline_version,
            "lmdb": {
                "path": str(self.lmdb.path),
                "map_size": self.lmdb.map_size,
                "max_dbs": self.lmdb.max_dbs,
            },
            "whisper": {
                "model_size": self.whisper.model_size,
                "device": self.whisper.device,
                "compute_type": self.whisper.compute_type,
                "language": self.whisper.language,
            },
            "ocr": {
                "engine": self.ocr.engine,
                "languages": self.ocr.languages,
                "use_gpu": self.ocr.use_gpu,
            },
            "pipeline": {
                "offline_mode": self.pipeline.offline_mode,
                "cache_enabled": self.pipeline.cache_enabled,
                "max_workers": self.pipeline.max_workers,
                "seed": self.pipeline.seed,
            },
            "vector": {
                "model": self.vector.model,
                "dimension": self.vector.dimension,
                "index_type": self.vector.index_type,
                "normalize": self.vector.normalize,
                "batch_size": self.vector.batch_size,
            },
            "llm": {
                "provider": self.llm.provider,
                "model": self.llm.model,
                "temperature": self.llm.temperature,
                "max_tokens": self.llm.max_tokens,
            },
        }
    
    def save(self, path: Path | str) -> None:
        """Save configuration to a YAML file."""
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w") as f:
            yaml.dump(self.to_dict(), f, default_flow_style=False)
    
    def ensure_directories(self) -> None:
        """Create all necessary directories."""
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.artifacts_dir.mkdir(parents=True, exist_ok=True)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.lmdb.path.mkdir(parents=True, exist_ok=True)


# Global configuration instance
_config: Config | None = None


def get_config() -> Config:
    """Get the global configuration instance."""
    global _config
    if _config is None:
        # Try to load from default locations
        config_paths = [
            Path.cwd() / "inception.yaml",
            Path.cwd() / "inception.yml",
            DEFAULT_DATA_DIR / "config.yaml",
        ]
        
        for path in config_paths:
            if path.exists():
                _config = Config.from_yaml(path)
                break
        else:
            _config = Config()
        
        # Apply environment variable overrides
        _apply_env_overrides(_config)
    
    return _config


def set_config(config: Config) -> None:
    """Set the global configuration instance."""
    global _config
    _config = config


def _apply_env_overrides(config: Config) -> None:
    """Apply environment variable overrides to configuration."""
    env_mappings = {
        "INCEPTION_DATA_DIR": ("data_dir", Path),
        "INCEPTION_ARTIFACTS_DIR": ("artifacts_dir", Path),
        "INCEPTION_CACHE_DIR": ("cache_dir", Path),
        "INCEPTION_OFFLINE": ("pipeline.offline_mode", lambda x: x.lower() in ("1", "true", "yes")),
        "INCEPTION_SEED": ("pipeline.seed", int),
        "INCEPTION_WHISPER_MODEL": ("whisper.model_size", str),
        "INCEPTION_OCR_ENGINE": ("ocr.engine", str),
    }
    
    for env_var, (attr_path, converter) in env_mappings.items():
        value = os.environ.get(env_var)
        if value is not None:
            parts = attr_path.split(".")
            obj = config
            for part in parts[:-1]:
                obj = getattr(obj, part)
            setattr(obj, parts[-1], converter(value))
    
    # Additional vector/LLM env overrides
    vector_env_mappings = {
        "INCEPTION_VECTOR_MODEL": ("vector.model", str),
        "INCEPTION_VECTOR_DIM": ("vector.dimension", int),
        "INCEPTION_LLM_PROVIDER": ("llm.provider", str),
        "INCEPTION_LLM_MODEL": ("llm.model", str),
        "INCEPTION_LLM_TEMPERATURE": ("llm.temperature", float),
    }
    
    for env_var, (attr_path, converter) in vector_env_mappings.items():
        value = os.environ.get(env_var)
        if value is not None:
            parts = attr_path.split(".")
            obj = config
            for part in parts[:-1]:
                obj = getattr(obj, part)
            setattr(obj, parts[-1], converter(value))
