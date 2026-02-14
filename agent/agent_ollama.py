import asyncio
import json
import logging
import os
import uuid
import aiohttp
import platform

# Configuration
SERVER_URL = os.environ.get("SERVER_URL", "ws://localhost:8000/ws/computing/")
OLLAMA_URL = os.environ.get("OLLAMA_URL", "http://localhost:11434")
NODE_ID = os.environ.get("NODE_ID", f"node-{uuid.uuid4().hex[:8]}")
AUTH_TOKEN = os.environ.get("AUTH_TOKEN", "dummy-token")

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("GPU-Agent")


async def check_ollama_status():
    """Checks if local Ollama is running and lists models."""
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{OLLAMA_URL}/api/tags") as response:
                if response.status == 200:
                    data = await response.json()
                    models = [m['name'] for m in data.get('models', [])]
                    logger.info(f"Ollama connected. Available models: {models}")
                    return models
                else:
                    logger.error(f"Ollama returned status {response.status}")
                    return []
    except Exception as e:
        logger.error(f"Could not connect to Ollama at {OLLAMA_URL}: {e}")
        return []


async def execute_task(task_data):
    """Executes a task on local Ollama. Fully async — does not block the event loop."""
    task_id = task_data.get('task_id')
    model = task_data.get('model')
    prompt = task_data.get('prompt')

    logger.info(f"Executing Task {task_id}: model={model} prompt='{prompt[:50]}...'")

    try:
        async with aiohttp.ClientSession() as session:
            payload = {
                "model": model,
                "prompt": prompt,
                "stream": False
            }
            async with session.post(
                f"{OLLAMA_URL}/api/generate",
                json=payload,
                timeout=aiohttp.ClientTimeout(total=600)
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    output_text = result.get("response", "")
                    logger.info(f"Task {task_id} Completed. ({len(output_text)} chars)")
                    return {"status": "success", "response": output_text, "task_id": task_id}
                else:
                    error_text = await response.text()
                    logger.error(f"Task {task_id} Failed: Ollama {response.status}")
                    return {"status": "failed", "error": error_text[:500], "task_id": task_id}
    except asyncio.TimeoutError:
        logger.error(f"Task {task_id} timed out (600s)")
        return {"status": "failed", "error": "Inference timed out after 600s", "task_id": task_id}
    except Exception as e:
        logger.error(f"Task {task_id} Exception: {e}")
        return {"status": "failed", "error": str(e), "task_id": task_id}


async def handle_job(ws, job_data):
    """Run a job in the background and send the result back.
    
    This runs as a separate asyncio task so it does NOT block the 
    WebSocket message loop. The agent can still respond to heartbeats 
    and other messages while the inference is running.
    """
    result = await execute_task(job_data)
    try:
        # Use ensure_ascii=False so Gujarati, Hindi, Chinese, etc. are sent as-is
        payload = json.dumps({"type": "job_result", "result": result}, ensure_ascii=False)
        await ws.send_str(payload)
        logger.info(f"Result for Task {result.get('task_id')} sent successfully")
    except Exception as e:
        logger.error(f"Failed to send result for Task {result.get('task_id')}: {e}")


async def agent_loop():
    """Main Agent Loop: Connects to Server, Registers, and Handles Tasks."""
    models = await check_ollama_status()
    if not models:
        logger.warning("No models found or Ollama not running. Agent will start but can't run jobs.")

    logger.info(f"Starting agent with NODE_ID={NODE_ID}")

    while True:
        try:
            async with aiohttp.ClientSession() as session:
                async with session.ws_connect(SERVER_URL, heartbeat=20) as ws:
                    logger.info(f"Connected to Server at {SERVER_URL}")

                    # 1. Register
                    register_msg = {
                        "type": "register",
                        "node_id": NODE_ID,
                        "gpu_info": {
                            "provider": "Ollama-Local",
                            "models": models,
                            "platform": platform.platform()
                        }
                    }
                    await ws.send_str(json.dumps(register_msg, ensure_ascii=False))

                    # 2. Listen for messages (this loop NEVER blocks on long tasks)
                    async for msg in ws:
                        if msg.type == aiohttp.WSMsgType.TEXT:
                            data = json.loads(msg.data)
                            msg_type = data.get("type")

                            if msg_type == "registered":
                                logger.info(f"✅ Node registered successfully as {NODE_ID}")
                            elif msg_type == "job_dispatch":
                                # CRITICAL: Run as background task — do NOT await here
                                asyncio.create_task(handle_job(ws, data.get("job_data")))
                            elif msg_type == "ping":
                                await ws.send_str(json.dumps({"type": "pong"}))

                        elif msg.type == aiohttp.WSMsgType.ERROR:
                            logger.error(f"WebSocket error: {ws.exception()}")
                            break
                        elif msg.type in (aiohttp.WSMsgType.CLOSE, aiohttp.WSMsgType.CLOSING, aiohttp.WSMsgType.CLOSED):
                            logger.warning("WebSocket closed by server")
                            break

        except aiohttp.ClientError as e:
            logger.error(f"Connection failed: {e}")
        except Exception as e:
            logger.error(f"Unexpected error: {e}")

        logger.info("Reconnecting in 5 seconds...")
        await asyncio.sleep(5)


if __name__ == "__main__":
    print(f"""
╔══════════════════════════════════════════╗
║       GPU Connect Agent v1.1            ║
║                                          ║
║  Node ID:  {NODE_ID:<28} ║
║  Server:   {SERVER_URL:<28} ║
║  Ollama:   {OLLAMA_URL:<28} ║
╚══════════════════════════════════════════╝
""")
    try:
        asyncio.run(agent_loop())
    except KeyboardInterrupt:
        logger.info("Agent stopped by user")
