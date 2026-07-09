import { ref, onMounted, onUnmounted } from 'vue'

export function useWebSocket() {
  const connected = ref(false)
  const clients = ref([])
  const scanProgress = ref(null)
  const lastMessage = ref(null)

  let ws = null
  let reconnectTimer = null
  let messageHandlers = []

  function connect() {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
    const host = window.location.host
    const url = `${protocol}//${host}/ws/frontend`

    ws = new WebSocket(url)

    ws.onopen = () => {
      connected.value = true
      console.log('[WS] Connected to frontend')
    }

    ws.onclose = () => {
      connected.value = false
      console.log('[WS] Disconnected')
      reconnectTimer = setTimeout(connect, 3000)
    }

    ws.onerror = (e) => {
      console.error('[WS] Error:', e)
    }

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data)
        lastMessage.value = data

        if (data.type === 'client_list') {
          clients.value = data.clients
        } else if (data.type === 'client_connected') {
          const existing = clients.value.find(c => c.client_id === data.client_id)
          if (!existing) {
            clients.value.push({ client_id: data.client_id, ...data.info })
          }
        } else if (data.type === 'client_disconnected') {
          clients.value = clients.value.filter(c => c.client_id !== data.client_id)
        } else if (data.type === 'client_info_update') {
          const client = clients.value.find(c => c.client_id === data.client_id)
          if (client) {
            if (data.device_count !== undefined) client.device_count = data.device_count
            if (data.online_count !== undefined) client.online_count = data.online_count
            if (data.version !== undefined) client.version = data.version
            if (data.is_online !== undefined) client.is_online = data.is_online
          }
        } else if (data.type === 'scan_progress') {
          scanProgress.value = data
        }

        messageHandlers.forEach(h => h(data))
      } catch (e) {
        console.error('[WS] Parse error:', e)
      }
    }
  }

  function disconnect() {
    if (reconnectTimer) {
      clearTimeout(reconnectTimer)
    }
    if (ws) {
      ws.close()
    }
  }

  function send(data) {
    if (ws && ws.readyState === WebSocket.OPEN) {
      ws.send(JSON.stringify(data))
    }
  }

  function requestScan(clientId, subnets = []) {
    send({
      type: 'scan_request',
      client_id: clientId,
      subnets: subnets
    })
  }

  function onMessage(handler) {
    messageHandlers.push(handler)
    return () => {
      messageHandlers = messageHandlers.filter(h => h !== handler)
    }
  }

  onMounted(() => {
    connect()
  })

  onUnmounted(() => {
    disconnect()
  })

  return {
    connected,
    clients,
    scanProgress,
    lastMessage,
    send,
    requestScan,
    onMessage,
    connect,
    disconnect
  }
}
