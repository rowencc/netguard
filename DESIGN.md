# NetGuard Design System

基于 Linear 设计系统构建，遵循 UI-UX-Pro-Max 原则。

## 设计原则

1. **深色优先** — 主题为深色画布 (#010102)，减少视觉疲劳
2. **紫蓝主色** — 使用 Linear lavender-blue (#5e6ad2) 作为唯一强调色
3. **层次分明** — 通过 surface 层级创建视觉深度
4. **简洁克制** — 避免装饰性元素，让内容说话

## 颜色系统

### 主色
| 名称 | 值 | 用途 |
|------|-----|------|
| Primary | #5e6ad2 | 主按钮、链接、强调 |
| Primary Hover | #828fff | 悬停状态 |
| Primary Focus | #5e69d1 | 聚焦状态 |

### 表面层级
| 层级 | 值 | 用途 |
|------|-----|------|
| Canvas | #010102 | 页面背景 |
| Surface 1 | #0f1011 | 卡片、面板 |
| Surface 2 | #141516 | 悬停卡片、表头 |
| Surface 3 | #18191a | 下拉菜单 |
| Surface 4 | #191a1b | 最高层级 |

### 文字颜色
| 名称 | 值 | 用途 |
|------|-----|------|
| Ink | #f7f8f8 | 主要文字 |
| Ink Muted | #d0d6e0 | 次要文字 |
| Ink Subtle | #8a8f98 | 辅助文字 |
| Ink Tertiary | #62666d | 禁用状态 |

### 语义色
| 名称 | 值 | 用途 |
|------|-----|------|
| Success | #27a644 | 成功状态 |
| Warning | #f59e0b | 警告状态 |
| Danger | #ef4444 | 危险状态 |

## 字体系统

### 字体族
- **Display**: Inter (SF Pro Display fallback)
- **Body**: Inter (SF Pro Text fallback)
- **Mono**: JetBrains Mono (SF Mono fallback)

### 字号层级
| Token | 大小 | 字重 | 行高 | 字间距 |
|-------|------|------|------|--------|
| Display | 28px | 600 | 1.2 | -0.6px |
| Headline | 20px | 600 | 1.3 | -0.3px |
| Body | 14px | 400 | 1.5 | 0 |
| Caption | 12px | 400 | 1.4 | 0 |
| Mono | 13px | 400 | 1.5 | 0 |

## 间距系统

基于 4px 网格：
| Token | 值 |
|-------|-----|
| xxs | 4px |
| xs | 8px |
| sm | 12px |
| md | 16px |
| lg | 24px |
| xl | 32px |
| xxl | 48px |

## 圆角系统

| Token | 值 | 用途 |
|-------|-----|------|
| xs | 4px | 小元素 |
| sm | 6px | 标签 |
| md | 8px | 按钮、输入框 |
| lg | 12px | 卡片 |
| xl | 16px | 大面板 |
| pill | 9999px | 药丸形状 |

## 组件规范

### 按钮
- **Primary**: 背景 #5e6ad2，文字白色，圆角 8px
- **Secondary**: 背景 Surface 2，边框 Hairline，圆角 8px
- **Ghost**: 透明背景，主色边框和文字

### 卡片
- 背景 Surface 1
- 1px Hairline 边框
- 圆角 12px
- 悬停时边框变为 Hairline Strong

### 标签
- 圆角 6px
- 根据类型使用语义色
- 字号 12px，字重 500

### 表格
- 表头背景 Surface 2
- 行悬停背景 Surface 2
- 分隔线使用 Hairline

## 响应式断点

| 断点 | 宽度 | 布局变化 |
|------|------|----------|
| Desktop XL | 1440px | 默认桌面布局 |
| Desktop | 1280px | 保持当前布局 |
| Tablet | 1024px | 卡片网格 2 列 |
| Mobile LG | 768px | 卡片网格 1 列，底部导航 |
| Mobile | 480px | 单列布局 |

## 移动端适配

- **底部导航栏**: 固定在底部，图标 + 文字
- **卡片列表**: 表格改为卡片布局
- **触摸目标**: 最小 44px 触摸区域
- **安全区域**: 适配 iPhone 刘海屏

## 动画规范

- **Fast**: 150ms - 按钮状态变化
- **Base**: 200ms - 卡片悬停
- **Slow**: 300ms - 页面过渡

## 交互原则

1. **即时反馈** — 所有操作都有视觉反馈
2. **渐进披露** — 复杂功能分步展示
3. **一致性** — 相同操作相同反馈
4. **容错性** — 允许撤销和重试
