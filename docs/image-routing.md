# 生图 / 改图 路由说明

本文档说明了 text_to_image 作业如何在 OpenAI、sora-image 等兼容 v1/chat/completions 的通道之间选择“生图”或“改图”。

![流程示意](./image-routing.svg)

## 关键判定逻辑
1. **Provider 能力**：`capabilities` 包含 `image` 才能生图，包含 `image-edit` 才能改图。
2. **是否携带源图**：`job.params.extras.source_image_url` 或 `source_image_urls` 存在时，认为是改图/参考图请求。
3. **适配器选择**：
   - `openai`、`sora-image`、`nano-banana-2` 等支持 chat-completions 图生图/改图的渠道走 `OpenAIImageAdapter`。
   - Qwen 等专用通道走对应适配器。
4. **具体动作**：
   - 有源图且 provider 具备 `image-edit` -> 调用 `adapter.edit_image`（OpenAI 与 sora-image 格式一致）。
   - 有源图但不支持改图 -> 作为参考图调用 `adapter.generate_image`（传 `image_url`）。
   - 无源图 -> 直接调用 `adapter.generate_image`。

## OpenAI 与 sora-image 区别/相同点
- **相同点**：都使用 `v1/chat/completions`，消息中包含 `type: image_url`，请求/响应结构一致，可流式返回图片 URL。
- **区别**：在 provider 名称和默认模型上有所不同，但路由逻辑和能力判定一致，只要 `capabilities` 包含 `image`/`image-edit` 就会走同一套处理。
