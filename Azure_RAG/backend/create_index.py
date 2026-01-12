"""
Create Azure AI Search index for RAG application.
"""
import os
from azure.search.documents.indexes import SearchIndexClient
from azure.search.documents.indexes.models import (
    SearchIndex,
    SearchField,
    SearchFieldDataType,
    SimpleField,
    SearchableField,
    VectorSearch,
    HnswAlgorithmConfiguration,
    VectorSearchProfile,
    SemanticConfiguration,
    SemanticField,
    SemanticPrioritizedFields,
    SemanticSearch
)
from azure.core.credentials import AzureKeyCredential

# Configuration from environment
AZURE_SEARCH_ENDPOINT = os.getenv("AZURE_SEARCH_ENDPOINT", "https://srch-rag-app-20250112.search.windows.net")
AZURE_SEARCH_API_KEY = os.getenv("AZURE_SEARCH_API_KEY")
AZURE_SEARCH_INDEX_NAME = os.getenv("AZURE_SEARCH_INDEX_NAME", "rag-index")

def create_index():
    """Create the RAG search index."""

    # Create index client
    index_client = SearchIndexClient(
        endpoint=AZURE_SEARCH_ENDPOINT,
        credential=AzureKeyCredential(AZURE_SEARCH_API_KEY)
    )

    # Define fields
    fields = [
        SimpleField(name="chunk_id", type=SearchFieldDataType.String, key=True),
        SearchableField(name="content", type=SearchFieldDataType.String, analyzer_name="standard.lucene"),
        SearchField(
            name="content_vector",
            type=SearchFieldDataType.Collection(SearchFieldDataType.Single),
            searchable=True,
            vector_search_dimensions=1536,
            vector_search_profile_name="default-vector-profile"
        ),
        SimpleField(name="document_id", type=SearchFieldDataType.String, filterable=True, facetable=True),
        SearchableField(name="filename", type=SearchFieldDataType.String),
        SimpleField(name="chunk_index", type=SearchFieldDataType.Int32, filterable=True, sortable=True),
        SimpleField(name="total_chunks", type=SearchFieldDataType.Int32),
        SearchField(
            name="page_numbers",
            type=SearchFieldDataType.Collection(SearchFieldDataType.Int32),
            filterable=True,
            sortable=False
        ),

        # Entity fields - all filterable and facetable
        SearchField(
            name="entities_people",
            type=SearchFieldDataType.Collection(SearchFieldDataType.String),
            filterable=True,
            facetable=True
        ),
        SearchField(
            name="entities_organizations",
            type=SearchFieldDataType.Collection(SearchFieldDataType.String),
            filterable=True,
            facetable=True
        ),
        SearchField(
            name="entities_locations",
            type=SearchFieldDataType.Collection(SearchFieldDataType.String),
            filterable=True,
            facetable=True
        ),
        SearchField(
            name="entities_topics",
            type=SearchFieldDataType.Collection(SearchFieldDataType.String),
            filterable=True,
            facetable=True
        ),
        SearchField(
            name="entities_technical_terms",
            type=SearchFieldDataType.Collection(SearchFieldDataType.String),
            filterable=True,
            facetable=True
        ),
        SearchableField(name="entity_summary", type=SearchFieldDataType.String),
    ]

    # Configure vector search
    vector_search = VectorSearch(
        algorithms=[
            HnswAlgorithmConfiguration(name="default-hnsw")
        ],
        profiles=[
            VectorSearchProfile(
                name="default-vector-profile",
                algorithm_configuration_name="default-hnsw"
            )
        ]
    )

    # Configure semantic search
    semantic_config = SemanticConfiguration(
        name="default",
        prioritized_fields=SemanticPrioritizedFields(
            title_field=SemanticField(field_name="filename"),
            content_fields=[
                SemanticField(field_name="content"),
                SemanticField(field_name="entity_summary")
            ]
        )
    )

    semantic_search = SemanticSearch(configurations=[semantic_config])

    # Create index
    index = SearchIndex(
        name=AZURE_SEARCH_INDEX_NAME,
        fields=fields,
        vector_search=vector_search,
        semantic_search=semantic_search
    )

    # Create or update the index
    result = index_client.create_or_update_index(index)
    print(f"Index '{result.name}' created successfully!")
    print(f"Fields: {len(result.fields)}")

    return result

if __name__ == "__main__":
    import sys

    if not AZURE_SEARCH_API_KEY:
        print("Error: AZURE_SEARCH_API_KEY environment variable not set")
        sys.exit(1)

    print(f"Creating index '{AZURE_SEARCH_INDEX_NAME}' at {AZURE_SEARCH_ENDPOINT}")
    create_index()
    print("Done!")
