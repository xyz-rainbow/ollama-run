import json
import os
import tempfile

import ollama

import main


def test_list_sessions_corrupt_file():
    with tempfile.TemporaryDirectory() as tmpdir:
        main.SESSIONS_DIR = tmpdir
        with open(os.path.join(tmpdir, "good.json"), "w") as f:
            json.dump({"id": "good", "messages": []}, f)
        with open(os.path.join(tmpdir, "bad.json"), "w") as f:
            f.write("not json")

        sessions = main.list_sessions()
        assert len(sessions) == 1
        assert sessions[0]["id"] == "good"

def test_save_config_no_dir():
    with tempfile.TemporaryDirectory() as tmpdir:
        config_path = os.path.join(tmpdir, "nested", "config.json")
        main.CONFIG_FILE = config_path

        s = main.Session()
        s.model = "test-model"
        s.save_config()

        assert os.path.exists(config_path)
        with open(config_path) as f:
            d = json.load(f)
            assert d["model"] == "test-model"

def test_stream_response_parsing(capsys):
    def gen_dict():
        yield {'message': {'content': 'hello ', 'thinking': 'think1'}}
        yield {'message': {'content': 'world'}}

    main.stream_response(gen_dict())

    out, err = capsys.readouterr()
    assert "think1" in out
    assert "hello " in out
    assert "world" in out

def test_stream_response_object_parsing(capsys):
    def gen_obj():
        yield ollama.ChatResponse(model='test', created_at='test', message=ollama.Message(role='assistant', content='hello ', thinking='think1'), done=False)
        yield ollama.ChatResponse(model='test', created_at='test', message=ollama.Message(role='assistant', content='world'), done=True)

    main.stream_response(gen_obj())

    out, err = capsys.readouterr()
    assert "think1" in out
    assert "hello " in out
    assert "world" in out

def test_serialize_msg():
    m1 = {'role': 'assistant', 'content': 'ok', 'tool_calls': [ollama.Message.ToolCall(function=ollama.Message.ToolCall.Function(name='web_search', arguments={'query': 'hi'}))]}
    s1 = main._serialize_msg(m1)
    assert s1['tool_calls'][0]['function']['name'] == 'web_search'

    m2 = {'role': 'assistant', 'content': 'ok', 'tool_calls': [{'function': {'name': 'web_search', 'arguments': {'query': 'hi'}}}]}
    s2 = main._serialize_msg(m2)
    assert s2['tool_calls'][0]['function']['name'] == 'web_search'

    m3 = {'role': 'assistant', 'content': 'ok', 'tool_calls': [{'name': 'web_search', 'arguments': {'query': 'hi'}}]}
    s3 = main._serialize_msg(m3)
    assert s3['tool_calls'][0]['function']['name'] == 'web_search'
