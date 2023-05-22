"""Mocking out the Plaxis 3D API behavior for testing of helper scripts."""

from unittest import mock

MOCK_OK = 'OK'


@mock.patch('plxscripting.server.Server')
class ServerMock:
    pass


@mock.patch('plxscripting.plxproxy.PlxProxyGlobalObject')
class PlxProxyGlobalObjectMock:
    def gotostructures(self):
        return MOCK_OK

    def gotomesh(self):
        return MOCK_OK

    def calculate(self):
        return MOCK_OK

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
