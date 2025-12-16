import axios from 'axios';

// Get API URL from environment variable or use same origin (empty string for relative URLs)
// In production, both frontend and backend are served from same domain via ingress
const API_URL = import.meta.env.VITE_API_URL || '';

// Create axios instance
const api = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 30000, // 30 seconds timeout
});

/**
 * Send chat message to backend with streaming
 * @param {Array} messages - Array of message objects with role and content
 * @param {Function} onChunk - Callback function for each chunk received
 * @returns {Promise} Resolves when stream is complete
 */
export const sendChatMessageStream = async (messages, onChunk) => {
  try {
    console.log('Starting stream request to:', `${API_URL}/api/chat/stream`);

    const response = await fetch(`${API_URL}/api/chat/stream`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ messages }),
    });

    console.log('Stream response status:', response.status);

    if (!response.ok) {
      const errorText = await response.text();
      console.error('Stream error response:', errorText);
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    let buffer = '';

    console.log('Starting to read stream...');

    while (true) {
      const { done, value } = await reader.read();

      if (done) {
        console.log('Stream complete');
        break;
      }

      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split('\n');

      // Keep the last incomplete line in the buffer
      buffer = lines.pop() || '';

      for (const line of lines) {
        if (line.startsWith('data: ')) {
          try {
            const data = JSON.parse(line.slice(6));

            if (data.error) {
              console.error('Stream error:', data.error);
              throw new Error(data.error);
            }

            if (data.done) {
              console.log('Stream done signal received');
              return;
            }

            if (data.content) {
              console.log('Received chunk:', data.content);
              onChunk(data.content);
            }
          } catch (e) {
            if (e instanceof SyntaxError) {
              // Ignore JSON parse errors for incomplete chunks
              console.warn('JSON parse error, skipping line:', line);
              continue;
            }
            throw e;
          }
        }
      }
    }
  } catch (error) {
    console.error('Error sending chat message:', error);
    throw new Error('No response from server. Please check your connection.');
  }
};

/**
 * Send chat message to backend (non-streaming fallback)
 * @param {Array} messages - Array of message objects with role and content
 * @returns {Promise} Response from the API
 */
export const sendChatMessage = async (messages) => {
  try {
    const response = await api.post('/api/chat', { messages });
    return response.data;
  } catch (error) {
    console.error('Error sending chat message:', error);

    if (error.response) {
      // Server responded with error
      throw new Error(error.response.data.detail || 'Failed to get response from server');
    } else if (error.request) {
      // No response received
      throw new Error('No response from server. Please check your connection.');
    } else {
      // Other errors
      throw new Error('Failed to send message. Please try again.');
    }
  }
};

/**
 * Health check endpoint
 * @returns {Promise} Health status
 */
export const checkHealth = async () => {
  try {
    const response = await api.get('/api/health');
    return response.data;
  } catch (error) {
    console.error('Health check failed:', error);
    throw error;
  }
};

export default api;
