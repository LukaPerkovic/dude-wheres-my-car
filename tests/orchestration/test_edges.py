import pytest

@pytest.mark.parametrize("intent", ["info", "reservation"])
def test_route_intent(intent):
    from src.graph.edges import route_intent
    assert route_intent({"intent": intent}) == intent


@pytest.mark.parametrize("status", ["collecting", "pending_approval"])
def test_check_reservation_complete(status):
    from src.graph.edges import check_reservation_complete
    assert check_reservation_complete({"reservation_status": status}) == status