/**
 * WebSocket context for managing real-time transaction and alert feeds
 * This lives at the app root so it's not affected by theme or other context changes
 */
import { createContext, useContext, useEffect, useRef, useState, useCallback, ReactNode } from 'react';
import { Transaction } from '../components/TransactionCard';
import { Alert } from '../components/AlertCard';

export interface WebSocketMessage {
  type: 'connected' | 'transaction' | 'alert' | 'stats' | 'heartbeat' | 'pong';
  timestamp: string;
  data?: any;
  channel?: string;
  message?: string;
}

interface WebSocketContextType {
  isConnected: boolean;
  isAlertsConnected: boolean;
  transactions: Transaction[];
  alerts: Alert[];
  stats: {
    totalToday: number;
    fraudDetected: number;
    amountBlocked: number;
    pendingAlerts: number;
  };
  updateAlertStatus: (alertId: string, newStatus: Alert['status']) => void;
}

const WebSocketContext = createContext<WebSocketContextType | undefined>(undefined);

const WS_TRANSACTIONS_URL = import.meta.env.VITE_WS_URL || 'ws://localhost:8000/api/v1/ws/transactions';
const WS_ALERTS_URL = import.meta.env.VITE_WS_ALERTS_URL || 'ws://localhost:8000/api/v1/ws/alerts';

function determinePriority(fraudScore: number, rulesCount: number): Alert['priority'] {
  if (fraudScore >= 90 || rulesCount >= 4) return 'critical';
  if (fraudScore >= 70 || rulesCount >= 3) return 'high';
  if (fraudScore >= 50 || rulesCount >= 2) return 'medium';
  return 'low';
}

