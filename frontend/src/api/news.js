import service from './index'

export const analyzeNews = payload => service.post('/api/news/analyze', payload)
