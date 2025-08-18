#!/usr/bin/env python3

"""
Interview Flow Module with RTVI Support

Defines the startup interview flow, including data collection,
flow states, handlers, and node configurations with RTVI push capability.
"""

import asyncio
from typing import Dict
from loguru import logger
from pipecat.processors.frameworks.rtvi import RTVIServerMessageFrame
from pipecat_flows import FlowArgs, FlowManager, FlowResult, NodeConfig


class InterviewData:
    """Centralized data storage for interview information."""
    
    def __init__(self):
        self.name: str = ""
        self.startup_history: str = ""
    
    def to_dict(self) -> Dict[str, str]:
        """Convert to dictionary for easy access."""
        return {
            "name": self.name,
            "startup_history": self.startup_history
        }
    
    def is_complete(self) -> bool:
        """Check if all required data has been collected."""
        return bool(self.name and self.startup_history)
    
    def print_summary(self) -> None:
        """Print formatted summary of collected data."""
        print("\n" + "=" * 50)
        print("INTERVIEW SUMMARY")
        print("=" * 50)
        print(f"Name: {self.name or 'Not provided'}")
        print(f"Startup History: {self.startup_history or 'Not provided'}")
        print("=" * 50 + "\n")


# Global interview data instance
interview_data = InterviewData()


# RTVI Helper Function
async def push_rtvi_data(flow_manager: FlowManager, function_name: str, result: FlowResult, args: FlowArgs, current_node: str = None):
    """Push collected data via RTVI using task.queue_frame()"""
    try:
        data_payload = {
            "type": "data_collected",
            "function": function_name,
            "node": current_node or flow_manager.current_node,
            "timestamp": asyncio.get_event_loop().time(),
            "data": {
                "result": result,
                "args": args,
                "interview_data": interview_data.to_dict()
            }
        }
        
        # Create and queue the RTVI server message frame
        rtvi_frame = RTVIServerMessageFrame(data=data_payload)
        await flow_manager.task.queue_frame(rtvi_frame)
        
        logger.info(f"✅ Pushed RTVI data for '{function_name}'")
        
    except Exception as e:
        logger.error(f"❌ Failed to push RTVI data: {str(e)}")


# Flow Result Classes
class NameCollectionResult(FlowResult):
    name: str


class StartupHistoryResult(FlowResult):
    startup_history: str


class EndCallResult(FlowResult):
    status: str


# Function Handlers (Updated with flow_manager parameter and RTVI push)
async def collect_name(args: FlowArgs, flow_manager: FlowManager) -> NameCollectionResult:
    """Process name collection and push data via RTVI."""
    name = args["name"]
    logger.debug(f"collect_name handler executing with name: {name}")
    interview_data.name = name
    
    result = NameCollectionResult(name=name)
    
    # Push data via RTVI before returning
    await push_rtvi_data(
        flow_manager=flow_manager,
        function_name="collect_name",
        result=result,
        args=args,
        current_node="initial"
    )
    
    return result


async def collect_startup_history(args: FlowArgs, flow_manager: FlowManager) -> StartupHistoryResult:
    """Process startup history collection and push data via RTVI."""
    history = args["startup_history"]
    logger.debug(f"collect_startup_history handler executing with history: {history}")
    interview_data.startup_history = history
    
    result = StartupHistoryResult(startup_history=history)
    
    # Push data via RTVI before returning
    await push_rtvi_data(
        flow_manager=flow_manager,
        function_name="collect_startup_history",
        result=result,
        args=args,
        current_node="startup_history"
    )
    
    return result


async def end_call(args: FlowArgs, flow_manager: FlowManager) -> EndCallResult:
    """Handle call completion, push final data via RTVI, and print collected data."""
    logger.info("=== CALL ENDING - COLLECTED DATA ===")
    data = interview_data.to_dict()
    logger.info(f"Name: {data['name'] or 'Not provided'}")
    logger.info(f"Startup History: {data['startup_history'] or 'Not provided'}")
    logger.info("=====================================")

    # Print to console for visibility
    interview_data.print_summary()
    
    result = EndCallResult(status="completed")
    
    # Push final data via RTVI
    await push_rtvi_data(
        flow_manager=flow_manager,
        function_name="end_call",
        result=result,
        args=args,
        current_node="summary"
    )
    
    return result


