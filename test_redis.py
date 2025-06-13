import redis
from django.conf import settings

def test_redis_connection():
    try:
        # Test broker connection
        broker = redis.Redis(host='127.0.0.1', port=6379, db=0)
        broker.ping()
        print("Broker connection successful!")
        
        # Test result backend connection
        backend = redis.Redis(host='127.0.0.1', port=6379, db=1)
        backend.ping()
        print("Result backend connection successful!")
        
        # Test cache connection
        cache = redis.Redis(host='127.0.0.1', port=6379, db=1)
        cache.ping()
        print("Cache connection successful!")
        
    except redis.ConnectionError as e:
        print(f"Connection error: {e}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_redis_connection() 