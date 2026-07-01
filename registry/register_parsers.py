from registry.parser_registry import ParserRegistry
from parsers.json_parser import JsonParser
from parsers.yaml_parser import YamlParser
from parsers.csv_parser import CsvParser
from parsers.ini_parser import IniParser
from parsers.toml_parser import TomlParser
from parsers.xml_parser import XmlParser
from parsers.python_parser import PythonParser
from parsers.text_parser import TextParser
from parsers.image_parser import ImageParser


# ============================================================================
# MIME Type Mapping
# ============================================================================
# Shared MIME type mapping for extension-to-mime conversion.
# This is the SOURCE OF TRUTH for mime_type during artifact discovery.
# All parsers and the collection watcher use this mapping.
#
# Architecture: mime_type is Discovery Metadata, not Enrichment Metadata.
# It is determined from the file extension and persisted immediately upon
# artifact discovery - no worker or parser dependency.

MIME_TYPE_MAPPING = {
    # Images
    '.jpg': 'image/jpeg',
    '.jpeg': 'image/jpeg',
    '.png': 'image/png',
    '.gif': 'image/gif',
    '.bmp': 'image/bmp',
    '.tiff': 'image/tiff',
    '.tif': 'image/tiff',
    '.webp': 'image/webp',
    '.heic': 'image/heic',
    '.heif': 'image/heif',
    '.svg': 'image/svg+xml',
    '.ico': 'image/x-icon',
    # Videos
    '.mp4': 'video/mp4',
    '.mov': 'video/quicktime',
    '.avi': 'video/x-msvideo',
    '.mkv': 'video/x-matroska',
    '.wmv': 'video/x-ms-wmv',
    '.flv': 'video/x-flv',
    '.webm': 'video/webm',
    '.m4v': 'video/x-m4v',
    # Audio
    '.mp3': 'audio/mpeg',
    '.wav': 'audio/wav',
    '.flac': 'audio/flac',
    '.aac': 'audio/aac',
    '.ogg': 'audio/ogg',
    '.m4a': 'audio/mp4',
    '.wma': 'audio/x-ms-wma',
    # Documents
    '.pdf': 'application/pdf',
    '.doc': 'application/msword',
    '.docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    '.xls': 'application/vnd.ms-excel',
    '.xlsx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    '.ppt': 'application/vnd.ms-powerpoint',
    '.pptx': 'application/vnd.openxmlformats-officedocument.presentationml.presentation',
    # Text
    '.txt': 'text/plain',
    '.md': 'text/markdown',
    '.html': 'text/html',
    '.htm': 'text/html',
    '.css': 'text/css',
    '.js': 'application/javascript',
    '.json': 'application/json',
    '.xml': 'application/xml',
    '.yaml': 'application/x-yaml',
    '.yml': 'application/x-yaml',
    '.toml': 'application/toml',
    '.ini': 'text/plain',
    '.csv': 'text/csv',
    '.tsv': 'text/tab-separated-values',
    # Code
    '.py': 'text/x-python',
    '.java': 'text/x-java',
    '.c': 'text/x-c',
    '.cpp': 'text/x-c++',
    '.h': 'text/x-c-header',
    '.hpp': 'text/x-c++-header',
    '.cs': 'text/x-csharp',
    '.ts': 'application/typescript',
    '.go': 'text/x-go',
    '.rs': 'text/x-rust',
    '.rb': 'text/x-ruby',
    '.php': 'text/x-php',
    '.sh': 'application/x-sh',
    '.bash': 'application/x-sh',
    '.zsh': 'application/x-sh',
    # Archives
    '.zip': 'application/zip',
    '.tar': 'application/x-tar',
    '.gz': 'application/gzip',
    '.bz2': 'application/x-bzip2',
    '.xz': 'application/x-xz',
    '.rar': 'application/vnd.rar',
    '.7z': 'application/x-7z-compressed',
    # Other
    '.bin': 'application/octet-stream',
    '.exe': 'application/x-msdownload',
    '.dll': 'application/x-msdownload',
    '.iso': 'application/x-iso9660-image',
}


def get_mime_type_from_extension(extension: str) -> str:
    """Get MIME type for a file extension.
    
    Args:
        extension: File extension (with or without dot)
        
    Returns:
        MIME type string, defaults to 'application/octet-stream' for unknown extensions
    """
    if not extension:
        return 'application/octet-stream'
    if not extension.startswith('.'):
        extension = '.' + extension
    return MIME_TYPE_MAPPING.get(extension.lower(), 'application/octet-stream')


registry = ParserRegistry()
registry.register('.json', JsonParser())
registry.register('.yaml', YamlParser())
registry.register('.csv', CsvParser())
registry.register('.ini', IniParser())
registry.register('.toml', TomlParser())
registry.register('.xml', XmlParser())
registry.register('.py', PythonParser())
registry.register('.txt', TextParser())
registry.register('.md', TextParser())

# Image parser - Artifact Ingestion Phase 1
# Required formats
registry.register('.jpg', ImageParser())
registry.register('.jpeg', ImageParser())
registry.register('.png', ImageParser())
registry.register('.heic', ImageParser())
registry.register('.webp', ImageParser())

# Optional formats
registry.register('.bmp', ImageParser())
registry.register('.tiff', ImageParser())
registry.register('.tif', ImageParser())
registry.register('.gif', ImageParser())
