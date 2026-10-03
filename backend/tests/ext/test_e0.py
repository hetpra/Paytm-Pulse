from app.ext import hooks


def test_hooks_are_ordered_and_isolated():
    hooks.clear()
    hooks.register_filter("value", lambda value, **_: value + "b", priority=60)
    hooks.register_filter("value", lambda value, **_: value + "a", priority=10)
    hooks.register_filter("value", lambda value, **_: 1 / 0, priority=20)
    assert hooks.apply("value", "") == "ab"
    hooks.clear()
