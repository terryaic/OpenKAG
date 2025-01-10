MODEL = "Mistral-Large-Instruct-2407-FP8"
RAG_MODEL = "Mistral-Large-Instruct-2407-FP8-RAG"
GRAPHRAG_MODEL = "Mistral-Large-Instruct-2407-FP8-GRAPHRAG"
models = {
        "object": "list",
        "data": [
            {
                "id": RAG_MODEL,
                "object": "model",
                "created": 1722215785,
                "owned_by": "vllm",
                "root": RAG_MODEL,
                "parent": None,
                "max_model_len": 131072,
                "permission": [
                    {
                        "id": "modelperm-afdb18aacf4247c7b6b0229c5d9e32b6",
                        "object": "model_permission",
                        "created": 1722215785,
                        "allow_create_engine": False,
                        "allow_sampling": True,
                        "allow_logprobs": True,
                        "allow_search_indices": False,
                        "allow_view": True,
                        "allow_fine_tuning": False,
                        "organization": "*",
                        "group": None,
                        "is_blocking": False
                    }
                ]
            }
        ]
    }
graphrag_models = {
        "object": "list",
        "data": [
            {
                "id": GRAPHRAG_MODEL,
                "object": "model",
                "created": 1722215785,
                "owned_by": "vllm",
                "root": GRAPHRAG_MODEL,
                "parent": None,
                "max_model_len": 131072,
                "permission": [
                    {
                        "id": "modelperm-afdb18aacf4247c7b6b0229c5d9e32b6",
                        "object": "model_permission",
                        "created": 1722215785,
                        "allow_create_engine": False,
                        "allow_sampling": True,
                        "allow_logprobs": True,
                        "allow_search_indices": False,
                        "allow_view": True,
                        "allow_fine_tuning": False,
                        "organization": "*",
                        "group": None,
                        "is_blocking": False
                    }
                ]
            }
        ]
    }

chat_completion = {
    "id": "chat-e8ce5ad9ecf84e4c9643006e632b39e0",
    "object": "chat.completion",
    "created": 1722492449,
    "model": "Mistral-Large-Instruct-2407-FP8",
    "choices": [
        {
            "index": 0,
            "message": {
                "role": "assistant",
                "content": " Hello! How can I assist you today? Let's have a friendly chat. 😊 How are you doing?",
                "tool_calls": []
            },
            "logprobs": None,
            "finish_reason": "stop",
            "stop_reason": None
        }
    ]
}
