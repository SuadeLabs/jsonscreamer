from .compile import compile_


class SchemaChecker(object):
    def __init__(self, defn, format_checkers=None):
        self.defn = defn
        self.validator = compile_(defn, format_checkers)

    def check(self, instance):
        return self.validator(instance)
