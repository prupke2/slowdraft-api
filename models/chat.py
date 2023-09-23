from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Query, Request

class SocketManager:
    def __init__(self):
        self.active_connections: List[(WebSocket, str)] = []

    async def connect(self, websocket: WebSocket, user: str):
        await websocket.accept(subprotocol="chat")
        self.active_connections.append((websocket, user))

    async def get_connected_users(self):
        user_list = []
        for connection in self.active_connections:
            user_list.append(connection[1])
        return user_list

    def disconnect(self, websocket: WebSocket, user: str):
        print(f"{user} disconnected.")
        try:
            self.active_connections.remove((websocket, user))
            print(f"Connection successfully closed for ({websocket}, {user}).")
        except Exception as e:
            print(f"Error closing connection for ({websocket}, {user}): {e}")
            pass
    async def broadcast_user_disconnect(self, user: str):
        user_list = await self.get_connected_users()
        response = {
            "user": user,
            "status": "disconnected",
            "users": user_list
        }
        print(f"response: {response}")
        await self.broadcast(response)

    async def broadcast(self, data):
        for connection in self.active_connections:
            try:
                print(f"connection: {connection}")
                await connection[0].send_json(data)
            except Exception as e:
                print(f"Error broadcasting to {connection[0]}: {e}")
                if connection in self.active_connections:
                    self.active_connections.remove(connection)
