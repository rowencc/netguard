/**
 * 浏览器本地网络扫描器
 * 通过 WebRTC 获取本地 IP，然后尝试探测局域网设备
 */

export class BrowserScanner {
  constructor() {
    this.localIP = null
    this.subnet = null
  }

  /**
   * 通过 WebRTC 获取本地 IP 地址
   */
  async getLocalIP() {
    return new Promise((resolve, reject) => {
      try {
        const pc = new RTCPeerConnection({ iceServers: [] })
        pc.createDataChannel('')
        pc.createOffer().then(offer => pc.setLocalDescription(offer))

        const ips = []
        pc.onicecandidate = (event) => {
          if (!event.candidate) {
            pc.close()
            // 选择非回环的 IPv4 地址
            const localIP = ips.find(ip => ip.startsWith('192.168.') || ip.startsWith('10.') || ip.startsWith('172.'))
            resolve(localIP || ips[0] || null)
            return
          }
          const candidate = event.candidate.candidate
          const ipMatch = candidate.match(/(\d+\.\d+\.\d+\.\d+)/)
          if (ipMatch && !ips.includes(ipMatch[1])) {
            ips.push(ipMatch[1])
          }
        }

        pc.onicecandidateerror = () => {
          pc.close()
          reject(new Error('Failed to get local IP'))
        }

        // 超时处理
        setTimeout(() => {
          pc.close()
          const localIP = ips.find(ip => ip.startsWith('192.168.') || ip.startsWith('10.') || ip.startsWith('172.'))
          resolve(localIP || ips[0] || null)
        }, 2000)
      } catch (e) {
        reject(e)
      }
    })
  }

  /**
   * 计算子网
   */
  getSubnet(ip) {
    const parts = ip.split('.')
    return `${parts[0]}.${parts[1]}.${parts[2]}`
  }

  /**
   * 通过探测常见端口来发现设备
   * 使用多种方法提高可靠性
   */
  async probeDevice(ip, timeout = 1000) {
    const commonPorts = [80, 443, 8080, 8443, 554, 8000, 8888]
    const foundPorts = []

    // Method 1: Image loading (works for HTTP servers)
    const imageProbePromises = commonPorts.map(port => {
      return new Promise((resolve) => {
        const img = new Image()
        const timer = setTimeout(() => {
          resolve(null)
        }, timeout)

        img.onload = () => {
          clearTimeout(timer)
          resolve(port)
        }
        img.onerror = () => {
          clearTimeout(timer)
          // onerror also indicates port is open (server returned non-image content)
          resolve(port)
        }

        img.src = `http://${ip}:${port}/favicon.ico?_=${Date.now()}`
      })
    })

    // Method 2: Fetch API with no-cors (more reliable for HTTPS)
    const fetchProbePromises = commonPorts.map(port => {
      return new Promise((resolve) => {
        const timer = setTimeout(() => {
          resolve(null)
        }, timeout)

        fetch(`http://${ip}:${port}/`, {
          method: 'HEAD',
          mode: 'no-cors',
          signal: AbortSignal.timeout(timeout)
        })
          .then(() => {
            clearTimeout(timer)
            resolve(port)
          })
          .catch(() => {
            clearTimeout(timer)
            resolve(null)
          })
      })
    })

    // Run both methods in parallel
    const [imageResults, fetchResults] = await Promise.all([
      Promise.all(imageProbePromises),
      Promise.all(fetchProbePromises)
    ])

    // Combine results
    const allPorts = new Set()
    imageResults.filter(Boolean).forEach(p => allPorts.add(p))
    fetchResults.filter(Boolean).forEach(p => allPorts.add(p))

    return Array.from(allPorts)
  }

  /**
   * 扫描本地网络
   * @param {function} onDeviceFound - 发现设备时的回调
   * @param {function} onProgress - 进度回调
   */
  async scan(onDeviceFound, onProgress) {
    try {
      // 获取本地 IP
      onProgress({ status: 'detecting_ip', message: '正在检测本地IP地址...' })
      this.localIP = await this.getLocalIP()

      if (!this.localIP) {
        throw new Error('无法获取本地IP地址。请确保浏览器有WebRTC权限。')
      }

      this.subnet = this.getSubnet(this.localIP)
      onProgress({ 
        status: 'scanning', 
        localIP: this.localIP, 
        subnet: this.subnet,
        message: `检测到本地网络: ${this.subnet}.0/24`
      })

      // 扫描当前 IP（本机）
      onProgress({ status: 'scanning', message: '正在扫描本机...', progress: 0 })
      const localPorts = await this.probeDevice(this.localIP)
      if (localPorts.length > 0) {
        onDeviceFound({
          ip_address: this.localIP,
          mac_address: '',
          hostname: window.location.hostname || '本机',
          device_type: 'computer',
          ports: localPorts,
          source: 'browser'
        })
      }

      // 扫描网关
      const gateway = `${this.subnet}.1`
      if (gateway !== this.localIP) {
        onProgress({ status: 'scanning', message: '正在扫描网关...', progress: 1 })
        const gatewayPorts = await this.probeDevice(gateway)
        if (gatewayPorts.length > 0) {
          onDeviceFound({
            ip_address: gateway,
            mac_address: '',
            hostname: 'gateway',
            device_type: 'router',
            ports: gatewayPorts,
            source: 'browser'
          })
        }
      }

      // 并行扫描子网中的常见 IP
      const scanRange = []
      for (let i = 2; i <= 254; i++) {
        scanRange.push(`${this.subnet}.${i}`)
      }

      // 分批扫描，每批 10 个 IP (smaller batch for better progress updates)
      const batchSize = 10
      const totalBatches = Math.ceil(scanRange.length / batchSize)
      
      for (let batchIndex = 0; batchIndex < totalBatches; batchIndex++) {
        const startIdx = batchIndex * batchSize
        const batch = scanRange.slice(startIdx, startIdx + batchSize)
        const progress = Math.round((batchIndex / totalBatches) * 100)
        
        onProgress({ 
          status: 'scanning', 
          progress, 
          current: startIdx + batch.length, 
          total: scanRange.length,
          message: `正在扫描第 ${batchIndex + 1}/${totalBatches} 批...`
        })

        const batchResults = await Promise.all(
          batch.map(async (ip) => {
            if (ip === this.localIP || ip === gateway) return null
            try {
              const ports = await this.probeDevice(ip, 800)
              if (ports.length > 0) {
                return {
                  ip_address: ip,
                  mac_address: '',
                  hostname: '',
                  device_type: 'unknown',
                  ports,
                  source: 'browser'
                }
              }
            } catch (e) {
              // Ignore errors for individual IPs
            }
            return null
          })
        )

        batchResults.filter(Boolean).forEach(device => onDeviceFound(device))
      }

      onProgress({ status: 'complete', message: '扫描完成' })
      return true
    } catch (e) {
      onProgress({ status: 'error', message: e.message })
      return false
    }
  }
}

export default BrowserScanner
