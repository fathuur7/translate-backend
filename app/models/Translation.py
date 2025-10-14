from pydantic import BaseModel
from typing import Optional

class TranslationResponse(BaseModel):
    """
    Model respons untuk endpoint /translate-video/.
    Ini mendefinisikan struktur JSON yang akan dikembalikan.
    """
    filename: str
    target_language: str
    original_transcript: str
    original_srt: str
    translated_srt: Optional[str] = None
