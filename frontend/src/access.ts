import router from '@/router'

/**
 * 全局权限校验（简化版，移除登录检查）
 */
router.beforeEach(async (to, from, next) => {
  next()
})
