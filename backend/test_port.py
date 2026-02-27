import socket

def test_port(port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            s.bind(("127.0.0.1", port))
            print(f"✅ Port {port} is available and can be bound.")
        except Exception as e:
            print(f"❌ Port {port} cannot be bound: {e}")

if __name__ == "__main__":
    test_port(8000)
