// C:\Users\Vinay\Project\frontend\src/services\notificationService.ts
// --- FINAL, RESILIENT VERSION ---

import { useAuthStore } from '@/stores/auth';
import { useToast } from 'vue-toastification';

class NotificationService {
  private socket: WebSocket | null = null;
  private isConnecting: boolean = false;

  // --- NEW: State for reconnection logic ---
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 10;
  private reconnectInterval = 1000; // Start with 1 second

  public connect(): void {
    const authStore = useAuthStore();
    console.log("Service: connect() called.");

    if (this.isConnecting || (this.socket && this.socket.readyState === WebSocket.OPEN)) {
      console.log("Service: Connection attempt ignored, already connecting or connected.");
      return;
    }

    // --- IMPROVEMENT: Use the authStore as the single source of truth ---
    if (!authStore.isAuthenticated || !authStore.authToken) {
      console.error("Service: No auth token found in store. Aborting.");
      return;
    }
    
    this.isConnecting = true;
    const baseUrl = import.meta.env.VITE_WS_BASE_URL || 'ws://localhost:8000/ws/';
    const url = `${baseUrl}activity/?token=${authStore.authToken}`;
    console.log(`Service: Attempting to connect to WebSocket at: ${url}`);

    this.socket = new WebSocket(url);

    this.socket.onopen = () => {
      console.log("✅ Service: WebSocket connection established successfully.");
      this.isConnecting = false;
      // --- NEW: Reset reconnect attempts on a successful connection ---
      this.resetReconnectState();
    };

    this.socket.onmessage = this.handleMessage.bind(this); // Use bound method for consistency

    this.socket.onclose = () => {
      console.warn("Service: WebSocket connection closed.");
      this.socket = null;
      this.isConnecting = false;
      // --- NEW: Instead of just stopping, schedule a reconnect attempt ---
      this.scheduleReconnect();
    };

    this.socket.onerror = (error) => {
      console.error("Service: WebSocket error:", error);
      this.isConnecting = false;
      // The 'onclose' event will usually fire after an error, triggering the reconnect.
    };
  }

  public disconnect(): void {
    if (this.socket) {
      console.log('Service: Manually disconnecting WebSocket.');
      // --- NEW: Prevent reconnection logic from firing on a manual disconnect ---
      this.socket.onclose = null; 
      this.socket.close();
      this.socket = null;
      this.isConnecting = false;
      this.resetReconnectState();
    }
  }

  // --- Private method for handling messages (your existing logic) ---
  private async handleMessage(event: MessageEvent): Promise<void> {
    try {
      const data = JSON.parse(event.data);
      const eventType = data.type;
      const payload = data.payload || data;
      
      if (!eventType) {
          console.warn("Service: Received malformed message, missing 'type'", data);
          return;
      }
      console.log(`Service: Received event type: '${eventType}'`, payload);
      
      switch (eventType) {
        case 'new_notification': {
          const { useNotificationStore } = await import('@/stores/notification');
          useNotificationStore().addLiveNotification(payload);
          break;
        }
        case 'new_post': {
          const { useFeedStore } = await import('@/stores/feed');
          useFeedStore().handleNewPostSignal(payload.id);
          break;
        }
        case 'post_deleted': {
          const postId = payload.post_id;
          if (!postId) {
            console.warn("Service: Received post_deleted event but missing post_id", payload);
            return;
          }
          console.log(`🚀 Service: Dispatching delete for post ID ${postId} to all stores.`);
          const { usePostsStore } = await import('@/stores/posts');
          const { useFeedStore } = await import('@/stores/feed');
          const { useProfileStore } = await import('@/stores/profile');
          const { useGroupStore } = await import('@/stores/group');
          usePostsStore().removePost(postId);
          useFeedStore().handlePostDeletedSignal(postId);
          useProfileStore().handlePostDeletedSignal(postId);
          useGroupStore().handlePostDeletedSignal(postId);
          break;
        }
        default:
          console.warn(`Service: Unhandled event type: '${eventType}'`);
      }
    } catch (e) {
        console.error("Service: Error processing message or importing store:", e);
    }
  }

  // --- NEW: Reconnection Logic Methods ---
  private scheduleReconnect(): void {
    if (this.reconnectAttempts >= this.maxReconnectAttempts) {
      console.error('Service: Max reconnect attempts reached. Giving up.');
      const toast = useToast();
      toast.error("Real-time connection failed. Please refresh the page.", { timeout: false });
      return;
    }

    const authStore = useAuthStore();
    if (!authStore.isAuthenticated) {
      console.log('Service: User is not authenticated. Aborting reconnect.');
      this.resetReconnectState();
      return;
    }
    
    this.reconnectAttempts++;
    const delay = Math.min(this.reconnectInterval * Math.pow(2, this.reconnectAttempts - 1), 30000);
    
    console.log(`Service: Reconnecting in ${delay / 1000} seconds (attempt ${this.reconnectAttempts})...`);

    setTimeout(() => {
      this.connect();
    }, delay);
  }

  private resetReconnectState(): void {
    this.reconnectAttempts = 0;
  }
}

export const notificationService = new NotificationService();