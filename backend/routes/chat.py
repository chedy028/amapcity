"""
Chat API Endpoint

Handles LLM-powered chat for cable design assistance.
Uses OpenRouter for model flexibility.
"""

import json
import os
from typing import Literal, Optional, List, Dict, Any

import httpx
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
from agent import TOOLS, execute_tool, SYSTEM_PROMPT

router = APIRouter()

# OpenRouter API configuration
OPENROUTER_API_URL = "https://openrouter.ai/api/v1/chat/completions"


class Message(BaseModel):
    role: Literal["user", "assistant", "system", "tool"]
    content: str
    tool_call_id: Optional[str] = None
    tool_calls: Optional[List[Any]] = None


class ChatRequest(BaseModel):
    messages: list[Message]
    model: str = Field(
        default="anthropic/claude-3.5-sonnet",
        description="OpenRouter model ID"
    )
    api_key: str = Field(..., description="OpenRouter API key")
    stream: bool = Field(default=False, description="Enable streaming response")
    design_context: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Current design parameters from the wizard form"
    )


class ChatResponse(BaseModel):
    message: Message
    tool_results: Optional[List[Dict[str, Any]]] = None
    usage: Optional[Dict[str, Any]] = None


class ModelsResponse(BaseModel):
    models: List[Dict[str, Any]]


# Available models for cable design (models good at function calling)
RECOMMENDED_MODELS = [
    {
        "id": "anthropic/claude-3.5-sonnet",
        "name": "Claude 3.5 Sonnet",
        "description": "Best for complex engineering analysis",
        "recommended": True,
    },
    {
        "id": "anthropic/claude-3-haiku",
        "name": "Claude 3 Haiku",
        "description": "Fast responses, good for quick questions",
        "recommended": False,
    },
    {
        "id": "openai/gpt-4-turbo",
        "name": "GPT-4 Turbo",
        "description": "Strong reasoning and calculation abilities",
        "recommended": False,
    },
    {
        "id": "openai/gpt-4o",
        "name": "GPT-4o",
        "description": "Latest OpenAI model, fast and capable",
        "recommended": False,
    },
    {
        "id": "google/gemini-pro-1.5",
        "name": "Gemini Pro 1.5",
        "description": "Google's advanced model",
        "recommended": False,
    },
    {
        "id": "meta-llama/llama-3.1-70b-instruct",
        "name": "Llama 3.1 70B",
        "description": "Open source, good performance",
        "recommended": False,
    },
]


@router.get("/models", response_model=ModelsResponse)
async def get_models():
    """Get list of recommended models for cable design."""
    return ModelsResponse(models=RECOMMENDED_MODELS)


@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Chat with the cable design assistant.

    Sends messages to OpenRouter, handles tool calls, and returns responses.
    """
    # Build messages with system prompt
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]

    # Add design context if provided
    if request.design_context:
        context_msg = f"\n\nCurrent design parameters from the wizard:\n```json\n{json.dumps(request.design_context, indent=2)}\n```"
        messages[0]["content"] += context_msg

    # Add conversation history
    for msg in request.messages:
        msg_dict = {"role": msg.role, "content": msg.content}
        if msg.tool_call_id:
            msg_dict["tool_call_id"] = msg.tool_call_id
        if msg.tool_calls:
            msg_dict["tool_calls"] = msg.tool_calls
        messages.append(msg_dict)

    # Call OpenRouter API
    headers = {
        "Authorization": f"Bearer {request.api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": "http://localhost:3000",
        "X-Title": "Cable Ampacity Design Assistant",
    }

    payload = {
        "model": request.model,
        "messages": messages,
        "tools": TOOLS,
        "tool_choice": "auto",
    }

    tool_results = []

    async with httpx.AsyncClient(timeout=60.0) as client:
        # Initial API call
        response = await client.post(
            OPENROUTER_API_URL,
            headers=headers,
            json=payload,
        )

        if response.status_code != 200:
            error_detail = response.text
            raise HTTPException(
                status_code=response.status_code,
                detail=f"OpenRouter API error: {error_detail}"
            )

        result = response.json()
        assistant_message = result["choices"][0]["message"]

        # Handle tool calls
        while assistant_message.get("tool_calls"):
            tool_calls = assistant_message["tool_calls"]

            # Execute each tool call
            tool_messages = []
            for tool_call in tool_calls:
                function_name = tool_call["function"]["name"]
                function_args = json.loads(tool_call["function"]["arguments"])

                # Execute the tool
                tool_result = execute_tool(function_name, function_args)
                tool_results.append({
                    "tool": function_name,
                    "arguments": function_args,
                    "result": tool_result,
                })

                tool_messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call["id"],
                    "content": json.dumps(tool_result),
                })

            # Add assistant message with tool calls and tool results
            messages.append({
                "role": "assistant",
                "content": assistant_message.get("content") or "",
                "tool_calls": tool_calls,
            })
            messages.extend(tool_messages)

            # Make another API call with tool results
            payload["messages"] = messages
            response = await client.post(
                OPENROUTER_API_URL,
                headers=headers,
                json=payload,
            )

            if response.status_code != 200:
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"OpenRouter API error: {response.text}"
                )

            result = response.json()
            assistant_message = result["choices"][0]["message"]

    return ChatResponse(
        message=Message(
            role="assistant",
            content=assistant_message.get("content") or "",
        ),
        tool_results=tool_results if tool_results else None,
        usage=result.get("usage"),
    )


@router.post("/chat/stream")
async def chat_stream(request: ChatRequest):
    """
    Stream chat response from the cable design assistant.

    Returns Server-Sent Events for real-time streaming.
    """
    # Build messages with system prompt
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]

    if request.design_context:
        context_msg = f"\n\nCurrent design parameters:\n```json\n{json.dumps(request.design_context, indent=2)}\n```"
        messages[0]["content"] += context_msg

    for msg in request.messages:
        messages.append({"role": msg.role, "content": msg.content})

    headers = {
        "Authorization": f"Bearer {request.api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": "http://localhost:3000",
        "X-Title": "Cable Ampacity Design Assistant",
    }

    payload = {
        "model": request.model,
        "messages": messages,
        "tools": TOOLS,
        "tool_choice": "auto",
        "stream": True,
    }

    async def event_generator():
        async with httpx.AsyncClient(timeout=60.0) as client:
            async with client.stream(
                "POST",
                OPENROUTER_API_URL,
                headers=headers,
                json=payload,
            ) as response:
                async for line in response.aiter_lines():
                    if line.startswith("data: "):
                        data = line[6:]
                        if data == "[DONE]":
                            yield f"data: {json.dumps({'done': True})}\n\n"
                        else:
                            try:
                                chunk = json.loads(data)
                                delta = chunk["choices"][0].get("delta", {})
                                if delta.get("content"):
                                    yield f"data: {json.dumps({'content': delta['content']})}\n\n"
                                if delta.get("tool_calls"):
                                    # Handle tool calls in streaming
                                    yield f"data: {json.dumps({'tool_calls': delta['tool_calls']})}\n\n"
                            except json.JSONDecodeError:
                                continue

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
    )
