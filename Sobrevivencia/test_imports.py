import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from Sobrevivencia.core.managers.buff_applicator import ensure_item_bonus_fields, recalc_item_buffs
from Sobrevivencia.main import SobrevivenciaGame

print("Imports bem sucedidos!")
