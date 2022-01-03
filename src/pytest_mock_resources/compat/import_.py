from types import ModuleType


class ImportAdaptor(ModuleType):
    __wrapped__ = False

    def __init__(self, package, recommended_extra, fail_message=None, **attrs):
        self.package = package
        self.recommended_extra = recommended_extra
        self.fail_message = fail_message

        for key, value in attrs.items():
            setattr(self, key, value)

    def fail(self):
        if self.fail_message:
            fail_message = self.fail_message
        else:
            fail_message = "Cannot use {recommended_extra} fixtures without {package}. pip install pytest-mock-resources[{recommended_extra}]".format(
                package=self.package, recommended_extra=self.recommended_extra
            )

        raise RuntimeError(fail_message)

    def __getattr__(self, attr):
        self.fail()
