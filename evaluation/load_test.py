import uuid
import random
from locust import HttpUser, task, between

# Due to nature of application and limitations of DB (SQLlite)
# we need to assign random id to threads and pick random questions

QUESTIONS = [
    "Where is my car?"  #  chatbot agent static
    "How do I book a parking spot?"  # chatbot agent static
    "What are the parking rates?"  # chatbot agent dynamic
    "I want to reserve a spot."  # reservation agent
]


class ChatbotUser(HttpUser):
    wait_time = between(2, 5)

    @task
    def ask_question(self):

        question = random.choice(QUESTIONS)

        unique_thread_id = str(uuid.uuid4())

        payload = {"message": question, "thread_id": f"locust-test-{unique_thread_id}"}

        with self.client.post("/chat", json=payload, catch_response=True) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Failed with status {response.status_code}")
