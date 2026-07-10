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
   */
  async probeDevice(ip, timeout = 800) {
    const commonPorts = [80, 443, 8080, 8443, 554, 8000, 8888]
    const foundPorts = []

    const probePromises = commonPorts.map(port => {
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
          // onerror 也表示端口开放（服务器返回了非图片内容）
          resolve(port)
        }

        img.src = `http://${ip}:${port}/favicon.ico?_=${Date.now()}`
      })
    })

    const results = await Promise.all(probePromises)
    return results.filter(p => p !== null)
  }

  /**
   * 扫描本地网络
   * @param {function} onDeviceFound - 发现设备时的回调
   * @param {function} onProgress - 进度回调
   */
  async scan(onDeviceFound, onProgress) {
    try {
      // 获取本地 IP
      onProgress({ status: 'detecting_ip' })
      this.localIP = await this.getLocalIP()

      if (!this.localIP) {
        throw new Error('无法获取本地 IP 地址')
      }

      this.subnet = this.getSubnet(this.localIP)
      onProgress({ status: 'scanning', localIP: this.localIP, subnet: this.subnet })

      // 扫描当前 IP（本机）
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

      // 分批扫描，每批 20 个 IP
      const batchSize = 20
      for (let i = 0; i < scanRange.length; i += batchSize) {
        const batch = scanRange.slice(i, i + batchSize)
        const progress = Math.round((i / scanRange.length) * 100)
        onProgress({ status: 'scanning', progress, current: i, total: scanRange.length })

        const batchResults = await Promise.all(
          batch.map(async (ip) => {
            if (ip === this.localIP || ip === gateway) return null
            try {
              const ports = await this.probeDevice(ip, 500)
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
              // 忽略错误
            }
            return null
          })
        )

        batchResults.filter(Boolean).forEach(device => onDeviceFound(device))
      }

      onProgress({ status: 'complete' })
      return true
    } catch (e) {
      onProgress({ status: 'error', message: e.message })
      return false
    }
  }
}

export default BrowserScanner
