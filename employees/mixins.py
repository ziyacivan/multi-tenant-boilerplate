class MultiSerializerViewSetMixin:
    def get_serializer_class(self):
        try:
            return self.serializer_action_classes[self.action]
        except (KeyError, AttributeError):
            return super(self).get_serializer_class()
