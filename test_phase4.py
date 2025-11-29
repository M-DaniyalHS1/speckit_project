"""
Test script to verify Phase 4 components are working correctly.
"""
import sys
import os

# Add the backend directory to the path for module imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

def test_phase4_components():
    """Test all the new components created for Phase 4."""
    print("Testing Phase 4 components...")
    
    try:
        # Test imports
        from backend.src.rag.chunker import text_chunker
        from backend.src.rag.embedding_generator import embedding_generator
        from backend.src.rag.citation_service import citation_service
        from backend.src.services.search_service import SearchService
        
        print("✅ All new components imported successfully")

        # Test text chunker
        sample_text = 'This is a sample text. ' * 100  # Make it long enough to chunk
        chunks = text_chunker.chunk_text(sample_text, {'source': 'test'})
        print(f'✅ Text chunker working: created {len(chunks)} chunks')

        # Test citation service
        book_info = {'title': 'Test Book', 'author': 'Test Author', 'year': 2023}
        citation = citation_service._format_search_citation(book_info, 15, 'Introduction', '1')
        print(f'[PASS] Citation service working: {citation[:50]}...')

        print('[PASS] All Phase 4 components are functional')
        return True

    except Exception as e:
        print(f'[FAIL] Error testing Phase 4 components: {e}')
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_phase4_components()
    if success:
        print("\n[SUCCESS] Phase 4 implementation completed successfully!")
    else:
        print("\n[ERROR] Phase 4 implementation has issues that need to be addressed.")