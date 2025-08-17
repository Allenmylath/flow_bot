#!/usr/bin/env python3

"""
Daily Transport Setup Module

Handles Daily room creation, token generation, and transport configuration.
"""

import aiohttp
from loguru import logger
from typing import Tuple

from pipecat.audio.vad.silero import SileroVADAnalyzer
from pipecat.transports.services.daily import DailyParams, DailyTransport
from pipecat.transports.services.helpers.daily_rest import (
    DailyRESTHelper,
    DailyRoomParams,
)

from bot_config import BotConfig


async def create_new_room_and_token(
    session: aiohttp.ClientSession, 
    config: BotConfig
) -> Tuple[str, str]:
    """
    Create a new Daily room and bot token for it.
    
    Args:
        session: aiohttp session for making requests
        config: Bot configuration containing API keys
        
    Returns:
        Tuple of (room_url, bot_token)
    """
    daily_helper = DailyRESTHelper(
        daily_api_key=config.daily_api_key, 
        aiohttp_session=session
    )

    # Create a new room
    room = await daily_helper.create_room(DailyRoomParams())
    if not room.url:
        raise ValueError("Failed to create Daily room")

    room_url = room.url

    # Generate bot token for the new room
    token = await daily_helper.get_token(room_url)
    if not token:
        raise ValueError(f"Failed to get token for room: {room_url}")

    logger.info(f"Created new room: {room_url}")
    _print_room_info(room_url)

    return room_url, token


def _print_room_info(room_url: str) -> None:
    """Print formatted room information to console."""
    print("\n" + "=" * 60)
    print("🎤 NEW STARTUP INTERVIEW ROOM CREATED")
    print("=" * 60)
    print(f"Room URL: {room_url}")
    print("📋 Share this link with users to join the interview!")
    print("=" * 60 + "\n")


def create_daily_transport(
    room_url: str, 
    token: str, 
    config: BotConfig
) -> DailyTransport:
    """
    Create and configure Daily transport.
    
    Args:
        room_url: URL of the Daily room
        token: Bot token for the room
        config: Bot configuration
        
    Returns:
        Configured DailyTransport instance
    """
    return DailyTransport(
        room_url,
        token,
        config.bot_name,
        DailyParams(
            audio_in_enabled=config.audio_in_enabled,
            audio_out_enabled=config.audio_out_enabled,
            transcription_enabled=config.transcription_enabled,
            vad_enabled=config.vad_enabled,
            vad_analyzer=SileroVADAnalyzer(),
            camera_out_enabled=config.camera_out_enabled,
        ),
    )
