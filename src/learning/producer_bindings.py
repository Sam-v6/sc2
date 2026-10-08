"""Persistent source-to-native identities for fixed human-plan execution."""


class ProducerBindings:
    def __init__(self):
        self.tags = {}

    def bind(self, source_tag, native_tag):
        if source_tag in self.tags:
            if self.tags[source_tag] != native_tag:
                raise ValueError('A bound source actor cannot change native identity')
        elif native_tag in self.tags.values():
            raise ValueError('Two source actors cannot share a native identity')
        self.tags[source_tag] = native_tag

    def resolve(self, source_tag, state):
        tag = self.tags.get(source_tag)
        return next((unit for unit in state['units']
                     if unit['tag'] == tag and unit['alliance'] == 1), None)
