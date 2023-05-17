import pytest


@pytest.fixture(scope="module")
def g_i():
    return type("GI", (), {})()


@pytest.fixture
def s_i():
    return type("SI", (), {})()


@pytest.fixture
def patch_plxscripting_new_server(g_i, s_i, monkeypatch):
    import plxscripting.easy
    monkeypatch.setattr(plxscripting.easy, "new_server", new_server := (lambda *args, **kwargs: (s_i, g_i)))
    assert new_server is plxscripting.easy.new_server


@pytest.fixture
def plaxis_helper_connected(patch_plxscripting_new_server, s_i, g_i):
    import plxhelper.plaxis_helper as plaxis_helper
    plaxis_helper.connect_server()


@pytest.fixture
def plaxis_helper(plaxis_helper_connected):
    import plxhelper.plaxis_helper as plaxis_helper
    return plaxis_helper
