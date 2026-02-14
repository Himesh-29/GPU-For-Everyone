import asyncio
import json
import logging
import os
import uuid
import getpass
import aiohttp
import platform

# Configuration
SERVER_URL = os.environ.get("SERVER_URL", "ws://localhost:8000/ws/computing/")
API_URL = os.environ.get("API_URL", "http://localhost:8000")
OLLAMA_URL = os.environ.get("OLLAMA_URL", "http://localhost:11434")
NODE_ID = os.environ.get("NODE_ID", f"node-{uuid.uuid4().hex[:8]}")

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("GPU-Agent")


async def authenticate(username: str, password: str) -> str | None:
    """Authenticate against the platform and return JWT access token."""
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{API_URL}/api/core/token/",
                json={"username": username, "password": password}
            ) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    logger.info(f"✅ Authenticated as '{username}'")
                    return data.get("access")
                else:
                    error = await resp.text()
                    logger.error(f"❌ Authentication failed: {error}")
                    return None
    except Exception as e:
        logger.error(f"❌ Could not reach server: {e}")
        return None


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
    """Run a job in the background and send the result back."""
    result = await execute_task(job_data)
    try:
        payload = json.dumps({"type": "job_result", "result": result}, ensure_ascii=False)
        await ws.send_str(payload)
        logger.info(f"Result for Task {result.get('task_id')} sent successfully")
    except Exception as e:
        logger.error(f"Failed to send result for Task {result.get('task_id')}: {e}")


async def agent_loop(auth_token: str):
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

                    # 1. Register with auth token
                    register_msg = {
                        "type": "register",
                        "node_id": NODE_ID,
                        "auth_token": auth_token,
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
                                owner = data.get("owner", "unknown")
                                logger.info(f"✅ Node registered as {NODE_ID} (owner: {owner})")
                            elif msg_type == "auth_error":
                                logger.error(f"❌ Authentication rejected: {data.get('error')}")
                                return  # Stop agent — token invalid
                            elif msg_type == "job_dispatch":
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


def main():
    print(f"""
╔══════════════════════════════════════════════════╗
║           GPU Connect Agent v2.0                ║
║                                                  ║
║  Node ID:  {NODE_ID:<36} ║
║  Server:   {API_URL:<36} ║
║  Ollama:   {OLLAMA_URL:<36} ║
╚══════════════════════════════════════════════════╝
""")

    # --- CLI Authentication ---
    print("  Login to GPU Connect to start earning credits.\n")
    username = input("  Username: ").strip()
    password = getpass.getpass("  Password: ").strip()

    if not username or not password:
        print("  ❌ Username and password are required.")
        return

    token = asyncio.run(authenticate(username, password))
    if not token:
        print("\n  ❌ Login failed. Check credentials and try again.")
        return

    print(f"\n  ✅ Logged in as '{username}'. Starting GPU agent...\n")

    try:
        asyncio.run(agent_loop(token))
    except KeyboardInterrupt:
        logger.info("Agent stopped by user")


if __name__ == "__main__":
    main()
