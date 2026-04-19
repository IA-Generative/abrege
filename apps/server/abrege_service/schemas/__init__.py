IMAGE_CONTENT_TYPES = [
    "image/jpeg",
    "image/png",
    "image/gif",
    "image/bmp",
    "image/webp",
    "image/svg+xml",
    "image/tiff",
]
MICROSOFT_WORD_CONTENT_TYPES_DOCX = [
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
]
MICROSOFT_WORD_CONTENT_TYPES_DOC = [
    "application/msword",
    "application/vnd.ms-word",
]

LIBRE_OFFICE_CONTENT_TYPES = ["application/vnd.oasis.opendocument.text"]
LIBRE_OFFICE_PRESENTATION_TYPES = ["application/vnd.oasis.opendocument.presentation"]

MICROSOFT_SPREADSHEET_CONTENT_TYPES = [
    "application/vnd.ms-excel",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
]
MICROSOFT_PRESENTATION_CONTENT_TYPES = [
    "application/vnd.ms-powerpoint",
    "application/vnd.openxmlformats-officedocument.presentationml.presentation",
]
AUDIO_CONTENT_TYPES = [
    # MP3
    "audio/mpeg",
    "audio/mp3",
    "audio/x-mpeg",
    # WAV
    "audio/wav",
    "audio/x-wav",
    "audio/vnd.wave",
    "audio/wave",
    # OGG
    "audio/ogg",
    "application/ogg",
    # MP4 / M4A
    "audio/mp4",
    "audio/x-m4a",
    # AAC
    "audio/aac",
    "audio/x-aac",
    # FLAC
    "audio/flac",
    "audio/x-flac",
    "application/x-flac",
    # WebM audio
    "audio/webm",
]

PDF_CONTENT_TYPES = [
    "application/pdf",
    "application/x-pdf",
    "application/x-bzpdf",
    "application/x-gzpdf",
]
ARCHIVE_CONTENT_TYPES = [
    "application/zip",
    "application/x-zip-compressed",
    "application/x-zip",
    "application/x-tar",
    "application/x-7z-compressed",
    "application/x-rar-compressed",
]
HTML_CONTENT_TYPE = [
    "text/html",
]
TEXT_CONTENT_TYPES = [
    "text/plain",
    "text/csv",
    "text/xml",
    "text/markdown",
]
VIDEO_CONTENT_TYPES = [
    "video/x-msvideo",  # AVI
    "video/x-flv",  # FLV
    "video/mp4",  # MP4
    "video/mpeg",  # MPEG
    "video/webm",  # WEBM
    "video/ogg",  # OGG
    "video/3gpp",  # 3GP
    "video/3gpp2",  # 3G2
    "video/quicktime",  # MOV
    "video/x-matroska",  # MKV
    "video/x-ms-wmv",  # WMV
    "video/mp2t",  # TS / MPEG-TS
    "video/x-m4v",  # M4V (iTunes)
]

ALL_CONTENT_TYPES = (
    IMAGE_CONTENT_TYPES
    + PDF_CONTENT_TYPES
    + MICROSOFT_WORD_CONTENT_TYPES_DOCX
    + MICROSOFT_WORD_CONTENT_TYPES_DOC
    + LIBRE_OFFICE_CONTENT_TYPES
    + LIBRE_OFFICE_PRESENTATION_TYPES
    + MICROSOFT_SPREADSHEET_CONTENT_TYPES
    + MICROSOFT_PRESENTATION_CONTENT_TYPES
    + AUDIO_CONTENT_TYPES
    + ARCHIVE_CONTENT_TYPES
    + TEXT_CONTENT_TYPES
    + VIDEO_CONTENT_TYPES
)
