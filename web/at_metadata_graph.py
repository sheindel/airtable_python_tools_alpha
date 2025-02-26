from at_types import AirTableFieldMetadata

class Node:
    def __init__(self, field_metadata: AirTableFieldMetadata):
        self.field_metadata: AirTableFieldMetadata = field_metadata
        self.children: set[Node] = []
        self.parents: set[Node] = []

    def get_parents(self):
        return self.parents

    def get_children(self):
        return self.children
    
    def add_parent(self, parent):
        self.parents.add(parent)
        parent.children.add(self)

    def __repr__(self):
        return self.name
    