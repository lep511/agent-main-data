import datetime
from zoneinfo import ZoneInfo
from google.adk.agents import LoopAgent, LlmAgent, BaseAgent
from social.instavibe import get_person_posts,get_person_friends,get_person_id_by_name,get_person_attended_events
from google.adk.agents.invocation_context import InvocationContext
from google.adk.events import Event, EventActions
from typing import AsyncGenerator
import logging

from google.genai import types # For types.Content
from google.adk.agents.callback_context import CallbackContext
from typing import Optional

# Get a logger instance
log = logging.getLogger(__name__)

#REPLACE FOR CheckCondition

#REPLACE FOR profile_agent

#REPLACE FOR summary_agent

#REPLACE FOR check_agent

#REPLACE FOR modify_output_after_agent

#REPLACE FOR root_agent
