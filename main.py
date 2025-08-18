#!/usr/bin/env python3

"""
Startup History Collection Bot with RTVI Support - Main Entry Point

A clean, modular chatbot that collects user name and startup history
using Daily, Cartesia TTS, and OpenAI with flow management and RTVI push capability.
"""

import asyncio
import aiohttp
from loguru import logger

from pipecat.pipeline.pipeline import Pipeline
from pipecat.pipeline.runner import PipelineRunner
from pipecat.pipeline.task import PipelineParams, PipelineTask
from pipecat.processors.aggregators.openai_llm_context import OpenAILLMContext
from pipecat.processors.frameworks.rtvi import RTVIProcessor, RTVIObserver
from pipecat.services.cartesia.tts import CartesiaTTSService
from pipecat.services.openai.llm import OpenAILLMService
from pipecat_flows import FlowManager

# Local imports
from bot_config import get_config, setup_logging
from daily_setup import create_new_room_and_token, create_daily_transport
from handlers.event_handlers import setup_event_handlers
from flows.interview_flow import reset_interview_data


async def create_services(config):
    """Create and configure all required services."""
    # Set up Cartesia TTS
    tts = CartesiaTTSService(
        api_key=config.cartesia_api_key,
        voice_id=config.cartesia_voice_id,
    )

    # Set up OpenAI LLM
    llm = OpenAILLMService(
        api_key=config.openai_api_key, 
        model=config.openai_model
    )

    # Set up conversation context
    context = OpenAILLMContext()
    context_aggregator = llm.create_context_aggregator(context)

    return tts, llm, context_aggregator


def create_pipeline_with_rtvi(transport, context_aggregator, llm, tts):
    """Create the processing pipeline with RTVI support."""
    # Initialize RTVI processor
    rtvi_processor = RTVIProcessor(transport=transport)
    rtvi_observer = RTVIObserver(rtvi_processor)

    # Create pipeline with RTVI integration
    pipeline = Pipeline([
        transport.input(),
        context_aggregator.user(),
        llm,
        tts,
        transport.output(),
        context_aggregator.assistant(),
        rtvi_processor,  # Add RTVI processor to pipeline
    ])

    # Add RTVI observer
    pipeline.add_observer(rtvi_observer)

    return pipeline, rtvi_processor


def setup_rtvi_handlers(rtvi_processor):
    """Set up RTVI-specific event handlers."""
    @rtvi_processor.event_handler("on_client_message")
    async def on_client_message(processor, message):
        logger.info(f"📨 Received RTVI client message: {message.type}")
        # Handle specific RTVI client messages if needed
        if hasattr(message, 'data'):
            logger.debug(f"RTVI message data: {message.data}")


async def main():
    """Main function that orchestrates the entire bot with RTVI support."""
    # Setup
    setup_logging()
    config = get_config()
    reset_interview_data()  # Start with clean data
    
    async with aiohttp.ClientSession() as session:
        try:
            # Create Daily room and transport
            room_url, token = await create_new_room_and_token(session, config)
            transport = create_daily_transport(room_url, token, config)

            # Create services
            tts, llm, context_aggregator = await create_services(config)

            # Create pipeline with RTVI support
            pipeline, rtvi_processor = create_pipeline_with_rtvi(transport, context_aggregator, llm, tts)

            # Setup RTVI handlers
            setup_rtvi_handlers(rtvi_processor)

            # Create pipeline task
            task = PipelineTask(
                pipeline,
                params=PipelineParams(
                    enable_metrics=config.enable_metrics,
                    enable_usage_metrics=config.enable_usage_metrics,
                    allow_interruptions=config.allow_interruptions,
                ),
            )

            # Initialize flow manager
            flow_manager = FlowManager(
                task=task, 
                llm=llm, 
                context_aggregator=context_aggregator, 
                tts=tts
            )

            # Setup event handlers
            setup_event_handlers(transport, task, flow_manager)

            # Run the bot
            runner = PipelineRunner()
            logger.info("Starting Startup Interview Bot with RTVI support...")
            await runner.run(task)

        except Exception as e:
            logger.error(f"Bot failed to start: {e}")
            raise


if __name__ == "__main__":
    asyncio.run(main())
