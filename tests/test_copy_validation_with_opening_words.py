# -*- coding: utf-8 -*-
"""
Test Suite: Copy Validation with Opening Words

Verifica que ClipCopy valida correctamente los nuevos campos:
- opening_words: palabras exactas del speaker
- opening_words_used: boolean flag
- speaker_hashtags_provided: lista de hashtags del speaker
"""

import pytest
from pydantic import ValidationError
from src.models.copy_schemas import ClipCopy, CopyMetadata


class TestOpeningWordsValidation:
    """Tests para validación de opening_words en ClipCopy"""

    @pytest.fixture
    def valid_metadata(self):
        """Metadata válida para todos los tests"""
        return CopyMetadata(
            sentiment="viral",
            sentiment_score=0.8,
            engagement_score=8.5,
            suggested_thumbnail_timestamp=5.0,
            primary_topics=["AI", "Tech", "Innovation"],
            hook_strength="high",
            viral_potential=8.0
        )

    def test_copy_with_opening_words_valid(self, valid_metadata):
        """Test: Copy que incluye opening_words es válido"""
        clip = ClipCopy(
            clip_id=1,
            copy="La IA es revolucionaria. 3 formas en que cambió mi negocio 🚀 #AICDMX",
            opening_words="La IA es revolucionaria",
            opening_words_used=True,
            speaker_hashtags_provided=["#AICDMX"],
            metadata=valid_metadata
        )

        assert clip.clip_id == 1
        assert clip.opening_words == "La IA es revolucionaria"
        assert clip.opening_words_used is True
        assert "#AICDMX" in clip.copy

    def test_copy_without_opening_words_specified_valid(self, valid_metadata):
        """Test: Copy sin opening_words especificado es válido (backward compatible)"""
        clip = ClipCopy(
            clip_id=2,
            copy="Amazing content que no comienza con speaker words #AICDMX",
            metadata=valid_metadata
        )

        assert clip.opening_words == ""
        assert clip.opening_words_used is False
        assert clip.speaker_hashtags_provided == []

    def test_copy_missing_opening_words_fails(self, valid_metadata):
        """Test: Copy que NO contiene opening_words cuando se especifica → FAIL"""
        with pytest.raises(ValidationError):
            ClipCopy(
                clip_id=3,
                copy="Este copy NO contiene las palabras del speaker 🎯 #AICDMX",
                opening_words="La IA es revolucionaria",  # Especificado
                opening_words_used=True,
                metadata=valid_metadata
            )

    def test_copy_opening_words_case_insensitive(self, valid_metadata):
        """Test: Validación case-insensitive para opening_words"""
        clip = ClipCopy(
            clip_id=4,
            copy="la ia es revolucionaria. Mira esto 🚀 #AICDMX",
            opening_words="La IA es revolucionaria",  # Diferentes mayúsculas
            opening_words_used=True,
            metadata=valid_metadata
        )

        # Debe pasar porque la validación es case-insensitive
        assert clip.opening_words == "La IA es revolucionaria"

    def test_copy_opening_words_partial_match_fails(self, valid_metadata):
        """Test: Si opening_words NO está completamente, debe fallar"""
        with pytest.raises(ValidationError):
            ClipCopy(
                clip_id=5,
                copy="Something else entirely 🎯 #AICDMX",
                opening_words="La IA es revolucionaria",
                opening_words_used=True,
                metadata=valid_metadata
            )

    def test_copy_opening_words_at_beginning(self, valid_metadata):
        """Test: opening_words idealmente al inicio (ideal case)"""
        clip = ClipCopy(
            clip_id=6,
            copy="La IA es revolucionaria y esto es importante 🚀 #AICDMX",
            opening_words="La IA es revolucionaria",
            opening_words_used=True,
            metadata=valid_metadata
        )

        assert clip.copy.startswith("La IA es revolucionaria")

    def test_copy_opening_words_in_middle_still_valid(self, valid_metadata):
        """Test: opening_words en el medio del copy (aceptable)"""
        clip = ClipCopy(
            clip_id=7,
            copy="Importante: La IA es revolucionaria en 2024 🚀 #AICDMX",
            opening_words="La IA es revolucionaria",
            opening_words_used=True,
            metadata=valid_metadata
        )

        # Debe pasar porque contains check, no needs to be at start
        assert "La IA es revolucionaria" in clip.copy

    def test_copy_with_opening_words_short_text(self, valid_metadata):
        """Test: Copy corto que contenga opening_words"""
        clip = ClipCopy(
            clip_id=8,
            copy="La IA es revolucionaria 🚀 #AICDMX",
            opening_words="La IA es revolucionaria",
            opening_words_used=True,
            metadata=valid_metadata
        )

        # Debe contener opening_words
        assert "La IA es revolucionaria" in clip.copy
        assert len(clip.copy) <= 150

    def test_empty_opening_words_with_empty_string(self, valid_metadata):
        """Test: opening_words vacío es válido"""
        clip = ClipCopy(
            clip_id=9,
            copy="Random copy without any specific opening #AICDMX",
            opening_words="",  # Empty
            opening_words_used=False,
            metadata=valid_metadata
        )

        assert clip.opening_words == ""
        assert clip.opening_words_used is False


