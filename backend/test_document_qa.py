#!/usr/bin/env python3
"""
Test script for Document Q&A system
"""

import asyncio
import os
import sys
import tempfile
from pathlib import Path

# Add the backend directory to the Python path
sys.path.insert(0, str(Path(__file__).parent))

from app.services.embedding_service import EmbeddingService
from app.services.vector_store import FAISSVectorStore
from app.services.groq_service import get_groq_service
from app.config.settings import settings

async def test_embedding_service():
    """Test the embedding service"""
    print("🧪 Testing Embedding Service...")
    
    try:
        embedding_service = EmbeddingService()
        
        # Test single embedding
        text = "This is a test document about artificial intelligence and machine learning."
        embedding = await embedding_service.generate_single_embedding(text)
        
        print(f"✅ Single embedding generated: shape={embedding.shape}, type={type(embedding)}")
        
        # Test batch embeddings
        texts = [
            "Machine learning is a subset of artificial intelligence.",
            "Deep learning uses neural networks with multiple layers.",
            "Natural language processing enables computers to understand text."
        ]
        
        embeddings = await embedding_service.generate_embeddings(texts)
        print(f"✅ Batch embeddings generated: shape={embeddings.shape}")
        
        # Test model info
        model_info = await embedding_service.get_model_info()
        print(f"✅ Model info: {model_info}")
        
        return True
        
    except Exception as e:
        print(f"❌ Embedding service test failed: {e}")
        return False

async def test_vector_store():
    """Test the FAISS vector store"""
    print("\n🧪 Testing FAISS Vector Store...")
    
    try:
        embedding_service = EmbeddingService()
        vector_store = FAISSVectorStore(embedding_service)
        
        # Test data
        texts = [
            "Machine learning algorithms learn patterns from data.",
            "Deep learning is inspired by neural networks in the brain.",
            "Natural language processing helps computers understand text.",
            "Computer vision enables machines to interpret images."
        ]
        
        # Generate embeddings
        embeddings = await embedding_service.generate_embeddings(texts)
        
        # Create metadata
        metadata = [
            {
                "chunk_id": f"chunk_{i}",
                "content": text,
                "page_number": 1,
                "chunk_index": i,
                "document_id": "test_doc_123"
            }
            for i, text in enumerate(texts)
        ]
        
        # Create test document ID
        from uuid import uuid4
        doc_id = uuid4()
        
        # Create index
        await vector_store.create_index(doc_id, embeddings, metadata)
        print(f"✅ FAISS index created for document {doc_id}")
        
        # Test search
        query = "What is machine learning?"
        query_embedding = await embedding_service.generate_single_embedding(query)
        
        results = await vector_store.search(doc_id, query_embedding, k=2)
        print(f"✅ Search results: {len(results)} results found")
        
        for i, result in enumerate(results):
            print(f"   Result {i+1}: score={result['relevance_score']:.3f}, content='{result['content'][:50]}...'")
        
        # Test index stats
        stats = await vector_store.get_index_stats(doc_id)
        print(f"✅ Index stats: {stats}")
        
        # Clean up
        await vector_store.delete_index(doc_id)
        print(f"✅ Index deleted")
        
        return True
        
    except Exception as e:
        print(f"❌ Vector store test failed: {e}")
        return False

async def test_groq_service():
    """Test the Groq service"""
    print("\n🧪 Testing Groq Service...")
    
    try:
        groq_service = get_groq_service()
        
        # Test simple completion
        messages = [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "What is machine learning? Please answer in one sentence."}
        ]
        
        response = await groq_service.create_chat_completion(
            messages=messages,
            temperature=0.1,
            max_tokens=100
        )
        
        answer = response['choices'][0]['message']['content']
        print(f"✅ Groq completion successful: '{answer[:100]}...'")
        
        # Test model info
        model_info = groq_service.get_model_info()
        print(f"✅ Model info: {model_info}")
        
        return True
        
    except Exception as e:
        print(f"❌ Groq service test failed: {e}")
        return False

