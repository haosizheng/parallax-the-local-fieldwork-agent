#!/bin/bash

# 测试 Parallax Chat API

echo "🧪 测试 Parallax API..."
echo ""

curl --location 'http://localhost:3001/v1/chat/completions' \
  --header 'Content-Type: application/json' \
  --data '{
    "max_tokens": 200,
    "messages": [
      {
        "role": "user",
        "content": "你好！请用一句话介绍你自己，然后告诉我今天是星期几。"
      }
    ],
    "stream": false
  }' | python3 -m json.tool

echo ""
echo "✅ 测试完成"
