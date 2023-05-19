from unittest import mock


@mock.patch('plxscripting.server.Server')
class ServerMock:
    pass


@mock.patch('plxscripting.plxproxy.PlxProxyGlobalObject')
class PlxProxyGlobalObjectMock:
    def soilmat(self, *args, **kwargs):
        return object()

    def platemat(self, *args, **kwargs):
        return object()

    def polycurve(self, *args, **kwargs):
        return PolycurveMock()


class SetPropertiesMock:
    def setproperties(self, *args):
        ...


class SegmentMock():
    def __init__(self):
        self.ArcProperties = SetPropertiesMock()
        self.LineProperties = SetPropertiesMock()


class PolycurveMock:
    def add(self):
        return SegmentMock()

    def extendtosymmetryaxis(self):
        ...

    def symmetricclose(self):
        ...
