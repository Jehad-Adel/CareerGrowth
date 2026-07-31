from unittest.mock import patch
from app.services import hybrid_rag


def test_cached_embed_query_lru_caching():
    hybrid_rag.cached_embed_query.cache_clear()
    with patch("app.ai.embeddings.embed_query") as mock_embed:
        mock_embed.return_value = [0.1, 0.2, 0.3]
        query = "Python developer job description"

        # First call should invoke embed_query
        res1 = hybrid_rag.cached_embed_query(query)
        assert res1 == [0.1, 0.2, 0.3]
        mock_embed.assert_called_once_with(query)

        # Second call should use cache
        res2 = hybrid_rag.cached_embed_query(query)
        assert res2 == [0.1, 0.2, 0.3]
        mock_embed.assert_called_once_with(query)

        # Different query should invoke embed_query again
        query2 = "Java developer job description"
        res3 = hybrid_rag.cached_embed_query(query2)
        assert res3 == [0.1, 0.2, 0.3]
        assert mock_embed.call_count == 2
