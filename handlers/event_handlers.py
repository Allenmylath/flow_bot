#!/usr/bin/env python3

"""
Event Handlers Module

Handles Daily transport events like participant joining/leaving and errors.
"""

from loguru import logger
from pipecat.pipeline.task import PipelineTask
from pipecat_flows import FlowManager

from flows.interview_flow import create_initial_node, get_interview_data


class EventHandlers:
    """Container for Daily transport event handlers."""
    
    def __init__(self, task: PipelineTask, flow_manager: FlowManager):
        self.task = task
        self.flow_manager = flow_manager
    
    async def on_first_participant_joined(self, transport, participant):
        """Handle when the first user joins the room."""
        logger.info(f"Participant joined: {participant}")
        await transport.capture_participant_transcription(participant["id"])

        # Initialize the flow
        logger.debug("Initializing flow")
        await self.flow_manager.initialize()
        logger.debug("Setting initial node")
        await self.flow_manager.set_node("initial", create_initial_node())

    async def on_participant_left(self, transport, participant, reason):
        """Handle when a participant leaves the room."""
        logger.info(f"Participant left: {participant}, reason: {reason}")

        # Print final data when participant leaves
        logger.info("=== PARTICIPANT LEFT - FINAL DATA ===")
        interview_data = get_interview_data()
        data = interview_data.to_dict()
        logger.info(f"Name: {data['name'] or 'Not provided'}")
        logger.info(f"Startup History: {data['startup_history'] or 'Not provided'}")
        logger.info("=====================================")

        # Print formatted summary
        print("\n" + "=" * 50)
        print("PARTICIPANT LEFT - FINAL SUMMARY")
        print("=" * 50)
        print(f"Name: {data['name'] or 'Not provided'}")
        print(f"Startup History: {data['startup_history'] or 'Not provided'}")
        print("=" * 50 + "\n")

        await self.task.cancel()

    async def on_error(self, transport, error):
        """Handle transport errors."""
        logger.error(f"Transport error: {error}")
        if "AlreadyInCall" in str(error):
            logger.warning("Room already has a connection.")
        await self.task.cancel()


def setup_event_handlers(transport, task: PipelineTask, flow_manager: FlowManager) -> None:
    """
    Set up all event handlers for the Daily transport.
    
    Args:
        transport: Daily transport instance
        task: Pipeline task
        flow_manager: Flow manager instance
    """
    handlers = EventHandlers(task, flow_manager)
    
    transport.event_handler("on_first_participant_joined")(
        handlers.on_first_participant_joined
    )
    transport.event_handler("on_participant_left")(
        handlers.on_participant_left
    )
    transport.event_handler("on_error")(
        handlers.on_error
    )
