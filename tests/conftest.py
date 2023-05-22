import pytest
import plaxismock as pm


@pytest.fixture
def g_i():
    return pm.PlxProxyGlobalObjectMock()


@pytest.fixture
def s_i():
    return pm.ServerMock()


@pytest.fixture
def patch_plxscripting_new_server(g_i, s_i, mocker):
    mocker.patch('plxscripting.easy.new_server', autospec=True)
    from plxscripting.easy import new_server
    new_server.return_value = (s_i, g_i)


@pytest.fixture
def plaxis_helper_connected(patch_plxscripting_new_server, s_i, g_i):
    import plxhelper.plaxis_helper as plaxis_helper
    plaxis_helper.connect_server()


@pytest.fixture
def plaxis_helper(plaxis_helper_connected):
    import plxhelper.plaxis_helper as plaxis_helper
    return plaxis_helper
