# 生图 / 改图 路由说明

本文档说明了 text_to_image 作业如何在 OpenAI、sora-image 等兼容 v1/chat/completions 的通道之间选择“生图”或“改图”。

![流程示意](./image-routing.svg)

## 关键判定逻辑
1. **Provider 能力**：`capabilities` 中：
   - `image` 控制基础生图；`image-edit` 或 `edit_image` 控制改图。
   - `chat-completions` 与 `images-generations` 用于区分走 `v1/chat/completions` 还是 `v1/images/generations` 协议（不配置时默认 chat-completions 兼容）。
2. **是否携带源图**：`job.params.extras.source_image_url` 或 `source_image_urls` 存在时，认为是改图/参考图请求。
3. **适配器选择**：
   - `openai`、`sora-image`、`nano-banana-2` 等支持 chat-completions 图生图/改图的渠道走 `OpenAIImageAdapter`。
   - Qwen 等专用通道走对应适配器。
4. **模型选择与具体动作**：
   - 有源图且 provider 具备 `image-edit` -> 调用 `adapter.edit_image`（OpenAI 与 sora-image 格式一致），并优先选择名称包含
     `edit` 的模型（如 `gpt-image-1-edit`）。
   - 有源图但不支持改图 -> 作为参考图调用 `adapter.generate_image`（传 `image_url`）。
   - 无源图 -> 直接调用 `adapter.generate_image`，并优先选择非 `edit` 的模型（如 `gpt-image-1`）。

## OpenAI 与 sora-image 区别/相同点
- **相同点**：都使用 `v1/chat/completions`，消息中包含 `type: image_url`，请求/响应结构一致，可流式返回图片 URL。
- **区别**：在 provider 名称和默认模型上有所不同，但路由逻辑和能力判定一致，只要 `capabilities` 包含 `image`/`image-edit` 就会走同一套处理。

## 请求示例（OpenAI/Sora 格式）
- **改图/参考图**：包含 `image_url`，流式返回图片地址。

  ```json
  {
    "model": "gemini-2.5-flash-image",
    "temperature": 1,
    "top_p": 1,
    "messages": [
      {
        "role": "user",
        "content": [
          {"type": "text", "text": "改成猪猪"},
          {"type": "image_url", "image_url": {"url": "data:image/png;base64,iVBOxxxx"}}
        ]
      }
    ],
    "stream": true,
    "stream_options": {"include_usage": true}
  }
  ```

- **文生图**：只包含文本内容，不带 `image_url`。

  ```json
  {
    "model": "gemini-2.5-flash-image",
    "temperature": 1,
    "top_p": 1,
    "messages": [
      {
        "role": "user",
        "content": [{"type": "text", "text": "一只可爱的太空小熊"}]
      }
    ],
    "stream": false
  }
  ```
