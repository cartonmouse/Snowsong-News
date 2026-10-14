from app.agent.provider import parse_openai_response


def test_parse_openai_tool_call_response() -> None:
    response = parse_openai_response(
        {
            "choices": [
                {
                    "finish_reason": "tool_calls",
                    "message": {
                        "role": "assistant",
                        "content": None,
                        "tool_calls": [
                            {
                                "id": "call-1",
                                "type": "function",
                                "function": {
                                    "name": "read_file",
                                    "arguments": '{"path":"brief.txt"}',
                                },
                            }
                        ],
                    },
                }
            ]
        }
    )

    assert response.content is None
    assert response.tool_calls[0].name == "read_file"
    assert response.tool_calls[0].arguments == {"path": "brief.txt"}


def test_parse_openai_final_response() -> None:
    response = parse_openai_response(
        {
            "choices": [
                {
                    "finish_reason": "stop",
                    "message": {
                        "role": "assistant",
                        "content": "done",
                    },
                }
            ]
        }
    )

    assert response.content == "done"
    assert response.tool_calls == ()