class TestSpeakerHashtagsValidation:
    """Tests para validación de speaker_hashtags_provided"""

    @pytest.fixture
    def valid_metadata(self):
        return CopyMetadata(
            sentiment="viral",
            sentiment_score=0.8,
            engagement_score=8.5,
            suggested_thumbnail_timestamp=5.0,
            primary_topics=["AI", "Tech", "Innovation"],
            hook_strength="high",
            viral_potential=8.0
        )

    def test_speaker_hashtags_list(self, valid_metadata):
        """Test: speaker_hashtags_provided como lista"""
        clip = ClipCopy(
            clip_id=10,
            copy="La IA es revolucionaria #AICDMX #Future",
            speaker_hashtags_provided=["#AICDMX", "#Future"],
            metadata=valid_metadata
        )

        assert len(clip.speaker_hashtags_provided) == 2
        assert "#AICDMX" in clip.speaker_hashtags_provided

    def test_speaker_hashtags_empty_list(self, valid_metadata):
        """Test: speaker_hashtags vacío"""
        clip = ClipCopy(
            clip_id=11,
            copy="Copy sin hashtags #AICDMX",
            speaker_hashtags_provided=[],
            metadata=valid_metadata
        )

        assert clip.speaker_hashtags_provided == []

    def test_speaker_hashtags_default_empty(self, valid_metadata):
        """Test: speaker_hashtags default es lista vacía"""
        clip = ClipCopy(
            clip_id=12,
            copy="Amazing content #AICDMX",
            opening_words="Amazing content",
            metadata=valid_metadata
        )

        assert clip.speaker_hashtags_provided == []
        assert isinstance(clip.speaker_hashtags_provided, list)


class TestCompleteOpeningWordsFlow:
    """Tests de integración: opening_words + metadata + truncation"""

    @pytest.fixture
    def valid_metadata(self):
        return CopyMetadata(
            sentiment="storytelling",
            sentiment_score=0.85,
            engagement_score=8.8,
            suggested_thumbnail_timestamp=12.5,
            primary_topics=["DevJourney", "Learning", "Experience"],
            hook_strength="very_high",
            viral_potential=8.5
        )

    def test_complete_spanish_clip_with_opening_words(self, valid_metadata):
        """Test: Clip completo español con opening_words"""
        clip = ClipCopy(
            clip_id=1,
            copy="Hace 2 años no sabía programar. Hoy trabajo en Google 🚀 #DevJourney #AICDMX",
            opening_words="Hace 2 años no sabía programar",
            opening_words_used=True,
            speaker_hashtags_provided=["#DevJourney", "#AICDMX"],
            metadata=valid_metadata
        )

        assert clip.opening_words == "Hace 2 años no sabía programar"
        assert "Hace 2 años no sabía programar" in clip.copy
        assert len(clip.speaker_hashtags_provided) == 2

    def test_complete_english_clip_with_opening_words(self, valid_metadata):
        """Test: Clip completo inglés con opening_words"""
        clip = ClipCopy(
            clip_id=2,
            copy="2 years ago I couldn't code. Now I work at Google 🚀 #DevJourney #AICDMX",
            opening_words="2 years ago I couldn't code",
            opening_words_used=True,
            speaker_hashtags_provided=["#DevJourney", "#AICDMX"],
            metadata=valid_metadata
        )

        assert clip.opening_words == "2 years ago I couldn't code"
        assert "2 years ago I couldn't code" in clip.copy

    def test_validation_error_message_clarity(self, valid_metadata):
        """Test: Error message es claro cuando falla opening_words"""
        try:
            clip = ClipCopy(
                clip_id=3,
                copy="Wrong content #AICDMX",
                opening_words="Expected opening words",
                opening_words_used=True,
                metadata=valid_metadata
            )
            # Si llegamos aquí sin excepción, el test debería fallar
            assert False, "Should have raised ValidationError"
        except ValidationError as e:
            error = e.errors()[0]
            # El mensaje de error debe mencionar opening_words o algo similar
            assert "opening" in str(error).lower() or "speaker" in str(error).lower() or "must contain" in str(error).lower()

    def test_backwards_compatibility_no_opening_words(self, valid_metadata):
        """Test: Clips viejos sin opening_words aún funcionan"""
        # Simular un clip antiguo que no tiene estos campos
        clip = ClipCopy(
            clip_id=4,
            copy="Antiguo copy sin opening words especificado #AICDMX",
            # No especificar opening_words, opening_words_used, speaker_hashtags_provided
            metadata=valid_metadata
        )

        assert clip.opening_words == ""
        assert clip.opening_words_used is False
        assert clip.speaker_hashtags_provided == []
