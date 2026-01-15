// src/services/notificationService.ts

type MessageHandler = (data: any) => void;

class NotificationService {
  private socket: WebSocket | null = null;
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 10;
  private reconnectTimeout: number | null = null;
  private messageHandler: MessageHandler | null = null;

  connect(token: string, onMessage?: MessageHandler) {
    if (this.socket && (this.socket.readyState === WebSocket.OPEN || this.socket.readyState === WebSocket.CONNECTING)) {
      console.log("NotificationService: already connected or connecting");
      return;
    }

    this.messageHandler = onMessage || null;

    // ✅ PRODUCTION-SAFE WS URL (NO localhost)
    const protocol = window.location.protocol === "https:" ? "wss" : "ws";
    const baseUrl = `${protocol}://${window.location.host}/ws/activity/`;
    const url = `${baseUrl}?token=${token}`;

    console.log("NotificationService: connecting to", url);

    try {
      this.socket = new WebSocket(url);

      this.socket.onopen = () => {
        console.log("NotificationService: WebSocket connected");
        this.reconnectAttempts = 0;
      };

      this.socket.onmessage = (event: MessageEvent) => {
        try {
          const data = JSON.parse(event.data);
          if (this.messageHandler) {
            this.messageHandler(data);
          }
        } catch (err) {
          console.error("NotificationService: invalid message", err);
        }
      };

      this.socket.onerror = (event) => {
        console.error("NotificationService: WebSocket error", event);
      };

      this.socket.onclose = () => {
        console.warn("NotificationService: WebSocket closed");
        this.socket = null;
        this.scheduleReconnect(token);
      };
    } catch (err) {
      console.error("NotificationService: failed to create WebSocket", err);
      this.scheduleReconnect(token);
    }
  }

  private scheduleReconnect(token: string) {
    if (this.reconnectAttempts >= this.maxReconnectAttempts) {
      console.error("NotificationService: max reconnect attempts reached");
      return;
    }

    const delay = Math.min(30000, Math.pow(2, this.reconnectAttempts) * 1000);
    this.reconnectAttempts += 1;

    console.log(`NotificationService: reconnecting in ${delay / 1000}s (attempt ${this.reconnectAttempts})`);

    if (this.reconnectTimeout) {
      window.clearTimeout(this.reconnectTimeout);
    }

    this.reconnectTimeout = window.setTimeout(() => {
      this.connect(token, this.messageHandler || undefined);
    }, delay);
  }

  disconnect() {
    if (this.socket) {
      console.log("NotificationService: disconnecting WebSocket");
      this.socket.close();
      this.socket = null;
    }

    if (this.reconnectTimeout) {
      window.clearTimeout(this.reconnectTimeout);
      this.reconnectTimeout = null;
    }

    this.reconnectAttempts = 0;
  }

  send(data: any) {
    if (this.socket && this.socket.readyState === WebSocket.OPEN) {
      this.socket.send(JSON.stringify(data));
    } else {
      console.warn("NotificationService: cannot send, socket not open");
    }
  }
}

export const notificationService = new NotificationService();
export default notificationService;

