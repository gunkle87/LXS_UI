from PySide6.QtWidgets import QComboBox
from PySide6.QtCore import Qt

class PrimitiveDropdown(QComboBox):
    def __init__(self, registry, parent=None):
        super().__init__(parent)
        self.registry = registry
        self._populate()
        
    def _populate(self):
        self.addItem("-- Select Primitive --", userData=None)
        categories = self.registry.get_categories()
        for cat in categories:
            primitives = self.registry.get_primitives_in_category(cat)
            if primitives:
                self.addItem(f"--- {cat} ---", userData=None)
                index = self.count() - 1
                self.setItemData(index, "header", Qt.UserRole)
                
                for p in primitives:
                    self.addItem(f"  {p.display_name}", userData=p.type_id)
        
        model = self.model()
        for i in range(self.count()):
            if self.itemData(i, Qt.UserRole) == "header":
                item = model.item(i)
                if item:
                    item.setFlags(item.flags() & ~Qt.ItemIsSelectable & ~Qt.ItemIsEnabled)
