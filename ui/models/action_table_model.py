"""Virtualized Action Table Model for high-performance rendering of macro action buffers."""

from PyQt6.QtCore import QAbstractTableModel, QModelIndex, Qt
from PyQt6.QtGui import QColor


class ActionTableModel(QAbstractTableModel):
    """High-performance virtualized table model capable of rendering 100k+ actions with O(1) memory overhead."""

    COLUMNS = ["#", "Timestamp", "Action Type", "Event Payload"]

    def __init__(self, parent=None):
        super().__init__(parent)
        self._actions: list[dict] = []

    def set_actions(self, actions: list[dict]) -> None:
        self.beginResetModel()
        self._actions = actions
        self.endResetModel()

    def clear(self) -> None:
        self.beginResetModel()
        self._actions = []
        self.endResetModel()

    def rowCount(self, parent=QModelIndex()) -> int:
        return len(self._actions)

    def columnCount(self, parent=QModelIndex()) -> int:
        return len(self.COLUMNS)

    def headerData(self, section: int, orientation: Qt.Orientation, role: int = Qt.ItemDataRole.DisplayRole):
        if orientation == Qt.Orientation.Horizontal and role == Qt.ItemDataRole.DisplayRole:
            if 0 <= section < len(self.COLUMNS):
                return self.COLUMNS[section]
        return None

    def data(self, index: QModelIndex, role: int = Qt.ItemDataRole.DisplayRole):
        if not index.isValid() or not (0 <= index.row() < len(self._actions)):
            return None

        row = index.row()
        col = index.column()
        action = self._actions[row]

        if role == Qt.ItemDataRole.DisplayRole:
            if col == 0:
                return str(row + 1)
            elif col == 1:
                return f"+{action.get('time', 0.0):.3f}s"
            elif col == 2:
                return str(action.get("type", "unknown"))
            elif col == 3:
                return self._describe_payload(action)

        elif role == Qt.ItemDataRole.TextAlignmentRole:
            if col in (0, 1):
                return Qt.AlignmentFlag.AlignCenter
            return Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft

        elif role == Qt.ItemDataRole.ForegroundRole:
            kind = action.get("type", "")
            if col == 2:
                if kind.startswith("key_"):
                    return QColor("#38bdf8")  # Sky blue for keys
                elif kind in ("mouse_down", "mouse_up"):
                    return QColor("#f472b6")  # Pink for clicks
                elif kind == "mouse_move":
                    return QColor("#94a3b8")  # Slate for moves
                elif kind == "mouse_scroll":
                    return QColor("#fbbf24")  # Amber for scroll
            elif col == 0:
                return QColor("#64748b")

        return None

    @staticmethod
    def _describe_payload(action: dict) -> str:
        kind = action.get("type", "")
        if kind == "mouse_move":
            return f"Position: ({action.get('x', 0)}, {action.get('y', 0)})"
        elif kind in ("mouse_down", "mouse_up"):
            btn = action.get("button", "left")
            return f"Position: ({action.get('x', 0)}, {action.get('y', 0)}) | Button: [{btn}]"
        elif kind == "mouse_scroll":
            return f"Position: ({action.get('x', 0)}, {action.get('y', 0)}) | Scroll: dx={action.get('dx', 0)}, dy={action.get('dy', 0)}"
        elif kind in ("key_down", "key_up"):
            key_data = action.get("key", {})
            if isinstance(key_data, dict):
                return f"Key: {key_data.get('value', '')} ({key_data.get('kind', 'char')})"
            return f"Key: {key_data}"
        return str(action)
