from __future__ import annotations

import json

from app.interface.openai_image import _extract_image_url, _extract_from_stream


def _print_result(name: str, message: dict):
    try:
        out = _extract_image_url(message)
        print(name, "->", out)
    except Exception as e:
        print(name, "ERROR", repr(e))


def _stream_resp(lines: list[str]):
    class R:
        def iter_lines(self, decode_unicode: bool = True):
            for l in lines:
                yield l if decode_unicode else l.encode("utf-8")

    return R()


def main():
    msg1 = {"content": [{"type": "image_url", "image_url": {"url": "https://ex.com/a.png"}}]}
    msg2 = {"content": "See https://ex.com/b.png"}
    msg3 = {"content": [{"type": "text", "text": "生成的图像 https://ex.com/c.png "}]}
    msg4 = {"content": {"images": [{"url": "https://ex.com/d.png"}]}}
    msg5 = {"content": []}
    msg6 = {"content": {"image_url": "https://ex.com/e.png"}}

    _print_result("case1_parts_image_url_dict", msg1)
    _print_result("case2_string_http", msg2)
    _print_result("case3_parts_text_http", msg3)
    _print_result("case4_nested_images_url", msg4)
    _print_result("case5_empty_list", msg5)
    _print_result("case6_image_url_string", msg6)

    sse1 = _stream_resp([
        'data: {"choices":[{"delta":{"content":[{"type":"image_url","image_url":{"url":"https://ex.com/s1.png"}}]}}]}',
        'data: [DONE]',
    ])
    sse2 = _stream_resp([
        'data: {"choices":[{"delta":{"content":"https://ex.com/s2.png"}}]}',
        'data: [DONE]',
    ])
    sse3 = _stream_resp([
        'data: https://ex.com/s3.png',
        'data: [DONE]',
    ])
    url1, chunks1 = _extract_from_stream(sse1)
    print("stream_case1", url1 or "", len(chunks1))
    url2, chunks2 = _extract_from_stream(sse2)
    print("stream_case2", url2 or "", len(chunks2))
    url3, chunks3 = _extract_from_stream(sse3)
    print("stream_case3", url3 or "", len(chunks3))


if __name__ == "__main__":
    main()

