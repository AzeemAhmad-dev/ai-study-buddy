"""Route modules."""

from app.routes.ai import router as ai_router
from app.routes.text_processing import router as text_processing_router
from app.routes.media import router as media_router
from app.routes.solver import router as solver_router
from app.routes.socratic import router as socratic_router

__all__ = ["ai_router", "text_processing_router", "media_router", "solver_router", "socratic_router"]
