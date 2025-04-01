


You can also test out the API server!
```
> uv run test_server.py

=== Testing Create Thread ===
Status Code: 200
Response: {'threadId': '8468fb51-7d77-47f6-82d8-0b9f66e11d51'}

=== Testing Get Thread ===
Status Code: 200
Response: {'id': '8468fb51-7d77-47f6-82d8-0b9f66e11d51', 'messages': []}

=== Testing Add Message: Hello! How are you today? ===
Status Code: 200
Response: {'id': '8468fb51-7d77-47f6-82d8-0b9f66e11d51', 'messages': [{'role': 'user', 'content': 'Hello! How are you today?'}, {'role': 'assistant', 'content': "As an artificial intelligence, I
don't have feelings, but I'm here and ready to assist you. How can I help you today?"}]}

=== Testing Add Message: What's your favorite programming language? ===
Status Code: 200
Response: {'id': '8468fb51-7d77-47f6-82d8-0b9f66e11d51', 'messages': [{'role': 'user', 'content': 'Hello! How are you today?'}, {'role': 'assistant', 'content': "As an artificial intelligence, I
don't have feelings, but I'm here and ready to assist you. How can I help you today?"}, {'role': 'user', 'content': "What's your favorite programming language?"}, {'role': 'assistant', 
'content': "As an artificial intelligence, I don't have personal preferences. But I was built and programmed using a variety of languages including Python, a highly versatile language that's 
often used for machine learning tasks."}]}

=== Testing Get Thread ===
Status Code: 200
Response: {'id': '8468fb51-7d77-47f6-82d8-0b9f66e11d51', 'messages': [{'role': 'user', 'content': 'Hello! How are you today?'}, {'role': 'assistant', 'content': "As an artificial intelligence, I
don't have feelings, but I'm here and ready to assist you. How can I help you today?"}, {'role': 'user', 'content': "What's your favorite programming language?"}, {'role': 'assistant', 
'content': "As an artificial intelligence, I don't have personal preferences. But I was built and programmed using a variety of languages including Python, a highly versatile language that's 
often used for machine learning tasks."}]}
```