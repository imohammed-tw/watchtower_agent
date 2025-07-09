"""
Base agent class for all agents
"""

from abc import ABC, abstractmethod
from typing import Any
import logging
from datetime import datetime

from models import WorkflowState


class BaseAgent(ABC):
    """Abstract base class for all agents"""

    def __init__(self, name: str):
        self.name = name
        self.logger = logging.getLogger(f"Agent.{name}")
        self.status = "inactive"
        self.last_execution = None

    async def initialize(self):
        """Initialize the agent"""
        self.logger.info(f"Initializing {self.name} agent")
        self.status = "active"

    @abstractmethod
    async def execute(self, input_data: Any, workflow_state: WorkflowState) -> Any:
        """Execute the agent's main functionality"""
        pass

    def get_status(self) -> dict:
        """Get agent status"""
        return {
            "name": self.name,
            "status": self.status,
            "last_execution": (
                self.last_execution.isoformat() if self.last_execution else None
            ),
        }