# Transition Callbacks
async def handle_name_collection(
    args: Dict, result: NameCollectionResult, flow_manager: FlowManager
):
    """Handle transition after name collection."""
    flow_manager.state["name"] = result["name"]
    await flow_manager.set_node("startup_history", create_startup_history_node())


async def handle_startup_history_collection(
    args: Dict, result: StartupHistoryResult, flow_manager: FlowManager
):
    """Handle transition after startup history collection."""
    flow_manager.state["startup_history"] = result["startup_history"]
    await flow_manager.set_node("summary", create_summary_node())


async def handle_end_call(args: Dict, result: EndCallResult, flow_manager: FlowManager):
    """Handle final transition."""
    await flow_manager.set_node("end", create_end_node())


# Node Configuration Functions (Updated handlers to use new signature)
def create_initial_node() -> NodeConfig:
    """Create the initial node asking for user's name."""
    return {
        "role_messages": [
            {
                "role": "system",
                "content": (
                    "You are a friendly interviewer collecting information about entrepreneurs "
                    "and their startup experiences. Your responses will be converted to audio, "
                    "so keep them conversational and avoid special characters. Always use the "
                    "available functions to progress the conversation."
                ),
            }
        ],
        "task_messages": [
            {
                "role": "system",
                "content": (
                    "Greet the user warmly and ask for their name. Explain that you're "
                    "conducting a brief interview about their startup experience."
                ),
            }
        ],
        "functions": [
            {
                "type": "function",
                "function": {
                    "name": "collect_name",
                    "handler": collect_name,  # Now uses modern signature with flow_manager
                    "description": "Record the user's name",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "name": {
                                "type": "string",
                                "description": "The user's full name",
                            }
                        },
                        "required": ["name"],
                    },
                    "transition_callback": handle_name_collection,
                },
            }
        ],
    }


def create_startup_history_node() -> NodeConfig:
    """Create node for collecting startup history."""
    return {
        "task_messages": [
            {
                "role": "system",
                "content": (
                    "Now ask about their startup history. Be encouraging and ask them to share "
                    "details about any startups they've founded, worked at, or been involved with. "
                    "Ask about their roles, what the companies did, outcomes, and key learnings."
                ),
            }
        ],
        "functions": [
            {
                "type": "function",
                "function": {
                    "name": "collect_startup_history",
                    "handler": collect_startup_history,  # Now uses modern signature
                    "description": "Record the user's startup history and experiences",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "startup_history": {
                                "type": "string",
                                "description": "Detailed description of the user's startup experience, companies, roles, and outcomes",
                            }
                        },
                        "required": ["startup_history"],
                    },
                    "transition_callback": handle_startup_history_collection,
                },
            }
        ],
    }


def create_summary_node() -> NodeConfig:
    """Create node for summarizing and ending the call."""
    return {
        "task_messages": [
            {
                "role": "system",
                "content": (
                    "Thank the user for sharing their information. Provide a brief, encouraging "
                    "summary of what they shared. Then ask if there's anything else they'd like "
                    "to add before ending the call."
                ),
            }
        ],
        "functions": [
            {
                "type": "function",
                "function": {
                    "name": "end_call",
                    "handler": end_call,  # Now uses modern signature
                    "description": "Complete the interview and end the call",
                    "parameters": {
                        "type": "object",
                        "properties": {},
                    },
                    "transition_callback": handle_end_call,
                },
            }
        ],
    }


def create_end_node() -> NodeConfig:
    """Create the final node."""
    return {
        "task_messages": [
            {
                "role": "system",
                "content": (
                    "Give a final thank you and mention that their information has been recorded. "
                    "End the conversation warmly."
                ),
            }
        ],
        "functions": [],
        "post_actions": [{"type": "end_conversation"}],
    }


def get_interview_data() -> InterviewData:
    """Get the current interview data instance."""
    return interview_data


def reset_interview_data() -> None:
    """Reset interview data for a new session."""
    global interview_data
    interview_data = InterviewData()
