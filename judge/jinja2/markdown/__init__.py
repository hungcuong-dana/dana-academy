from .. import registry
from judge.markdown import markdown as _markdown


@registry.filter
def markdown(value, lazy_load=False, breaks=True):
    return _markdown(value, lazy_load, breaks)
