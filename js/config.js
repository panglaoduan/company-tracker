/**
 * config.js
 * 前端配置常量：公司映射、分类映射、情绪映射
 */

const COMPANIES = {
    tesla:            { name: '特斯拉',      color: '#e82127' },
    spacex:           { name: 'SpaceX',      color: '#1a1a2e' },
    ast_spacemobile:  { name: 'AST 太空',    color: '#0066cc' },
    xiaomi:           { name: '小米',        color: '#ff6900' },
    horizon_robotics: { name: '地平线',      color: '#00aa44' },
    ganli_pharma:     { name: '甘李药业',    color: '#9b27af' },
};

const CATEGORIES = {
    strategy:    { name: '经营战略', icon: '📈', color: '#2196f3', bg: '#e3f2fd' },
    executive:   { name: '高管动态', icon: '👔', color: '#9c27b0', bg: '#f3e5f5' },
    competition: { name: '行业竞争', icon: '⚔️', color: '#ff5722', bg: '#fbe9e7' },
    earnings:    { name: '财报发布', icon: '📋', color: '#4caf50', bg: '#e8f5e9' },
    volatility:  { name: '股价异动', icon: '⚡', color: '#ff9800', bg: '#fff3e0' },
    social:      { name: '社媒观点', icon: '📺', color: '#e91e8c', bg: '#fce4f3' },
};

const SENTIMENTS = {
    positive: { name: '正面', color: '#22a06b' },
    negative: { name: '负面', color: '#e5483c' },
    neutral:  { name: '中性', color: '#888'    },
};
