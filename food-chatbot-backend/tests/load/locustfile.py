"""
Load Testing Suite for Food Chatbot Backend

This module uses Locust for load testing the chatbot API.

Run with:
    locust -f tests/load/locustfile.py --host=http://localhost:8000

Or headless:
    locust -f tests/load/locustfile.py --host=http://localhost:8000 --users 100 --spawn-rate 10 --run-time 5m --headless
"""

import random
import string
import json
from locust import HttpUser, task, between, events
from locust.runners import MasterRunner


# Sample test data
SAMPLE_MESSAGES = [
    "Tìm quán ăn Nhật ở quận 1",
    "Có quán phở nào ngon không?",
    "Gợi ý quán ăn chay giá rẻ",
    "Nhà hàng hải sản quận 7",
    "Quán cafe view đẹp",
    "Địa chỉ quán bún bò Huế ngon",
    "Tìm quán buffet BBQ",
    "Quán lẩu Thái ở Thủ Đức",
    "Nhà hàng Hàn Quốc gần đây",
    "Quán ăn sáng ngon ở quận 3",
    "Tìm quán bún chả cá",
    "Địa điểm ăn uống cho gia đình",
    "Quán nhậu có phòng riêng",
    "Nhà hàng Ý ở quận 2",
    "Quán ăn vặt buổi tối",
    "Where can I find good pho?",
    "Best Japanese restaurant in District 1",
    "Cheap vegetarian food near me",
    "Korean BBQ recommendations",
    "Best coffee shop with nice view",
]

SAMPLE_FEEDBACK = [
    "Rất hữu ích, cảm ơn!",
    "Gợi ý tốt",
    "Cần cải thiện thêm",
    "Chính xác lắm!",
    "Không đúng lắm với yêu cầu",
]


def generate_session_id():
    """Generate a random session ID."""
    return "".join(random.choices(string.ascii_lowercase + string.digits, k=32))


def generate_user_id():
    """Generate a random user ID."""
    return f"loadtest-{random.randint(1000, 9999)}"


class ChatbotUser(HttpUser):
    """
    Simulates a typical chatbot user behavior.
    
    User flow:
    1. Check health endpoint
    2. Create a new session
    3. Send multiple chat messages
    4. View session history
    5. Optionally submit feedback
    """
    
    wait_time = between(1, 5)  # Wait 1-5 seconds between tasks
    
    def on_start(self):
        """Called when a simulated user starts."""
        self.session_id = None
        self.user_id = generate_user_id()
        self.message_count = 0
        
    @task(1)
    def check_health(self):
        """Check the health endpoint."""
        with self.client.get("/health", catch_response=True, name="/health") as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Health check failed: {response.status_code}")
    
    @task(2)
    def check_ready(self):
        """Check the readiness endpoint."""
        with self.client.get("/ready", catch_response=True, name="/ready") as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Ready check failed: {response.status_code}")
    
    @task(10)
    def send_chat_message(self):
        """Send a chat message and get a response."""
        message = random.choice(SAMPLE_MESSAGES)
        
        payload = {
            "message": message,
            "user_id": self.user_id,
        }
        
        if self.session_id:
            payload["session_id"] = self.session_id
        
        with self.client.post(
            "/api/chat",
            json=payload,
            catch_response=True,
            name="/api/chat"
        ) as response:
            if response.status_code == 200:
                try:
                    data = response.json()
                    # Store session_id for subsequent requests
                    if "session_id" in data:
                        self.session_id = data["session_id"]
                    self.message_count += 1
                    response.success()
                except json.JSONDecodeError:
                    response.failure("Invalid JSON response")
            elif response.status_code == 429:
                # Rate limited - this is expected under load
                response.success()  # Don't count rate limits as failures
            else:
                response.failure(f"Chat failed: {response.status_code}")
    
    @task(5)
    def get_session_history(self):
        """Get session history if we have a session."""
        if not self.session_id:
            return
        
        with self.client.get(
            f"/api/sessions/{self.session_id}",
            catch_response=True,
            name="/api/sessions/{session_id}"
        ) as response:
            if response.status_code == 200:
                response.success()
            elif response.status_code == 404:
                # Session not found - might be cleaned up
                self.session_id = None
                response.success()
            else:
                response.failure(f"Get session failed: {response.status_code}")
    
    @task(3)
    def list_sessions(self):
        """List all sessions for the user."""
        with self.client.get(
            f"/api/sessions?user_id={self.user_id}",
            catch_response=True,
            name="/api/sessions"
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"List sessions failed: {response.status_code}")
    
    @task(2)
    def submit_feedback(self):
        """Submit feedback for a session."""
        if not self.session_id or self.message_count < 2:
            return
        
        payload = {
            "session_id": self.session_id,
            "rating": random.randint(1, 5),
            "feedback": random.choice(SAMPLE_FEEDBACK),
            "user_id": self.user_id,
        }
        
        with self.client.post(
            "/api/feedback",
            json=payload,
            catch_response=True,
            name="/api/feedback"
        ) as response:
            if response.status_code in [200, 201]:
                response.success()
            elif response.status_code == 400:
                # Already submitted feedback
                response.success()
            else:
                response.failure(f"Feedback failed: {response.status_code}")


