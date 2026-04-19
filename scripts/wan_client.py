"""
Wan2.7 API client
支持：文生图（T2I with multi-ref）+ 图生视频（I2V async polling）
纯 stdlib 实现，无外部依赖。
"""
import base64
import json
import os
import time
import urllib.request

T2I_ENDPOINT = "https://dashscope.aliyuncs.com/api/v1/services/aigc/multimodal-generation/generation"
I2V_ENDPOINT = "https://dashscope.aliyuncs.com/api/v1/services/aigc/video-generation/video-synthesis"
TASK_ENDPOINT = "https://dashscope.aliyuncs.com/api/v1/tasks/"

T2I_MODEL = "wan2.7-image-pro"
I2V_MODEL = "wanx2.1-i2v-plus"


class WanClient:
    """Wan2.7 图像生成 + 图生视频客户端"""

    def __init__(self, api_key=None):
        self.api_key = api_key or os.environ.get("DASHSCOPE_API_KEY")
        if not self.api_key:
            raise ValueError(
                "DASHSCOPE_API_KEY 未设置。请设置环境变量或传入 api_key 参数。\n"
                "  Windows CMD:        set DASHSCOPE_API_KEY=sk-xxx\n"
                "  Windows PowerShell: $env:DASHSCOPE_API_KEY='sk-xxx'\n"
                "  Linux/Mac:          export DASHSCOPE_API_KEY=sk-xxx"
            )

    def _headers(self, async_=False):
        h = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        if async_:
            h["X-DashScope-Async"] = "enable"
        return h

    @staticmethod
    def img_to_datauri(path):
        """本地图片文件 → data URI"""
        ext = "jpeg" if path.lower().endswith((".jpg", ".jpeg")) else "png"
        with open(path, "rb") as f:
            return f"data:image/{ext};base64,{base64.b64encode(f.read()).decode()}"

    def t2i(self, prompt, refs=None, size="1024*1024", model=None):
        """
        文生图（支持多图参考 Multi-Ref）。

        Args:
            prompt: 结构化 prompt（含绝对禁项）
            refs: 参考图本地路径列表 或 data URI 列表
            size: 图像尺寸（"1024*1024" / "1920*1080" / "1080*1920"）
            model: 模型名（默认 wan2.7-image-pro）

        Returns:
            生成图片的 URL（需自行下载）
        """
        content = []
        for ref in (refs or []):
            if isinstance(ref, str) and ref.startswith("data:"):
                content.append({"image": ref})
            else:
                content.append({"image": self.img_to_datauri(ref)})
        content.append({"text": prompt})

        payload = {
            "model": model or T2I_MODEL,
            "input": {"messages": [{"role": "user", "content": content}]},
            "parameters": {"size": size, "n": 1},
        }
        req = urllib.request.Request(
            T2I_ENDPOINT,
            data=json.dumps(payload).encode("utf-8"),
            headers=self._headers(),
        )
        with urllib.request.urlopen(req, timeout=300) as r:
            j = json.loads(r.read().decode())
        return j["output"]["choices"][0]["message"]["content"][0]["image"]

    def i2v(self, img_path, prompt, duration=5, resolution="720P", model=None):
        """
        图生视频（异步轮询）。

        Args:
            img_path: 输入图片本地路径 或 data URI
            prompt: 动态描述（咕嘟冒泡 / 热气升腾 / 拉丝动态等）
            duration: 视频时长（秒），一般 5
            resolution: "720P" / "1080P"
            model: 模型名（默认 wanx2.1-i2v-plus）

        Returns:
            生成视频的 URL
        """
        data_uri = (
            img_path
            if isinstance(img_path, str) and img_path.startswith("data:")
            else self.img_to_datauri(img_path)
        )
        payload = {
            "model": model or I2V_MODEL,
            "input": {"prompt": prompt, "img_url": data_uri},
            "parameters": {"duration": duration, "resolution": resolution},
        }
        req = urllib.request.Request(
            I2V_ENDPOINT,
            data=json.dumps(payload).encode("utf-8"),
            headers=self._headers(async_=True),
        )
        with urllib.request.urlopen(req, timeout=60) as r:
            j = json.loads(r.read().decode())
        task_id = j["output"]["task_id"]
        return self._poll(task_id)

    def _poll(self, task_id, timeout=900, interval=15):
        start = time.time()
        while time.time() - start < timeout:
            req = urllib.request.Request(
                TASK_ENDPOINT + task_id, headers=self._headers()
            )
            with urllib.request.urlopen(req, timeout=30) as r:
                j = json.loads(r.read().decode())
            status = j["output"]["task_status"]
            elapsed = int(time.time() - start)
            print(f"  [i2v] task {task_id[:8]} · {status} · {elapsed}s")
            if status == "SUCCEEDED":
                return j["output"].get("video_url")
            if status == "FAILED":
                raise RuntimeError(f"任务失败：{j}")
            time.sleep(interval)
        raise TimeoutError(f"任务 {task_id} 超时（>{timeout}s）")

    @staticmethod
    def download(url, out_path):
        with urllib.request.urlopen(url, timeout=180) as r:
            with open(out_path, "wb") as f:
                f.write(r.read())
        return out_path