export function WebSocketProvider({ children }: { children: ReactNode }) {
  const [isConnected, setIsConnected] = useState(false);
  const [isAlertsConnected, setIsAlertsConnected] = useState(false);
  const [transactions, setTransactions] = useState<Transaction[]>([]);
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [stats, setStats] = useState({
    totalToday: 0,
    fraudDetected: 0,
    amountBlocked: 0,
    pendingAlerts: 0,
  });

  // Transaction WebSocket refs
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const heartbeatIntervalRef = useRef<ReturnType<typeof setInterval> | null>(null);

  // Alerts WebSocket refs
  const wsAlertsRef = useRef<WebSocket | null>(null);
  const alertsReconnectTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const alertsHeartbeatIntervalRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const mountedRef = useRef(true);

  const updateAlertStatus = useCallback((alertId: string, newStatus: Alert['status']) => {
    setAlerts((prev) =>
      prev.map((alert) =>
        alert.id === alertId
          ? { ...alert, status: newStatus, updated_at: new Date().toISOString() }
          : alert
      )
    );
    // Update pending alerts count
    if (newStatus === 'resolved' || newStatus === 'false_positive') {
      setStats((prev) => ({
        ...prev,
        pendingAlerts: Math.max(0, prev.pendingAlerts - 1),
      }));
    }
  }, []);

  const handleTransactionMessage = useCallback((message: WebSocketMessage) => {
    if (message.type === 'transaction' && message.data) {
      const txn: Transaction = {
        ...message.data,
        timestamp: message.timestamp,
      };

      // Add to transactions list (keep last 50)
      setTransactions((prev) => [txn, ...prev].slice(0, 50));

      // Update stats
      setStats((prev) => ({
        totalToday: prev.totalToday + 1,
        fraudDetected: txn.is_fraud ? prev.fraudDetected + 1 : prev.fraudDetected,
        amountBlocked: txn.is_blocked
          ? prev.amountBlocked + txn.amount
          : prev.amountBlocked,
        pendingAlerts: txn.is_fraud ? prev.pendingAlerts + 1 : prev.pendingAlerts,
      }));
    }
  }, []);

  const handleAlertMessage = useCallback((message: WebSocketMessage) => {
    if (message.type === 'alert' && message.data) {
      const newAlert: Alert = {
        id: message.data.id || `alert-${Date.now()}`,
        transaction_id: message.data.transaction_id,
        user_id: message.data.user_id,
        amount: message.data.amount,
        merchant_name: message.data.merchant_name,
        fraud_score: message.data.fraud_score,
        triggered_rules: message.data.triggered_rules || [],
        explanation: message.data.explanation,
        status: 'new',
        priority: determinePriority(message.data.fraud_score, message.data.triggered_rules?.length || 0),
        created_at: message.timestamp,
      };

      // Add to alerts list (keep last 100)
      setAlerts((prev) => [newAlert, ...prev].slice(0, 100));
    }
  }, []);

  const connectTransactions = useCallback(() => {
    if (!mountedRef.current || wsRef.current?.readyState === WebSocket.OPEN) {
      return;
    }

    // Clean up existing connection
    if (wsRef.current) {
      wsRef.current.onopen = null;
      wsRef.current.onmessage = null;
      wsRef.current.onerror = null;
      wsRef.current.onclose = null;
      if (wsRef.current.readyState === WebSocket.OPEN || wsRef.current.readyState === WebSocket.CONNECTING) {
        wsRef.current.close();
      }
    }

    try {
      const ws = new WebSocket(WS_TRANSACTIONS_URL);

      ws.onopen = () => {
        if (!mountedRef.current) {
          ws.close();
          return;
        }
        console.log('WebSocket connected:', WS_TRANSACTIONS_URL);
        setIsConnected(true);

        // Start heartbeat
        heartbeatIntervalRef.current = setInterval(() => {
          if (ws.readyState === WebSocket.OPEN) {
            ws.send('ping');
          }
        }, 30000);
      };

      ws.onmessage = (event) => {
        if (!mountedRef.current) return;

        try {
          const message: WebSocketMessage = JSON.parse(event.data);
          handleTransactionMessage(message);
        } catch (error) {
          console.error('Error parsing WebSocket message:', error);
        }
      };

      ws.onerror = (error) => {
        if (!mountedRef.current) return;
        console.error('WebSocket error:', error);
      };

      ws.onclose = () => {
        if (!mountedRef.current) return;

        console.log('WebSocket disconnected:', WS_TRANSACTIONS_URL);
        setIsConnected(false);

        // Clear heartbeat
        if (heartbeatIntervalRef.current) {
          clearInterval(heartbeatIntervalRef.current);
          heartbeatIntervalRef.current = null;
        }

        // Attempt reconnect
        if (mountedRef.current) {
          reconnectTimeoutRef.current = setTimeout(() => {
            if (mountedRef.current) {
              connectTransactions();
            }
          }, 5000);
        }
      };

      wsRef.current = ws;
    } catch (error) {
      console.error('Error creating WebSocket:', error);
    }
  }, [handleTransactionMessage]);

  const connectAlerts = useCallback(() => {
    if (!mountedRef.current || wsAlertsRef.current?.readyState === WebSocket.OPEN) {
      return;
    }

    // Clean up existing connection
    if (wsAlertsRef.current) {
      wsAlertsRef.current.onopen = null;
      wsAlertsRef.current.onmessage = null;
      wsAlertsRef.current.onerror = null;
      wsAlertsRef.current.onclose = null;
      if (wsAlertsRef.current.readyState === WebSocket.OPEN || wsAlertsRef.current.readyState === WebSocket.CONNECTING) {
        wsAlertsRef.current.close();
      }
    }

    try {
      const ws = new WebSocket(WS_ALERTS_URL);

      ws.onopen = () => {
        if (!mountedRef.current) {
          ws.close();
          return;
        }
        console.log('WebSocket connected:', WS_ALERTS_URL);
        setIsAlertsConnected(true);

        // Start heartbeat
        alertsHeartbeatIntervalRef.current = setInterval(() => {
          if (ws.readyState === WebSocket.OPEN) {
            ws.send('ping');
          }
        }, 30000);
      };

      ws.onmessage = (event) => {
        if (!mountedRef.current) return;

        try {
          const message: WebSocketMessage = JSON.parse(event.data);
          handleAlertMessage(message);
        } catch (error) {
          console.error('Error parsing alerts WebSocket message:', error);
        }
      };

      ws.onerror = (error) => {
        if (!mountedRef.current) return;
        console.error('Alerts WebSocket error:', error);
      };

      ws.onclose = () => {
        if (!mountedRef.current) return;

        console.log('Alerts WebSocket disconnected:', WS_ALERTS_URL);
        setIsAlertsConnected(false);

        // Clear heartbeat
        if (alertsHeartbeatIntervalRef.current) {
          clearInterval(alertsHeartbeatIntervalRef.current);
          alertsHeartbeatIntervalRef.current = null;
        }

        // Attempt reconnect
        if (mountedRef.current) {
          alertsReconnectTimeoutRef.current = setTimeout(() => {
            if (mountedRef.current) {
              connectAlerts();
            }
          }, 5000);
        }
      };

      wsAlertsRef.current = ws;
    } catch (error) {
      console.error('Error creating Alerts WebSocket:', error);
    }
  }, [handleAlertMessage]);

  useEffect(() => {
    mountedRef.current = true;
    connectTransactions();
    connectAlerts();

    return () => {
      mountedRef.current = false;

      // Clean up transactions WebSocket
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
      }
      if (heartbeatIntervalRef.current) {
        clearInterval(heartbeatIntervalRef.current);
      }
      if (wsRef.current) {
        wsRef.current.onopen = null;
        wsRef.current.onmessage = null;
        wsRef.current.onerror = null;
        wsRef.current.onclose = null;
        wsRef.current.close();
      }

      // Clean up alerts WebSocket
      if (alertsReconnectTimeoutRef.current) {
        clearTimeout(alertsReconnectTimeoutRef.current);
      }
      if (alertsHeartbeatIntervalRef.current) {
        clearInterval(alertsHeartbeatIntervalRef.current);
      }
      if (wsAlertsRef.current) {
        wsAlertsRef.current.onopen = null;
        wsAlertsRef.current.onmessage = null;
        wsAlertsRef.current.onerror = null;
        wsAlertsRef.current.onclose = null;
        wsAlertsRef.current.close();
      }
    };
  }, []); // Empty deps - only run once on mount

  return (
    <WebSocketContext.Provider value={{ isConnected, isAlertsConnected, transactions, alerts, stats, updateAlertStatus }}>
      {children}
    </WebSocketContext.Provider>
  );
}

export function useTransactionFeed() {
  const context = useContext(WebSocketContext);
  if (context === undefined) {
    throw new Error('useTransactionFeed must be used within a WebSocketProvider');
  }
  return context;
}
