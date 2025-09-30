"""Abstract interface for a language model service."""

from abc import ABC, abstractmethod


class LLMService(ABC):
    """Abstract interface for a language model service."""

    @abstractmethod
    async def analyze_media_files(
        self, media_filenames: list[str], prompt: str, source_directory: str = "videos"
    ) -> str:
        """Analyzes media files with a given prompt."""
