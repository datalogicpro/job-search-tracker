from .hackernews import HackerNewsSource
from .himalayas import HimalayasSource
from .jobicy import JobicySource
from .jsearch import JSearchSource
from .remoteok import RemoteOKSource
from .theirstack import TheirStackSource
from .themuse import TheMuseSource
from .weworkremotely import WeWorkRemotelySource

SOURCES = [
    HimalayasSource,
    RemoteOKSource,
    WeWorkRemotelySource,
    JobicySource,
    TheMuseSource,
    HackerNewsSource,
    JSearchSource,
    TheirStackSource,
]
