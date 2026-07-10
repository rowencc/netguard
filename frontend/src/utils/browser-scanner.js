/**
 * 浏览器本地网络扫描器
 * 通过 WebRTC 获取本地 IP，然后调用后端 API 执行真正的 ARP 扫描
 */

import api from '@/api'

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
   * 轮询扫描状态
   */
  async pollScanStatus(scanId, onProgress) {
    const maxPolls = 120 // 最多轮询 120 次 (约 2 分钟)
    const pollInterval = 1000 // 每秒轮询一次

    for (let i = 0; i < maxPolls; i++) {
      await new Promise(resolve => setTimeout(resolve, pollInterval))

      try {
        const response = await api.get(`/devices/scan-subnet/${scanId}`)
        const status = response.data

        if (status.status === 'complete') {
          return status
        } else if (status.status === 'error') {
          throw new Error(status.message || '扫描失败')
        }

        // 仍在运行中，更新进度
        const progress = Math.min(90, 10 + Math.round((i / maxPolls) * 80))
        onProgress({
          status: 'scanning',
          message: `正在扫描网络... (${i + 1}s)`,
          progress
        })
      } catch (e) {
        if (e.response && e.response.status === 404) {
          // 扫描ID还没创建，继续等待
          continue
        }
        throw e
      }
    }

    throw new Error('扫描超时')
  }

  /**
   * 扫描本地网络
   * 通过 WebRTC 获取本地 IP，然后调用后端 API 执行真正的 ARP 扫描
   * @param {function} onDeviceFound - 发现设备时的回调
   * @param {function} onProgress - 进度回调
   */
  async scan(onDeviceFound, onProgress) {
    try {
      // 获取本地 IP
      onProgress({ status: 'detecting_ip', message: '正在检测本地IP地址...' })
      this.localIP = await this.getLocalIP()

      console.log('[BrowserScanner] Detected local IP:', this.localIP)

      if (!this.localIP) {
        throw new Error('无法获取本地IP地址。请确保浏览器有WebRTC权限。')
      }

      this.subnet = this.getSubnet(this.localIP)
      const subnetCidr = `${this.subnet}.0/24`

      console.log('[BrowserScanner] Subnet:', this.subnet, 'CIDR:', subnetCidr)

      onProgress({
        status: 'scanning',
        localIP: this.localIP,
        subnet: this.subnet,
        message: `检测到本地网络: ${subnetCidr}，正在启动扫描...`,
        progress: 5
      })

      // 启动后端扫描（异步）
      console.log('[BrowserScanner] Calling /devices/scan-subnet...')
      const response = await api.post('/devices/scan-subnet', {
        subnet: subnetCidr,
        client_ip: this.localIP
      })

      console.log('[BrowserScanner] Scan started:', response.data)
      const { scan_id } = response.data

      onProgress({
        status: 'scanning',
        message: '网络扫描已启动，正在等待结果...',
        progress: 10
      })

      // 轮询扫描状态
      const result = await this.pollScanStatus(scan_id, onProgress)

      console.log('[BrowserScanner] Scan result:', result)

      onProgress({
        status: 'scanning',
        message: `扫描完成，正在加载设备列表...`,
        progress: 95
      })

      // 从数据库获取最新的设备列表
      const devicesResponse = await api.get('/devices/')
      const allDevices = devicesResponse.data

      console.log('[BrowserScanner] Total devices in DB:', allDevices.length)

      const subnetPrefix = this.subnet
      const scannedDevices = allDevices.filter(d =>
        d.ip_address.startsWith(subnetPrefix) &&
        d.scan_source === 'browser'
      )

      scannedDevices.forEach(device => {
        onDeviceFound({
          ip_address: device.ip_address,
          mac_address: device.mac_address,
          hostname: device.hostname || '',
          device_type: device.device_type || 'unknown',
          vendor: device.vendor || '',
          ports: [],
          source: 'browser'
        })
      })

      onProgress({
        status: 'complete',
        message: `扫描完成！发现 ${result.device_count} 台设备，新增 ${result.new_device_count} 台`
      })

      return true
    } catch (e) {
      console.error('[BrowserScanner] Error:', e)
      onProgress({ status: 'error', message: e.message || '扫描失败' })
      return false
    }
  }
}

export default BrowserScanner
