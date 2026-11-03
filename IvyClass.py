from ivy.ivy import IvyServer
class IvyAgent(IvyServer):

    def __init__(self, event_queue,IVY_BUS = "127.255.255.255:2010"):
        self.IVY_BUS = IVY_BUS
        super().__init__("PygameWhiteboard")
        self.event_queue = event_queue

        # Messages reçus depuis le moteur de fusion
        self.bind_msg(
            self.on_create,
            r"^PALETTE_CREATE shape=(\w+) color=(\w+) x=(\d+) y=(\d+)$"
        )

        self.bind_msg(
            self.on_move,
            r"^PALETTE_MOVE id=(\d+) x=(\d+) y=(\d+)$"
        )

        self.bind_msg(
            self.on_clear,
            r"^PALETTE_CLEAR$"
        )

        # Connexion au bus Ivy
        self.start(IVY_BUS)

        print(f"[IVY] Connected to {IVY_BUS}")

    def on_create(self, agent, shape, color, x, y):
        self.event_queue.put({
            "type": "create",
            "shape": shape,
            "color": color,
            "x": int(x),
            "y": int(y),
        })

    def on_move(self, agent, object_id, x, y):
        self.event_queue.put({
            "type": "move",
            "id": int(object_id),
            "x": int(x),
            "y": int(y),
        })

    def on_clear(self, agent):
        self.event_queue.put({"type": "clear"})

    def send(self, message):
        self.send_msg(message)
        print(f"[IVY TX] {message}")