async def test_document_qa_flow():
    """Test the complete document Q&A flow"""
    print("\n🧪 Testing Complete Document Q&A Flow...")
    
    try:
        # Initialize services
        embedding_service = EmbeddingService()
        vector_store = FAISSVectorStore(embedding_service)
        groq_service = get_groq_service()
        
        # Sample document content
        document_content = """
        Machine Learning and Artificial Intelligence
        
        Machine learning is a subset of artificial intelligence (AI) that enables computers to learn and improve from experience without being explicitly programmed. It focuses on developing algorithms that can access data and learn from it automatically.
        
        There are three main types of machine learning:
        1. Supervised Learning: Uses labeled data to train models
        2. Unsupervised Learning: Finds patterns in unlabeled data
        3. Reinforcement Learning: Learns through interaction with environment
        
        Deep learning is a subset of machine learning that uses neural networks with multiple layers to model and understand complex patterns in data. It has been particularly successful in areas like computer vision and natural language processing.
        
        Applications of machine learning include:
        - Image recognition and computer vision
        - Natural language processing and translation
        - Recommendation systems
        - Autonomous vehicles
        - Medical diagnosis
        - Financial trading
        """
        
        # Split into chunks (simple splitting)
        chunk_size = 200
        chunks = []
        words = document_content.split()
        
        for i in range(0, len(words), chunk_size):
            chunk_text = ' '.join(words[i:i + chunk_size])
            chunks.append({
                "content": chunk_text,
                "chunk_index": len(chunks),
                "page_number": 1
            })
        
        print(f"✅ Document split into {len(chunks)} chunks")
        
        # Generate embeddings
        texts = [chunk["content"] for chunk in chunks]
        embeddings = await embedding_service.generate_embeddings(texts)
        
        # Create metadata
        metadata = [
            {
                "chunk_id": f"chunk_{i}",
                "content": chunk["content"],
                "page_number": chunk["page_number"],
                "chunk_index": chunk["chunk_index"],
                "document_id": "test_ml_doc"
            }
            for i, chunk in enumerate(chunks)
        ]
        
        # Create vector index
        from uuid import uuid4
        doc_id = uuid4()
        await vector_store.create_index(doc_id, embeddings, metadata)
        print(f"✅ Vector index created")
        
        # Test Q&A
        questions = [
            "What is machine learning?",
            "What are the three types of machine learning?",
            "What are some applications of machine learning?",
            "What is deep learning?"
        ]
        
        for question in questions:
            print(f"\n❓ Question: {question}")
            
            # Get query embedding
            query_embedding = await embedding_service.generate_single_embedding(question)
            
            # Search for relevant chunks
            search_results = await vector_store.search(doc_id, query_embedding, k=3)
            
            if search_results:
                # Build context
                context_chunks = [result['content'] for result in search_results]
                context_text = "\n\n".join([
                    f"[Context {i+1}]\n{chunk}" 
                    for i, chunk in enumerate(context_chunks)
                ])
                
                # Create prompt
                system_prompt = f"""You are an expert document analyst. Your task is to answer questions based strictly on the provided context.

IMPORTANT GUIDELINES:
1. ONLY use information from the provided context
2. If the context doesn't contain relevant information, say so clearly
3. Be precise and concise in your answers
4. Include specific references when possible (e.g., "According to Context 1...")
5. If you're uncertain, express that uncertainty
6. Do not make up information not found in the context

CONTEXT FROM DOCUMENT:
{context_text}

Please answer the following question based ONLY on the context provided above."""
                
                messages = [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"QUESTION: {question}"}
                ]
                
                # Generate answer
                response = await groq_service.create_chat_completion(
                    messages=messages,
                    temperature=0.1,
                    max_tokens=200
                )
                
                answer = response['choices'][0]['message']['content']
                print(f"✅ Answer: {answer}")
                
                # Show source information
                print(f"📊 Sources: {len(search_results)} chunks used")
                for i, result in enumerate(search_results):
                    print(f"   - Chunk {i+1}: relevance={result['relevance_score']:.3f}")
            else:
                print("❌ No relevant context found")
        
        # Clean up
        await vector_store.delete_index(doc_id)
        print(f"\n✅ Test completed and cleaned up")
        
        return True
        
    except Exception as e:
        print(f"❌ Document Q&A flow test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """Run all tests"""
    print("🚀 Starting Document Q&A System Tests\n")
    
    # Test individual components
    tests = [
        ("Embedding Service", test_embedding_service),
        ("Vector Store", test_vector_store),
        ("Groq Service", test_groq_service),
        ("Complete Q&A Flow", test_document_qa_flow)
    ]
    
    results = {}
    for test_name, test_func in tests:
        try:
            result = await test_func()
            results[test_name] = result
        except Exception as e:
            print(f"❌ {test_name} test crashed: {e}")
            results[test_name] = False
    
    # Summary
    print("\n" + "="*50)
    print("🎯 TEST SUMMARY")
    print("="*50)
    
    total_tests = len(results)
    passed_tests = sum(1 for result in results.values() if result)
    
    for test_name, result in results.items():
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{test_name}: {status}")
    
    print(f"\nTotal: {passed_tests}/{total_tests} tests passed")
    
    if passed_tests == total_tests:
        print("🎉 All tests passed! Document Q&A system is working correctly.")
    else:
        print("⚠️  Some tests failed. Please check the implementation.")
    
    return passed_tests == total_tests

if __name__ == "__main__":
    # Set up environment
    os.environ.setdefault("GROQ_API_KEY", "")  # Will use fallback keys
    
    # Run tests
    success = asyncio.run(main())
    sys.exit(0 if success else 1)