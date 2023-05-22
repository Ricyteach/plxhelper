import pytest
from plxhelper.task_chain import TaskChain

TRUTHY_VALUE = 'OK'


@pytest.fixture
def task_chain():
    return TaskChain()


@pytest.fixture
def task_chain_start(task_chain):
    @task_chain.link
    def start():
        return TRUTHY_VALUE
    assert start() == TRUTHY_VALUE
    return start


@pytest.fixture
def task_chain_step_1(task_chain, task_chain_start):
    @task_chain.link
    def step_1():
        return TRUTHY_VALUE
    assert step_1() == TRUTHY_VALUE
    return step_1


def test_task_chain(task_chain):
    assert tuple(task_chain()) == ()
    assert not task_chain


def test_task_chain_start(task_chain_start, task_chain):
    assert tuple(task_chain()) == (task_chain_start(),)
    assert task_chain
    assert task_chain_start.__name__ == 'start'


def test_task_chain_step_1(task_chain_start, task_chain_step_1, task_chain):
    assert tuple(task_chain()) == (task_chain_start(), task_chain_step_1())
    assert len(task_chain) == 2
    assert task_chain_step_1.__name__ == 'step_1'


def test_task_chain_start_by_idx(task_chain_start, task_chain):
    assert task_chain[-1] is task_chain_start
    assert task_chain[-1]() == task_chain_start()
    assert len(task_chain) == 1


def test_task_chain_step_1_by_idx(task_chain_step_1, task_chain):
    assert task_chain[-1] is task_chain_step_1
    assert task_chain[-1]() == task_chain_step_1()
    assert len(task_chain) == 2


def test_task_chain_start_by_slice(task_chain_start, task_chain):
    assert tuple((task_chain_slice:= task_chain[0:])()) == (task_chain_start(),)
    assert len(task_chain_slice) == 1
    assert task_chain_slice._seq == [task_chain_start]


def test_task_chain_step_1_by_slice(task_chain_step_1, task_chain):
    assert tuple((task_chain_slice:= task_chain[1:])()) == (task_chain_step_1(),)
    assert len(task_chain_slice) == 1
    assert task_chain_slice._seq == [task_chain_step_1]


def test_task_chain_start_by_name(task_chain_start, task_chain):
    assert tuple((task_chain_getattr:=task_chain.start)()) == (task_chain_start(),)
    assert len(task_chain_getattr) == 1
    assert task_chain_getattr._seq == [task_chain_start]


def test_task_chain_step_1_by_name(task_chain_start, task_chain_step_1, task_chain):
    assert tuple((task_chain_getattr := task_chain.step_1)()) == (task_chain_start(),
                                                                          task_chain_step_1(),)
    assert len(task_chain_getattr) == 2
    assert task_chain_getattr._seq == [task_chain_start, task_chain_step_1]


@pytest.fixture
def mixed_chain(task_chain, task_chain_step_1):
    task_chain[1:1] = task_chain
    return task_chain


def test_mixed_chain(mixed_chain, task_chain_start, task_chain_step_1):
    assert len(mixed_chain) == 4
    assert all(mixed_chain())
    assert tuple(mixed_chain()) == (task_chain_start(), task_chain_start(), task_chain_step_1(), task_chain_step_1())
