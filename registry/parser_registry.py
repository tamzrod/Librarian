from pathlib import Path


# Artifact type classifications
class ArtifactType:
    TEXT = 'text'
    DOCUMENT = 'document'
    STRUCTURED = 'structured'
    IMAGE = 'image'
    VIDEO = 'video'
    AUDIO = 'audio'
    ARCHIVE = 'archive'
    EXECUTABLE = 'executable'
    UNKNOWN = 'unknown'


# Mapping from parser name to artifact type
PARSER_ARTIFACT_TYPES = {
    'text': ArtifactType.TEXT,
    'image': ArtifactType.IMAGE,
    'photo': ArtifactType.IMAGE,
    'video': ArtifactType.VIDEO,
    'audio': ArtifactType.AUDIO,
    'csv': ArtifactType.STRUCTURED,
    'json': ArtifactType.STRUCTURED,
    'xml': ArtifactType.STRUCTURED,
    'yaml': ArtifactType.STRUCTURED,
    'archive': ArtifactType.ARCHIVE,
    'zip': ArtifactType.ARCHIVE,
    'pdf': ArtifactType.DOCUMENT,
    'document': ArtifactType.DOCUMENT,
}


class ParserRegistry:
    def __init__(self):
        self.parsers = {}

    def register(self, extension, parser):
        self.parsers[extension] = parser

    def register_with_artifact_type(self, extension, parser, artifact_type):
        """Register a parser with an artifact type."""
        self.parsers[extension] = parser

    def get_parser(self, file_path):
        """Get parser for a file path or extension."""
        if isinstance(file_path, Path):
            file_path = str(file_path)
        if isinstance(file_path, str):
            # Extract extension and try both with and without dot
            ext = Path(file_path).suffix.lower()
            if ext in self.parsers:
                return self.parsers[ext]
            # Also try without dot
            if ext.startswith('.') and ext[1:] in self.parsers:
                return self.parsers[ext[1:]]
        return self.parsers.get(file_path, None)
    
    def get_artifact_type(self, file_path) -> str:
        """Get the artifact type for a file based on its extension.
        
        Args:
            file_path: Path to the file
            
        Returns:
            Artifact type string (image, document, video, audio, archive, executable, structured, text, unknown)
        """
        if isinstance(file_path, Path):
            file_path = str(file_path)
        
        ext = Path(file_path).suffix.lower()
        
        # Image types
        image_exts = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp', '.svg', '.tiff', '.tif', '.heic', '.heif'}
        if ext in image_exts:
            return ArtifactType.IMAGE
        
        # Video types
        video_exts = {'.mp4', '.mov', '.avi', '.mkv', '.wmv', '.flv', '.webm', '.m4v'}
        if ext in video_exts:
            return ArtifactType.VIDEO
        
        # Audio types
        audio_exts = {'.mp3', '.wav', '.flac', '.aac', '.ogg', '.m4a', '.wma', '.opus'}
        if ext in audio_exts:
            return ArtifactType.AUDIO
        
        # Archive types
        archive_exts = {'.zip', '.tar', '.gz', '.bz2', '.xz', '.rar', '.7z', '.tgz'}
        if ext in archive_exts:
            return ArtifactType.ARCHIVE
        
        # Structured data types
        structured_exts = {'.csv', '.tsv', '.json', '.xml', '.yaml', '.yml', '.toml', '.db', '.sqlite', '.sql'}
        if ext in structured_exts:
            return ArtifactType.STRUCTURED
        
        # Executable types
        exec_exts = {'.exe', '.dll', '.so', '.dylib', '.bin', '.app', '.sh', '.bash', '.bat', '.cmd', '.ps1', '.py', '.js'}
        if ext in exec_exts:
            return ArtifactType.EXECUTABLE
        
        # Document types
        doc_exts = {'.pdf', '.doc', '.docx', '.odt', '.rtf', '.md', '.rst', '.tex'}
        if ext in doc_exts:
            return ArtifactType.DOCUMENT
        
        # Text types (plain text without specific format)
        text_exts = {'.txt', '.log', '.text'}
        if ext in text_exts:
            return ArtifactType.TEXT
        
        # Default to unknown
        return ArtifactType.UNKNOWN
