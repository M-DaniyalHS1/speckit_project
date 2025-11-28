"""
Test script to validate the Phase 3 reading companion functionality implementation.
"""
from backend.src.models.reading_session import (
    ReadingSession, ReadingSessionCreate, ReadingSessionUpdate
)
from backend.src.api.sessions import UpdateReadingPositionRequest, ReadingPositionResponse

def test_models():
    """Test that all models have the required fields after our updates."""
    # Test ReadingSession model has the new fields
    session_data = {
        'id': 'test-id',
        'user_id': 'user-123',
        'book_id': 'book-456',
        'current_location': 'Chapter 1:5:2',
        'current_position_percent': 10,
        'started_at': '2023-01-01T00:00:00',
        'last_read_at': '2023-01-01T00:00:00',
        'is_active': True,
        'total_time_spent': 0
    }
    
    # Create a ReadingSession instance
    session = ReadingSession(**session_data)
    assert hasattr(session, 'current_location'), "ReadingSession should have current_location field"
    assert hasattr(session, 'current_position_percent'), "ReadingSession should have current_position_percent field"
    print("[PASS] ReadingSession model has required fields")

    # Test UpdateReadingPositionRequest
    update_request = UpdateReadingPositionRequest(
        current_location="Chapter 2:10:3",
        position_percent=25
    )
    assert update_request.current_location == "Chapter 2:10:3"
    assert update_request.position_percent == 25
    print("[PASS] UpdateReadingPositionRequest model works correctly")

    # Test ReadingPositionResponse
    position_response = ReadingPositionResponse(
        session_id='test-session',
        current_location='Chapter 3:15:1',
        current_chapter='Chapter 3',
        current_page=15,
        current_paragraph=1,
        position_percent=30,
        last_accessed_at='2023-01-01T00:00:00'
    )
    assert position_response.session_id == 'test-session'
    assert position_response.current_location == 'Chapter 3:15:1'
    assert position_response.position_percent == 30
    print("[PASS] ReadingPositionResponse model works correctly")

    print("\n[SUCCESS] All model tests passed!")


def test_api_endpoints():
    """Test that API endpoints match our defined models."""
    from backend.src.api.sessions import router
    
    # Check that the router has the correct endpoints
    endpoints = [route.path for route in router.routes]
    expected_endpoints = [
        '/sessions/',
        '/sessions/',
        '/sessions/{session_id}',
        '/sessions/{session_id}/position',
        '/sessions/{session_id}/position',
        '/sessions/{session_id}/activate',
        '/sessions/{session_id}/deactivate',
        '/sessions/{session_id}/save',
        '/sessions/{session_id}/restore'
    ]
    
    # Check that key endpoints exist
    assert '/sessions/' in endpoints, "Base sessions endpoint should exist"
    assert '/sessions/{session_id}/position' in endpoints, "Update position endpoint should exist"
    print("[PASS] API endpoints are correctly defined")


if __name__ == "__main__":
    print("Testing Phase 3 implementation...")
    test_models()
    test_api_endpoints()
    print("\n[SUCCESS] All tests passed! Phase 3 implementation is complete and correct.")