class HeavyLoadUser(HttpUser):
    """
    Simulates a power user who sends many messages rapidly.
    Use this for stress testing.
    """
    
    wait_time = between(0.5, 2)
    weight = 2  # 2x weight compared to normal users
    
    def on_start(self):
        """Called when a simulated user starts."""
        self.session_id = None
        self.user_id = generate_user_id()
        
    @task(20)
    def rapid_chat(self):
        """Send chat messages rapidly."""
        message = random.choice(SAMPLE_MESSAGES)
        
        payload = {
            "message": message,
            "user_id": self.user_id,
        }
        
        if self.session_id:
            payload["session_id"] = self.session_id
        
        with self.client.post(
            "/api/chat",
            json=payload,
            catch_response=True,
            name="/api/chat [heavy]"
        ) as response:
            if response.status_code == 200:
                try:
                    data = response.json()
                    if "session_id" in data:
                        self.session_id = data["session_id"]
                    response.success()
                except json.JSONDecodeError:
                    response.failure("Invalid JSON response")
            elif response.status_code == 429:
                # Rate limiting is working correctly
                response.success()
            else:
                response.failure(f"Rapid chat failed: {response.status_code}")
    
    @task(5)
    def health_check(self):
        """Rapid health checks."""
        self.client.get("/health", name="/health [heavy]")


class StreamingUser(HttpUser):
    """
    Simulates a user using streaming responses.
    """
    
    wait_time = between(2, 8)
    weight = 1
    
    def on_start(self):
        """Called when a simulated user starts."""
        self.session_id = None
        self.user_id = generate_user_id()
    
    @task
    def streaming_chat(self):
        """Send a streaming chat request."""
        message = random.choice(SAMPLE_MESSAGES)
        
        payload = {
            "message": message,
            "user_id": self.user_id,
            "stream": True,
        }
        
        if self.session_id:
            payload["session_id"] = self.session_id
        
        with self.client.post(
            "/api/chat/stream",
            json=payload,
            catch_response=True,
            name="/api/chat/stream",
            stream=True
        ) as response:
            if response.status_code == 200:
                # Read streaming response
                content = b""
                for chunk in response.iter_content(chunk_size=1024):
                    content += chunk
                
                if content:
                    response.success()
                else:
                    response.failure("Empty streaming response")
            elif response.status_code == 404:
                # Streaming endpoint might not exist
                response.success()
            elif response.status_code == 429:
                response.success()
            else:
                response.failure(f"Streaming failed: {response.status_code}")


# ============================================================================
# Event Hooks for Test Reporting
# ============================================================================

@events.init.add_listener
def on_locust_init(environment, **kwargs):
    """Called when Locust is initialized."""
    if isinstance(environment.runner, MasterRunner):
        print("🚀 Load test initialized (Master)")
    else:
        print("🚀 Load test initialized")


@events.test_start.add_listener
def on_test_start(environment, **kwargs):
    """Called when the test starts."""
    print("=" * 60)
    print("📊 Starting load test for Food Chatbot Backend")
    print(f"   Target host: {environment.host}")
    print("=" * 60)


@events.test_stop.add_listener  
def on_test_stop(environment, **kwargs):
    """Called when the test stops."""
    print("=" * 60)
    print("📊 Load test completed")
    print("=" * 60)
    
    # Print summary statistics
    stats = environment.stats
    print(f"\n📈 Summary:")
    print(f"   Total requests: {stats.total.num_requests}")
    print(f"   Failures: {stats.total.num_failures}")
    print(f"   Avg response time: {stats.total.avg_response_time:.2f}ms")
    print(f"   Requests/s: {stats.total.current_rps:.2f}")
    
    if stats.total.num_failures > 0:
        failure_rate = (stats.total.num_failures / stats.total.num_requests) * 100
        print(f"   Failure rate: {failure_rate:.2f}%")


# ============================================================================
# Custom Shape for Staged Load Testing
# ============================================================================

from locust import LoadTestShape


class StagesShape(LoadTestShape):
    """
    A staged load test shape that increases users in steps.
    
    Stages:
    1. Warm-up: 10 users for 1 minute
    2. Ramp-up: Increase to 50 users over 2 minutes
    3. Sustained: 50 users for 3 minutes
    4. Peak: 100 users for 2 minutes
    5. Cool-down: Decrease to 10 users over 1 minute
    """
    
    stages = [
        {"duration": 60, "users": 10, "spawn_rate": 2},
        {"duration": 180, "users": 50, "spawn_rate": 5},
        {"duration": 360, "users": 50, "spawn_rate": 5},
        {"duration": 480, "users": 100, "spawn_rate": 10},
        {"duration": 540, "users": 10, "spawn_rate": 5},
    ]
    
    def tick(self):
        """Return the current user count and spawn rate."""
        run_time = self.get_run_time()
        
        for stage in self.stages:
            if run_time < stage["duration"]:
                return (stage["users"], stage["spawn_rate"])
        
        return None  # End test
