from .enemy_renderer import EnemyRendererMixin
from .feedback_renderer import FeedbackRendererMixin
from .minimap_renderer import MinimapRendererMixin
from .pickup_renderer import PickupRendererMixin
from .player_renderer import PlayerRendererMixin
from .projectile_renderer import ProjectileRendererMixin


class EntityRendererMixin(
    PickupRendererMixin,
    ProjectileRendererMixin,
    EnemyRendererMixin,
    PlayerRendererMixin,
    FeedbackRendererMixin,
    MinimapRendererMixin,
):
    pass