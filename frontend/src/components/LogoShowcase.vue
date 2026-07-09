<template>
  <div class="logo-showcase">
    <h2>Logo 设计方案</h2>
    
    <div class="logo-grid">
      <!-- 方案1: 雷达扫描 + 盾牌 -->
      <div class="logo-card">
        <div class="logo-preview dark">
          <svg viewBox="0 0 120 120" fill="none" xmlns="http://www.w3.org/2000/svg">
            <!-- 盾牌轮廓 -->
            <path d="M60 10L20 30V60C20 85 35 105 60 115C85 105 100 85 100 60V30L60 10Z" 
                  stroke="url(#grad1)" stroke-width="2" fill="none" opacity="0.3"/>
            <!-- 雷达波纹 -->
            <circle cx="60" cy="55" r="12" stroke="#6366f1" stroke-width="2" fill="none" opacity="0.4">
              <animate attributeName="r" values="12;25;12" dur="2s" repeatCount="indefinite"/>
              <animate attributeName="opacity" values="0.6;0;0.6" dur="2s" repeatCount="indefinite"/>
            </circle>
            <circle cx="60" cy="55" r="18" stroke="#6366f1" stroke-width="1.5" fill="none" opacity="0.3">
              <animate attributeName="r" values="18;35;18" dur="2s" repeatCount="indefinite" begin="0.3s"/>
              <animate attributeName="opacity" values="0.4;0;0.4" dur="2s" repeatCount="indefinite" begin="0.3s"/>
            </circle>
            <circle cx="60" cy="55" r="24" stroke="#6366f1" stroke-width="1" fill="none" opacity="0.2">
              <animate attributeName="r" values="24;45;24" dur="2s" repeatCount="indefinite" begin="0.6s"/>
              <animate attributeName="opacity" values="0.3;0;0.3" dur="2s" repeatCount="indefinite" begin="0.6s"/>
            </circle>
            <!-- 中心点 -->
            <circle cx="60" cy="55" r="4" fill="#6366f1"/>
            <!-- 扫描线 -->
            <line x1="60" y1="55" x2="60" y2="30" stroke="#6366f1" stroke-width="2" stroke-linecap="round">
              <animateTransform attributeName="transform" type="rotate" from="0 60 55" to="360 60 55" dur="3s" repeatCount="indefinite"/>
            </line>
            <!-- 网络节点 -->
            <circle cx="40" cy="35" r="3" fill="#22c55e" opacity="0.8"/>
            <circle cx="80" cy="35" r="3" fill="#22c55e" opacity="0.8"/>
            <circle cx="35" cy="65" r="3" fill="#f59e0b" opacity="0.8"/>
            <circle cx="85" cy="65" r="3" fill="#22c55e" opacity="0.8"/>
            <circle cx="45" cy="85" r="3" fill="#ef4444" opacity="0.8"/>
            <circle cx="75" cy="85" r="3" fill="#22c55e" opacity="0.8"/>
            <!-- 连接线 -->
            <line x1="40" y1="35" x2="60" y2="55" stroke="#6366f1" stroke-width="0.5" opacity="0.3"/>
            <line x1="80" y1="35" x2="60" y2="55" stroke="#6366f1" stroke-width="0.5" opacity="0.3"/>
            <line x1="35" y1="65" x2="60" y2="55" stroke="#6366f1" stroke-width="0.5" opacity="0.3"/>
            <line x1="85" y1="65" x2="60" y2="55" stroke="#6366f1" stroke-width="0.5" opacity="0.3"/>
            <defs>
              <linearGradient id="grad1" x1="20" y1="10" x2="100" y2="115">
                <stop offset="0%" stop-color="#6366f1"/>
                <stop offset="100%" stop-color="#8b5cf6"/>
              </linearGradient>
            </defs>
          </svg>
        </div>
        <p class="logo-name">方案1: 雷达守护</p>
      </div>

      <!-- 方案2: 眼睛 + 网络 -->
      <div class="logo-card">
        <div class="logo-preview dark">
          <svg viewBox="0 0 120 120" fill="none" xmlns="http://www.w3.org/2000/svg">
            <!-- 外圈 -->
            <circle cx="60" cy="60" r="45" stroke="#6366f1" stroke-width="2" fill="none" opacity="0.2"/>
            <circle cx="60" cy="60" r="38" stroke="#6366f1" stroke-width="1" fill="none" opacity="0.1"/>
            <!-- 眼睛轮廓 -->
            <path d="M15 60C15 60 35 30 60 30C85 30 105 60 105 60C105 60 85 90 60 90C35 90 15 60 15 60Z" 
                  stroke="url(#grad2)" stroke-width="2.5" fill="none"/>
            <!-- 瞳孔 -->
            <circle cx="60" cy="60" r="18" stroke="#6366f1" stroke-width="2" fill="none"/>
            <circle cx="60" cy="60" r="10" fill="url(#grad2)"/>
            <circle cx="60" cy="60" r="4" fill="#0a0a0f"/>
            <!-- 扫描线 -->
            <line x1="60" y1="15" x2="60" y2="42" stroke="#6366f1" stroke-width="1.5" stroke-linecap="round" opacity="0.6">
              <animateTransform attributeName="transform" type="rotate" from="0 60 60" to="360 60 60" dur="4s" repeatCount="indefinite"/>
            </line>
            <!-- 数据点 -->
            <circle cx="30" cy="40" r="2" fill="#22c55e">
              <animate attributeName="opacity" values="0.3;1;0.3" dur="1.5s" repeatCount="indefinite"/>
            </circle>
            <circle cx="90" cy="45" r="2" fill="#22c55e">
              <animate attributeName="opacity" values="0.3;1;0.3" dur="1.5s" repeatCount="indefinite" begin="0.5s"/>
            </circle>
            <circle cx="25" cy="70" r="2" fill="#f59e0b">
              <animate attributeName="opacity" values="0.3;1;0.3" dur="1.5s" repeatCount="indefinite" begin="1s"/>
            </circle>
            <circle cx="95" cy="75" r="2" fill="#22c55e">
              <animate attributeName="opacity" values="0.3;1;0.3" dur="1.5s" repeatCount="indefinite" begin="0.3s"/>
            </circle>
            <defs>
              <linearGradient id="grad2" x1="15" y1="30" x2="105" y2="90">
                <stop offset="0%" stop-color="#6366f1"/>
                <stop offset="50%" stop-color="#8b5cf6"/>
                <stop offset="100%" stop-color="#6366f1"/>
              </linearGradient>
            </defs>
          </svg>
        </div>
        <p class="logo-name">方案2: 全知之眼</p>
      </div>

      <!-- 方案3: 信号塔 + 波纹 -->
      <div class="logo-card">
        <div class="logo-preview dark">
          <svg viewBox="0 0 120 120" fill="none" xmlns="http://www.w3.org/2000/svg">
            <!-- 信号塔 -->
            <path d="M60 95V45" stroke="#6366f1" stroke-width="3" stroke-linecap="round"/>
            <path d="M50 45L60 25L70 45" stroke="#6366f1" stroke-width="2.5" fill="none" stroke-linecap="round" stroke-linejoin="round"/>
            <!-- 信号波纹 -->
            <path d="M40 55C40 55 50 40 60 40C70 40 80 55 80 55" stroke="#6366f1" stroke-width="2" fill="none" stroke-linecap="round" opacity="0.8">
              <animate attributeName="d" values="M40 55C40 55 50 40 60 40C70 40 80 55 80 55;M35 60C35 60 48 35 60 35C72 35 85 60 85 60;M40 55C40 55 50 40 60 40C70 40 80 55 80 55" dur="2s" repeatCount="indefinite"/>
              <animate attributeName="opacity" values="0.8;0.3;0.8" dur="2s" repeatCount="indefinite"/>
            </path>
            <path d="M30 65C30 65 45 25 60 25C75 25 90 65 90 65" stroke="#8b5cf6" stroke-width="1.5" fill="none" stroke-linecap="round" opacity="0.5">
              <animate attributeName="d" values="M30 65C30 65 45 25 60 25C75 25 90 65 90 65;M25 70C25 70 42 20 60 20C78 20 95 70 95 70;M30 65C30 65 45 25 60 25C75 25 90 65 90 65" dur="2s" repeatCount="indefinite" begin="0.3s"/>
              <animate attributeName="opacity" values="0.5;0.1;0.5" dur="2s" repeatCount="indefinite" begin="0.3s"/>
            </path>
            <path d="M20 75C20 75 40 15 60 15C80 15 100 75 100 75" stroke="#a78bfa" stroke-width="1" fill="none" stroke-linecap="round" opacity="0.3">
              <animate attributeName="d" values="M20 75C20 75 40 15 60 15C80 15 100 75 100 75;M15 80C15 80 38 10 60 10C82 10 105 80 105 80;M20 75C20 75 40 15 60 15C80 15 100 75 100 75" dur="2s" repeatCount="indefinite" begin="0.6s"/>
              <animate attributeName="opacity" values="0.3;0.05;0.3" dur="2s" repeatCount="indefinite" begin="0.6s"/>
            </path>
            <!-- 底座 -->
            <rect x="45" y="95" width="30" height="4" rx="2" fill="#6366f1" opacity="0.6"/>
            <!-- 监测点 -->
            <circle cx="45" cy="50" r="3" fill="#22c55e">
              <animate attributeName="r" values="3;4;3" dur="1s" repeatCount="indefinite"/>
            </circle>
            <circle cx="75" cy="50" r="3" fill="#22c55e">
              <animate attributeName="r" values="3;4;3" dur="1s" repeatCount="indefinite" begin="0.5s"/>
            </circle>
            <circle cx="35" cy="65" r="2.5" fill="#f59e0b"/>
            <circle cx="85" cy="65" r="2.5" fill="#22c55e"/>
          </svg>
        </div>
        <p class="logo-name">方案3: 信号监测</p>
      </div>

      <!-- 方案4: 盾牌 + 扫描 -->
      <div class="logo-card">
        <div class="logo-preview dark">
          <svg viewBox="0 0 120 120" fill="none" xmlns="http://www.w3.org/2000/svg">
            <!-- 盾牌主体 -->
            <path d="M60 15L25 32V58C25 82 40 102 60 112C80 102 95 82 95 58V32L60 15Z" 
                  fill="url(#grad4)" opacity="0.15"/>
            <path d="M60 15L25 32V58C25 82 40 102 60 112C80 102 95 82 95 58V32L60 15Z" 
                  stroke="url(#grad4)" stroke-width="2" fill="none"/>
            <!-- 扫描弧线 -->
            <path d="M40 50A25 25 0 0 1 80 50" stroke="#6366f1" stroke-width="2" fill="none" stroke-linecap="round">
              <animate attributeName="d" values="M40 50A25 25 0 0 1 80 50;M35 55A30 30 0 0 1 85 55;M40 50A25 25 0 0 1 80 50" dur="2s" repeatCount="indefinite"/>
            </path>
            <path d="M45 60A20 20 0 0 1 75 60" stroke="#8b5cf6" stroke-width="1.5" fill="none" stroke-linecap="round" opacity="0.6">
              <animate attributeName="d" values="M45 60A20 20 0 0 1 75 60;M42 63A23 23 0 0 1 78 63;M45 60A20 20 0 0 1 75 60" dur="2s" repeatCount="indefinite" begin="0.3s"/>
            </path>
            <!-- 盾牌中心 -->
            <circle cx="60" cy="55" r="8" fill="#6366f1" opacity="0.8"/>
            <circle cx="60" cy="55" r="4" fill="#0a0a0f"/>
            <!-- 检查标记 -->
            <path d="M52 55L58 61L68 49" stroke="#22c55e" stroke-width="2.5" fill="none" stroke-linecap="round" stroke-linejoin="round"/>
            <!-- 周围节点 -->
            <circle cx="35" cy="40" r="2.5" fill="#22c55e" opacity="0.7"/>
            <circle cx="85" cy="40" r="2.5" fill="#22c55e" opacity="0.7"/>
            <circle cx="30" cy="70" r="2" fill="#f59e0b" opacity="0.7"/>
            <circle cx="90" cy="70" r="2" fill="#22c55e" opacity="0.7"/>
            <!-- 连接线 -->
            <line x1="35" y1="40" x2="52" y2="50" stroke="#6366f1" stroke-width="0.5" opacity="0.3"/>
            <line x1="85" y1="40" x2="68" y2="50" stroke="#6366f1" stroke-width="0.5" opacity="0.3"/>
            <defs>
              <linearGradient id="grad4" x1="25" y1="15" x2="95" y2="112">
                <stop offset="0%" stop-color="#6366f1"/>
                <stop offset="100%" stop-color="#8b5cf6"/>
              </linearGradient>
            </defs>
          </svg>
        </div>
        <p class="logo-name">方案4: 安全守护</p>
      </div>
    </div>
  </div>
</template>

<style scoped>
.logo-showcase {
  padding: var(--space-xl);
}

h2 {
  font-family: var(--font-display);
  font-size: 24px;
  font-weight: 600;
  color: var(--color-ink);
  margin-bottom: var(--space-xl);
  text-align: center;
}

.logo-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: var(--space-lg);
}

.logo-card {
  background: var(--color-surface-1);
  border: 1px solid var(--color-hairline);
  border-radius: var(--radius-xl);
  overflow: hidden;
  transition: all var(--transition-base);
}

.logo-card:hover {
  transform: translateY(-4px);
  box-shadow: var(--shadow-lg);
  border-color: var(--color-primary);
}

.logo-preview {
  height: 200px;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: var(--space-lg);
}

.logo-preview.dark {
  background: linear-gradient(135deg, #0a0a0f 0%, #1a1a2e 100%);
}

.logo-preview svg {
  width: 120px;
  height: 120px;
}

.logo-name {
  padding: var(--space-md);
  text-align: center;
  font-size: 14px;
  font-weight: 500;
  color: var(--color-ink-muted);
  background: var(--color-surface-2);
}
</style>
