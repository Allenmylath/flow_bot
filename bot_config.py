#!/usr/bin/env python3

"""
Bot Configuration Module

Handles environment variables, logging setup, and configuration validation.
"""

import os
import sys
from dataclasses import dataclass
from typing import Optional
from dotenv import load_dotenv
from loguru import logger


@dataclass
class BotConfig:
    """Configuration container for the startup interview bot."""
    
    # API Keys
    daily_api_key: str
    cartesia_api_key: str
    openai_api_key: str
    
    # OpenAI Configuration
    openai_model: str = "gpt-4o"
    
    # Cartesia Configuration
    cartesia_voice_id: str = "a0e99841-438c-4a64-b679-ae501e7d6091"
    
    # Bot Configuration
    bot_name: str = "Startup Interview Bot"
    
    # Daily Configuration
    audio_in_enabled: bool = True
    audio_out_enabled: bool = True
    transcription_enabled: bool = True
    vad_enabled: bool = True
    camera_out_enabled: bool = False
    
    # Pipeline Configuration
    enable_metrics: bool = True
    enable_usage_metrics: bool = True
    allow_interruptions: bool = True


def setup_logging(level: str = "DEBUG") -> None:
    """Configure logging for the application."""
    try:
        logger.remove(0)
        logger.add(sys.stderr, level=level)
    except ValueError:
        pass


def load_config() -> BotConfig:
    """Load and validate configuration from environment variables."""
    # Load environment variables
    load_dotenv(override=True)
    
    # Required environment variables
    required_vars = {
        "DAILY_API_KEY": "Daily API key not found in environment variables",
        "CARTESIA_API_KEY": "Cartesia API key not found in environment variables", 
        "OPENAI_API_KEY": "OpenAI API key not found in environment variables"
    }
    
    # Validate required variables
    for var_name, error_msg in required_vars.items():
        if not os.getenv(var_name):
            raise ValueError(error_msg)
    
    return BotConfig(
        daily_api_key=os.getenv("DAILY_API_KEY"),
        cartesia_api_key=os.getenv("CARTESIA_API_KEY"),
        openai_api_key=os.getenv("OPENAI_API_KEY"),
        openai_model=os.getenv("OPENAI_MODEL", "gpt-4o"),
        cartesia_voice_id=os.getenv("CARTESIA_VOICE_ID", "a0e99841-438c-4a64-b679-ae501e7d6091"),
        bot_name=os.getenv("BOT_NAME", "Startup Interview Bot")
    )


def get_config() -> BotConfig:
    """Get validated configuration instance."""
    return load_config()
