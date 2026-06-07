from .processes.tci_by_mo import TciByMo
from .processes.tci_graph import TciGraph

processes = [
    TciByMo(),
    TciGraph()
]